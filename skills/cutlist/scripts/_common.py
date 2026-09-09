"""Shared helpers for the podcast clipper toolkit.

Every tool in this folder imports from this file.
Python 3.9 or newer. Standard library only.
"""

import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Limits on untrusted input. A caption file comes from a recorder or a third party,
# so a script must never hang or exhaust memory on one. See SECURITY.md.
CAPTION_MAX_BYTES = 50 * 1024 * 1024  # a two-hour episode is well under 1 MB
CUE_MAX_CHARS = 2000                   # one cue is a sentence or two

# Local files only. A playlist or index hidden inside a media file cannot reach the
# network or another protocol through ffmpeg when this precedes its -i.
FF_IN = ["-protocol_whitelist", "file"]

# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

_TS_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?$")


def parse_time(text):
    """Turn 'HH:MM:SS,mmm', 'HH:MM:SS.mmm', 'MM:SS', or plain seconds into float seconds.

    Rejects anything that is not a finite, non-negative time: 'nan' and 'inf' parse
    as floats, then pass every range check and reach ffmpeg as garbage.
    """
    text = str(text).strip()
    try:
        value = float(text)
    except ValueError:
        m = _TS_RE.match(text)
        if not m:
            raise ValueError("Bad time value: %r" % text)
        h = int(m.group(1) or 0)
        mnt = int(m.group(2))
        s = int(m.group(3))
        ms_txt = m.group(4) or "0"
        ms = int(ms_txt.ljust(3, "0"))
        value = h * 3600 + mnt * 60 + s + ms / 1000.0
    if not math.isfinite(value) or value < 0:
        raise ValueError("Bad time value: %r (must be a finite, non-negative time)" % text)
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

# ANSI escape sequences (CSI and two-byte escapes) can drive the terminal the agent
# prints into. C0/C1 controls, zero-width, bidi override, and BOM characters can hide
# words from a human reader while a model still reads them. None of them are speech.
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-Z\\-_]")
_INVISIBLE_RE = re.compile("[\x00-\x08\x0b-\x1f\x7f-\x9f​-‏‪-‮⁦-⁩﻿]")


def clean_text(text):
    """Strip control characters, ANSI escapes, zero-width and bidi characters."""
    text = _ANSI_RE.sub("", text)
    text = _INVISIBLE_RE.sub("", text)
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

_SPEAKER_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 ._'-]{0,40}?)\s*:\s+(.*)$", re.S)
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
# ffmpeg / ffprobe
# ---------------------------------------------------------------------------

def media_path(path):
    """Absolute path string for ffmpeg. It never starts with '-', so it is never read as an option."""
    return os.path.abspath(str(path))


def require_tool(name):
    """Exit with a clear message when a required command-line tool is missing."""
    if shutil.which(name) is None:
        sys.exit(
            "Missing tool: %s. Install it first.\n"
            "  macOS:   brew install ffmpeg\n"
            "  Windows: winget install Gyan.FFmpeg\n" % name
        )


def run(cmd, quiet=False):
    """Run a command, return stdout text. Exit on failure."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if not quiet:
            sys.stderr.write(proc.stderr)
        sys.exit("Command failed: %s" % " ".join(cmd))
    return proc.stdout


def probe(video):
    """Return {"duration", "width", "height", "fps"} for a media file."""
    require_tool("ffprobe")
    out = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", *FF_IN, media_path(video),
    ])
    data = json.loads(out)
    try:
        duration = float(data.get("format", {}).get("duration", 0.0))
    except (TypeError, ValueError):
        duration = 0.0
    if not math.isfinite(duration) or duration < 0:
        duration = 0.0
    info = {"duration": duration, "width": None, "height": None, "fps": None}
    for st in data.get("streams", []):
        if st.get("codec_type") == "video" and info["width"] is None:
            info["width"] = st.get("width")
            info["height"] = st.get("height")
            rate = st.get("avg_frame_rate", "0/1")
            try:
                num, den = rate.split("/")
                info["fps"] = round(float(num) / float(den), 3) if float(den) else None
            except (ValueError, ZeroDivisionError):
                info["fps"] = None
    return info


# Backward-compatible alias.
parse_srt = parse_captions
