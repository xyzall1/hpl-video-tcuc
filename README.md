# learning-video-storytelling

A Claude Code skill that turns a scene folder into a finished learning video in the Telkom CorpU storytelling style.

## Install (for each team member)
1. Copy this folder to `~/.claude/skills/learning-video-storytelling/`.
2. Requirements: ffmpeg/ffprobe, Python 3 with Pillow, Node (for `npx hyperframes`), Tesseract CLI 0.2.x, and the skills `hyperframes`, `tesseract-video`, and `tts-script-enhancer`.
3. API keys — each person uses their own, stored as one line in a private file (never inside this folder):
   ```bash
   mkdir -p ~/.config/elevenlabs && read -s -p "ElevenLabs key: " K && printf '%s' "$K" > ~/.config/elevenlabs/key && chmod 600 ~/.config/elevenlabs/key && unset K
   mkdir -p ~/.config/pexels && read -s -p "Pexels key: " K && printf '%s' "$K" > ~/.config/pexels/key && chmod 600 ~/.config/pexels/key && unset K
   ```
   (env vars `ELEVENLABS_API_KEY` / `PEXELS_API_KEY` also work). Paste each key exactly once.
4. Only needed if you generate VO from a script:
   - Optionally create `config.json` with your `voice_id` (see `references/assemble-config.md`). This file is personal and is not shared.

## Usage
Open Claude Code in a scene folder and say, for example: "buat learning video dari folder ini" or "buat VO dari script.txt lalu jadikan learning video".
Claude pauses for approval twice: once at the storyboard, and once at the motion-graphics preview.
