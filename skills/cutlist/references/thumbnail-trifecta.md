# Workflow: thumbnail (the trifecta rule)

## The rule

A thumbnail must describe three things at once:

1. The first 10 seconds of the video (the cold open).
2. The title.
3. The first line of the description.

If the three do not say the same thing, the viewer clicks on one promise and gets another.
That is a bounce. Fix the words until all three match. Then make the picture say it too.

## Inputs

- `episodes/<id>/clip_plan.json` with `episode.cold_open`, `episode.title`, `episode.description`.
- `episodes/<id>/episode.mp4`.

If `cold_open` is missing, run the clip-plan workflow first. Do not invent one here.

## Step 1. Write the words

Take the cold-open sentence. Reduce it to 2 to 4 words that also appear in (or plainly restate)
the title and the first description line. Uppercase. One idea. Examples of the shape:

- "QUIT VC. GO SOLO."
- "README = FUNNEL"
- "SHIP FIRST. QUIT LATER."

Test: read the words, then read the title. Same promise? Read the first description line.
Same promise? If not, change the weakest of the three, not the strongest.

## Step 2. Pick the frame

Pull frames from the 20 seconds around the cold open, two seconds apart:

```
python3 $SKILL/scripts/frames.py episodes/<id>/episode.mp4 --range <cold_open_start - 5 s> <cold_open_end + 5 s> --step 2 --cols 5
```

Open `frames/contact_sheet.jpg` with view_image. Choose the frame where:

- the person who says the cold-open line is on camera,
- eyes are open and the face is expressive (mid-word is fine, a closed-eye blink is not),
- the face sits on the left or right third, leaving room for text on the other side,
- nothing ugly is in the frame (hands blocking the face, an overlay, a glitch).

Record `frame_time` and which side the face is on. Text goes on the opposite side.

## Step 3. Render the mockup

```
python3 $SKILL/scripts/thumbnail_mockup.py --video episodes/<id>/episode.mp4 --time <frame_time> \
  --text "<the words>" --side <left|right> --out episodes/<id>/thumb_mock.png
```

Open `thumb_mock_feed_320.png` with view_image. That is the size viewers see in the feed.
If you cannot read the words, cut words and re-run. Do not shrink the font by hand.

## Step 4. Write `episodes/<id>/thumbnail_brief.md`

The creator rebuilds the mockup in their design tool. Give them exactly this:

```
# Thumbnail brief - <episode id>

Frame: <frame_time> (file: frames/f_<time>.jpg). Face on the <left|right>.
Text: <the words> (uppercase, 2 lines max, on the <side>).
Style: white bold sans, thick black outline, accent bar under the text.
Darken the text side about 60 percent so the words read at small size.
Safe zone: keep text away from the bottom-right corner (YouTube puts the duration there).
Export: 1280x720 PNG or JPG, under 2 MB.

Trifecta check
- First 10 s: "<cold open quote>" -> thumbnail says "<words>"
- Title: "<title>" -> thumbnail says "<words>"
- Description line 1: "<line>" -> thumbnail says "<words>"

Shorts frame (no custom thumbnail needed): for each clip, grab the frame at the clip's start
plus 1 second. The editor sets it on export; YouTube Studio can change it later.
```

For a series (a numbered vlog, an episode number), add `--tag "EP 5"` or `--tag "WEEK 7"` to the mockup command.

Copy the three trifecta lines into `clip_plan.json` under `episode.thumbnail.trifecta_check`
and run `python3 $SKILL/scripts/check_plan.py` again. It fails if any of the three is missing.

## What this skill does not do

- No AI-generated faces. The frame is always a real frame of the host or the guest.
- No second mockup. One image, one promise. If the creator wants variants, they ask.
- No claims in the text that the episode does not pay off in the first 10 seconds.
