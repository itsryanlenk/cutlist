# Reference: getting captions and video out of common recorders

The skill needs two files from the same export: the video (MP4 or MOV) and a caption file
(.srt or .vtt) with timestamps. "Same export" means both raw, or both from the edited
timeline. Mixed sources have different timestamps and `check_inputs.py` will stop the run.

Facts below were checked against vendor documentation on 2026-09-09. Vendors change plans and
menus; when a creator reports something different, trust the creator and tell them to
download whatever their tool offers as SRT or VTT.

| Tool | Captions | Live markers | Notes |
|---|---|---|---|
| Riverside | Automatic on all plans; download TXT or SRT from the Recordings tab, or from the editor after cuts | Yes, press M during recording (all plans); markers show as comments in the editor | Paid plans add speaker labels, text-based editing, and burned captions. Free plan puts all text under one speaker |
| Descript | Transcript export includes SRT/VTT | Markers exist in the editor, not during recording | Export from the same composition you export the video from |
| Zoom (cloud recording) | Audio transcript as VTT when enabled by the account | No | Speaker names come from Zoom display names |
| Premiere Pro / DaVinci Resolve | Auto-transcribe, export SRT from the sequence | Sequence markers | Export SRT and video from the same sequence, same in and out points |
| Any video, no captions | Run Whisper locally: `whisper episode.mp4 --output_format srt` (needs `pip install openai-whisper` and ffmpeg) | No | Speaker labels will be missing; the creator tells you who is who in `notes.md` |
| YouTube auto captions (already published) | Download from YouTube Studio > Subtitles as .srt | No | Timestamps match the published video, so use the published video file |

## Speaker labels

The parser reads `Name: text` at the start of a cue, or a WebVTT `<v Name>` tag. When the
file has no labels, ask the creator who the host and guest are and lean on the context of
each line (questions are usually the host).

## Markers

Markers are timestamps the creator dropped during recording. They arrive as a list in
`episodes/<id>/markers.txt` (one per line, `MM:SS note`). Treat each as a lead to check,
not a decision. A marker with no good line near it is dropped with one line of reason.
