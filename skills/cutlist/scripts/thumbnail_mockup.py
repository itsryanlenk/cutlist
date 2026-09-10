#!/usr/bin/env python3
"""Step 7. Build ONE thumbnail mockup from a real frame of the episode.

The mockup is a layout guide, not a finished thumbnail. The creator rebuilds it in
her design tool with the same frame, the same words, and the same placement.

What it does
  1. Grabs a frame from the video at the time you give (or uses a frame file).
  2. Fits it to 1280 x 720 (YouTube's 16:9 thumbnail size).
  3. Darkens the text side with a gradient so the words stay readable.
  4. Draws the text in big bold letters (4 words or fewer, 2 lines max).
  5. Writes thumb_mock.png and thumb_mock_feed_320.png (what it looks like
     at feed size). If you cannot read the small one, the text is too long.

Needs Pillow:  python3 -m pip install pillow

Usage
  python3 scripts/thumbnail_mockup.py --video episodes/ep05/episode.mp4 --time 12:40 \
      --text "QUIT VC. $25K MRR" --side right --out episodes/ep05/thumb_mock.png
  python3 scripts/thumbnail_mockup.py --frame episodes/ep05/frames/f_00-12-40.000.jpg --text "..." --out ...
  python3 scripts/thumbnail_mockup.py --video vlog.mp4 --time 0:12 --text "20 SIGNED UP ANYWAY" --tag "WEEK 7" --out ...
"""

import argparse
import os
import re
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (FF_IN, IMG_OUT, check_source, commit_target, find_font, media_path, parse_time, probe,  # noqa: E402
                     refuse_link, require_tool, run_writing, show, temp_target, utf8_stdout)

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
except ImportError:
    sys.exit("Pillow is not installed. Run: python3 -m pip install pillow")

W, H = 1280, 720
ASPECT_MAX = 8.0  # wider or taller than this is not a video frame
# Bare names are looked up in the system font folders only (see find_font), never in the
# working folder, so a font file among the creator's inputs is never parsed.
FONT_CANDIDATES = ["impact.ttf", "Impact.ttf", "arialbd.ttf", "Arial Bold.ttf",
                   "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
_FONT_PATH = None


def load_font(size):
    global _FONT_PATH
    if _FONT_PATH is None:
        _FONT_PATH = find_font(FONT_CANDIDATES) or ""
    if _FONT_PATH:
        try:
            return ImageFont.truetype(_FONT_PATH, size), _FONT_PATH
        except OSError:
            pass
    return ImageFont.load_default(), "default (install a bold TTF for a real preview)"


TEXT_MAX_CHARS = 60  # four words; anything longer never fits at feed size anyway
TAG_MAX_CHARS = 20
FRAME_MAX_PIXELS = 8192 * 4320  # an 8K frame; larger is not a frame from a video
FRAME_MAX_BYTES = 50 * 1024 * 1024  # Pillow keeps every metadata segment of a JPEG in memory


def check_frame_file(path):
    """Refuse a frame that is a link, not a regular file, or too large to hold."""
    refuse_link(path)
    st = os.stat(path)
    if not stat.S_ISREG(st.st_mode):
        raise ValueError("%s is not a regular file." % show(path))
    if st.st_size > FRAME_MAX_BYTES:
        raise ValueError("%s is %d MB; a frame is under %d MB." % (show(path), st.st_size // (1024 * 1024), FRAME_MAX_BYTES // (1024 * 1024)))
_HEX_RE = re.compile(r"#?[0-9a-fA-F]{6}")


def hex_to_rgb(h):
    """'#RRGGBB' or 'RRGGBB' to a tuple. Anything else is a ValueError, never a traceback."""
    if not _HEX_RE.fullmatch(h or ""):
        raise ValueError("--accent must be a six-digit hex color like #FFD400, got %r" % (h[:20] if h else h))
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cover(img):
    """Crop img to 16:9 in its own coordinates, then scale to W x H.

    Cropping first keeps the intermediate at most the source size. Scaling first would
    turn a 4096x2 frame into a gigapixel image before the crop.
    """
    return ImageOps.fit(img, (W, H), method=Image.LANCZOS, centering=(0.5, 0.5))


def gradient(side):
    """Black gradient, opaque on the text side, clear on the other."""
    g = Image.new("L", (W, 1))
    px = g.load()
    for x in range(W):
        f = x / (W - 1)
        if side == "left":
            f = 1 - f
        # strong near the text edge, fading to nothing past the middle
        a = max(0.0, min(1.0, (f - 0.35) / 0.65))
        px[x, 0] = int(a * 205)
    return g.resize((W, H))


def wrap_lines(words, max_lines=2):
    if len(words) <= 2 or max_lines == 1:
        return [" ".join(words)]
    mid = (len(words) + 1) // 2
    return [" ".join(words[:mid]), " ".join(words[mid:])]


def fit_text(draw, lines, max_w, max_h):
    for size in range(170, 60, -6):
        font, name = load_font(size)
        widths = [draw.textlength(ln, font=font) for ln in lines]
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        line_h = (bbox[3] - bbox[1]) + int(size * 0.28)
        if max(widths) <= max_w and line_h * len(lines) <= max_h:
            return font, name, widths, line_h
    font, name = load_font(60)
    widths = [draw.textlength(ln, font=font) for ln in lines]
    return font, name, widths, 70


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video")
    ap.add_argument("--time", help="time in the video to grab, like 12:40 or 00:12:40.5")
    ap.add_argument("--frame", help="use this image instead of grabbing from the video")
    ap.add_argument("--text", required=True, help="4 words or fewer")
    ap.add_argument("--side", choices=["left", "right"], default="right",
                    help="which side the TEXT goes on (put it opposite the face)")
    ap.add_argument("--accent", default="#FFD400", help="accent color hex, default warm yellow")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", help='small series tag in the top corner opposite the text, like "WEEK 7" or "EP 5"')
    ap.add_argument("--no-badge", action="store_true", help="omit the small MOCKUP tag")
    args = ap.parse_args()
    utf8_stdout()

    out = Path(args.out)
    feed_path = out.with_name(out.stem + "_feed_320.png")
    # Never write over the input. The frame and the video belong to the creator.
    for src in (args.frame, args.video):
        if src and Path(src).resolve() in (out.resolve(), feed_path.resolve()):
            sys.exit("--out must not be the same file as --frame or --video. Pick another output name.")
    # Write only inside the episode folder: the folder of --video, or the folder of --frame
    # and its parent (frames/ sits inside the episode folder). Never create folders.
    roots = []
    if args.video:
        roots.append(Path(args.video).resolve().parent)
    if args.frame:
        fp = Path(args.frame).resolve().parent
        roots += [fp, fp.parent]
    if not roots:
        sys.exit("Give --frame, or both --video and --time.")
    out_parent = out.resolve().parent
    if not out_parent.is_dir():
        sys.exit("--out folder does not exist: %s. The script writes into the episode folder and never creates folders." % show(out_parent))
    if not any(out_parent == r or r in out_parent.parents for r in roots):
        sys.exit("--out must be inside the episode folder (%s)." % show(roots[0]))
    try:
        for target in (out, feed_path):
            refuse_link(target)
            for src in (args.frame, args.video):
                if src and target.exists() and os.path.samefile(src, target):
                    sys.exit("--out must not be the same file as --frame or --video. Pick another output name.")
        if args.frame:
            frame_path = Path(args.frame)
        elif args.video and args.time:
            require_tool("ffmpeg")
            info = probe(args.video)  # refuses playlist formats before ffmpeg reads them
            check_source(info["width"], info["height"])
            frame_path = out.parent / "thumb_source_frame.jpg"
            tmp = temp_target(frame_path)
            run_writing(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % parse_time(args.time), *FF_IN, "-i",
                         media_path(args.video), "-frames:v", "1", "-q:v", "2", *IMG_OUT, str(tmp)], tmp)
            commit_target(tmp, frame_path)
        else:
            sys.exit("Give --frame, or both --video and --time.")
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    if len(args.text) > TEXT_MAX_CHARS:
        sys.exit("--text is %d characters; the limit is %d. Four words, one idea." % (len(args.text), TEXT_MAX_CHARS))
    if args.tag and len(args.tag) > TAG_MAX_CHARS:
        sys.exit("--tag is %d characters; the limit is %d." % (len(args.tag), TAG_MAX_CHARS))
    try:
        accent = hex_to_rgb(args.accent)
    except ValueError as exc:
        sys.exit(str(exc))
    words = args.text.strip().split()
    if not words:
        sys.exit("--text is empty.")
    if len(words) > 4:
        print("WARN: %d words. 4 or fewer reads at feed size. Shorten it." % len(words))

    # Only the two image formats a frame can be. Pillow otherwise picks a plugin by content,
    # and an EPS disguised as a .jpg would hand the file to Ghostscript.
    try:
        check_frame_file(frame_path)
        src_img = Image.open(frame_path, formats=["JPEG", "PNG"])
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        sys.exit("%s is not a JPEG or PNG frame this tool will open (%s)." % (show(frame_path), str(exc)[:120]))
    with src_img:
        # Opening reads the header only. Check the shape and the pixel count before decoding.
        if src_img.width * src_img.height > FRAME_MAX_PIXELS:
            sys.exit("The frame is %dx%d, which is %d megapixels; a video frame is under %d." % (
                src_img.width, src_img.height, src_img.width * src_img.height // 1_000_000, FRAME_MAX_PIXELS // 1_000_000))
        if src_img.width / src_img.height > ASPECT_MAX or src_img.height / src_img.width > ASPECT_MAX:
            sys.exit("The frame is %dx%d, which is not a video frame." % (src_img.width, src_img.height))
        base = cover(src_img.convert("RGB"))
    shade = Image.new("RGB", (W, H), (0, 0, 0))
    base = Image.composite(shade, base, gradient(args.side))

    draw = ImageDraw.Draw(base)
    lines = wrap_lines([w.upper() for w in words])
    max_w = int(W * 0.56)
    font, font_name, widths, line_h = fit_text(draw, lines, max_w, int(H * 0.62))
    accent = hex_to_rgb(args.accent)

    total_h = line_h * len(lines)
    y = (H - total_h) // 2
    margin = 48
    for ln, wdt in zip(lines, widths):
        x = W - margin - wdt if args.side == "right" else margin
        draw.text((x, y), ln, font=font, fill=(255, 255, 255), stroke_width=max(4, line_h // 14),
                  stroke_fill=(0, 0, 0))
        y += line_h
    # accent bar under the text block
    bar_w = int(max(widths))
    bar_x = W - margin - bar_w if args.side == "right" else margin
    draw.rectangle([bar_x, y + 6, bar_x + bar_w, y + 22], fill=accent)

    if args.tag:
        tag_font, _ = load_font(44)
        tag = args.tag.strip().upper()
        tw = draw.textlength(tag, font=tag_font) + 36
        tx = W - margin - tw if args.side == "left" else margin
        draw.rectangle([tx, 40, tx + tw, 104], fill=accent)
        draw.text((tx + 18, 48), tag, font=tag_font, fill=(0, 0, 0))

    if not args.no_badge:
        small, _ = load_font(22)
        draw.rectangle([14, H - 46, 126, H - 14], fill=(0, 0, 0))
        draw.text((22, H - 42), "MOCKUP", font=small, fill=accent)

    try:
        tmp = temp_target(out)
        base.save(tmp)
        commit_target(tmp, out)
        feed = base.resize((320, 180), Image.LANCZOS)
        tmp = temp_target(feed_path)
        feed.save(tmp)
        commit_target(tmp, feed_path)
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))
    print("font: %s" % font_name)
    print("WROTE %s" % show(out))
    print("WROTE %s  <- open this one. If you cannot read it, cut words." % show(feed_path))


if __name__ == "__main__":
    main()
