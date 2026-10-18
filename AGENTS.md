# AGENTS.md: HPL Video TCUC (learning video, storytelling, Telkom CorpU house style)

These are instructions for any coding agent that can run shell commands and read and write local files, such as Codex CLI, Cursor, Gemini CLI, Windsurf, or Cline. The same workflow is packaged for Claude as `SKILL.md`. This file is the agent-neutral version.

`$SKILL` = the folder that contains this file. Scripts, templates, and references are relative to it.

## Goal
Turn a scene folder into a finished learning video: 16:9, 1280×720, 30 fps MP4, plus an editable project.
The video runs **Bumper In → VO section (motion graphics + scene images/stock + subtitles) → Bumper Out**.
The input can be a plain script (VO is generated with ElevenLabs) or a recorded VO with a Whisper transcript.

## Required tools on the machine
- `ffmpeg` / `ffprobe`, Python 3.9+ with Pillow, Node.js 18+
- **HyperFrames** (`npx hyperframes`) renders the motion graphics from HTML. Docs: https://github.com/heygen-com/hyperframes
- **Tesseract CLI 0.2.x** (`tsrct`) assembles and exports the video. Releases: https://github.com/mirage-hq/tesseract. Default macOS path: `~/Library/Application Support/Tesseract/bin/tsrct`. It can be overridden with env `TSRCT`.
- API keys, each person's own, stored as one line in a private file. Never ask for them in chat or write them into project files:
  - `~/.config/elevenlabs/key` (or env `ELEVENLABS_API_KEY`), only needed for VO generation
  - `~/.config/pexels/key` (or env `PEXELS_API_KEY`), only needed for stock footage

## Rules
- Work in a new subfolder `<Scene>_Video/` inside the scene folder. Never overwrite the user's source files.
- **Two approval stops** (✋): the storyboard, and the motion-graphics preview. Everything else runs without asking.
- Read `references/house-style.md` before designing and `references/pitfalls.md` before assembling.
- Keep all work editable: the HyperFrames HTML source and the Tesseract `.tsrct` project.
- Use the skill's scripts as written; never replace a failing step with a hand-made substitute. HyperFrames needs a headless browser and Tesseract/ffmpeg need normal file access: in a sandbox (e.g. Codex), if a command is blocked, stop and ask the user to approve running it outside the sandbox.

## Workflow

### 0. Inventory
List the folder: script or transcript `.txt`, `VO*.mp3|wav`, `Bumper In*.mp4`, `Bumper Out*.mp4`, scene images, extra footage. Probe durations with ffprobe. **Look at every image** (open it or describe it) so you know what moment it shows. Choose path A (script, no VO) or path B (VO supplied).

### 1A. VO from script (ElevenLabs)
**No audio tags.** Remove every `[...]` tag (`[short pause]`, `[sighs]`, `[firmly]`…) before synthesis and do not add any: ElevenLabs fills tags with breaths and throat-clears that reviewers hear as a cough ("uhuk"). Make pauses with punctuation (comma, period, ellipsis) and with the breathing pauses added at assembly. Do not change words. The voice id comes from `config.json` or `--voice-id`.

Spell English terms the way the narrator should say them, for example KPI → "key-pee-eye", CTR → "si ti ar"; offer the user a few spellings to pick by ear when unsure.
```bash
python3 "$SKILL/scripts/make_vo.py" --script script.txt --out-dir <work>/vo [--voice-id ID]
```
A blank line marks a paragraph. Output: `vo.wav`, `vo.mp3`, `timing.json` (exact per-character timing, with breathing pauses of 0.4 s per sentence and 1.0 s per paragraph). Listen to every sentence for coughs, breaths or throat-clears and regenerate (or cut) any sentence that has one.

### 1B. Supplied VO: add breathing pauses
```bash
python3 "$SKILL/scripts/vo_pauses.py" detect --vo VO.mp3 --transcript transcript.txt --out <work>/vo/cuts.json
# review cuts.json: P for topic changes, '-' for mid-sentence, fix subtitle text
python3 "$SKILL/scripts/vo_pauses.py" apply --cuts <work>/vo/cuts.json --out-dir <work>/vo
```

### 2. Storyboard ✋
Build a table of beats: time range, VO line, visual. Visual priority: supplied scene, then motion graphic, then Pexels stock (short real-world context only).
- No image should stay on screen longer than about 8 s. No motion-graphic beat should go more than about 4 s without a visual change.
- Stock search:
```bash
python3 "$SKILL/scripts/pexels.py" search --query "..." --kind video --out <work>/stock/beatNN.json
python3 "$SKILL/scripts/pexels.py" download --candidates <work>/stock/beatNN.json --id ID --dest <work>/stock --name NAME
```
- **Reuse cap:** one Pexels item may be used in at most 2 videos. `pexels.py` counts uses from every `stock/credits.txt` in the workspace (`--usage-root` / env `HPL_STOCK_ROOT` to override), hides capped items from search and refuses to download them. Do not repeat a clip within one video either.
- Fragmented MP4 downloads (no frame count, which Tesseract rejects) are re-encoded automatically to `<name>-fix.mp4`.
- When a beat is about a named character, the stock subject must match that character (gender, role); avoid ambiguous hands-only shots.

Show the table and the stock thumbnail sheets, then wait for approval.

### 3. Motion graphics (HyperFrames)
Copy `$SKILL/assets/hf-template/` to `<work>/hf/` and `$SKILL/assets/fonts/` to `<work>/hf/fonts/`.
- Add one `<section class="clip">` per motion-graphic beat. All times are **VO seconds from timing.json**.
- Set the root `data-duration` to the VO duration plus 0.7.
- Keep content between y 80 and 900. The subtitle zone starts at y 940.
- **Layout precision:** lay out every row or grid of cards, chips or badges with flex or CSS grid and one `gap`; never position siblings with hand-typed `left`/`top`. Centre each group on the canvas. Animate with transforms (`x`, `y`, `scale`, `opacity`) only, so entrances never shift the final layout. Compute arrow and connector ends from the connected elements' bounding boxes so both ends touch their cards. Draw symbols inside circles (+, −, ✓, ×) and connector arrows as SVG, not font glyphs. Same-role elements share the same size.
- **Cue timing:** take each reveal time from the **word** it illustrates in `timing.json`, not the sentence start; an element may enter at most ~0.2 s before its word. Keep every element visible until its beat exits, and start each beat's first element on the sentence's opening word so no frame is blank. After a VO regenerate, re-derive all cue times.
- Do not add any "Generated by AI" label to the frames.
- Run `npx hyperframes check` until it reports 0 errors.

### 4. Preview ✋
Run `npx hyperframes snapshot --no-end --at <times>`: per beat, one frame just after the last element enters and one just before the beat ends. Check every frame yourself first (equal spacing, groups centred, arrows touching both ends, nothing missing or early), fix, re-snapshot, then show the contact sheet and wait for approval. Then render:
`npx hyperframes render -o <work>/mg.mp4 -q delivery --quiet`

### 5. Assemble (Tesseract)
Write `<work>/assemble.json` (see `references/assemble-config.md`) with the bumpers, `vo/vo.wav`, `vo/timing.json`, `mg.mp4`, and the scenes (VO-second windows that overlap motion-graphic fades by about 0.3 s). Then:
```bash
python3 "$SKILL/scripts/build_tesseract.py" <work>/assemble.json
```
This produces `<Scene>.tsrct`, `<Scene>.mp4`, `Previews/Filmstrip.png`, and a loudness report. Target −16…−14 LUFS with peak ≤ −1 dB. Scan the VO section at 2 fps for near-blank frames above the subtitle zone (std < 4 on a 160×90 grey downscale); a run ≥ 0.6 s that is not a scene fade means a beat starts before its first element or a stock window ends too early.

### 5b. Background music (optional, Pixabay)
**Default track:** "Educational Tutorial Presentation Music" by ViacheslavStarostin (3:26, Pixabay Content License, https://pixabay.com/music/electronic-educational-tutorial-presentation-music-381788/). Use it unless the VO section is longer or the user asks for another; ask before the first download into a project. The earlier "Corporate Explainer Video" track was judged unsuitable by reviewers.
For another track, search Pixabay Music (e.g. "educational presentation", "presentation background") and offer only tracks **longer than the VO section**, with title, creator and duration. The user listens and picks; download the MP3 to `<work>/music/` and note the attribution in `<work>/music/credits.txt`. Then:
```bash
python3 "$SKILL/scripts/add_bgm.py" --video <work>/<Scene>.mp4 --vo <work>/vo/vo.wav --music <work>/music/<track>.mp3 \
  --start <Bumper In seconds> --out <work>/<Scene>_bgm.mp4
```
The music plays only in the VO section (bumpers keep their own audio), fades in 2 s, keeps running 2.5 s past the last word and fades out into Bumper Out, sits at −26 LUFS (config `bgm.music_lufs`; −22 was too loud, −30 too quiet) and is lightly ducked under the VO (config `bgm`). Keep the music-less MP4 too.

### 6. Deliver
Report the MP4, the `.tsrct`, the HyperFrames source, the duration, and anything approximate. On a revision, keep previous renders in `Versions/`.

### Related skill
`hpl-thumbnail/` (in this repo) makes the matching thumbnails: competency cover, course covers, video/article (16:9) and audio (1:1). See `hpl-thumbnail/AGENTS.md`.

### Batch
Run step 1 for all folders first, then one combined storyboard ✋, then one combined preview ✋, then assemble each folder.
