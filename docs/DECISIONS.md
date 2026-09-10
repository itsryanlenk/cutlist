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
processing, and every candidate comes off the text. Loudness (`audio_energy.py`) and frames
(`frames.py`) are read only after that list exists: they score one row of the six in
`references/clip-plan.md` and they confirm a pick. Neither one puts a candidate on the list.
Reason: a laugh with nothing said is not a clip, and a face on camera does not make a point.
*(Wording sharpened 2026-09-10. It used to read "they never pick", which a reader could set
against the Energy row in the rubric. The behaviour did not change; the sentence now says
which part of scoring energy is allowed to touch.)*

**D4. Same-source rule with a hard stop.** Captions and video must come from the same export.
`check_inputs.py` compares the last cue time to the video duration and fails over 3 seconds.
Guessing an offset produces confident, wrong cuts. Stopping produces one re-download.
*(Superseded in part on 2026-09-10 by D17, which keeps the tolerance and splits the verdict by
the direction of the gap. The version above failed a correctly matched pair whenever the video
carried an outro.)*

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

## 2026-09-09 - Any long video, any recorder, any editor

**D14. The unit is a long video with captions, not a podcast.** The scripts never cared: any
video plus an SRT or VTT file, under six hours. The rules that assumed a podcast were three
sentences, and they now say when they apply. The "guest value" scoring row applies only when
there are two or more speakers; a solo lecture, tutorial, stream, or keynote is scored out of
10 on the other five tests. The thumbnail rule keeps "a real frame from the video" and adds
the screen case: an expressive face when a person is on camera, the strongest screen detail
when the video is a screen, slides, or gameplay. D8's "real expressive face" reads that way
from this date. The numbers (15 to 30 second clips, 10 second cold open, 3 second sync
tolerance, the validator limits) did not move.

**D15. The recorder and the editor are decided at setup, once, and written into the profile.**
Earlier copy named Riverside's marker key in the README, the checklist, and the quickstart,
which made the skill read as Riverside-only. The setup workflow now asks for the recorder,
the editor, and whether a person is on camera, then copies the matching export, marker, jump,
split, 9:16, and caption lines from `references/tools.md` into the profile's Tools section.
Every later workflow reads the profile, so an instruction never names a tool the creator
does not have. `tools.md` replaces `recorders.md` and covers editors as well; its facts are
dated and demoted the same way D11 demoted recorder facts: when the creator reports
something different, the creator is right.

## 2026-09-09 - Second and third security reviews, same day

Two more reviewers, fresh context each, were told to break the D13 fixes and find what the
first review missed. What they proved, and what changed, each with a unit test:

- `frames.py --range` with a start near 1e18 never ended: `t + step == t` in floating point,
  and the count check ran on the unclamped range. Times are now clamped to the video and
  generated by index, and `parse_time` refuses anything past hour 100 everywhere.
- On Windows, a bare `ffprobe` resolves against the working folder before PATH, so a program
  file inside an export bundle would run with the creator's rights and no model in the loop.
  `tool_path()` walks PATH itself, skips relative entries, and passes absolute paths;
  `NoDefaultCurrentDirectoryInExePath` is set at import. Fonts are found the same way.
- The invisible-character filter listed ranges and missed the Unicode tag block, the word
  joiner, the soft hyphen, variation selectors, and more. It now drops every format,
  control, private-use, and surrogate character by category, plus the named extras.
- `check_inputs.py` wrote its files before the verdict, and one speaker name outside the
  console code page raised on Windows before the NOTE and SYNC lines printed. Every script
  now writes UTF-8 to the console, and the files follow the verdict.
- `ffprobe` output was decoded with the locale code page; a media title with the wrong bytes
  killed every probe on Windows. All program output is decoded as UTF-8, with a timeout.
- `rebrand.py` followed Windows junctions out of the tree. It now rewrites only files whose
  real location is inside the repository.
- A local HLS playlist can name other local files. `probe()` refuses playlist formats by
  name, every script probes before it cuts, and `ffmpeg` will not read a playlist that is
  named like a video in the first place.
- `thumbnail_mockup.py --out` could point anywhere. It now stays inside the episode folder
  and never creates folders, which is what SECURITY.md had promised.
- Plans have a size cap and a shape check; `publish_order` is bounded because it names a
  file; wrong types produce `FAIL` lines instead of tracebacks; `duration_s` must be finite.
- Tests that could pass for the wrong reason were fixed: the PowerShell installer has a
  positive control, the tag regex is timed directly, and the self-test reports skipped tests.
- `.gitignore` covers what the installers write inside a clone and every file the scripts
  produce, so a creator's `git add -A` in a working folder commits none of it. Pillow is
  pinned in CI.
- Accepted as is: the plugin's `source` is the repo root, so a plugin install ships the
  docs, prompts, tests, and the one-shot rebrand script alongside the skill. Nothing there
  is private and nothing runs on install; splitting the tree would put a Claude-only folder
  inside the agent-agnostic skill.

## 2026-09-09 - Fourth review: links, junctions, and the format whitelist

The third reviewer proved three bypasses of the rules above, all with unprivileged fixtures,
and each now has a unit test:

- A file in the bundle named like an output (`transcript_compact.txt`, `energy.csv`,
  `thumb_mock.png`) as a hard link to `episode.mp4` truncated the video through that name;
  the thumbnail's "never overwrite" check compared resolved paths, which cannot see hard
  links. Every output name is now refused if it is a symlink, a junction, or has more than
  one hard link; every output goes to a fresh temp file beside it and is moved into place
  with a replace, so an existing name is unlinked and never written into.
- A junction named `frames/` or `previews/` sent output outside the episode folder.
  `output_dir()` refuses a linked folder and requires the real folder to sit inside the
  episode folder.
- A 4096x2 frame made the thumbnail scale to gigapixels before cropping. It now crops to
  16:9 in source coordinates first and refuses frames that are not video-shaped.
- `-format_whitelist` now names the media formats the scripts open, so a playlist, an IMF
  composition, or an AviSynth script named like a video is refused before any demuxer reads
  it. The format-name denylist stays as a second layer.
- Plans are capped at 200 clips and the overlap check reports one line per clip, so a plan
  of identical clips cannot print n squared lines. `publish_order` is bounded in
  `check_plan.py` as well as in `cut_previews.py`. Deep JSON nesting and a denormal
  `--every` are `FAIL` lines, not tracebacks.
- Injection and role-label flags normalize fullwidth and accented spellings first. A
  lookalike letter from another alphabet still passes; SECURITY.md says so.
- Two tests that could pass for the wrong reason now cannot: the PATH-walk test puts `.` and
  an empty entry first, and the playlist test uses a concat script that is refused by name.

## 2026-09-09 - Fifth review: the image muxer, special files, and cleanup

The fourth reviewer found nothing that reached the source recording or left the folder for
good, and two Lows plus eight smaller items, each now with a unit test:

- ffmpeg's image muxer expands `%d` in an output path, so a bundle folder named `ep%d` put a
  frame into a sibling `ep1/`. Every image output now carries `-update 1`, which writes one
  file to the literal path.
- A symlink to a device, or a pipe, standing in for a caption or plan file reports zero
  bytes and would have been read without end. Both loaders now require a regular file and
  cap the read itself.
- A failed or timed-out `ffmpeg` left its temp file behind, up to a partial encode; it is
  removed on every failure path. A directory where an output file should be, and junk in
  the audio cache, are clean exits instead of tracebacks; the cache is re-extracted.
- `refuse_link` refused every reparse point, which would have refused a cloud placeholder
  of a previous output. It now refuses only name-redirecting tags (symlink, junction).
- `--frame` is opened as JPEG or PNG only; Pillow would otherwise pick a plugin by content
  and hand a PostScript file to Ghostscript.
- The validator checks that text fields are text and list fields are lists of text; a
  `--cols` of zero is an argument error; `install.sh` refuses `--into` under the
  repository's own `skills/`; SKILL.md rule 4 says never to pass `--force` unasked.
- The format whitelist wording in SECURITY.md now says what it does: refusal after
  detection and before the header is parsed, with the accepted containers listed.

## 2026-09-09 - Sixth review: the source's shape, the tool's own cache, and the leftovers

The fifth reviewer (the first run after a review proof crashed the machine, so every proof
now runs small) found two Mediums and a tail of smaller items, each now with a unit test:

- A tall or wide source made every contact-sheet tile follow its shape, so a 64x2048 video
  at the default width gave 13-megapixel tiles. `frames.py` refuses a source with a shape no
  video has, scales tiles by the longer side, and budgets the total pixels of tiles and
  sheet before the first frame is written.
- A planted `episode.16k.wav` with a valid header and a 1 Hz sample rate turned every sample
  into a row of `energy.csv`. The cache is accepted only when it is a regular file with the
  exact shape this script writes (16 kHz, mono, 16-bit), and `--window` is bounded.
- Cleaning a large non-ASCII caption built a list of one-character strings; it now decides
  once per distinct character and translates in C. A failed move onto a directory or a
  read-only file left the finished temp file; it is removed. Image inputs carry
  `-pattern_type none` so the demuxer never expands a `%d` in a folder name. A frame is
  refused by pixel count before it is decoded. Bad hashtags are reported as a count with five
  examples. A device or a pipe is refused before ffprobe opens it.
- `markers.txt` is read and reported by `check_inputs.py` the way captions are: cleaned,
  with instruction-like lines named, and rule 13 now covers every file in the episode
  folder. The first-run prompt tells the agent to stop on a failure instead of editing the
  skill. The installers use physical paths and literal paths, and say when a link fell back
  to a copy.

## 2026-09-09 - Seventh review: the preview cutter, tool shims, and the print path

The sixth reviewer found one Medium and four Lows, each now with a unit test:

- `cut_previews.py` scaled by width only, so a tall source encoded at 854 by sixteen
  thousand. It now checks the source's shape after the probe (the same check the frame
  tool uses, now shared), scales by the longer side with even dimensions, never crops a
  vertical preview wider than the source, and refuses two clips that would write the same
  preview name.
- On Windows the tool resolver accepted every extension in PATHEXT, so an `ffmpeg.bat` shim
  earlier on PATH would have run through `cmd.exe`, which reads metacharacters out of a file
  name we pass as an argument. Only `.exe` and `.com` are accepted now.
- `-pattern_type none` was rejected when ffmpeg picked the single-image demuxer for a tiny
  tile, which broke the no-Pillow contact sheet. `-f image2` names the demuxer first, and a
  test runs the fallback on tiny tiles.
- The caption cap drops from 50 MB to 10 MB and 100,000 cues, because parsing costs about
  twenty times the file.
- `show()` now escapes a line break too, and every path a script prints or names in a
  refusal goes through it, so a folder name cannot forge a status line.
- Smaller: an integer too large for a float, a PNG with an oversized text chunk, and an
  unparsable `frame_time` all produce `FAIL` lines; a cache longer than the video counts as
  stale; the speaker list on the console is capped; the pixel budget comment states the peak.

## 2026-09-09 - Eighth review: the console is part of the surface

The seventh reviewer found one Medium and two Lows, each now with a unit test:

- `check_inputs.py` echoed up to five flagged marker lines to the console. A `markers.txt`
  that is a link to a credentials file would have printed a token into the context the agent
  reads. Flagged marker lines are now named by time stamp only, and every input file
  (captions, plan, markers, frame) is refused when it is a link of any kind, before it is read.
- Six paths still printed raw, including every failed `ffmpeg` call. The command echo and
  the program's own output now pass through the same cleaning as every other path, so a
  folder name with a line separator cannot forge a status line.
- `rebrand.py` rewrote its own `brand.json` through a link. It now requires a plain file
  inside the repository and writes it through a temp file and a replace.
- Smaller: ffprobe dimensions are coerced before the shape check; a `--frame` file is capped
  at 50 MB before Pillow opens it; every documented command quotes its paths; the tests
  resolve `ffmpeg` and `ffprobe` the way the scripts do; the README says what a local-folder
  plugin install copies.

## 2026-09-09 - Ninth review: hard links in rebrand, argparse, message volume

The eighth reviewer found three Lows and one item to verify on POSIX, each now with a test:

- `rebrand.py` protected its own `brand.json` from links and rewrote every other file in
  place, so a hard-linked file carried the write outside the tree. It now refuses any file
  with more than one hard link and writes every file through a temp file and a replace.
- argparse's own refusal ("unrecognized arguments") echoed the argument raw. Every script
  now uses a parser whose refusals pass through the same cleaning as every other message.
- A bad `category_id` or time value was quoted in full in a `FAIL` line; a 5 MB plan could
  put 5 MB into the console. Quoted values are cut at 60 characters.
- The thumbnail's episode-folder rule resolved a symlinked video to its target's folder and
  named that folder in its refusal. It now uses the folder of the name it was given, the same
  rule as every other output.
- Smaller: the validator's cold-open limit is 10 seconds, the number `SKILL.md` states
  (it had been 12); speaker labels on the console are cut at 40 characters; the one unquoted
  `--out` in the thumbnail reference is quoted; the self-test checks a preview's duration.

## 2026-09-09 - Tenth review: temp names and save failures

The ninth reviewer found one Low and four small items, each now with a test:

- `rebrand.py` wrote through a temp name that anyone could guess (`README.md.rebrand-tmp`),
  so a hard link planted under that name in a clone was written through before the replace.
  Every rebrand write now goes through `mkstemp`, the same primitive the scripts use, and
  the test plants both old names as links and checks that neither is touched.
- A Pillow save that failed (an output name with an unknown extension) left an empty temp
  file. The thumbnail, its feed-size copy, and the contact sheet are now rendered in memory
  and written through the same safe write as every text output.
- The thumbnail's folder rule resolved the frames folder before taking its parent, so a
  junction there could widen the rule to another tree. It now resolves the frame's folder
  and that folder's parent as named.
- `check_plan.py --help` prints its usage; SECURITY.md says "at most hour 100", which is
  what the code does.

## 2026-09-09 - Eleventh review, and the exit rule

The tenth reviewer found two Lows and four one-line items, each now with a test, and stated
the finding that matters for the gate: nothing in the round overwrote a source, executed
bundle content, or escaped the episode folder without the agent itself typing the escape.

- The thumbnail's folder rule always added the frame folder's parent, so a frame in the
  episode root (where the script writes `thumb_source_frame.jpg`) let `--out` name a sibling
  episode. The parent is added only when the frame sits in a `frames/` subfolder.
- `ffprobe -show_format` echoed every metadata tag, and a tag can be as large as the file.
  The probe now asks only for the five fields it reads.
- Smaller: a truncated image, an unreadable caption file, and a symlink loop on Python 3.9
  to 3.12 are clean exits; temp paths are absolute so ffmpeg never reads a leading name as a
  protocol; SECURITY.md says what the boundary is when the episode folder is itself a link.

**D17. The sync verdict depends on which way the gap runs.** Added 2026-09-10 after a red team
read the launch copy against the code and found that `check_inputs.py` failed a correctly
matched export. It computed `gap = abs(duration - last_cue_end)` and printed one cause: "one
file is the raw recording and the other is an edited export." A video with an outro, an end
card, or trailing silence longer than the tolerance is a matched pair, and it was failed with
that wrong cause, so the creator re-exports and gets an identical file. The two directions mean
different things and are now handled separately:

- **Captions past the end of the video** stays a hard stop with no way through. Those cue times
  are not in that file, so nothing can be cut at them whatever caused the mismatch.
- **Video past the last word** stops and names both causes, the silent tail and the mismatched
  export, and tells the creator how to say which it is. `--silent-tail` proceeds and prints the
  accepted gap on its own line, so an accepted tail is never swallowed quietly.

The flag is the creator's answer about their own file, and it is the one thing the agent cannot
see from here. `SKILL.md` rules 4 and 9 forbid the agent passing it on its own judgement, the
same way rule 4 forbids `--force` on `cut_previews.py`. The 3 second tolerance did not move.
Five unit tests in `tests/test_hardening.py` (class `SyncCheckTailGap`) pin all of it, including
that the flag does not rescue an overrun and that a matched pair still passes untouched.

**D18. A safety rule that a doc claims is everywhere has to be everywhere.** Added 2026-09-10.
The README said the never-publish rule was "in the skill, in every prompt, and in the
validator's design" and D9 said "repeated in every prompt". No prompt stated it, and the
validator has nothing to enforce, since a plan is a file. Rather than soften the claim, the rule
went into all five prompts, which is the path used by agents with no skill support and the last
place a safety rule should depend on a second file being read. The README's "validator's design"
clause was dropped because nothing backed it.

**D16. The exit rule for security review is impact, not label.** Ten adversarial rounds ran
before release. Rounds one to three found Highs a hostile export bundle could use against a
creator; rounds four to seven found Mediums that were each a few lines; rounds eight to ten
found Lows that needed a hostile clone of the maintainer's own tool or a message cosmetic. A
fresh reviewer told to find something will always find a Low. So the gate is: a round
passes when nothing in it lets an attacker-controlled bundle run code, read or write outside
the episode folder or through the creator's files, put attacker text into the agent's
context, or exhaust the machine within the stated limits. Findings outside that rule are
logged here and fixed when they are cheap.
