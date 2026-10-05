---
name: hpl-video-tcuc
description: Produce a storytelling learning video (Telkom CorpU house style) from a scene folder — plain script or recorded VO, scene images, bumper in/out — into a 16:9 720p MP4 with white/teal HyperFrames motion graphics, breathing pauses, and teal pill subtitles assembled in Tesseract. Use for "buat learning video", "video storytelling dari script/VO", a DV/KB/SC scene folder, generating VO with ElevenLabs from a script, or batch-producing several scene folders in the same style.
---

# Learning video — storytelling (house style)

Pipeline: **script/VO → timing.json → storyboard ✋ → HyperFrames motion graphics → preview ✋ → Tesseract assembly → MP4 720p**.
✋ = stop and get the user's approval. Everything else runs without asking.

Skill root = the directory containing this file (`$SKILL`). Work inside the scene folder in a new subfolder `<SceneName>_Video/` (claim it with `mkdir` without `-p`; never overwrite). Keep the user's source files untouched.

Load these skills as you reach their step: `hyperframes` + `hyperframes-core` (motion graphics), `tesseract-video` (assembly; its installation reference pins the CLI version), `tts-script-enhancer` (optional audio tags). Read `references/house-style.md` before designing and `references/pitfalls.md` before assembling.

## 0. Inventory the scene folder

Expect some of: `*.txt` script or Whisper transcript, `VO*.mp3|wav`, `Bumper In*.mp4`, `Bumper Out*.mp4`, scene images (`*.png|jpg|jpeg`, filenames describe the moment), extra footage (`*.mp4|mov`). Probe durations with ffprobe and **look at every image**. Decide the path:

- **A — VO from script** (no VO audio, a plain script present) → step 1A.
- **B — VO supplied** (audio + transcript) → step 1B.

Ask only what is missing and changes the result (e.g. no bumper found, script and VO both present but disagree).

## 1A. Generate VO with ElevenLabs

1. Optionally run `tts-script-enhancer` on the plain script to add voice-only tags (`[sighs]`, emphasis). Show the enhanced script; do not change words.
2. Voice: use `voice_id` from `$SKILL/config.json`, else ask the user once (they may pick via the connector's `creative_list_voices`) and suggest saving it in config.json.
3. The API key comes from env `ELEVENLABS_API_KEY` (or `~/.config/elevenlabs/key`). Never ask the user to paste a key in chat, never print or write it into project files. If missing, tell the user how to set it (`export ELEVENLABS_API_KEY=...` in their shell profile) and stop.
4. Run:
```bash
python3 "$SKILL/scripts/make_vo.py" --script script_enhanced.txt --out-dir <work>/vo --voice-id <id>
```
Script format: blank line = paragraph; sentences end with `.?!`. The tool synthesizes per sentence, joins with breathing pauses (0.4 s sentence / 1.0 s paragraph, config), and writes `vo.wav` (+ `vo.mp3` copy) + `timing.json` with exact per-sentence and subtitle-cue times (tags stripped from subtitles). Listen-check a few joins (`ffplay`/afplay are fine) before continuing.

## 1B. Supplied VO: add breathing pauses

```bash
python3 "$SKILL/scripts/vo_pauses.py" detect --vo VO.mp3 --transcript transcript.txt --out <work>/vo/cuts.json
```
It snaps each transcript line to a real silence and proposes cuts (`S` sentence / `P` paragraph). Review `cuts.json`: mark topic changes `P`, delete cuts that fall mid-sentence (commas), fix subtitle text (typos, names). Then:
```bash
python3 "$SKILL/scripts/vo_pauses.py" apply --vo VO.mp3 --cuts <work>/vo/cuts.json --out-dir <work>/vo
```
→ padded `vo.wav` + `timing.json` (same schema as 1A). Whisper timestamps are only per second; say that cue timing is approximate (±0.3 s).

## 2. Storyboard ✋

From `timing.json` build a beat table: time range · VO line · visual (scene image **or** motion-graphic concept). Rules:
- Scene images carry story moments (character, emotion, situation); motion graphics carry the concept (numbers, structure, process, comparison). Alternate them; no image longer than ~8 s, no MG beat without a visual change for more than ~4 s.
- Every MG beat must reinforce the spoken sentence at its time (key reveal lands on the word).
- **Gaps → Pexels stock.** When a beat needs a real-world moment that no supplied scene or motion graphic covers, search stock (video first, photo as fallback):
```bash
python3 "$SKILL/scripts/pexels.py" search --query "field worker checking phone" --kind video --out <work>/stock/beat07.json
```
  Use short English queries. The command writes candidates and a numbered thumbnail sheet (`beat07.jpg`). Put the sheet in the storyboard with your pick. Stock clips are live-action, while supplied scenes are hand-drawn, so use stock for bridges or context and not for the main character. Aim for at most a few clips per video (unless the visual cue asks for stock in every scene). When the beat is about a named character, the stock subject must match that character (gender, role); avoid ambiguous hands-only shots.
Present the table (plus any stock sheets) and wait for approval or edits. After approval, download the chosen items:
```bash
python3 "$SKILL/scripts/pexels.py" download --candidates <work>/stock/beat07.json --id <id> --dest <work>/stock --name field-phone
```
  This appends the attribution to `<work>/stock/credits.txt`. Add the file to `scenes` in assemble.json. Footage is muted by default; set `src_start` to pick the best moment.

## 3. Motion graphics (HyperFrames)

Copy `$SKILL/assets/hf-template/` to `<work>/hf/` and `$SKILL/assets/fonts/` to `<work>/hf/fonts/`. The template already holds the house style, helpers (`el`, `miniTile`, `popIn`, `rise`, `out`, `fadeScene`, seeded `rnd`) and one sample scene — replace the sample with one `<section class="clip">` per MG beat, all times in **VO seconds from timing.json** (VO t=0 = MG t=0). Set root `data-duration` = VO duration + 0.7. Leave image beats as plain background; Tesseract lays the images on top. Keep content inside y 80–900 (subtitle zone below). Then `npx hyperframes check` until 0 errors (fade-frame contrast warnings are fine).

## 4. Preview ✋

`npx hyperframes snapshot --no-end --at <one time per beat>` and show the contact sheet(s) to the user (send the image). Fix feedback, then `npx hyperframes render -o <work>/mg.mp4 -q delivery --quiet`.

## 5. Assemble in Tesseract

Write `<work>/assemble.json` (schema in `references/assemble-config.md`): bumpers, `vo/vo.wav`, `timing.json`, `mg.mp4`, and the scene images with VO-second windows from the storyboard (let images overlap MG scene fades by ~0.3 s). Then:
```bash
python3 "$SKILL/scripts/build_tesseract.py" <work>/assemble.json
```
It creates `<Scene>.tsrct`, imports everything, lays out bumper in → VO section → bumper out, image crossfades + slow push-in, subtitles in the house preset, bumper gain, and exports `<Scene>.mp4` (720p30) + `Previews/Filmstrip.png`, printing loudness. Open the filmstrip and a couple of `tsrct preview` frames; check subtitles sit in the pill and no scene is blank. Target −16…−14 LUFS, peak ≤ −1 dBTP-ish; adjust `bumper_gain` if the bumpers dominate, and `vo_gain` (default 0.8, calibrated for the −16 LUFS normalised VO from `make_vo.py`; a supplied VO must be normalised first) if the VO section is off. The build runs in a local temp dir and copies results to `out_dir`, so cloud-synced folders (OneDrive) are safe.

## 5b. Background music (optional, Pixabay)

When the user wants a music bed: search Pixabay Music in the browser (themes like "corporate explainer", "educational presentation", "presentation background"), read each track page for its CDN mp3 URL and its duration (an `Audio` element's `loadedmetadata` works), and offer only tracks **longer than the VO section** so nothing loops. Show title · creator · duration; the user listens and picks, and the pick is their OK to download. Save to `<work>/music/` and write the attribution to `<work>/music/credits.txt` (Pixabay Content License). Then:
```bash
python3 "$SKILL/scripts/add_bgm.py" --video <work>/<Scene>.mp4 --vo <work>/vo/vo.wav --music <work>/music/<track>.mp3 \
  --start <Bumper In seconds> --out <work>/<Scene>_bgm.mp4
```
It trims the track to the VO section only (bumpers keep their own audio), fades in 2 s / out 3 s, normalises the music to −26 LUFS (raised from −30 after user feedback: too quiet) and side-chain ducks it under the VO (config `bgm`). It prints loudness: keep integrated −16…−14 LUFS and peak ≤ −1 dB; if the music feels loud in pauses, lower `--music-lufs` (e.g. −32). `--music-offset` skips a slow intro. Keep the music-less MP4 as well.

## 6. Deliver

Report the MP4, the `.tsrct` (editable), the HF source, duration, and anything approximate. On a revision, keep the previous render in `Versions/`.

## Batch (several scene folders)

Run steps 0–1 for every folder first, then present all storyboards together (one ✋), build MG per folder, one combined preview ✋, then assemble each. Same house style and config for all.
