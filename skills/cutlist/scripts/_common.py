"""Shared helpers for the cutlist toolkit.

Every tool in this folder imports from this file.
Python 3.9 or newer. Standard library only.
"""

import json
import math
import os
import re
import stat
import subprocess
import sys
import tempfile
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
CAPTION_MAX_BYTES = 10 * 1024 * 1024  # a two-hour episode is well under 1 MB; parsing costs about 20x the file
CUE_MAX_CHARS = 2000                   # one cue is a sentence or two
CUES_MAX = 100_000                     # ten cues a second for three hours; anything more is not a caption file
ASPECT_MAX = 8.0                       # wider or taller than this is not a video
PLAN_MAX_BYTES = 5 * 1024 * 1024       # a plan is tens of kilobytes
CLIPS_MAX = 200                        # a plan has 5 to 8 clips; the validator is quadratic on overlaps
ORDER_MAX = 999                        # publish_order names a file
TIME_MAX_S = 100 * 3600                # no clip lives past hour 100; larger values feed float tricks
RUN_TIMEOUT_S = 900                    # the longest legitimate ffmpeg call is a six-hour audio extract

# What ffmpeg and ffprobe may open. The format whitelist is checked after format detection
# and before the header is parsed, so a playlist, an index, or a script named like a video
# is refused up front; the protocol whitelist keeps anything inside a file from reaching
# the network or another protocol. probe() checks the reported format name as a second layer.
MEDIA_FORMATS = "mov,mp4,m4a,3gp,3g2,mj2,matroska,webm,avi,mpegts,mpeg,mxf,asf,flv,wav,aiff,mp3,aac,flac,ogg"
FF_IN = ["-format_whitelist", MEDIA_FORMATS, "-protocol_whitelist", "file"]
# Our own frame tiles. -f image2 names the demuxer (ffmpeg would pick jpeg_pipe for a tiny
# JPEG and then reject the option), and -pattern_type none stops it from expanding a %d in
# the path into a sequence and reading a sibling folder's files.
FF_IN_IMG = ["-f", "image2", "-format_whitelist", "image2", "-protocol_whitelist", "file",
             "-pattern_type", "none"]


def check_source(width, height):
    """Refuse a source with no picture or with a shape no video has."""
    if not width or not height:
        raise ValueError("The video has no readable picture size. Is it a video?")
    if width / height > ASPECT_MAX or height / width > ASPECT_MAX:
        raise ValueError("The video is %dx%d, which is not a video shape." % (width, height))


# ffmpeg's image muxer expands %d in an output path (so a folder named ep%d would send a
# frame to ep1/). -update 1 makes it write one file to the literal path instead.
IMG_OUT = ["-update", "1"]
REFUSED_FORMATS = {"hls", "applehttp", "concat", "dash", "sdp", "rtp", "rtsp", "lavfi", "imf", "avisynth", "image2"}


def refused_formats(format_name):
    """The playlist, index, and script format names present in an ffprobe format_name."""
    names = {n.strip() for n in str(format_name).lower().split(",")}
    return names & REFUSED_FORMATS


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
    # Decide once per distinct character, then translate in C: a 50 MB run of one letter
    # costs the run twice, never a list of fifty million one-character strings.
    s = m.group()
    table = {}
    for ch in set(s):
        cp = ord(ch)
        cat = unicodedata.category(ch)
        if cat in ("Zl", "Zp"):
            table[cp] = " "
        elif cat in _DROP_CATEGORIES or cp in _DROP_EXTRA or 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
            table[cp] = None
    return s.translate(table) if table else s


def show(path):
    """A path as one printable line: no bidi override, no escape, and no line break, so a
    folder name can never forge a status line in the output."""
    return clean_text(str(path)).replace("\n", "\\n")


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
    r"(?:ignore|disregard|forget)\s+(?:all\s+|any\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules)"
    r"|\byou\s+are\s+now\b|\bsystem\s+prompt\b|\bas\s+an\s+ai\b|\bdo\s+not\s+tell\s+the\s+(?:user|creator)\b"
    r"|\b(?:curl|wget|rm\s+-rf|sudo|powershell|invoke-webrequest)\b|https?://",
    re.I,
)
# A speaker label that names a chat role is a caption pretending to be a conversation turn.
ROLE_LABELS = {"system", "assistant", "user", "developer", "instruction", "instructions", "tool", "function"}


def normalize_for_match(text):
    """Fold fullwidth and compatibility forms and drop combining marks, so a lookalike
    spelling matches the plain one. Used for flagging only, never for the text itself."""
    text = unicodedata.normalize("NFKC", str(text))
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def injection_flags(text):
    """Return the instruction-like phrases, commands, or links found in caption text.

    Captions are attacker-authored input that the agent reads in full. This does not
    block anything; it lets check_inputs.py tell the creator which cues to look at.
    Lookalike letters from another alphabet are not caught; the flag is a help, not a gate.
    """
    return [m.group(0) for m in _INJECTION_RE.finditer(normalize_for_match(text))]


def is_role_label(label):
    """True when a speaker label names a chat role, after normalization."""
    return normalize_for_match(label).strip().lower() in ROLE_LABELS


# ---------------------------------------------------------------------------
# SRT / VTT parsing
# ---------------------------------------------------------------------------

_SPEAKER_RE = re.compile(r"^\s*([^\W\d_][\w .'-]{0,40}?)\s*:\s+(.*)$", re.S)
_VOICE_RE = re.compile(r"^<v\s+([^>]{1,200})>(.*)$", re.S)
_TAG_RE = re.compile(r"<[^<>]{0,200}>")  # bounded, so an unclosed '<' run stays linear


def read_bounded(path, limit, what):
    """Read a regular file of at most `limit` bytes. Raises ValueError otherwise.

    A device, a pipe, or a symlink to one reports a size of zero and then never ends, so
    the size alone is not a bound: the type is checked and the read itself is capped.
    """
    p = Path(path)
    refuse_link(p)  # a caption, plan, or marker file reached through a link is someone else's file
    st = p.stat()
    if not stat.S_ISREG(st.st_mode):
        raise ValueError("%s is not a regular file. %s must be a plain file." % (show(p), what))
    if st.st_size > limit:
        raise ValueError("%s is too large (%d bytes; the limit is %d). Is this really %s?" % (
            show(p), st.st_size, limit, what.lower()))
    with open(p, "rb") as fh:
        data = fh.read(limit + 1)
    if len(data) > limit:
        raise ValueError("%s is too large (over %d bytes)." % (show(p), limit))
    return data


def _read_caption_text(path):
    data = read_bounded(path, CAPTION_MAX_BYTES, "A caption file")
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
        if len(cues) >= CUES_MAX:
            raise ValueError("More than %d cues. That is not a caption file for one video." % CUES_MAX)
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
    data = read_bounded(path, PLAN_MAX_BYTES, "A plan file")
    try:
        plan = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise ValueError("Plan is not valid JSON: %s" % str(exc)[:200])
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object at the top level")
    ep = plan.get("episode", {})
    if not isinstance(ep, dict):
        raise ValueError("'episode' must be an object")
    clips = plan.get("clips", [])
    if not isinstance(clips, list) or not all(isinstance(c, dict) for c in clips):
        raise ValueError("'clips' must be a list of objects")
    if len(clips) > CLIPS_MAX:
        raise ValueError("%d clips; a plan has 5 to 8 and the limit is %d" % (len(clips), CLIPS_MAX))
    for key in ("cold_open", "thumbnail"):
        if ep.get(key) is not None and not isinstance(ep[key], dict):
            raise ValueError("'episode.%s' must be an object" % key)
    plan["episode"] = ep
    plan["clips"] = clips
    return plan


def order_number(clip):
    """publish_order (or rank) as a whole number from 1 to ORDER_MAX. It names a file."""
    v = clip.get("publish_order", clip.get("rank"))
    bad = ValueError("publish_order must be a whole number from 1 to %d" % ORDER_MAX)
    if v is None or isinstance(v, bool):
        raise bad
    if isinstance(v, float):
        if not v.is_integer():
            raise bad
        v = int(v)
    if not isinstance(v, int):
        try:
            v = int(str(v).strip())
        except (TypeError, ValueError):
            raise bad
    if not 1 <= v <= ORDER_MAX:
        raise bad
    return v


# ---------------------------------------------------------------------------
# Output files: never written through a link, always replaced whole
# ---------------------------------------------------------------------------
# A bundle can carry a file named like one of our outputs (transcript_compact.txt,
# thumb_mock.png, previews/) as a hard link, a symlink, or a junction pointing at the
# creator's source recording. Opening that name for writing would truncate the source.
# So every output is refused if the name is any kind of link, written to a fresh temp
# file beside it, and moved into place with os.replace, which swaps the directory entry.

_NAME_SURROGATE = 0x20000000  # set on every reparse tag that redirects a name (symlink, junction)
_LINK_TAGS = {getattr(stat, "IO_REPARSE_TAG_SYMLINK", 0xA000000C), getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)}


def refuse_link(path):
    """Raise ValueError when path exists as a symlink, a junction, or a multiply linked file.

    Only name-redirecting reparse points count: a cloud placeholder (OneDrive, Dropbox) is a
    reparse point too, and a previous output that was dehydrated is still ours.
    """
    path = Path(path)
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return
    tag = getattr(st, "st_reparse_tag", 0)
    if stat.S_ISLNK(st.st_mode) or tag in _LINK_TAGS or (tag & _NAME_SURROGATE):
        raise ValueError("%s is a link. Remove it; the scripts never write through links." % show(path))
    if stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
        raise ValueError("%s has more than one hard link. Remove it; the scripts never write through links." % show(path))


def temp_target(path):
    """A fresh temp file beside path, carrying path's suffix, for a program or Pillow to fill."""
    path = Path(path)
    refuse_link(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".cutlist-", suffix=path.suffix)
    os.close(fd)
    return Path(tmp)


def commit_target(tmp, path):
    """Move a finished temp file onto path. The old entry is unlinked, never written into.

    When the move fails (a directory or a read-only file under that name), the temp file is
    removed too, so a failure never leaves a copy of the output under a random name.
    """
    try:
        refuse_link(path)
        os.replace(str(tmp), str(path))
    except BaseException:
        try:
            Path(tmp).unlink()
        except OSError:
            pass
        raise


def run_writing(cmd, tmp):
    """run(), but remove the temp output when the program fails or times out."""
    try:
        return run(cmd)
    except BaseException:
        try:
            Path(tmp).unlink()
        except OSError:
            pass
        raise


def write_bytes_safely(path, data):
    """Write data to path through a temp file and a replace."""
    tmp = temp_target(path)
    try:
        tmp.write_bytes(data)
        commit_target(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def output_dir(video, name):
    """<episode folder>/<name>, created if missing, refused if the name is a link of any kind."""
    base = Path(os.path.abspath(str(video))).parent
    d = base / name
    refuse_link(d)
    d.mkdir(exist_ok=True)
    real = d.resolve()
    if real.parent != base.resolve():
        raise ValueError("%s is not inside the episode folder" % show(d))
    return real


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
        # Native binaries only. A .bat or .cmd shim would run through cmd.exe, which reads
        # metacharacters out of our arguments, and a file name is one of our arguments.
        exts = [".exe", ".com"]
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
        sys.exit("Command timed out after %d s: %s" % (timeout, show(os.path.basename(cmd[0]))))
    if proc.returncode != 0:
        if not quiet:
            # The program's own message can quote a file name; a name can carry a line break.
            sys.stderr.write("\n".join(show(line) for line in proc.stderr.splitlines()) + "\n")
        sys.exit("Command failed: %s" % " ".join(show(c) for c in cmd))
    return proc.stdout


def as_int(value):
    """A positive int from an ffprobe field, or None. ffprobe writes ints, but a field is a field."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def media_path(path):
    """Absolute path string for ffmpeg. It never starts with '-', so it is never read as an option."""
    return os.path.abspath(str(path))


def probe(video):
    """Return {"duration", "width", "height", "fps"} for a media file.

    Refuses playlist and stream-index formats (HLS, DASH, concat, SDP): a text file with a
    video's name can point those demuxers at any other local file. Refuses anything that is
    not a regular file, so a device or a pipe cannot hold ffprobe open.
    """
    try:
        st = os.stat(media_path(video))
    except OSError as exc:
        sys.exit("Cannot read %s: %s" % (show(video), exc.strerror or exc))
    if not stat.S_ISREG(st.st_mode):
        sys.exit("%s is not a regular file. The video must be a plain file." % show(video))
    out = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", *FF_IN, media_path(video),
    ])
    try:
        data = json.loads(out)
    except ValueError:
        sys.exit("ffprobe returned no readable information for %s" % show(video))
    fmt = data.get("format", {}) if isinstance(data, dict) else {}
    refused = refused_formats(fmt.get("format_name", ""))
    if refused:
        sys.exit("Refusing %s: ffprobe reads it as a playlist, index, or script (%s), which can pull in other "
                 "files. Point the scripts at the media file itself." % (show(video), ",".join(sorted(refused))))
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
            info["width"] = as_int(st.get("width"))
            info["height"] = as_int(st.get("height"))
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
