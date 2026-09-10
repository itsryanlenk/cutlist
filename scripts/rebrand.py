#!/usr/bin/env python3
"""Rebrand this repository from the working name to your brand.

Reads brand.json, then:
  1. Replaces the placeholders [AUTHOR NAME], [GITHUB USER], [SLUG] everywhere.
  2. Replaces the working slug "podcast-clipper" with your slug, and the working
     display name "Podcast Clipper" with your brand name, in every text file.
  3. Renames skills/podcast-clipper/ to skills/<your-slug>/.
  4. Prints every file it touched. Run with --dry-run first to see the plan.

Usage
  python3 scripts/rebrand.py brand.json --dry-run
  python3 scripts/rebrand.py brand.json

Run it once, on a clean git tree, then commit. It refuses to run a second time.
Files are rewritten byte for byte apart from the replaced text, so line endings
survive on every platform (a shell script rewritten as CRLF stops running).
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

TEXT_EXT = {".md", ".py", ".sh", ".ps1", ".json", ".yml", ".yaml", ".txt", ".toml", ""}
SKIP_DIRS = {".git", "__pycache__", "node_modules", "episodes", "channel"}
OLD_SLUG = "podcast-clipper"
OLD_NAME = "Podcast Clipper"


def replace_with(p, data):
    """Write data over p through a temp file with an unguessable name, then a replace.
    A predictable temp name could be pre-planted as a hard link and written through."""
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix="." + p.name + ".", suffix=".rebrand-tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg_path = Path(sys.argv[1])
    dry = "--dry-run" in sys.argv
    root = Path(__file__).resolve().parent.parent
    root_real = Path(os.path.realpath(root))
    # brand.json is rewritten below, so it gets the same rules as every other file: a regular
    # file, not a link, and really inside this repository.
    st = os.lstat(cfg_path)
    if os.path.islink(cfg_path) or not os.path.isfile(cfg_path) or st.st_nlink > 1:
        sys.exit("%s must be a plain file inside the repository, not a link." % cfg_path)
    cfg_real = Path(os.path.realpath(cfg_path))
    if root_real != cfg_real.parent and root_real not in cfg_real.parents:
        sys.exit("%s is outside the repository." % cfg_path)
    cfg = json.loads(cfg_path.read_bytes().decode("utf-8"))

    if cfg.get("_applied"):
        sys.exit("brand.json says the rebrand was already applied. It runs once; start from a clean copy to redo it.")

    slug = cfg["slug"].strip()
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", slug):
        sys.exit("slug must be lowercase letters, digits, and hyphens: %r" % slug)
    name = cfg["brand_name"].strip()
    author = cfg["author"].strip()
    gh = cfg["github_user"].strip()
    if "[" in author or "[" in gh:
        sys.exit("Fill in author and github_user in brand.json first.")

    pairs = [
        ("[AUTHOR NAME]", author),
        ("[GITHUB USER]", gh),
        ("[SLUG]", slug),
        (OLD_SLUG, slug),
        (OLD_NAME, name),
    ]
    tagline = (cfg.get("tagline") or "").strip()
    if tagline and tagline.lower() != "keep":
        pairs.append(("Transcript-first clip planning, metadata, and thumbnail mockups for video podcasts.", tagline))

    touched = []
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_symlink() or not p.is_file() or p.suffix.lower() not in TEXT_EXT:
            continue
        if p.name == "rebrand.py" or p.name == "brand.json":
            continue
        # rglob follows Windows junctions (and, on older Pythons, symlinked folders).
        # Only rewrite files whose real location is inside this repository.
        real = Path(os.path.realpath(p))
        if real != root_real and root_real not in real.parents:
            continue
        if os.lstat(p).st_nlink > 1:
            sys.exit("%s has more than one hard link; rebrand never writes through links. Copy the tree first." % p.relative_to(root))
        data = p.read_bytes()
        try:
            s = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new = s
        for a, b in pairs:
            new = new.replace(a, b)
        if new != s:
            touched.append(p.relative_to(root))
            if not dry:
                replace_with(p, new.encode("utf-8"))

    # Fill brand.json's own placeholders so no bracket text remains anywhere, and mark it applied.
    if not dry:
        cfg["homepage"] = cfg.get("homepage", "").replace("[GITHUB USER]", gh).replace("[SLUG]", slug)
        cfg["_comment"] = "Applied on this repo. Do not run rebrand.py again."
        cfg["_applied"] = True
        replace_with(cfg_path, (json.dumps(cfg, indent=2) + "\n").encode("utf-8"))

    old_dir = root / "skills" / OLD_SLUG
    new_dir = root / "skills" / slug
    rename = old_dir.exists() and slug != OLD_SLUG
    if rename and not dry:
        old_dir.rename(new_dir)

    print("%s%d files changed:" % ("DRY RUN: " if dry else "", len(touched)))
    for t in touched:
        print("  " + str(t))
    if rename:
        print("%srenamed skills/%s -> skills/%s" % ("would have " if dry else "", OLD_SLUG, slug))
    print("Next: review the diff, run bash tests/selftest.sh, then commit.")


if __name__ == "__main__":
    main()
