# Episode checklist - Cutlist

Video: ________  Guest (or solo): ________________  Record date: ________  Publish date: ________

Your recorder, your editor, and the export and cut steps for them are in
`channel/channel_profile.md` under Tools. The steps below point there instead of naming a tool.

## A. Record (during the session)
- [ ] If your recorder has live markers, drop one when a good moment happens. Add a one-word note if you can.
- [ ] If there is a guest, get their name spelling, product name, and links before you stop recording.

## B. Export (10 minutes)
- [ ] Decide: raw recording, or edited export. Both files must come from the same place.
- [ ] Download **video** as MP4 -> `episodes/<id>/episode.mp4` (the profile says where the button is)
- [ ] Download **captions** as SRT or VTT -> `episodes/<id>/captions.srt`
- [ ] Copy `skills/cutlist/assets/notes.template.md` -> `episodes/<id>/notes.md`. Fill the kind of video, guest, and links.
- [ ] Copy marker times from the recorder or the editor -> `episodes/<id>/markers.txt` (optional)

## C. Plan (your agent, 5 minutes of your time)
- [ ] Open the folder in your agent. Paste **prompt 01**. Sync check must say OK.
- [ ] Read the bottom line and the plan. Watch every file in `previews/`.
- [ ] Swap or trim with **prompt 03** until you like all clips.
- [ ] Paste **prompt 02**. Open `thumb_mock_feed_320.png`. Can you read it? If not, cut words.

## D. Cut in your editor (per clip, about 3 minutes each)
- [ ] Follow the cut recipe in your profile: jump to the start time, split. Jump to the end time, split.
- [ ] Keep only that range. Frame 9:16 the way the profile says (speaker focus, or the screen detail the plan names).
- [ ] Captions on. Export. Name the file with the publish order number.
- [ ] Cold open: place the cold-open range at 00:00 of the full video, then export the video.

## E. Publish the video (YouTube Studio)
- [ ] Title from `clip_plan.md` (under 100 characters; the hook in the first 40).
- [ ] Description pasted in full. First line under 100 characters. Hashtags on the last line.
- [ ] Tags pasted. Category set.
- [ ] Thumbnail rebuilt from `thumbnail_brief.md`: same frame, same words, same side. 1280x720, under 2 MB.
- [ ] Trifecta check: thumbnail words = first 10 seconds = title = first description line.

## F. Publish the clips (one per day, or as the profile says)
- [ ] Vertical file uploaded. Title, description, hashtags, tags, category from the plan.
- [ ] Description ends with "Full video on the channel." and 3 to 5 hashtags.
- [ ] Related video set to the full video when the option is offered.

## G. Close out (2 minutes)
- [ ] Note anything the agent got wrong in `episodes/<id>/notes.md` under "Feedback".
- [ ] If a rule should change for every video, edit `channel/channel_profile.md`, not the prompt.

Limits to remember: title 100 chars, description 5,000 bytes, tags 500 chars total,
hashtags 3 to 5 (over 60 and YouTube ignores all), clips 15 to 30 s, cold open 10 s or less.
