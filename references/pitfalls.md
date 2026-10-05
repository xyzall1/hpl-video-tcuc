# Pitfalls learned in production (read before assembling)

## Tesseract (CLI 0.2.x)
- **Fonts:** Plus Jakarta Sans (fontsource or Google static) and Nunito Sans import fine but render `missing_fonts`, as do variable fonts (import rejected). Poppins and Inter work. Subtitles therefore use Poppins Bold. Test a new face in a scratch project before relying on it.
- A `Rect` layer's `rect.position` is the **top-left corner**, not the centre. `roundness` is in px (pill = height / 2).
- `scale` is not an animatable property type. Keyframe `scaleX` and `scaleY` separately.
- Layer `activeRange.duration` must be > 0. When two cues snap to the same pause, one gets zero length, so check the cue list.
- `project commit` replaces the document. Re-apply keyframe actions after every commit. `build_tesseract.py` does this.
- Video layers need an explicit `volume` (`1.0` = unity) or their audio is muted.
- Canvas 1920×1080, then export with `--resolution 720p`.

## Audio
- The supplied bumpers are mastered hot (about −10 LUFS, peaks above 0 dBFS). Trim them to 0.5 gain (≈ −6 dB → about −16 LUFS) so they match the VO and do not clip.
- A mono VO is played on both stereo channels in Tesseract, so it measures about +3 dB louder than the source file. `make_vo.py` normalises the VO to −16 LUFS / −2 dBTP first, and `vo_gain` 0.8 is calibrated for that. Measure the VO section (`ffmpeg -ss 30 -t 60 -i out.mp4 -af ebur128 -f null -`) and adjust.
- Target about −16…−14 LUFS integrated and peak ≤ −1 dB. Measure with `ffmpeg -af ebur128=peak=true`.
- Join VO segments as PCM WAV. Concatenating MP3s adds encoder padding per segment and drifts timing by about 25 ms each.

## Timing
- Whisper transcripts are floored to whole seconds. Snap each line to a detected silence (`vo_pauses.py detect`). Two lines can snap to the same gap, so fix it by hand in `cuts.json`.
- ElevenLabs `with-timestamps` gives per-character times, so cues are exact. Strip `[audio tags]` from subtitle text; `timing_lib` does this.
- `eleven_v3` does not accept `previous_text` / `next_text`. `make_vo.py` does not send them for v3 or v4 (v4 untested with stitching).
- Default model is `eleven_v4` (confirmed working, Sep 2026). The API key may lack `models_read`, so the model list cannot be queried; test with a real call instead.

## Cloud-synced folders
- Tesseract aborts with "source .tsrct file changed after it was opened" when the project lives in OneDrive/iCloud: the sync client touches the file mid-build. `build_tesseract.py` builds in a local temp dir and copies `.tsrct`, MP4 and filmstrip to `out_dir` at the end.
- In the Claude Code sandbox, HyperFrames render and tsrct cannot start ffmpeg ("FFmpeg cannot start"). Run those commands with the sandbox disabled.

## HyperFrames
- No `Math.random` or `gsap.utils.random`. Use the seeded `rnd(a, b)` from the template.
- Do not tween `left`/`top`/`width` for motion. Use `x`/`y`/`scale` (lint error `gsap_non_transform_motion`). Width or height "growth" on bars is tolerated.
- Do not give an element a CSS `transform` and then tween it (lint `gsap_css_transform_conflict`). Centre a pill with `left: 960px` plus `gsap.set(el, { xPercent: -50 })` (the template does this for `.pill`).
- Text beside a `<span>` inside a flex `.center` loses its space. Write `&nbsp;<span>`.
- Contrast warnings on frames in the middle of a fade are expected. Overlapping text at rest is a real error.
- A long composition renders in about 100 s per 134 s of video at 1080p.

## Stock (Pexels)
- Free to use under the Pexels license. Attribution is not required but is recorded in `credits.txt` (good practice for internal and training material). Do not use stock people in a way that implies they endorse Telkom or that they are real employees.
- The Pexels image CDN rejects requests without a User-Agent (blank white contact sheet). `pexels.py` sends one and prints any thumbnail that fails; never present a blank sheet as candidates.
- When a beat's subject is a named character, the stock person must match that character (e.g. a female protagonist → a woman on screen). Hands-only or ambiguous shots are not enough; check every pick.
- `pexels.py` picks a landscape MP4 between 720p and 1080p. 4K is unnecessary for a 720p export and slow to download.
- Live-action stock clashes with the hand-drawn scenes. Use it briefly for context, and let the white/teal motion graphics or a crossfade carry the transition.
