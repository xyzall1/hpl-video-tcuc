# Data formats

## timing.json (written by make_vo.py or vo_pauses.py apply)
```json
{
  "source": "elevenlabs | supplied",
  "duration": 159.6,
  "sentences": [{"text": "Semua bagiannya sudah benar.", "paragraph": 0, "start": 0.3, "end": 1.9}],
  "cues":      [{"start": 0.3, "end": 2.3, "text": "Semua bagiannya sudah benar."}]
}
```
Times are seconds on the **final (padded) VO clock**. Motion graphics, scenes, and subtitles all use this clock.

## assemble.json (paths are relative to this file)
```json
{
  "name": "SC3",
  "out_dir": ".",
  "bumper_in": "../Bumper In Telkom CorpU.mp4",
  "bumper_out": "../Bumper Out Telkom.mp4",
  "vo": "vo/vo.wav",
  "timing": "vo/timing.json",
  "mg": "mg.mp4",
  "scenes": [
    {"file": "../bagas put every graph at once.png", "start": 0.0, "end": 8.7},
    {"file": "../extra footage.mp4", "start": 40.0, "end": 46.0, "src_start": 2.0, "volume": 0.0, "push_in": false}
  ],
  "bumper_gain": 0.63,
  "vo_gain": 1.0
}
```
- `scenes[].start/end` are VO seconds. Overlap each neighbouring motion-graphic scene fade by about 0.3 s so there is never a blank frame.
- Images and footage are cover-scaled to the canvas automatically, whatever their size.
- Footage audio is muted by default (`volume: 0`). Set a value above 0 only if its sound belongs in the mix.

## config.json (personal, optional, next to config.default.json)
Overrides the defaults, e.g.:
```json
{"elevenlabs": {"voice_id": "YOUR_VOICE_ID"}, "pauses": {"sentence": 0.4, "paragraph": 1.0}}
```
Do not commit or share `config.json`. The API key never goes in any file of this skill. Use env `ELEVENLABS_API_KEY` or `~/.config/elevenlabs/key`.
