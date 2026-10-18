# AGENTS.md: HPL Thumbnail (Telkom CorpU)

These are instructions for any coding agent that can run shell commands and read and write local files, such as Codex CLI, Cursor, Gemini CLI, Windsurf, or Cline. The same workflow is packaged for Claude as `SKILL.md`. This file is the agent-neutral version.

`$SKILL` = the folder that contains this file. Scripts, backgrounds and ornament data are relative to it.

## Goal
Make the thumbnails for HPL learning content, matching the HPL thumbnail decks:
- competency cover, course covers, video and article thumbnails: 16:9, 1920×1080 PNG
- audio thumbnails: 1:1, 1080×1080 PNG

## Required tools on the machine
- Python 3.9+ with Pillow and openpyxl
- Node.js 18+ with **HyperFrames** (`npx hyperframes`); each thumbnail is a one-frame HyperFrames snapshot
- Arial Bold: the macOS system copy is used automatically; elsewhere put it at `$SKILL/fonts/ArialBold.ttf` (not included in the repo because of its licence)

## Rendering rule (important)
- Always render with `scripts/make_thumb.py` or `scripts/batch_from_cms.py`. **Never write your own renderer** (Pillow, canvas, ImageMagick, etc.): hand-made versions break the letter-spacing, the en dash in the course label, line wrapping and the shadow.
- The scripts need a headless browser (HyperFrames snapshot). In a sandbox (e.g. Codex) the browser may be blocked. Then **stop and ask the user to approve running the command outside the sandbox** (escalated permissions); do not fall back to another method.
- After rendering, open the PNG and check: label on one line, the dash in `COURSE n – …` sits at mid-height, title inside the left text area, ornament complete.

## Design rules
- **Level = background brightness:** Fundamental = second-brightest, Developing = brightest, Intermediate = darkest.
- **Colour per competency, chosen by the user by name:** kuning, tosca, biru, ungu, hijau, pink (`--palette=<name>`; aliases: oranye = kuning, biru muda = tosca, merah muda = pink). One competency uses one colour at every level. Name colours only; do not show hex codes or tables to the user. Preview: `palettes_preview.jpg`.
- **Ornament per competency, chosen by the user by name:** cincin, diagram, grafik, heksagon, kubus, orbit, panah, piramida, sarang, satelit, tabung, target, tumpukan (`--ornament=<name>`). The shapes come exactly from the decks (`ornaments.json`) and each has a 16:9 and a 1:1 version, so the audio thumbnails use the same ornament. Preview: `ornaments_preview.jpg`.
- For a new competency, ask for colour and ornament together in one short question and show `ornaments_preview.jpg` with it. Remember the answer for later levels of the same competency.
- Existing choice: TC262 Strategic Media Planning = kuning, heksagon for 16:9 and tumpukan for audio (`--audio-ornament=tumpukan`).
- Text: Arial Bold, white, with a soft shadow. The label uses the palette's light colour, uppercase with wide letter-spacing. Title size: cover 46 pt, course 40 pt, content 32 pt; audio 23 pt, centred under the ornament. Hyphenated words are never split across lines.

## Where the titles come from (CMS workbook, one sheet per level)
| Thumbnail | Content |
|---|---|
| Competency cover | label = level name (FUNDAMENTAL / DEVELOPING / INTERMEDIATE), title = competency name |
| Course cover n | label = `COURSE n – <COMPETENCY>`, title = column **Course Design** (order of first appearance) |
| Video | column **Judul Video** |
| Article | column **Judul Artikel** |
| Audio (1:1) | column **Judul Audio** |
Column **LU** reads like `KB1 · Modul 1`. Always read titles from the workbook; never retype them.

## File names
- `<CODE>_L<n>_00_Cover Kompetensi - <Competency> (<Level>).png`
- `<CODE>_L<n>_0<k>_Cover Course <k> - <Course Design>.png`
- `<CODE>_L<n>_KB<k>_M<m>_{Video|Artikel|Audio} - <Title>.png`

The characters `: / ? \ * " < > |` are dropped from file names only; the title on the image stays complete. Save each level in its own folder, e.g. `_thumbnail/out/L1`.

## Workflow
1. Check that the CMS workbook has the columns above. Ask for colour and ornament if the competency has none yet.
2. Do **one level first**:
```bash
python3 "$SKILL/scripts/batch_from_cms.py" <CMS.xlsx> "TC262 L1" fundamental TC262_L1 "Strategic Media Planning" _thumbnail/out/L1 \
  --palette=kuning --ornament=heksagon --audio-ornament=tumpukan
```
3. Open the contact sheet it writes next to the output folder (`<CODE>_contact_sheet.jpg`). Check that no title is cut off or outside its box, labels are right, and the background matches the level. Show it to the user with the file names grouped per LU (course cover at the start of each KB; video, article, audio per LU).
4. After approval, run the next level with its sheet, level and code.

A single thumbnail:
```bash
python3 "$SKILL/scripts/make_thumb.py" out.png <fundamental|developing|intermediate> <ornament> "<Title>" ["<LABEL>"] \
  [--size=cover|course|content] [--format=square] [--palette=kuning|tosca|biru|ungu|hijau|pink]
```
