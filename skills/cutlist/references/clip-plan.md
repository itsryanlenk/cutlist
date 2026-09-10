# Workflow: clip plan

You turn one episode into a plan the creator can execute in their editor without thinking.
Transcript first. Audio and frames confirm. Your judgment decides.

## Step 0. Read context

1. `channel/channel_profile.md` (audience, tone, title formulas, links, hashtag pool, category
   default, and the Tools section: which recorder and editor the creator uses, whether a
   person is on camera, and the export and cut recipes written at setup). Every instruction
   you give the creator about exporting or cutting uses the tools named there.
2. `episodes/<id>/notes.md` and `episodes/<id>/markers.txt` if present. Markers are the creator's
   live "this was good" flags. Treat each one as a lead you must check, not a decision.

The video can be anything long with captions: a podcast, an interview, a webinar, a lecture, a
tutorial, a stream VOD, a keynote, a vlog. The rules below are the same for all of them. Where
a rule mentions a guest or a face, it applies when there is one.

## Step 1. Check inputs

```
python3 $SKILL/scripts/check_inputs.py "episodes/<id>/episode.mp4" "episodes/<id>/captions.srt"
```

If it prints `SYNC: FAIL`, stop. Tell the creator: "Captions and video are from different exports.
Export both from the same place (both raw, or both from the edited timeline)." Do not continue.

Read `episodes/<id>/transcript_compact.txt` end to end. It is short enough. Do not skim.

## Step 2. Build the candidate list (aim for 12 to 20)

While reading, mark any moment that has one of these:

- A specific number, name, tool, or date said out loud.
- A contrarian claim ("everyone says X, actually Y").
- A short story with a turning point ("and then I realized...").
- A direct instruction to the viewer ("do this before you...").
- A quotable phrase (something the host reacts to or repeats).
- Visible disagreement or surprise between host and guest.

Then run the audio pass and add any loud run you had not marked:

```
python3 $SKILL/scripts/audio_energy.py "episodes/<id>/episode.mp4" --top 25
```

Loud runs are leads. A laugh with nothing said is not a clip.

## Step 3. Score each candidate (0 to 2 on each, keep 8 or better out of 12)

| Test | 2 | 1 | 0 |
|---|---|---|---|
| Self-contained | Makes full sense with zero context | Needs one line of setup | Needs the episode |
| Hook in 2 s | First sentence is a claim, number, question, or contradiction | Hook arrives by 5 s | Slow start |
| One idea | Exactly one point, one payoff | Two points | Rambles |
| Payoff | Ends on a punchline, answer, or instruction | Ends fine | Trails off |
| Energy | Laugh, emphasis, or loud run confirms | Neutral | Flat |
| Speaker value (two or more speakers only) | The guest or the expert says the important part | Shared | Host only (allowed, but cap at 2 of these) |

With one speaker (a lecture, a tutorial, a solo vlog, a keynote), skip the last row and keep
8 or better out of 10.

Automatic reject: "as I said earlier", inside jokes, crosstalk, dead air over 1.5 s inside the
clip, anything that could be read as a promise of results ("you will make $X").

## Step 4. Set the exact cuts

For each keeper, set `start` on the first word of the hook sentence and `end` right after the
payoff word. Read the cue times in `segments.csv`. Use the cue start for `start`; use the cue
end plus 0.3 s for `end`. Target 15 to 30 s. If a great moment runs 32 s, keep it and say why
in `trim_notes`. Never over 35.

Check the picture:

```
python3 $SKILL/scripts/frames.py "episodes/<id>/episode.mp4" <start of each keeper> --cols 4
```

Open `frames/contact_sheet.jpg` with view_image. When a person is on camera, reject a clip if
the speaker is off camera, the frame is a glitch, or the face is hidden, and note in
`trim_notes` which speaker should fill the vertical frame ("speaker focus: guest"). When the
video is a screen, slides, or gameplay, reject a clip whose picture shows nothing for the
words (a blank slide, a loading screen) and note what the vertical frame should hold
("frame focus: the code editor, top half").

## Step 5. Pick the cold open and the thumbnail concept

The cold open is the strongest complete sentence in the whole episode, 10 seconds or less.
It becomes the first thing viewers hear. The episode title and the thumbnail must describe it.
That is the trifecta rule (see `$thumbnail-trifecta`). Pick it now, then write the title to match.

## Step 6. Write metadata

Read the formulas in `channel/channel_profile.md`. Defaults below apply when the profile is silent. Per item:

- **Title**: 100 characters max, aim under 70. The hook idea in the first 40 characters.
  No clickbait that the clip does not pay off. Numbers stay as the speaker's claim.
- **Description**: first line under 100 characters and it must restate the hook. Clips: two
  lines plus "Full episode on the channel." plus hashtags. Episode: hook line, "What we cover"
  bullets, chapters, guest links, the creator's link block from the profile, hashtags last.
- **Hashtags**: 3 to 5 from the pool. No spaces. The first three show above the title.
- **Tags**: 8 to 15 short phrases. Total field under 500 characters. Include the guest's name
  and product when public.
- **Category**: `27` Education for lessons and how-to, `28` Science & Technology for tools and
  dev topics, `22` People & Blogs for story-led episodes. One id per item. Use the profile default when unsure.
  Non-YouTube targets (TikTok, Reels): keep the same title and hook; skip tags and category.

## Step 7. Write the two outputs

`episodes/<id>/clip_plan.json` in the shape of `$SKILL/references/output-schema.md` (copy its keys).
`episodes/<id>/clip_plan.md` in the shape of `$SKILL/assets/clip_plan.template.md`, in publish order.

Publish order rule: strongest clip first, then alternate topics so two similar clips are not
back to back. The cold open moment can also be clip 1.

## Step 8. Validate and preview

```
python3 $SKILL/scripts/check_plan.py "episodes/<id>/clip_plan.json" "episodes/<id>/episode.mp4"
python3 $SKILL/scripts/cut_previews.py "episodes/<id>/episode.mp4" "episodes/<id>/clip_plan.json"
```

Fix every FAIL. Read every WARN and either fix it or explain it in the plan. Then report:
bottom line, the plan, risks. Tell the creator to watch `previews/` before cutting.
