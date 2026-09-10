# Reference: clip_plan.json (the output contract)

`check_plan.py` validates this file. Copy the keys exactly. Times are `HH:MM:SS.mmm`.

```json
{
  "episode_id": "ep06",
  "generated_by": "cutlist",
  "source": {"video": "episode.mp4", "captions": "captions.srt", "same_source": "raw", "sync_gap_s": 1.1},
  "episode": {
    "title": "He made $0 for 12 months. Now $20k+/month (Guest Name)",
    "description": "Hook line under 100 characters.\n\nWhat we cover:\n- ...\n\nChapters:\n00:00 Cold open\n...\n\nGuest links:\n...\n\n<creator link block from the profile>\n\n#tag #tag #tag",
    "tags": ["short phrase", "..."],
    "hashtags": ["#tag", "#tag", "#tag"],
    "category_id": "27",
    "cold_open": {
      "start": "00:12:30.100", "end": "00:12:39.800",
      "transcript_quote": "exact words from the captions",
      "why": "one line"
    },
    "thumbnail": {
      "frame_time": "00:12:31.000",
      "text": "2 TO 4 WORDS",
      "side": "right",
      "why": "where the face is, why this frame",
      "trifecta_check": {
        "first_10s": "how the words match the cold open",
        "title": "how the words match the title",
        "description": "how the words match description line 1"
      }
    }
  },
  "clips": [
    {
      "rank": 1, "publish_order": 1,
      "start": "00:12:30.100", "end": "00:12:55.000", "duration_s": 24.9,
      "speaker": "Guest",
      "hook_line": "exact first sentence the viewer hears",
      "title": "under 70 characters, hook in the first 40",
      "description": "one hook line\none context line\nFull episode on the channel.\n\n#tag #tag #tag",
      "hashtags": ["#tag", "#tag", "#tag"],
      "tags": ["...", "..."],
      "category_id": "27",
      "why": "one line on why this moment earns a clip",
      "trim_notes": "start on word X, end after word Y, speaker focus: guest",
      "risk": "none, or what could go wrong"
    }
  ],
  "rejected": [
    {"start": "00:00:00.500", "end": "00:00:05.000", "reason": "needs context; not self-contained"}
  ]
}
```

## What the validator checks

Platform limits (source: YouTube Data API `videos` resource and YouTube Help on hashtags):

| Field | Limit | Validator behavior |
|---|---|---|
| title | 100 characters, no `<` or `>` | fail over 100, warn over 70 |
| description | 5,000 bytes UTF-8 | fail over 5,000, warn if line 1 is over 100 characters |
| tags | 500 characters total; commas count; a tag with a space counts as quoted | fail over 500 |
| hashtags | more than 60 and the platform ignores all of them | fail over 60, warn over 5, must start with `#` and contain no spaces |
| category_id | known YouTube id | fail on unknown |

Clip rules (this skill's rules): duration 15 to 30 s target, 12 to 35 s hard; no overlaps;
`publish_order` present and unique; `hook_line` present; cold open 10 s or less;
thumbnail text 4 words or fewer; all three `trifecta_check` lines present.

A full, validated example lives in `examples/_example/clip_plan.json` at the repo root.
