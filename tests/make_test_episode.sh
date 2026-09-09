#!/usr/bin/env bash
# Rebuild the synthetic test episode in examples/_example.
# It is a 3-minute color-bar video with a quiet tone and three loud bursts
# (at 0:40, 1:35, 2:30). The matching transcript.srt is already in the folder.
# Use it to prove the tool chain works on a new machine. It is not real content.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=examples/_example/episode.mp4
command -v ffmpeg >/dev/null || { echo "ffmpeg is missing. See README.md"; exit 1; }
ffmpeg -y -v error -f lavfi -i "testsrc2=size=1280x720:rate=30" \
  -f lavfi -i "sine=frequency=220:sample_rate=16000" \
  -filter_complex "[1:a]volume='if(between(t,40,43)+between(t,95,99)+between(t,150,152),1.0,0.05)':eval=frame[a]" \
  -map 0:v -map "[a]" -t 180 -c:v libx264 -preset veryfast -crf 30 -c:a aac "$OUT"
echo "WROTE $OUT"
