# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) once the project
reaches 1.0. It is pre-1.0; anything may change.

## [Unreleased]

### Fixed

- `check_inputs.py` failed a correctly matched export whenever the video carried an outro, an
  end card, or trailing silence longer than the 3 second tolerance, and printed a single cause
  that was wrong in that case ("one file is the raw recording and the other is an edited
  export"), so the re-export it asked for came back identical. The verdict now depends on which
  way the gap runs. Captions reaching past the end of the video stays a hard stop with no way
  through. A video running on past the last word names both causes and takes `--silent-tail`
  from the creator. Five tests in `tests/test_hardening.py` pin it (D17).
- The never-publish rule is now in all five files under `prompts/`. The README said it was "in
  every prompt" and D9 said it was "repeated in every prompt"; no prompt stated it. The README's
  unsupported "and in the validator's design" clause was dropped (D18).
- Two items the eleventh-review entry listed as covered by a test had none: an unreadable caption
  file and a symlink loop. Both now have one, POSIX-only, in class `EleventhReviewGaps`.

### Changed

- D3's wording no longer reads "loudness and frames never pick", which a reader could set against
  the Energy row in the scoring rubric. It now says candidates come off the transcript and energy
  scores one row of six after that list exists. Behaviour did not change.

## [0.1.0] - 2026-09-09

First public release.

- One self-contained Agent Skill with five workflows: channel profile setup, clip plan,
  thumbnail trifecta, back-catalog retitle, and recorder export notes.
- Seven Python scripts, standard library plus Pillow: caption and video sync check, audio
  energy, still frames, plan validator, preview cuts, and thumbnail mockup.
- Installers for the Codex, Claude Code, Cursor, and Gemini CLI skill paths, plus a Claude
  Code plugin manifest and marketplace for one-command install.
- A thirteen-check self-test that builds a synthetic episode and runs every script. It runs in
  CI on Ubuntu.
- Paste-ready prompts for agents with no skill support, and a per-episode publish checklist.
- Input limits from ten pre-release security reviews, each with a unit test: finite and
  bounded times, caption and plan size caps, invisible-character stripping by Unicode
  category, frame and preview caps, a format whitelist and playlist refusal, programs and
  fonts never resolved from the working folder, outputs never written through a link and
  always confined to the episode folder, and installers that refuse to run without a real
  skill folder. Reasons in `docs/DECISIONS.md`.
