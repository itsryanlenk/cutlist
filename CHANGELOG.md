# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) once the project
reaches 1.0. It is pre-1.0; anything may change.

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
- Input limits from eight pre-release security reviews, each with a unit test: finite and
  bounded times, caption and plan size caps, invisible-character stripping by Unicode
  category, frame and preview caps, a format whitelist and playlist refusal, programs and
  fonts never resolved from the working folder, outputs never written through a link and
  always confined to the episode folder, and installers that refuse to run without a real
  skill folder. Reasons in `docs/DECISIONS.md`.
