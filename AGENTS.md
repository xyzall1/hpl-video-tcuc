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

## Workflow

### 0. Inventory
List the folder: script or transcript `.txt`, `VO*.mp3|wav`, `Bumper In*.mp4`, `Bumper Out*.mp4`, scene images, extra footage. Probe durations with ffprobe. **Look at every image** (open it or describe it) so you know what moment it shows. Choose path A (script, no VO) or path B (VO supplied).

### 1A. VO from script (ElevenLabs)
Optionally add voice-only audio tags such as `[sighs]` without changing words. The voice id comes from `config.json` or `--voice-id`.
```bash
python3 "$SKILL/scripts/make_vo.py" --script script.txt --out-dir <work>/vo [--voice-id ID]
```
A blank line marks a paragraph. Output: `vo.wav`, `vo.mp3`, `timing.json` (exact per-character timing, with breathing pauses of 0.4 s per sentence and 1.0 s per paragraph).

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
Show the table and the stock thumbnail sheets, then wait for approval.

### 3. Motion graphics (HyperFrames)
Copy `$SKILL/assets/hf-template/` to `<work>/hf/` and `$SKILL/assets/fonts/` to `<work>/hf/fonts/`.
- Add one `<section class="clip">` per motion-graphic beat. All times are **VO seconds from timing.json**.
- Set the root `data-duration` to the VO duration plus 0.7.
- Keep content between y 80 and 900. The subtitle zone starts at y 940.
- Run `npx hyperframes check` until it reports 0 errors.

### 4. Preview ✋
Run `npx hyperframes snapshot --no-end --at <one time per beat>`. Show the contact sheet and wait for approval. Then render:
`npx hyperframes render -o <work>/mg.mp4 -q delivery --quiet`

### 5. Assemble (Tesseract)
Write `<work>/assemble.json` (see `references/assemble-config.md`) with the bumpers, `vo/vo.wav`, `vo/timing.json`, `mg.mp4`, and the scenes (VO-second windows that overlap motion-graphic fades by about 0.3 s). Then:
```bash
python3 "$SKILL/scripts/build_tesseract.py" <work>/assemble.json
```
This produces `<Scene>.tsrct`, `<Scene>.mp4`, `Previews/Filmstrip.png`, and a loudness report. Target −16…−14 LUFS with peak ≤ −1 dB.

### 6. Deliver
Report the MP4, the `.tsrct`, the HyperFrames source, the duration, and anything approximate. On a revision, keep previous renders in `Versions/`.

### Batch
Run step 1 for all folders first, then one combined storyboard ✋, then one combined preview ✋, then assemble each folder.
