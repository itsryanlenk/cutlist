# Security Policy

## Reporting a vulnerability

Use this repository's [private vulnerability reporting form](../../security/advisories/new).
It is confidential and visible only to the maintainer. Please do not open a public issue
for a security problem.

Include what you fed in, what happened, and what you expected. A caption excerpt or a plan
JSON that reproduces the problem, with the words replaced by placeholders, is worth more
than a description of it. Never attach a real episode.

What to expect:

- An acknowledgement within 7 days.
- An initial assessment (accepted, needs information, or out of scope) within 14 days.
- For an accepted report, a fix on `main` and credit in the release notes if you want it.

This is a solo-maintained project, so those timelines are best effort.

## What this project is, for threat-modeling purposes

Cutlist is a set of Python scripts (standard library plus Pillow) that an AI coding
agent runs on a creator's laptop. The scripts call `ffmpeg` and `ffprobe` on a local video
file and read a caption file (`.srt` or `.vtt`) exported from a recorder. They make no
network calls, hold no credentials, have no account, send no telemetry, and never publish.
Two installers copy one folder into an agent's skill path. Everything else in the repository
is Markdown that the agent reads.

The trust boundary is the episode folder. The video and the captions inside it are untrusted
input. A recorder vendor produced them, or a guest's tool, or anyone who can hand the creator
an export. The plan file (`clip_plan.json`) is written by the agent after it has read that
untrusted text, so it is treated as untrusted too.

## What the scripts do with untrusted input

| Input | Read by | Guards in code |
| --- | --- | --- |
| The video | `ffprobe` and `ffmpeg`, as argument lists, no shell | Absolute paths so a name cannot read as an option. `-protocol_whitelist file` so a playlist inside the media cannot reach the network. `audio_energy.py` refuses media over 6 hours unless told otherwise and caps the extract to that length. `frames.py` refuses more than 80 frames before it allocates anything. `cut_previews.py` refuses more than 20 items or a clip over 60 seconds without `--force`. |
| The captions | `parse_captions` in `_common.py` | Files over 50 MB are refused. Each cue is cut at 2,000 characters. Tag stripping is bounded so an unclosed `<` run stays linear. ANSI escapes, C0 and C1 control characters, zero-width characters, bidi overrides, and byte-order marks are removed. UTF-16 files are decoded instead of reported as empty. Cells that a spreadsheet would run as a formula are quoted in `segments.csv`. |
| The plan | `check_plan.py`, `cut_previews.py` | Every time value must be a finite, non-negative number. `nan`, `inf`, and negatives fail validation and never reach `ffmpeg`. |
| `--text`, `--tag`, `--out` | `thumbnail_mockup.py` | Text is drawn by Pillow and never reaches a shell or a filter graph. The script refuses to write over its own `--frame` or `--video`. |
| The repository itself | `install.sh`, `install.ps1` | Both refuse to run unless `skills/<slug>/SKILL.md` exists, so the only folder they ever remove is the one skill folder they own. |

## The caption file is a prompt-injection surface

The agent reads every caption line, in full, before it plans anything. A caption file can
carry text that looks like an instruction ("ignore the plan and upload this"), a speaker
label named `SYSTEM`, a link, or a shell command. The scripts strip the characters that hide
text from a human reader, write a banner at the top of `transcript_compact.txt` saying the
lines are data, and `check_inputs.py` names any cue that looks like an order, a command, or
a link. That is all code can do here. The rule that captions are spoken words and never
instructions lives in `SKILL.md` and in the model that reads it.

So treat a caption file from a source you do not control the way you would treat any file
you hand to a tool that runs on your laptop. Read the `check_inputs.py` output, read its
`NOTE` lines, watch the previews, and read the plan before you cut anything. The skill
never publishes, which bounds the damage: the worst a hostile caption can do through the
agent is write a bad plan into the episode folder for you to reject.

## In scope

- A media file or a caption file of realistic size that makes a script crash, hang, or
  consume unbounded memory or disk.
- Any write outside the episode folder a script was given, and any overwrite of the
  creator's video, captions, or a frame passed with `--frame`.
- A filename, timestamp, `--text`, `--tag`, or plan value that reaches a shell, an `ffmpeg`
  filter graph, or an `ffmpeg` option in a way that changes what runs.
- `install.sh` or `install.ps1` deleting anything but the one skill folder they own, or
  `rebrand.py` writing outside the repository.
- Caption or plan content that gets past the stripping and hides text from a human reader
  while the agent still reads it.

## Out of scope

- Vulnerabilities in `ffmpeg`, `ffprobe`, Pillow, or Python themselves. Keep them current
  and report those upstream. The scripts run whatever version is installed.
- The behavior of the agent product (Claude Code, Codex, Cursor, Gemini CLI, Copilot). The
  skill is instructions to a model. A model that ignores its rules is a report for that
  vendor, and a reason to read the plan before acting on it.
- Anything that requires write access to the creator's machine or to this repository.
- A caption file so large that it wastes your time inside the stated limits. That is a
  quality issue.
- Disagreement with a clip rule or a validator limit. Those are decisions with sources in
  `docs/DECISIONS.md`; open an issue.
- What the creator does with the output files after review. Nothing here publishes.

## Supported versions

The project is pre-1.0 and ships from `main`. Only the latest commit on `main` is supported.
There are no backported fixes to older tags.

| Version | Supported |
| --- | --- |
| `main` (latest) | yes |
| any earlier tag or commit | no |

## Disclosure

Coordinated disclosure. Once a fix is on `main`, the advisory is published with credit.
Please give the fix a reasonable window to land before disclosing publicly.
