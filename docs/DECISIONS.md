# Decisions

Dated design decisions and the sources behind them. Add a dated entry when you change a rule.

## 2026-09-09 - v0.1.0 design

**D1. One self-contained skill, not three.** One folder holds the router (`SKILL.md`), the
workflows (`references/`), the scripts, and the templates. Installing that one folder anywhere
gives every workflow. Three separate skills would have shared scripts by relative path, which
breaks the moment a skill is copied to a global location. Both the OpenAI and Anthropic skill
guides recommend the SKILL.md + references + scripts layout with progressive disclosure.
Sources: developers.openai.com/codex/skills; the Agent Skills open format.

**D2. Agent-agnostic by format, not by adapter.** The skill is plain markdown and Python.
`install.sh` copies it to the discovery path of Codex (`.agents/skills`), Claude Code
(`.claude/skills`), Cursor (`.cursor/skills`), and Gemini CLI (`.gemini/skills`). `AGENTS.md`
covers agents that read that file. `CLAUDE.md` imports `AGENTS.md`. `prompts/` covers agents
with no skill support. Discovery paths were current on 2026-09-09 and will drift; the README says so.

**D3. Transcript first.** The agent reads the whole compact transcript before any signal
processing. Loudness (`audio_energy.py`) and frames (`frames.py`) confirm; they never pick.
Reason: a laugh with nothing said is not a clip, and a face on camera does not make a point.

**D4. Same-source rule with a hard stop.** Captions and video must come from the same export.
`check_inputs.py` compares the last cue time to the video duration and fails over 3 seconds.
Guessing an offset produces confident, wrong cuts. Stopping produces one re-download.

**D5. Numbers stay quotes.** A figure spoken in the episode is the speaker's claim. It goes in
titles only in their words and never as a verified fact in a description. This is a
publishing-safety rule and a credibility rule.

**D6. Platform limits come from primary documentation, checked 2026-09-09.**
- Title 100 characters; description 5,000 bytes; tags 500 characters total with commas and
  quotes counted. Source: YouTube Data API, `videos` resource, `snippet.title`,
  `snippet.description`, `snippet.tags`.
- More than 60 hashtags on a video and YouTube ignores them all; up to three show by the
  title. Source: YouTube Help, "Find playlists & videos using hashtags". The "15 hashtag limit"
  seen in many guides is not in YouTube's documentation.
- Custom thumbnails for Shorts upload from desktop YouTube Studio, 9:16 recommended.
  Source: YouTube Help article 72431.

**D7. Cold open drives the thumbnail.** The trifecta rule (thumbnail matches the first 10
seconds, the title, and the description) only works when the first 10 seconds are the hook.
So the clip plan picks a cold-open sentence, and title, description, and thumbnail all describe it.

**D8. The trifecta is a consistency rule, not a quality rule.** Four constraints sit on top:
4 words or fewer, readable at 320 pixels wide, a real expressive face, and a promise the first
10 seconds pay off. `thumbnail_mockup.py` writes the 320 px preview for that reason.

**D9. The agent never publishes.** Output files only. The creator clicks publish. This is
non-negotiable in `SKILL.md` and repeated in every prompt.

**D10. Standard library only, Pillow excepted.** Scripts must run on a creator's laptop with
`ffmpeg` and `python3` and one `pip install pillow`. No numpy, no OpenCV, no model downloads.

**D11. Recorder facts are dated and demoted.** `references/recorders.md` records what vendors
documented on 2026-09-09 and tells the agent to trust the creator when they report otherwise.
Riverside facts checked: automatic transcription on all plans with TXT and SRT download
(riverside.com/transcription); markers during recording on all plans with the M key
(support.riverside.com, "Add markers while recording").

**D12. Retitle before rethumbnail, on different days.** Two changes on the same video on the
same day cannot be told apart in analytics.

## 2026-09-09 - Manifests verified against live documentation

Checked the day of the v0.1.0 release. Each line names what was checked, where, and what changed.

- `.claude-plugin/plugin.json`: only `name` is required; `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords` are optional and kept. A `skills/` folder at the plugin root is scanned without a manifest entry. Source: code.claude.com/docs/en/plugins-reference. No change to the fields.
- `.claude-plugin/marketplace.json`: added. `/plugin marketplace add owner/repo` requires it in the repo; without it the only install path is `--plugin-dir` from a local copy. One plugin, `source` is the repo root. Source: code.claude.com/docs/en/discover-plugins.
- `.codex-plugin/plugin.json`: deleted. Codex has no plugin manifest. Skills are found by folder under `.agents/skills` (project, walking up to the repo root), `~/.agents/skills` (user), and `/etc/codex/skills`. The optional `agents/openai.yaml` beside a SKILL.md carries UI metadata only. Source: developers.openai.com/codex/skills.
- Cursor: reads `.cursor/skills` and `~/.cursor/skills`, and also the shared `.agents/skills` paths. Source: cursor.com/docs/skills. No change.
- Gemini CLI: reads `.gemini/skills` and `~/.gemini/skills`, and the `.agents/skills` alias. A `gemini-extension.json` is only for shipping as a distributable extension; not needed for discovery. Source: geminicli.com/docs/cli/skills. No change.
- GitHub Copilot: reads `.github/skills` in a repo and `~/.copilot/skills` or `~/.agents/skills` for the user. Added `--copilot` to both installers. Source: docs.github.com, "Add skills" under Copilot CLI.
- Windsurf: no first-party page found. Third-party sources describe `.windsurf/skills` and a move to `.agents/skills`. Not added to the installers; the README says to copy the folder by hand.
- SKILL.md frontmatter: `name` must be lowercase letters, digits, and hyphens, at most 64 characters, and equal to the folder name; `description` at most 1,024 characters. Both hold. Source: agentskills.io/specification.

## 2026-09-09 - Untrusted-input limits (pre-release security review)

**D13. The episode folder is the trust boundary.** The video and the captions are produced by
a recorder, a guest's tool, or anyone who can hand the creator an export. The plan is written by
the agent after reading that text. Every script treats all of them as untrusted. The limits
below came out of a defensive review of the scripts and installers before the first public
release; each one has a unit test in `tests/test_hardening.py`, and the self-test runs them.

- Times must be finite and non-negative. `nan` and `inf` parse as floats, passed every range
  check, and would have reached `ffmpeg` as garbage.
- Caption files over 50 MB are refused; a cue is cut at 2,000 characters; tag stripping is
  bounded so an unclosed `<` run stays linear (the old pattern was quadratic: about 7 minutes
  on a 1 MB cue). UTF-16 files are decoded instead of reported as "no cues".
- ANSI escapes, C0 and C1 controls, zero-width characters, bidi overrides, and byte-order marks
  are removed from caption text. They can drive a terminal or hide words from a human reader.
- Cells that a spreadsheet would run as a formula are quoted in `segments.csv`.
- `check_inputs.py` names cues that look like an instruction, a command, or a link, and
  `transcript_compact.txt` opens with a line saying the transcript is data. The rule that
  captions are never instructions still lives in `SKILL.md` and the model; see `SECURITY.md`.
- `frames.py` computes the frame count before building the list and refuses over 80;
  `--every` and `--step` must be positive. A media file can claim any duration.
- `audio_energy.py` refuses media over 6 hours unless `--max-hours` says otherwise, and caps
  the WAV extract to that length (about 115 MB per hour beside the creator's video).
- `cut_previews.py` refuses more than 20 items or a clip over 60 seconds without `--force`.
- `thumbnail_mockup.py` refuses an `--out` that is its own `--frame` or `--video`.
- Media paths are passed absolute and with `-protocol_whitelist file`, so a name cannot read
  as an option and a playlist inside the media cannot reach the network.
- Both installers refuse to run unless `skills/<slug>/SKILL.md` exists. With an empty
  `skills/` folder the old versions computed an empty slug and removed the whole skills root.
- `rebrand.py` rewrites bytes, so line endings survive (on Windows it rewrote every shell
  script as CRLF), skips symlinks, and refuses a second run.
- CI runs with `contents: read` and pins both actions to commit SHAs.
