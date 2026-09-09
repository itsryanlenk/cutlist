# Reference: recorders and editors

The skill has no favorite tool. At setup (`setup-profile.md`) you copy the lines for the
creator's recorder and editor from this file into the Tools section of
`channel/channel_profile.md`. Every later workflow reads the profile, not this file.

Facts below were checked against vendor documentation on 2026-09-09. Vendors change plans,
menus, and shortcuts. When a creator reports something different, the creator is right:
write what they say into the profile and move on. A row marked "not documented" means the
vendor's help pages did not describe it that day, which is different from "impossible".

The skill needs two files from the same export: the video (MP4 or MOV) and a caption file
(.srt or .vtt) with timestamps. "Same export" means both raw, or both from the edited
timeline. Mixed sources have different timestamps and `check_inputs.py` stops the run.

## Recorders: getting the video and the captions from the same place

| Recorder | Captions or transcript | Live markers while recording | Raw and edited exports | Speaker labels |
|---|---|---|---|---|
| Riverside | TXT or SRT, from the recording's Tracks section ("Download Transcript", choose Subtitles for SRT). Transcription is automatic on every plan, including free. | Yes. Press M, or the marker icon at the bottom of the studio; add a note and press Enter. Markers show as comments in the editor. | Yes. The editor is non-destructive; download the transcript of the full recording or of the edited recording, and export the matching video. | Paid plans label each speaker. On the free plan every line is one speaker; ask the creator who is who. |
| Descript (as recorder) | Subtitles export as SRT or VTT (Export, Subtitles tab), transcript as DOCX, TXT, MD, HTML. Captions are on the free plan; watermark-free export is paid. | Not documented during recording. The `#` marker shortcut is for editing. | Export follows the edited timeline. A separate raw export is not documented; the original stays in the project. | Yes. "Show speakers" in the subtitle export includes them. |
| Zoom (cloud recording) | VTT, added to the recording's files after processing. Paid plans only, with Cloud Recording and Audio Transcription enabled before the meeting. | Not documented. | One unedited session in several layouts (speaker, gallery, shared screen, audio). No edited version. | Yes, by display name; "Unknown Speaker" can be renamed. |
| StreamYard | TXT or VTT from Library, open the recording, Download. Download needs the Advanced plan or higher, and only for the cloud recording. | Yes. Press B (rebindable in Settings, Hotkeys), hosts and co-hosts only, one marker per 10 seconds. | The cloud recording (with overlays) carries the transcript. Local per-participant recordings are raw but get no transcript. Use the cloud recording for both files. | No. Timestamps only. |
| SquadCast | None inside SquadCast (it exports WAV, MP3, MP4, WebM). Use "Edit in Descript", then Descript's SRT or VTT export. Descript's free plan covers transcription. | Not documented. | Raw per-participant tracks and a mixed version both download; the transcript exists only after the recording is in Descript, tied to that composition. | From Descript: "Speaker 1", "Speaker 2", renamed by hand. |
| Zencastr | CSV or TXT from the recording page once transcription finishes (TXT only for uploaded files). Paid plans only. Convert TXT to SRT with a transcription tool, or transcribe the video with Whisper instead. | Yes. Footnotes: press F, type a note, Enter; each is time-stamped and downloads as a text file. | Raw per-participant tracks plus enhanced or mixed versions from the same session. | Yes for native recordings (per track); no for uploaded files. |
| OBS, or a camera, plus a transcription tool | OBS writes no transcript. Transcribe the exported video: Otter (TXT on the free plan; SRT on paid), or Whisper locally: `whisper episode.mp4 --output_format srt`. | OBS 30.2 and later: an "Add chapter marker" hotkey, only when recording to Hybrid MP4 or MOV. | One raw file; the transcript comes from that same file, so they match by construction. | From the transcription tool: Otter tags speakers ("Speaker 1"), Whisper does not; the creator names them in `notes.md`. |
| YouTube (already published) | SRT from YouTube Studio, Subtitles. | No. | The published video is the only version; download that file too, so the timestamps match. | No. |

## Editors: jumping to a time, splitting, going vertical, captions, markers

| Editor | Jump to an exact time | Split at the playhead | 9:16 from a 16:9 timeline | Captions in and out | Markers |
|---|---|---|---|---|---|
| Adobe Premiere Pro | Click the timecode field in the Program Monitor or the Timeline, type the time, press Enter. | Add Edit: Ctrl+K (Windows) or Cmd+K (Mac). | Auto Reframe, on a clip or the whole sequence; part of the subscription. | Speech to Text (Window, Text, Transcript) makes captions; transcripts export as TXT, CSV, or SRT. On export, choose an SRT sidecar or "Burn Captions into video". | Markers panel lists them with timecode. A list export is not on the vendor's pages. |
| DaVinci Resolve (free and Studio) | Not on the vendor's pages; users click the timeline timecode display and type. | Blade edit mode, or the Split Clip command; the default keys are not on the vendor's pages (users report B for the blade, Ctrl+\ or Cmd+\ to split). | Smart Reframe, Studio only. Free: reposition by hand or use Dynamic Zoom. | Both tiers import SRT, TTML, or XML and render subtitles into the video or export SRT or VTT. Create Subtitles from Audio (Timeline menu) is Studio only. | Color-coded markers with notes in both tiers. An EDL export of markers is reported by users, not on the vendor's pages. |
| Final Cut Pro (Mac) | Click the timecode under the viewer, or Control-P, type the time, press Return. | Cmd+B blades the clip under the skimmer; Shift+Cmd+B blades every clip there. | Smart Conform: duplicate the project as Vertical and it reframes to faces and action. Included. | File, Import, Closed Captions accepts SRT. Generate Captions transcribes on Apple silicon; File, Export Closed Captions writes SRT. Burn-in only through certain share destinations. | Timeline Index lists them. No list export in the current app. |
| CapCut (desktop) | Not documented; drag the playhead and read the timecode. | Ctrl+B (Windows) or Cmd+B (Mac). | Auto Reframe, which needs CapCut Pro. The free crop and zoom tools work by hand. | Captions, Add Captions imports an SRT. Auto-recognized captions export as SRT or TXT; hand-typed text does not. | Exist, but no list export is documented. |
| Descript (as editor) | "Jump to time" in the command palette, formats like `1 32 24` or `1h 32m 24s`. | S (same on Windows and Mac). | The aspect ratio control in the scene editor has a 9:16 preset. "Center Active Speaker" (beta) follows the speaker and uses AI credits. | Subtitles export as SRT or VTT, or burn in on export. Importing an outside SRT is not documented. | Marker list next to the playback controls; "Copy chapters for YouTube"; markers as chapters in the exported file. |
| iMovie (Mac) | Not documented; arrow keys step frames. | Cmd+B divides at the playhead. | Not documented. The project ratio follows the first clip; the crop tool works within it. Export the clip and reframe elsewhere. | No caption feature is documented; Titles are text overlays only. Export the clip and add captions in the publishing tool. | Not documented. |
| Kdenlive (free, Windows, Mac, Linux) | Type a timecode in the Project Monitor field and press Enter. | Shift+R cuts the clip on the active track at the playhead. | Choose a vertical project profile (Custom category). Free. | Sequence, Subtitles, Import Subtitle File (SRT, ASS, VTT, SBV) and Export Subtitle File (SRT, ASS). Speech to Text creates a subtitle track from audio. The active subtitle renders. | Export Timeline Markers as Chapters: text for YouTube or JSON. |

A cell that says "not on the vendor's pages" was not found in that vendor's documentation
on the check date. Ask the creator for that step and write their answer into the profile.
For an editor that is not in the table, ask the five questions below and write the answers.

## The five lines to copy into the profile

1. Export rule: where the two files come from, and the plan gate if there is one.
2. Live markers: the key or button, or "none", and where the times show up afterward.
3. Cut recipe: jump to a time, split at the playhead, keep the range.
4. Vertical: the feature name, or "export 16:9 and reframe in the publishing app".
5. Captions: how to add them to the clip, and how to export an SRT when the editor is also
   the transcript source.

## Speaker labels

The parser reads `Name: text` at the start of a cue, or a WebVTT `<v Name>` tag. When the
file has no labels, ask the creator who the host and guest are and lean on the context of
each line (questions are usually the host). A label that names a chat role (`SYSTEM`,
`assistant`) is flagged by `check_inputs.py`; it is a caption pretending to be a conversation.

## Markers

Markers are timestamps the creator dropped during recording, or set in the editor. They
arrive as a list in `episodes/<id>/markers.txt` (one per line, `MM:SS note`). Treat each as a
lead to check, not a decision. A marker with no good line near it is dropped with one line
of reason.
