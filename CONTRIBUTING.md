# Contributing

Thanks for looking at Cutlist. It is a small, opinionated skill, and the bar for a
change is that it keeps the skill's promise true: every clip points to real words in the
captions, and the agent never publishes anything.

## Before you open a pull request

```bash
bash tests/selftest.sh
```

Thirteen checks should pass. Paste the `RESULT:` line into the pull request. Run it before and
after any change under `skills/cutlist/scripts/`.

The self-test needs `ffmpeg`, `ffprobe`, `python3` 3.9 or newer, and the Python package
`pillow`. It builds a three-minute synthetic episode in `examples/_example/`, runs every
script against it, and cleans up. No real content is involved.

## Ground rules

1. Standard library only, plus Pillow. Pillow is used in `frames.py` and
   `thumbnail_mockup.py` and nowhere else. No numpy, no OpenCV, no model downloads, no
   network calls. A creator's laptop with `ffmpeg`, `python3`, and one `pip install pillow`
   must run everything.
2. Keep `SKILL.md` short. It is the router and the hard rules. Detail goes in `references/`.
   Under 200 lines.
3. No creator data in commits. No real episode, caption file, channel profile, guest name,
   handle, or link. `.gitignore` blocks `channel/`, `episodes/`, and all media except the
   synthetic example captions. Keep it that way. If you need an example, make it up and say
   so in the file.
4. The rules in `docs/DECISIONS.md` have sources. Clip length (15 to 30 seconds, 12 to 35
   hard), the 3-second sync tolerance, the validator limits, and the trifecta rule change
   only with a dated entry there that names the source. A pull request that changes one
   without the entry will be asked for it.
5. The agent never publishes. No workflow, script, or prompt may upload, post, schedule, or
   log in to anything. Output files only.

## Copy rules

Everything written for a reader, from `SKILL.md` to this file, follows the same rules:

- American English. No em dashes and no en dashes. Use a comma, a colon, a period, or
  parentheses.
- Short sentences, active voice. Define a term before you use it. Bottom line first.
- A number a speaker says in an episode is their claim, in their words. This applies to
  examples in the docs too.

## Scripts

Each script is one file, runs with `python3`, takes its inputs as arguments, and writes
only inside the episode folder it was given. It never deletes or overwrites the creator's
source files. If you add a script, add it to the table in `SKILL.md`, add a step to
`tests/selftest.sh`, and keep the argument style of the others.

## Skill format

The skill follows the open Agent Skills format: a folder with `SKILL.md` at the top,
YAML frontmatter with `name` and `description`, and `references/`, `scripts/`, and
`assets/` beside it. `name` must equal the folder name. Every agent that reads skills
routes on the description, so keep it concrete and keep the trigger phrases in it.

## Style

Match the file you are editing. The Python is terse and commented where a decision is not
obvious. The prose follows the copy rules above.
