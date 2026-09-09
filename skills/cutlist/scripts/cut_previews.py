#!/usr/bin/env python3
"""Step 6. Cut rough preview clips from clip_plan.json.

These previews are for REVIEW only. They are 16:9, no captions, no reframing.
The creator makes the real vertical clips in their editor using the same start/end times.
The optional --vertical flag also writes a center-cropped 9:16 preview so the creator
can see whether a center crop keeps the speaker in frame.

A plan with more than 20 items, or a clip over 60 seconds, is refused unless you pass
--force. The plan is written by the agent, and a runaway plan means hundreds of encodes.

Usage
  python3 scripts/cut_previews.py episodes/ep05/episode.mp4 episodes/ep05/clip_plan.json
  python3 scripts/cut_previews.py episodes/ep05/episode.mp4 episodes/ep05/clip_plan.json --vertical
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import FF_IN, fmt_mmss, load_plan, media_path, parse_time, probe, require_tool, run, utf8_stdout  # noqa: E402

ITEM_LIMIT = 20
CLIP_MAX_S = 60.0
ORDER_MAX = 999


def _order(clip):
    """publish_order (or rank) as a whole number from 1 to ORDER_MAX. It names a file."""
    v = clip.get("publish_order", clip.get("rank"))
    if isinstance(v, bool) or not isinstance(v, int):
        try:
            v = int(str(v).strip())
        except (TypeError, ValueError):
            raise ValueError("publish_order must be a whole number from 1 to %d" % ORDER_MAX)
    if not 1 <= v <= ORDER_MAX:
        raise ValueError("publish_order must be a whole number from 1 to %d" % ORDER_MAX)
    return v


def plan_items(plan, force=False):
    """List of (name, start_s, end_s) from a plan. Refuses an oversized plan unless forced."""
    items = []
    co = plan.get("episode", {}).get("cold_open")
    if co:
        items.append(("cold_open", parse_time(co["start"]), parse_time(co["end"])))
    for c in plan.get("clips", []):
        items.append(("clip_%03d" % _order(c), parse_time(c["start"]), parse_time(c["end"])))
    for name, s, e in items:
        if e <= s:
            raise ValueError("%s ends before it starts (%s to %s)" % (name, fmt_mmss(s), fmt_mmss(e)))
    if not force:
        if len(items) > ITEM_LIMIT:
            raise ValueError("%d items to cut; a plan has 5 to 8 clips. Pass --force if you mean it." % len(items))
        for name, s, e in items:
            if e - s > CLIP_MAX_S:
                raise ValueError("%s runs %.1f s; previews are for clips under %.0f s. Pass --force if you mean it." % (
                    name, e - s, CLIP_MAX_S))
    return items


def cut(video, start, end, out, vertical=False):
    vf = ["-vf", "crop=ih*9/16:ih,scale=540:960"] if vertical else ["-vf", "scale=854:-2"]
    run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % start, "-to", "%.3f" % end, *FF_IN, "-i", media_path(video),
         *vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-c:a", "aac", "-b:a", "96k",
         "-movflags", "+faststart", str(out)])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("plan")
    ap.add_argument("--vertical", action="store_true", help="also write 9:16 center-crop previews")
    ap.add_argument("--force", action="store_true", help="cut even if the plan is oversized")
    args = ap.parse_args()
    utf8_stdout()
    require_tool("ffmpeg")

    video = Path(args.video)
    if not video.exists():
        sys.exit("File not found: %s" % video)
    probe(video)  # refuses playlist formats before any cut
    try:
        plan = load_plan(args.plan)
        items = plan_items(plan, force=args.force)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        sys.exit("Bad plan: %s" % exc)
    out_dir = video.parent / "previews"
    out_dir.mkdir(exist_ok=True)

    for name, s, e in items:
        out = out_dir / ("%s_%s.mp4" % (name, fmt_mmss(s).replace(":", "-")))
        cut(video, s, e, out)
        print("wrote %s  (%s to %s, %.1f s)" % (out, fmt_mmss(s), fmt_mmss(e), e - s))
        if args.vertical:
            outv = out_dir / ("%s_%s_9x16.mp4" % (name, fmt_mmss(s).replace(":", "-")))
            cut(video, s, e, outv, vertical=True)
            print("wrote %s  (center crop, rough guide only)" % outv)


if __name__ == "__main__":
    main()
