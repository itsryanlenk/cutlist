#!/usr/bin/env python3
"""Step 2. Find the loud moments in the episode audio.

Why
  Laughter, emphasis, and excitement raise the volume for a few seconds.
  A list of the loudest one-second windows is a cheap signal for
  "something happened here". The agent cross-checks these times with the
  transcript. Loudness alone never picks a clip.

What it does
  1. Pulls a mono 16 kHz WAV from the video with ffmpeg (cached next to the video).
  2. Computes RMS loudness in dBFS for every 1-second window (standard library only).
  3. Writes energy.csv (t_s, mmss, db) and prints the top windows, merged into
     runs so one laugh does not show up five times.

Usage
  python3 scripts/audio_energy.py episodes/ep05/episode.mp4 --top 25
"""

import argparse
import array
import csv
import io
import math
import operator
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (FF_IN, commit_target, fmt_mmss, media_path, probe, refuse_link, require_tool,  # noqa: E402
                     run_writing, temp_target, utf8_stdout, write_bytes_safely)

MAX_HOURS_DEFAULT = 6.0  # a 16 kHz mono WAV is about 115 MB per hour beside the creator's video


def cache_ok(wav):
    """True when a cached WAV opens and has frames. Anything else is stale, whatever its mtime."""
    try:
        with wave.open(str(wav), "rb") as wf:
            return wf.getnframes() > 0
    except (wave.Error, EOFError, OSError):
        return False


def extract_wav(video, wav, max_hours):
    require_tool("ffmpeg")
    refuse_link(wav)
    if wav.exists() and wav.stat().st_mtime >= video.stat().st_mtime and cache_ok(wav):
        return
    tmp = temp_target(wav)
    run_writing(["ffmpeg", "-y", "-v", "error", *FF_IN, "-i", media_path(video), "-t", "%.3f" % (max_hours * 3600),
                 "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(tmp)], tmp)
    commit_target(tmp, wav)


def window_db(wav_path, window_s=1.0):
    rows = []
    with wave.open(str(wav_path), "rb") as wf:
        rate = wf.getframerate()
        n_per = int(rate * window_s)
        t = 0.0
        while True:
            frames = wf.readframes(n_per)
            if not frames:
                break
            samples = array.array("h", frames)
            if len(samples) < n_per // 2:
                break
            acc = sum(map(operator.mul, samples, samples))
            rms = math.sqrt(acc / len(samples))
            db = 20 * math.log10(rms / 32768.0) if rms > 0 else -120.0
            rows.append((t, db))
            t += window_s
    return rows


def merge_runs(rows, threshold_db, min_gap_s=3.0):
    """Group consecutive loud windows into runs. Return list of (start, end, peak_db)."""
    runs = []
    cur = None
    for t, db in rows:
        if db >= threshold_db:
            if cur and t - cur[1] <= min_gap_s:
                cur[1] = t + 1.0
                cur[2] = max(cur[2], db)
            else:
                if cur:
                    runs.append(tuple(cur))
                cur = [t, t + 1.0, db]
    if cur:
        runs.append(tuple(cur))
    return runs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--top", type=int, default=25, help="how many loud runs to print")
    ap.add_argument("--window", type=float, default=1.0, help="window size in seconds")
    ap.add_argument("--max-hours", type=float, default=MAX_HOURS_DEFAULT,
                    help="refuse media longer than this (default %.0f h); raise it on purpose for a marathon" % MAX_HOURS_DEFAULT)
    args = ap.parse_args()
    utf8_stdout()

    video = Path(args.video)
    if not video.exists():
        sys.exit("File not found: %s" % video)
    if args.window <= 0 or args.max_hours <= 0:
        sys.exit("--window and --max-hours must be positive.")
    duration = probe(video)["duration"]
    if duration > args.max_hours * 3600:
        sys.exit("The media reports %.1f hours. Pass --max-hours %.0f if that is right." % (
            duration / 3600, math.ceil(duration / 3600)))
    wav = video.with_suffix(".16k.wav")
    try:
        extract_wav(video, wav, args.max_hours)
        rows = window_db(wav, args.window)
    except (OSError, ValueError, wave.Error, EOFError) as exc:
        sys.exit(str(exc))
    if not rows:
        sys.exit("No audio windows measured.")

    out = video.parent / "energy.csv"
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["t_s", "mmss", "db"])
    for t, db in rows:
        w.writerow(["%.1f" % t, fmt_mmss(t), "%.1f" % db])
    try:
        write_bytes_safely(out, buf.getvalue().encode("utf-8"))
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    dbs = sorted(db for _, db in rows if db > -80)
    if not dbs:
        sys.exit("Audio is silent.")
    median = dbs[len(dbs) // 2]
    p90 = dbs[int(len(dbs) * 0.90)]
    threshold = max(p90, median + 3.0)
    runs = [r for r in merge_runs(rows, threshold) if r[2] >= median + 3.0]
    runs.sort(key=lambda r: r[2], reverse=True)
    if not runs:
        print("No windows stand out above the median by 3 dB. Use the transcript alone.")

    print("AUDIO  windows=%d  median=%.1f dBFS  p90=%.1f dBFS  threshold=%.1f dBFS" % (
        len(rows), median, p90, threshold))
    print("Loud runs (start-end, peak). These are LEADS, not picks. Check the transcript at each time.")
    for start, end, peak in runs[: args.top]:
        print("  %s-%s  peak %.1f dB  (+%.1f over median)" % (
            fmt_mmss(start), fmt_mmss(end), peak, peak - median))
    silent = [t for t, db in rows if db < median - 25]
    if silent:
        print("Quiet windows (possible dead air): %d. First few: %s" % (
            len(silent), ", ".join(fmt_mmss(t) for t in silent[:8])))
    print("WROTE %s" % out)


if __name__ == "__main__":
    main()
