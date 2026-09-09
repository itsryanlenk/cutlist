# Prompt 01 - clip plan for one episode

Folder must contain: `episodes/<id>/episode.mp4`, `episodes/<id>/captions.srt` (or .vtt),
`episodes/<id>/notes.md`, and optionally `episodes/<id>/markers.txt`.

```
Read skills/cutlist/SKILL.md, then follow references/clip-plan.md.

Episode folder: episodes/<id>
Guest: <name>
Both files are from the <raw recording | edited export>.

I want 5 to 8 clips of 15 to 30 seconds in publish order, each with title, description,
hashtags, tags, and category, plus the episode title, description, tags, category, and the
cold open. Use markers.txt as leads. Stop and tell me if the sync check fails.
When check_plan.py reports 0 fail, cut the previews and give me the bottom line.
```

If your agent supports skills, `$cutlist` or `/cutlist` plus the same text works.
