# Episode checklist - Cutlist

Episode: ________  Guest: ________________  Record date: ________  Publish date: ________

## A. Record (during the session)
- [ ] Drop a marker when a good moment happens (Riverside: press **M**). Add a one-word note if you can.
- [ ] Get the guest's name spelling, product name, and links before you stop recording.

## B. Export (10 minutes)
- [ ] Decide: raw recording, or edited export. Both files must come from the same place.
- [ ] Download **video** as MP4 -> `episodes/<id>/episode.mp4`
- [ ] Download **captions** as SRT or VTT -> `episodes/<id>/captions.srt`
- [ ] Copy `skills/cutlist/assets/notes.template.md` -> `episodes/<id>/notes.md`. Fill guest name and links.
- [ ] Copy marker times from the editor -> `episodes/<id>/markers.txt` (optional)

## C. Plan (your agent, 5 minutes of your time)
- [ ] Open the folder in your agent. Paste **prompt 01**. Sync check must say OK.
- [ ] Read the bottom line and the plan. Watch every file in `previews/`.
- [ ] Swap or trim with **prompt 03** until you like all clips.
- [ ] Paste **prompt 02**. Open `thumb_mock_feed_320.png`. Can you read it? If not, cut words.

## D. Cut in your editor (per clip, about 3 minutes each)
- [ ] Go to the start time from the plan. Split. Go to the end time. Split.
- [ ] Keep only that range. Speaker focus as the plan says. Frame 9:16.
- [ ] Captions on. Export. Name the file with the publish order number.
- [ ] Cold open: place the cold-open range at 00:00 of the full episode, then export the episode.

## E. Publish the episode (YouTube Studio)
- [ ] Title from `clip_plan.md` (under 100 characters; the hook in the first 40).
- [ ] Description pasted in full. First line under 100 characters. Hashtags on the last line.
- [ ] Tags pasted. Category set.
- [ ] Thumbnail rebuilt from `thumbnail_brief.md`: same frame, same words, same side. 1280x720, under 2 MB.
- [ ] Trifecta check: thumbnail words = first 10 seconds = title = first description line.

## F. Publish the clips (one per day, or as the profile says)
- [ ] Vertical file uploaded. Title, description, hashtags, tags, category from the plan.
- [ ] Description ends with "Full episode on the channel." and 3 to 5 hashtags.
- [ ] Related video set to the full episode when the option is offered.

## G. Close out (2 minutes)
- [ ] Note anything the agent got wrong in `episodes/<id>/notes.md` under "Feedback".
- [ ] If a rule should change for every episode, edit `channel/channel_profile.md`, not the prompt.

Limits to remember: title 100 chars, description 5,000 bytes, tags 500 chars total,
hashtags 3 to 5 (over 60 and YouTube ignores all), clips 15 to 30 s, cold open 10 s or less.
