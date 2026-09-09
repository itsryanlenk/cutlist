"""Shared helpers for the cutlist toolkit.

Every tool in this folder imports from this file.
Python 3.9 or newer. Standard library only.
"""

import json
import math
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# Windows searches the working directory for a bare program name before PATH. The folder
# the agent opens holds files from a recorder or a guest, so a planted ffprobe.exe there
# would run with the creator's rights. This variable turns that search off, and tool_path()
# below never looks there anyway.
os.environ.setdefault("NoDefaultCurrentDirectoryInExePath", "1")

# Limits on untrusted input. A caption file comes from a recorder or a third party, a plan
# is written by the agent after reading it, so a script must never hang or exhaust memory
# on either. See SECURITY.md.
CAPTION_MAX_BYTES = 50 * 1024 * 1024  # a two-hour episode is well under 1 MB
CUE_MAX_CHARS = 2000                   # one cue is a sentence or two
PLAN_MAX_BYTES = 5 * 1024 * 1024       # a plan is tens of kilobytes
TIME_MAX_S = 100 * 3600                # no clip lives past hour 100; larger values feed float tricks
RUN_TIMEOUT_S = 900                    # the longest legitimate ffmpeg call is a six-hour audio extract

# Local files only. A playlist or index hidden inside a media file cannot reach the network
# or another protocol through ffmpeg when this precedes its -i. probe() separately refuses
# the playlist formats themselves, because a local playlist can still name other local files.
FF_IN = ["-protocol_whitelist", "file"]
REFUSED_FORMATS = {"hls", "applehttp", "concat", "dash", "sdp", "rtp", "rtsp", "lavfi"}


def utf8_stdout():
    """Print UTF-8 regardless of the console code page.

    Agents run these scripts with stdout piped. On Windows that pipe defaults to the
    locale code page, and one speaker name outside it would raise mid-report.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

_TS_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?$")


def parse_time(text):
    """Turn 'HH:MM:SS,mmm', 'HH:MM:SS.mmm', 'MM:SS', or plain seconds into float seconds.

    Rejects anything that is not a finite time between 0 and TIME_MAX_S: 'nan' and 'inf'
    parse as floats, and a value near 1e18 makes t + step == t, so a loop never ends.
    """
    text = str(text).strip()
    try:
        value = float(text)
    except ValueError:
        m = _TS_RE.match(text)
        if not m:
            raise ValueError("Bad time value: %r" % text)
        h = int(m.group(1)[:9]) if m.group(1) else 0
        mnt = int(m.group(2))
        s = int(m.group(3))
        ms_txt = m.group(4) or "0"
        ms = int(ms_txt.ljust(3, "0"))
        value = h * 3600 + mnt * 60 + s + ms / 1000.0
    if not math.isfinite(value) or value < 0:
        raise ValueError("Bad time value: %r (must be a finite, non-negative time)" % text)
    if value > TIME_MAX_S:
        raise ValueError("Bad time value: %r (past hour %d)" % (text, TIME_MAX_S // 3600))
    return value


def fmt_time(seconds, ms=True):
    """Float seconds -> 'HH:MM:SS.mmm' (or 'HH:MM:SS' when ms=False)."""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    mnt = int((seconds % 3600) // 60)
    s = seconds % 60
    if ms:
        return "%02d:%02d:%06.3f" % (h, mnt, s)
    return "%02d:%02d:%02d" % (h, mnt, int(s))


def fmt_mmss(seconds):
    """Float seconds -> 'MM:SS' (minutes may exceed 59)."""
    seconds = max(0.0, float(seconds))
    return "%02d:%02d" % (int(seconds // 60), int(seconds % 60))


# ---------------------------------------------------------------------------
# Text hygiene for untrusted caption text
# ---------------------------------------------------------------------------

# ASCII controls and ANSI escape sequences can drive the terminal the agent prints into.
_ASCII_CTRL_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-Z\\-_]|[\x00-\x08\x0b-\x1f\x7f]")
_NON_ASCII_RE = re.compile(r"[^\x00-\x7f]+")
# Every format, control, private-use, and surrogate character (zero-width joiners, bidi
# overrides, soft hyphens, the U+E0000 tag block used to smuggle text past a human reader),
# plus the invisible marks the categories miss: combining grapheme joiner, variation
# selectors, and the Hangul fillers. None of them are speech.
_DROP_CATEGORIES = {"Cf", "Cc", "Co", "Cs"}
_DROP_EXTRA = {0x034F, 0x115F, 0x1160, 0x3164, 0xFFA0}


def _scrub_non_ascii(m):
    out = []
    for ch in m.group():
        cp = ord(ch)
        cat = unicodedata.category(ch)
        if cat in ("Zl", "Zp"):
            out.append(" ")
            continue
        if cat in _DROP_CATEGORIES or cp in _DROP_EXTRA or 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
            continue
        out.append(ch)
    return "".join(out)


def clean_text(text):
    """Strip control characters, ANSI escapes, and every invisible or format character."""
    text = _ASCII_CTRL_RE.sub("", text)
    text = _NON_ASCII_RE.sub(_scrub_non_ascii, text)
    return text.replace("\t", " ")


def csv_safe(cell):
    """Prefix a cell a spreadsheet would run as a formula (=, +, -, @ first)."""
    s = str(cell)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


_INJECTION_RE = re.compile(
    r"ignore (?:all |any )?(?:previous|prior|above|earlier) (?:instructions|prompts|rules)"
    r"|\byou are now\b|\bsystem prompt\b|\bas an ai\b|\bdo not tell the (?:user|creator)\b"
    r"|\b(?:curl|wget|rm -rf|sudo|powershell|invoke-webrequest)\b|https?://",
    re.I,
)


def injection_flags(text):
    """Return the instruction-like phrases, commands, or links found in caption text.

    Captions are attacker-authored input that the agent reads in full. This does not
    block anything; it lets check_inputs.py tell the creator which cues to look at.
    """
    return [m.group(0) for m in _INJECTION_RE.finditer(str(text))]


# ---------------------------------------------------------------------------
# SRT / VTT parsing
# ---------------------------------------------------------------------------

_SPEAKER_RE = re.compile(r"^\s*([^\W\d_][\w .'-]{0,40}?)\s*:\s+(.*)$", re.S)
_VOICE_RE = re.compile(r"^<v\s+([^>]{1,200})>(.*)$", re.S)
_TAG_RE = re.compile(r"<[^<>]{0,200}>")  # bounded, so an unclosed '<' run stays linear


def _read_caption_text(path):
    p = Path(path)
    size = p.stat().st_size
    if size > CAPTION_MAX_BYTES:
        raise ValueError("Caption file is too large (%d MB; the limit is %d MB). Is this really a caption file?" % (
            size // (1024 * 1024), CAPTION_MAX_BYTES // (1024 * 1024)))
    data = p.read_bytes()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        # Some Windows editors save SRT as UTF-16. Decode it instead of reporting "no cues".
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8-sig", errors="replace")


def parse_captions(path):
    """Parse an .srt or .vtt caption file into a list of dicts.

    Each dict: {"index", "start", "end", "speaker", "text"}.
    Speaker is taken from a leading 'Name: ' pattern (or a WebVTT <v Name> tag)
    when present, else ''. Raises ValueError for a file this tool will not read.
    """
    raw = _read_caption_text(path)
    raw = clean_text(raw.replace("\r\n", "\n"))
    blocks = re.split(r"\n\s*\n", raw.strip())
    cues = []
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines or lines[0].startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        if len(lines) < 2:
            continue
        # Line 0 may be the index, line 1 the time range. Tolerate a missing index.
        time_line = lines[1] if "-->" in lines[1] else lines[0]
        if "-->" not in time_line:
            continue
        text_start = 2 if "-->" in lines[1] else 1
        left, right = [p.strip() for p in time_line.split("-->")[:2]]
        right = right.split(" ")[0]  # drop position tags like X1:0
        try:
            start = parse_time(left)
            end = parse_time(right)
        except ValueError:
            continue
        text = " ".join(lines[text_start:]).strip()[:CUE_MAX_CHARS]
        speaker = ""
        v = _VOICE_RE.match(text)  # WebVTT voice tag
        if v:
            speaker, text = v.group(1).strip(), v.group(2).strip()
        text = _TAG_RE.sub("", text)  # strip html-like tags
        m = _SPEAKER_RE.match(text)
        if m:
            speaker, text = m.group(1).strip(), m.group(2).strip()
        idx = lines[0] if text_start == 2 else ""
        cues.append({"index": idx, "start": start, "end": end, "speaker": speaker, "text": text})
    return cues


# ---------------------------------------------------------------------------
# Plan JSON (written by the agent after it has read untrusted text)
# ---------------------------------------------------------------------------

def load_plan(path):
    """Read clip_plan.json and check its shape. Raises ValueError for anything else.

    Guarantees on return: a dict; plan["episode"] is a dict; plan["clips"] is a list of
    dicts; episode.cold_open and episode.thumbnail are dicts when present.
    """
    p = Path(path)
    size = p.stat().st_size
    if size > PLAN_MAX_BYTES:
        raise ValueError("Plan file is too large (%d bytes; the limit is %d). A plan is tens of kilobytes." % (
            size, PLAN_MAX_BYTES))
    try:
        plan = json.loads(p.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("Plan is not valid JSON: %s" % exc)
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object at the top level")
    ep = plan.get("episode", {})
    if not isinstance(ep, dict):
        raise ValueError("'episode' must be an object")
    clips = plan.get("clips", [])
    if not isinstance(clips, list) or not all(isinstance(c, dict) for c in clips):
        raise ValueError("'clips' must be a list of objects")
    for key in ("cold_open", "thumbnail"):
        if ep.get(key) is not None and not isinstance(ep[key], dict):
            raise ValueError("'episode.%s' must be an object" % key)
    plan["episode"] = ep
    plan["clips"] = clips
    return plan


# ---------------------------------------------------------------------------
# Programs and fonts: resolved from fixed places, never from the working folder
# ---------------------------------------------------------------------------

def tool_path(name):
    """Absolute path of a program found on PATH, or None.

    Walks PATH itself and skips empty, '.', and relative entries, so a file in the folder
    the agent opened can never be what runs.
    """
    exts = [""]
    if os.name == "nt":
        exts = [e.lower() for e in os.environ.get("PATHEXT", ".EXE;.COM;.BAT;.CMD").split(os.pathsep) if e] + [""]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        entry = entry.strip().strip('"')
        if not entry or entry == os.curdir or not os.path.isabs(entry):
            continue
        for ext in exts:
            cand = os.path.join(entry, name + ext)
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return os.path.abspath(cand)
    return None


def require_tool(name):
    """Return the absolute path of a required program, or exit with the install line."""
    path = tool_path(name)
    if path is None:
        sys.exit(
            "Missing tool: %s. Install it first.\n"
            "  macOS:   brew install ffmpeg\n"
            "  Windows: winget install Gyan.FFmpeg\n"
            "  Linux:   sudo apt install ffmpeg\n" % name
        )
    return path


def run(cmd, quiet=False, timeout=RUN_TIMEOUT_S):
    """Run a program, return stdout text. Exit on failure or timeout.

    A bare program name is resolved through tool_path() first. Output is decoded as UTF-8
    (ffprobe writes UTF-8 JSON whatever the console code page says).
    """
    cmd = [str(c) for c in cmd]
    if cmd and os.sep not in cmd[0] and "/" not in cmd[0]:
        cmd[0] = require_tool(cmd[0])
    try:
        proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        sys.exit("Command timed out after %d s: %s" % (timeout, os.path.basename(cmd[0])))
    if proc.returncode != 0:
        if not quiet:
            sys.stderr.write(proc.stderr)
        sys.exit("Command failed: %s" % " ".join(cmd))
    return proc.stdout


def media_path(path):
    """Absolute path string for ffmpeg. It never starts with '-', so it is never read as an option."""
    return os.path.abspath(str(path))


def probe(video):
    """Return {"duration", "width", "height", "fps"} for a media file.

    Refuses playlist and stream-index formats (HLS, DASH, concat, SDP): a text file with a
    video's name can point those demuxers at any other local file.
    """
    out = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", *FF_IN, media_path(video),
    ])
    try:
        data = json.loads(out)
    except ValueError:
        sys.exit("ffprobe returned no readable information for %s" % video)
    fmt = data.get("format", {}) if isinstance(data, dict) else {}
    names = {n.strip() for n in str(fmt.get("format_name", "")).lower().split(",")}
    if names & REFUSED_FORMATS:
        sys.exit("Refusing %s: ffprobe reads it as a playlist or stream index (%s), which can pull in other "
                 "files. Point the scripts at the media file itself." % (video, ",".join(sorted(names & REFUSED_FORMATS))))
    try:
        duration = float(fmt.get("duration", 0.0))
    except (TypeError, ValueError):
        duration = 0.0
    if not math.isfinite(duration) or duration < 0:
        duration = 0.0
    info = {"duration": duration, "width": None, "height": None, "fps": None}
    streams = data.get("streams", []) if isinstance(data, dict) else []
    for st in streams:
        if isinstance(st, dict) and st.get("codec_type") == "video" and info["width"] is None:
            info["width"] = st.get("width")
            info["height"] = st.get("height")
            rate = str(st.get("avg_frame_rate", "0/1"))
            try:
                num, den = rate.split("/")
                info["fps"] = round(float(num) / float(den), 3) if float(den) else None
            except (ValueError, ZeroDivisionError):
                info["fps"] = None
    return info


def _font_dirs():
    home = Path.home()
    if os.name == "nt":
        dirs = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
                Path(os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))) / "Microsoft" / "Windows" / "Fonts"]
    elif sys.platform == "darwin":
        dirs = [Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
                Path("/Library/Fonts"), home / "Library" / "Fonts"]
    else:
        dirs = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), home / ".fonts", home / ".local" / "share" / "fonts"]
    return [d for d in dirs if d.is_dir()]


def find_font(candidates):
    """Absolute path of the first font found in the system font folders, or None.

    Pillow would otherwise try a bare name against the working folder first, and a font
    file is parsed by FreeType, which is not a parser to point at a guest's files.
    """
    dirs = _font_dirs()
    for cand in candidates:
        c = Path(cand)
        if c.is_absolute():
            if c.is_file():
                return str(c)
            continue
        for d in dirs:
            direct = d / c
            if direct.is_file():
                return str(direct.resolve())
        for d in dirs:
            for p in d.rglob(c.name):
                if p.is_file():
                    return str(p.resolve())
    return None


# Backward-compatible alias.
parse_srt = parse_captions
