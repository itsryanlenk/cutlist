# AGENTS.md - cutlist

This repository is a skill, not an app. The skill lives in `skills/cutlist/`.
Read `skills/cutlist/SKILL.md` first. Its hard rules apply to every task in this repo.

When a creator uses this repo as their working folder:
- Their channel profile is `channel/channel_profile.md` (created by the setup workflow; not committed).
- Their episodes are `episodes/<id>/` (not committed).
- Invoke the skill by name (`$cutlist` in Codex, `/cutlist` in Claude Code) or
  say what you want ("clip plan for episodes/ep06") and follow the matching workflow.

When a maintainer works on the repo itself:
- Run `bash tests/selftest.sh` before and after any change to `skills/cutlist/scripts/`.
- Keep scripts standard-library only, except Pillow in `frames.py` and `thumbnail_mockup.py`.
- Keep `SKILL.md` under 200 lines. Put detail in `references/`.
- American English. No em dashes. Short sentences.
- Never commit a real episode, caption file, or channel profile. `.gitignore` blocks them; keep it that way.
