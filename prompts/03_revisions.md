# Prompt 03 - revisions (paste the one you need)

Every revision ends with check_plan.py passing.

Swap one clip:
```
Clip 3 in episodes/<id>/clip_plan.json is weak. Replace it with the next-best candidate from
your rejected list or the captions. Keep the other clips. Update both plan files, re-run
check_plan.py, re-cut only the new preview.
```

Shorten:
```
Clip 2 runs long. Tighten it to under 25 seconds without losing the payoff line. Tell me the
new start and end, update both plan files, re-cut its preview.
```

Retitle one item:
```
Clip 1 is the right moment but the title reads like clickbait. Rewrite it using formula 2
from channel/channel_profile.md. Keep the number as the speaker's words.
```

Search:
```
Find every place in episodes/<id>/transcript_compact.txt where the guest talks about pricing.
List the times and one line each. Do not change the plan.
```

Re-exported episode:
```
I re-exported the episode from the editor. New episode.mp4 and captions.srt are in episodes/<id>/.
Re-run check_inputs.py, then map every clip in clip_plan.json to the new timestamps by matching
hook_line text in the new captions. Show me old time -> new time per clip before writing anything.
```
