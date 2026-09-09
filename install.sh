#!/usr/bin/env bash
# Install the skill where your agent looks for skills. Copies (default) or symlinks the folder.
#
#   bash install.sh --codex            ->  ./.agents/skills/<slug>           (Codex, project; Cursor and Gemini CLI read it too)
#   bash install.sh --claude           ->  ./.claude/skills/<slug>           (Claude Code, project)
#   bash install.sh --cursor           ->  ./.cursor/skills/<slug>           (Cursor, project)
#   bash install.sh --gemini           ->  ./.gemini/skills/<slug>           (Gemini CLI, project)
#   bash install.sh --copilot          ->  ./.github/skills/<slug>           (GitHub Copilot, project)
#   bash install.sh --all              ->  all of the above
#   bash install.sh --global --codex   ->  ~/.agents/skills/<slug>           (Codex, every project)
#   bash install.sh --global --claude  ->  ~/.claude/skills/<slug>           (Claude Code, every project)
#   bash install.sh --global --copilot ->  ~/.copilot/skills/<slug>          (GitHub Copilot, every project)
#   add --link to symlink instead of copy (edits in this repo show up live)
#   add --into /path/to/project to install into another project folder
#
# Skill discovery paths change between agent versions. If your agent does not find the skill,
# check its documentation for the current path and copy skills/<slug> there by hand.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# Exactly one skill folder ships under skills/. Find it, and refuse to run unless it is real:
# an empty slug would make the destination below the skills root itself, and rm -rf on that
# would delete every skill the user has installed.
SLUG="$(find "$HERE/skills" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | head -1 || true)"
SRC="$HERE/skills/$SLUG"
if [ -z "$SLUG" ] || [ ! -f "$SRC/SKILL.md" ]; then
  echo "No skill found under $HERE/skills/ (expected skills/<slug>/SKILL.md). Nothing installed." >&2
  exit 1
fi
TARGET_ROOT="$(pwd)"; GLOBAL=0; LINK=0; AGENTS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --codex|--claude|--cursor|--gemini|--copilot) AGENTS+=("${1#--}") ;;
    --all) AGENTS=(codex claude cursor gemini copilot) ;;
    --global) GLOBAL=1 ;;
    --link) LINK=1 ;;
    --into) shift; TARGET_ROOT="$(cd "$1" && pwd)" ;;
    *) echo "unknown option $1"; exit 1 ;;
  esac; shift
done
[ ${#AGENTS[@]} -gt 0 ] || { sed -n '2,17p' "$0"; exit 1; }
for a in "${AGENTS[@]}"; do
  case "$a" in
    codex)  dir=".agents/skills" ;;
    claude) dir=".claude/skills" ;;
    cursor) dir=".cursor/skills" ;;
    gemini) dir=".gemini/skills" ;;
    copilot) if [ $GLOBAL -eq 1 ]; then dir=".copilot/skills"; else dir=".github/skills"; fi ;;
  esac
  if [ $GLOBAL -eq 1 ]; then base="$HOME/$dir"; else base="$TARGET_ROOT/$dir"; fi
  mkdir -p "$base"
  dest="$base/$SLUG"
  [ "$dest" != "$base" ] && [ "$dest" != "$base/" ] || { echo "refusing to touch $base" >&2; exit 1; }
  rm -rf "$dest"
  if [ $LINK -eq 1 ]; then ln -s "$SRC" "$dest"; echo "linked  $dest -> $SRC"
  else cp -R "$SRC" "$dest"; echo "copied  $SRC -> $dest"; fi
done
echo "Done. Restart your agent so it re-scans skills. Invoke with \$$SLUG (Codex) or /$SLUG (Claude Code), or just describe the task."
