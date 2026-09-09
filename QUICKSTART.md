# Quickstart - Cutlist

What this is: a skill your agent reads (Codex, Claude Code, Cursor, Gemini CLI, or any agent that reads AGENTS.md). It turns one podcast recording into 5 to 8 clip cuts with
exact times, ready-to-paste YouTube titles, descriptions, hashtags, tags, categories, and one thumbnail
mockup. You cut in your editor. You publish. The agent never touches YouTube.

## One-time setup (about 15 minutes)
1. Install your agent (Codex, Claude Code, Cursor, or Gemini CLI).
2. Install ffmpeg. Mac: `brew install ffmpeg`. Windows: `winget install Gyan.FFmpeg`.
3. Install Pillow: `python3 -m pip install pillow` (Windows: `python -m pip install pillow`).
4. Clone this repo. Run `bash install.sh --codex` (or `--claude`, `--cursor`, `--gemini`, `--all`).
5. Open your project folder in your agent. Paste `prompts/00_first_time_setup.md`. It self-tests, then asks ten
   questions and writes `channel/channel_profile.md`. Check that file; it is the only one you edit by hand.

## Every episode (about 20 minutes of your attention)
1. **Record.** Drop a marker at good moments if your recorder has one (Riverside: press **M**). Get the guest's links before you stop.
2. **Download two files from the same place** (both raw, or both from the editor after cuts): the video as MP4
   and the captions as SRT or VTT. See `skills/cutlist/references/recorders.md` for your tool.
3. **Make the folder** `episodes/ep06/` and put in it: `episode.mp4`, `captions.srt`, `notes.md`
   (copy from `skills/cutlist/assets/`, add guest name and links), `markers.txt` (optional).
4. **Paste prompt 01** (`prompts/01_run_clip_plan.md`), with the folder name and guest filled in.
   The agent returns `clip_plan.md`, `clip_plan.json`, and rough previews in `previews/`.
5. **Watch the previews.** Swap or trim anything weak with a line from `prompts/03_revisions.md`.
6. **Paste prompt 02** (`prompts/02_run_thumbnail.md`). The agent returns `thumb_mock.png` and
   `thumbnail_brief.md`. Open `thumb_mock_feed_320.png`; if you cannot read it, tell the agent to cut words.
7. **Cut in your editor.** For each clip: go to the start time, split, go to the end time, split, keep that
   range, speaker focus as the plan says, 9:16, captions on, export. Put the cold open at 00:00 of the episode.
8. **Publish from `CHECKLIST.md`.** Copy each field from `clip_plan.md`. Rebuild the thumbnail from the brief.

## Which prompt when
| File | Use it when |
|---|---|
| `prompts/00_first_time_setup.md` | Once, on a new computer |
| `prompts/01_run_clip_plan.md` | Every episode, first |
| `prompts/02_run_thumbnail.md` | Every episode, after 01 |
| `prompts/03_revisions.md` | You want a clip swapped, shorter, retitled, or the episode was re-exported |
| `prompts/04_retitle_backlog.md` | A batch of already-published videos needs consistent titles |

## Three things that will stop a run, on purpose
- **SYNC: FAIL.** The video and transcript came from different exports. Re-download both from the same place.
- **A missing tool.** The agent names it. Install it with the line above, then paste prompt 00 again.
- **check_plan.py FAIL.** A title over 100 characters, a clip outside 12 to 35 seconds, a bad category.
  The agent fixes these itself before it says done. If it says done with a FAIL, tell it to run the check again.

## Rules the agent follows (so you do not have to)
Numbers a guest says stay in quotes, never stated as fact. Every clip points to real words in the transcript.
Titles under 70 characters, hook in the first 40, guest name last in parentheses, no show name in the title.
3 to 5 hashtags. The thumbnail words must match the first 10 seconds, the title, and the first description line.

Worked example: `examples/_example/` has a finished, validated plan. Full detail: `README.md`.
