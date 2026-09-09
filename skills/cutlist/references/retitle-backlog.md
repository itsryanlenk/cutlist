# Workflow: retitle a back catalog

Give every published video on a channel a title that follows one formula per series.
Nothing gets published by you. The creator changes each title in their studio.

## Inputs

`channel/backlog.md` in the creator's project, one line per video:

```
<url or id> | <current title> | <guest name or "solo"> | <series> | <length> | <views> | <age>
```

If the file does not exist, ask the creator to paste titles from their studio's content page,
or to screenshot it. Build the file from what they give you. Views and age are optional.

## Step 1. Find the series and the voices

Group titles by series (interview show, solo vlog, tutorial). Note how many title voices
exist inside each series: Title Case vs sentence case vs lowercase, suffix patterns like
`| Guest | Show Name`, and series tags written three different ways.

## Step 2. Look for the shape of the winners

If views are present, sort each series by views per day of age. Read the top three titles
aloud. Look for what they share in the first sentence: a concrete number, a reversal
("made $0 for a year, now..."), a direct claim, a question. Write one line naming the shape.

State the caveats every time: small counts, recency (videos under 48 hours old say nothing),
and any performance badge from a browser extension whose definition you do not know.
Call it a pattern worth copying, not a proven cause.

## Step 3. Set one formula per series

Defaults, used when the winners do not suggest something better:

- Interview show: `<Reversal or claim with the guest's own number>. <Result> (Guest Name)`
- Solo vlog or series: `<One-sentence hook in the host's voice>. <Series tag>[, week N]`
- Tutorial: `How to <result> with <tool> in <constraint>`

Rules for every formula:
- Sentence case. Hook in the first 40 characters. Under 70 characters when possible; 100 is the hard limit.
- No show name in the title (it belongs in the thumbnail wordmark and the playlist).
- Guest name last, in parentheses.
- Numbers stay as the speaker's claim. Add no numbers the video did not state.
- One series tag, written one way.

## Step 4. Propose

Write `channel/backlog_retitled.md` with a table:

| # | Series | Current (chars) | Proposed (chars) | Note |

Keep any title that already follows the formula and performs well. Say "keep as is" and why.
Do not touch a winner.

## Step 5. Sequence the change

Tell the creator: retitle the whole batch in one sitting; change thumbnails on a different
day, one series at a time, so the two changes can be told apart. Then offer to derive the
title formula into `channel/channel_profile.md` so new uploads follow it.
