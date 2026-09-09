#!/usr/bin/env bash
# Self-test for cutlist. Rebuilds the synthetic example episode and runs every script.
# Exit code 0 means every step passed. Used by CI and by the first-time setup prompt.
set -euo pipefail
cd "$(dirname "$0")/.."
S=skills/cutlist/scripts
E=examples/_example
pass=0; fail=0
step() { printf '\n== %s\n' "$1"; }
ok()   { pass=$((pass+1)); echo "PASS $1"; }
bad()  { fail=$((fail+1)); echo "FAIL $1"; }

for t in ffmpeg ffprobe python3; do command -v $t >/dev/null && ok "tool $t" || bad "tool $t missing"; done
python3 -c "import PIL" 2>/dev/null && ok "pillow" || bad "pillow missing (python3 -m pip install pillow)"
[ $fail -eq 0 ] || { echo "Fix the missing tools, then run again."; exit 1; }

step "make test episode"; bash tests/make_test_episode.sh && ok "episode.mp4" || bad "make_test_episode"
step "check_inputs";   out=$(python3 $S/check_inputs.py $E/episode.mp4 $E/captions.srt); echo "$out" | grep -q "SYNC: OK" && ok "sync" || bad "check_inputs"
step "audio_energy";   out=$(python3 $S/audio_energy.py $E/episode.mp4 --top 5); echo "$out" | grep -q "02:30" && ok "loud run at 02:30 found" || bad "audio_energy"
step "frames";         python3 $S/frames.py $E/episode.mp4 2:31 --range 2:25 2:45 --step 5 >/dev/null && [ -f $E/frames/contact_sheet.jpg ] && ok "contact sheet" || bad "frames"
step "check_plan";     python3 $S/check_plan.py $E/clip_plan.json $E/episode.mp4 && ok "plan validates" || bad "check_plan"
step "cut_previews";   python3 $S/cut_previews.py $E/episode.mp4 $E/clip_plan.json --vertical >/dev/null && [ "$(ls $E/previews/*.mp4 | wc -l)" -ge 10 ] && ok "previews" || bad "cut_previews"
step "thumbnail";      python3 $S/thumbnail_mockup.py --video $E/episode.mp4 --time 2:31 --text "QUIT VC. GO SOLO." --side right --tag "EP 1" --out $E/thumb_mock.png >/dev/null && [ -f $E/thumb_mock_feed_320.png ] && ok "mockup" || bad "thumbnail_mockup"
step "vtt parse";      python3 - <<'EOF' && ok "vtt" || bad "vtt"
import sys; sys.path.insert(0, "skills/cutlist/scripts")
from _common import parse_captions
import tempfile, pathlib
p = pathlib.Path(tempfile.mkdtemp()) / "t.vtt"
p.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:03.500\n<v Host>Hello there.\n\n00:00:04.000 --> 00:00:06.000\nGuest: Hi.\n")
c = parse_captions(p); assert len(c) == 2 and c[0]["speaker"] == "Host" and c[1]["speaker"] == "Guest", c
EOF

step "unit tests";     python3 -m unittest discover -s tests >/dev/null 2>&1 && ok "hardening tests" || bad "hardening tests (run: python3 -m unittest discover -s tests -v)"

step "cleanup"; rm -rf $E/previews $E/frames $E/energy.csv $E/episode.16k.wav $E/episode.mp4 $E/segments.csv $E/transcript_compact.txt $E/thumb_source_frame.jpg
printf '\nRESULT: %d pass, %d fail\n' $pass $fail
[ $fail -eq 0 ]
