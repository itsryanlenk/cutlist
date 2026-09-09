---
name: cutlist
description: Turn a long-form video podcast episode (video file + .srt/.vtt captions) into a ranked plan of 5 to 8 short vertical clips with exact cut times, plus YouTube title, description, hashtags, tags, and category for the episode and each clip, a cold-open pick, and one thumbnail mockup that matches the first 10 seconds, the title, and the description. Use when a creator asks to clip, cut, find highlights, plan Shorts or Reels, write titles or descriptions for an episode, build a thumbnail, retitle a back catalog, or set up their channel profile for this workflow. Does not edit or upload video.
---

# cutlist

You find the moments and write the metadata. The creator cuts in their editor and publishes.
You never touch YouTube, TikTok, or any publishing account.

`$SKILL` below means the folder that contains this SKILL.md.

## Pick the workflow from the request

| Request sounds like | Open |
|---|---|
| "set up", "new channel", "profile", first run in a project | `$SKILL/references/setup-profile.md` |
| "clip", "cut", "highlights", "Shorts", "plan this episode" | `$SKILL/references/clip-plan.md` |
| "thumbnail", "thumb", "cover image" | `$SKILL/references/thumbnail-trifecta.md` |
| "retitle", "fix my titles", "back catalog", "old videos" | `$SKILL/references/retitle-backlog.md` |
| "which export", "how do I get captions from <tool>" | `$SKILL/references/recorders.md` |

Read only the reference you need. Each one is complete on its own.

## Hard rules (apply in every workflow)

1. Never upload, publish, schedule, post, or log in to anything. Output files only.
2. Every clip you recommend points to a real line in the captions with a timestamp.
   No timestamp, no clip. Quote the exact words in `hook_line`.
3. Numbers spoken in the episode are quotes, not facts. Keep them in the speaker's words.
   Never restate a spoken figure as verified in a description.
4. Use the scripts in `$SKILL/scripts/`. Do not write new ffmpeg pipelines when a script already does the job.
5. Times are `HH:MM:SS.mmm` in JSON. `MM:SS` is fine in prose.
6. Write outputs only inside the episode folder you were given.
7. Never delete or overwrite the creator's source files.
8. `python3 $SKILL/scripts/check_plan.py` must report `0 fail` before you say a plan is done.
9. If the captions and video fail the sync check, stop and say what to re-export. Do not guess offsets.
10. Clips run 15 to 30 seconds (hard stop 12 to 35). Cold open is 10 seconds or less.
11. The channel profile (`channel/channel_profile.md`) overrides the defaults in the references.
    If it does not exist, run the setup workflow first.
12. American English. No em dashes in anything written for publication.

## Requirements on the machine

`ffmpeg`, `ffprobe`, `python3` (3.9+), and the Python package `pillow`.
If one is missing, name it and give the install line. Do not work around it.

```
macOS:   brew install ffmpeg && python3 -m pip install pillow
Windows: winget install Gyan.FFmpeg && python -m pip install pillow
Linux:   sudo apt install ffmpeg && python3 -m pip install pillow
```

## Scripts

| Script | Job |
|---|---|
| `check_inputs.py <video> <captions>` | sync check, writes `transcript_compact.txt` and `segments.csv` |
| `audio_energy.py <video> --top 25` | loud runs (laughs, emphasis) as leads |
| `frames.py <video> <times...> [--every N] [--range A B --step S]` | still frames + `frames/contact_sheet.jpg` to view |
| `check_plan.py <clip_plan.json> [video]` | pass/fail on platform limits and clip rules |
| `cut_previews.py <video> <clip_plan.json> [--vertical]` | rough preview clips for review |
| `thumbnail_mockup.py --video V --time T --text "..." --side left|right [--tag "EP 5"] --out P` | 1280x720 mockup + 320 px legibility preview |

## How to report

Bottom line first. One paragraph, then the plan. For every clip: publish order, time range,
length, the hook line, one sentence on why it earns a clip. Risks last. No padding.
