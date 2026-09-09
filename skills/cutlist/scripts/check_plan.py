#!/usr/bin/env python3
"""Step 5. Check clip_plan.json before anyone acts on it.

Limits come from YouTube's own documentation (see README, "Sources").
  title        max 100 characters      (warn above 70: search results cut it)
  description  max 5,000 bytes UTF-8   (warn if the hook is not in the first 100 chars)
  tags         max 500 characters total, commas count, a tag with a space counts 2 extra
  hashtags     more than 60 on a video makes YouTube ignore all of them (warn above 5)
  category_id  must be a known YouTube category id

Clip rules (this system's rules, not YouTube's):
  duration 15 to 30 s (hard fail under 12 or over 35), no overlaps, clean order,
  cold open 12 s or less, thumbnail text 4 words or fewer.

Usage
  python3 scripts/check_plan.py episodes/ep05/clip_plan.json [episodes/ep05/episode.mp4]
Exit code 0 = pass (warnings allowed). Exit code 1 = fail.
"""

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_plan, order_number, parse_time, probe, utf8_stdout  # noqa: E402

CATEGORIES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music", "15": "Pets & Animals",
    "17": "Sports", "19": "Travel & Events", "20": "Gaming", "22": "People & Blogs",
    "23": "Comedy", "24": "Entertainment", "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology", "29": "Nonprofits & Activism",
}
TITLE_MAX = 100
TITLE_WARN = 70
DESC_MAX_BYTES = 5000
TAGS_MAX = 500
HASHTAG_POLICY_MAX = 60
HASHTAG_WARN = 5
CLIP_MIN, CLIP_MAX = 12.0, 35.0
CLIP_TARGET_MIN, CLIP_TARGET_MAX = 15.0, 30.0
COLD_OPEN_MAX = 12.0
THUMB_WORDS_MAX = 4

fails, warns = [], []


def fail(msg):
    fails.append(msg)


def warn(msg):
    warns.append(msg)


def tag_field_length(tags):
    parts = []
    for t in tags:
        t = str(t).strip()
        parts.append('"%s"' % t if " " in t else t)
    return len(",".join(parts))


def text_field(label, obj, key):
    """The field as a string. Anything else is a FAIL and an empty string."""
    value = obj.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        fail("%s: %s must be text, not %s" % (label, key, type(value).__name__))
        return ""
    return value


def text_list(label, obj, key):
    """The field as a list of strings. Anything else is a FAIL and an empty list."""
    value = obj.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        fail("%s: %s must be a list of text values" % (label, key))
        return []
    return value


def check_meta(label, obj):
    title = text_field(label, obj, "title")
    if not title:
        fail("%s: title is missing" % label)
    elif len(title) > TITLE_MAX:
        fail("%s: title is %d chars (max %d)" % (label, len(title), TITLE_MAX))
    elif len(title) > TITLE_WARN:
        warn("%s: title is %d chars; search results cut around %d" % (label, len(title), TITLE_WARN))
    if "<" in title or ">" in title:
        fail("%s: title contains < or > (YouTube rejects these)" % label)

    desc = text_field(label, obj, "description")
    if not desc:
        fail("%s: description is missing" % label)
    else:
        nbytes = len(desc.encode("utf-8"))
        if nbytes > DESC_MAX_BYTES:
            fail("%s: description is %d bytes (max %d)" % (label, nbytes, DESC_MAX_BYTES))
        first = desc.strip().splitlines()[0] if desc.strip() else ""
        if len(first) > 100:
            warn("%s: first description line is %d chars; only about 100 show before 'more'" % (label, len(first)))

    tags = text_list(label, obj, "tags")
    if tags:
        n = tag_field_length(tags)
        if n > TAGS_MAX:
            fail("%s: tags field is %d chars (max %d)" % (label, n, TAGS_MAX))
    else:
        warn("%s: no tags" % label)

    hashtags = text_list(label, obj, "hashtags")
    for h in hashtags:
        if not re.match(r"^#[^\s#]+$", str(h)):
            fail("%s: bad hashtag %r (must start with # and contain no spaces)" % (label, h))
    if len(hashtags) > HASHTAG_POLICY_MAX:
        fail("%s: %d hashtags; over %d and YouTube ignores all of them" % (label, len(hashtags), HASHTAG_POLICY_MAX))
    elif len(hashtags) > HASHTAG_WARN:
        warn("%s: %d hashtags; 3 to 5 is the working rule" % (label, len(hashtags)))
    elif not hashtags:
        warn("%s: no hashtags" % label)

    cat = obj.get("category_id", "")
    cat = str(cat) if isinstance(cat, (str, int)) and not isinstance(cat, bool) else ""
    if cat not in CATEGORIES:
        fail("%s: category_id %r is not a known id (use one of %s)" % (
            label, cat, ", ".join("%s=%s" % kv for kv in CATEGORIES.items())))


def report(clips):
    for w in warns:
        print("WARN  " + w)
    for f in fails:
        print("FAIL  " + f)
    print("RESULT: %d fail, %d warn, %d clips" % (len(fails), len(warns), len(clips)))
    sys.exit(1 if fails else 0)


def main(argv):
    utf8_stdout()
    if len(argv) < 2:
        sys.exit(__doc__)
    try:
        plan = load_plan(argv[1])
    except (OSError, ValueError) as exc:
        fail("plan: %s" % exc)
        report([])
    duration = None
    if len(argv) > 2 and Path(argv[2]).exists():
        duration = probe(argv[2])["duration"]
    try:
        check(plan, duration)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        # A wrong type somewhere in the plan is a failed check, never a traceback.
        fail("plan: unexpected value (%s: %s)" % (type(exc).__name__, exc))
    report(plan.get("clips", []))


def check(plan, duration):
    ep = plan.get("episode", {})
    if not ep:
        fail("plan has no 'episode' block")
    else:
        check_meta("episode", ep)
        co = ep.get("cold_open")
        if not co:
            warn("episode: no cold_open recommended (the first 10 s drive the thumbnail rule)")
        else:
            try:
                d = parse_time(co["end"]) - parse_time(co["start"])
            except (KeyError, TypeError, ValueError) as exc:
                fail("cold_open: bad start/end (%s)" % exc)
                d = None
            if d is None:
                pass
            elif d <= 0:
                fail("cold_open: end is before start")
            elif d > COLD_OPEN_MAX:
                warn("cold_open: %.1f s is long; keep it at or under %.0f s" % (d, COLD_OPEN_MAX))
        th = ep.get("thumbnail")
        if not th:
            fail("episode: no thumbnail block")
        else:
            words = text_field("thumbnail", th, "text").split()
            if not words:
                fail("thumbnail: text is empty")
            elif len(words) > THUMB_WORDS_MAX:
                warn("thumbnail: text has %d words; %d or fewer reads at feed size" % (len(words), THUMB_WORDS_MAX))
            tc = th.get("trifecta_check", {})
            for key in ("first_10s", "title", "description"):
                if not tc.get(key):
                    fail("thumbnail.trifecta_check.%s is missing (must state how the image matches it)" % key)
            if not th.get("frame_time"):
                fail("thumbnail: frame_time is missing")

    clips = plan.get("clips", [])
    if not clips:
        fail("plan has no clips")
    if len(clips) < 5:
        warn("only %d clips; the target is 5 to 8" % len(clips))
    spans = []
    orders = []
    for i, c in enumerate(clips, 1):
        label = "clip %d" % i
        try:
            s, e = parse_time(c["start"]), parse_time(c["end"])
        except (KeyError, TypeError, ValueError) as exc:
            fail("%s: bad start/end (%s)" % (label, exc))
            continue
        d = e - s
        if d <= 0:
            fail("%s: end is before start" % label)
        elif d < CLIP_MIN or d > CLIP_MAX:
            fail("%s: %.1f s is outside the hard range %.0f to %.0f s" % (label, d, CLIP_MIN, CLIP_MAX))
        elif d < CLIP_TARGET_MIN or d > CLIP_TARGET_MAX:
            warn("%s: %.1f s is outside the target %.0f to %.0f s; say why in trim_notes" % (
                label, d, CLIP_TARGET_MIN, CLIP_TARGET_MAX))
        if duration and e > duration + 0.5:
            fail("%s: ends at %.1f s but the video is %.1f s long" % (label, e, duration))
        if "duration_s" in c:
            try:
                ds = float(c["duration_s"])
            except (TypeError, ValueError):
                ds = None
            if ds is None or not math.isfinite(ds):
                fail("%s: duration_s is not a number" % label)
            elif abs(ds - d) > 0.6:
                warn("%s: duration_s says %.1f but start/end give %.1f" % (label, ds, d))
        for (s2, e2, j) in spans:
            if s < e2 and s2 < e:
                fail("%s overlaps clip %d" % (label, j))
                break  # one line per clip; a plan of identical clips would otherwise print n squared lines
        spans.append((s, e, i))
        if not text_field(label, c, "hook_line"):
            fail("%s: hook_line is missing (the first sentence the viewer hears)" % label)
        if not c.get("why"):
            warn("%s: no 'why' (one line on why this moment earns a clip)" % label)
        try:
            orders.append(order_number(c))
        except ValueError as exc:
            fail("%s: %s" % (label, exc))
        check_meta(label, c)
    if len(set(orders)) != len(orders):
        fail("publish_order must be unique on every clip")


if __name__ == "__main__":
    main(sys.argv)
