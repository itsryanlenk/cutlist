# Prompt 00 - first-time setup (run once per machine)

Open the folder that contains `skills/cutlist/` in your agent. Paste:

```
Read skills/cutlist/SKILL.md.

1. Check for ffmpeg, ffprobe, python3 (3.9 or newer), and the Python package pillow.
   Tell me what is missing and give me the install line from SKILL.md. Ask before installing.
2. Run: bash tests/selftest.sh
   Show me the RESULT line. If anything fails, show me the error before changing anything.
3. Then run the setup workflow in skills/cutlist/references/setup-profile.md
   and write channel/channel_profile.md from my answers. I will tell you which recorder
   and which editor I use; write the export and cut steps for those tools into the profile.
If a script fails, show me the error and stop. Do not edit anything under skills/.
```
