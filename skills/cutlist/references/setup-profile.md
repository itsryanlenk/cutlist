# Workflow: set up the channel profile

Run this once per channel, before the first clip plan. It creates `channel/channel_profile.md`
in the creator's project folder from `$SKILL/assets/channel_profile.template.md`.

This is also where the skill learns which recorder and which editor the creator uses. Every
later instruction (how to export, how to cut, how to go vertical, how to add captions) is
written for those tools. The skill has no favorite tool.

## Step 1. Ask, in one message, for these facts

Ask only for what you do not already have. Keep it to one message with numbered questions.

1. Channel handle and platform(s) you publish to (YouTube, TikTok, Instagram).
2. Show name, if the videos have one separate from the channel name.
3. Who the audience is, in one sentence.
4. What the long videos are (interview podcast, solo lecture or tutorial, webinar, stream VOD,
   keynote, vlog) and the typical length of each kind.
5. Is a person on camera for most of the video, or is it mostly a screen, slides, or gameplay?
6. Host name as it should appear, and how speakers are labeled in the caption files.
7. Tone in a few words, and any banned words or phrases.
8. The link block to put in every description (newsletter, site, product, socials).
9. Hashtag pool: 8 to 15 hashtags they want to draw from.
10. Default YouTube category: Education (27), Science & Technology (28), People & Blogs (22),
    Entertainment (24), or Howto & Style (26).
11. Clip cadence: how many clips per video and per day.
12. Which recorder produces the video and the captions (Riverside, Descript, Zoom, StreamYard,
    SquadCast, Zencastr, OBS or a camera plus a transcription tool, other).
13. Which editor they cut in (Premiere Pro, DaVinci Resolve, Final Cut Pro, CapCut, Descript,
    iMovie, Kdenlive, other).

## Step 2. Write the profile

Copy the template to `channel/channel_profile.md` and fill every `[ ]` with the answers.
Leave a `[ ]` where the creator gave no answer; do not invent.

For the Tools section, open `$SKILL/references/tools.md`, find the creator's recorder and
editor, and copy the matching lines into the profile: how to export the video and the
captions from the same place, whether the recorder has live markers and which key, how to
jump to a time and split in the editor, how to make a 9:16 clip, and how to add captions.
If a tool is not in the reference, ask the creator for those five answers and write what
they say. Later runs read the profile, not the reference.

For title formulas: if the creator already has three or more published videos, ask them to
paste the titles and run the retitle workflow to derive the formula. Otherwise keep the
defaults in the template.

## Step 3. Confirm

Show the creator the finished file path and the four things that most change results:
the Tools section, the title formula, the hashtag pool, and the link block. Ask them to
correct anything wrong. Do not proceed to a clip plan in the same turn unless they ask.
