#!/usr/bin/env python3
"""Add a background-music bed under the VO section of a finished learning video.

The music plays only between Bumper In and Bumper Out (the VO section), is trimmed to that
length, fades in/out, is loudness-normalised low, and is side-chain ducked by the VO so it
never competes with the narration. The bumpers keep their own audio untouched.

    python3 add_bgm.py --video <Scene>.mp4 --vo vo/vo.wav --music music/track.mp3 \
        --start <bumper-in seconds> --out <Scene>_bgm.mp4

Defaults come from config ("bgm" block); flags override. Requires ffmpeg.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def cfg():
    c = json.loads((SKILL / "config.default.json").read_text())
    user = SKILL / "config.json"
    if user.exists():
        for k, v in json.loads(user.read_text()).items():
            c[k] = {**c.get(k, {}), **v} if isinstance(v, dict) else v
    return c.get("bgm", {})


def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(f)], text=True).strip())


def loudness(f, start=None, length=None):
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start is not None:
        cmd += ["-ss", str(start), "-t", str(length)]
    cmd += ["-i", str(f), "-af", "ebur128=peak=true", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    return (float(i[-1]) if i else None, float(p[-1]) if p else None)


def main():
    d = cfg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--vo", required=True, help="the VO wav used in assembly (side-chain key)")
    ap.add_argument("--music", required=True)
    ap.add_argument("--start", type=float, required=True, help="VO section start in the video (= Bumper In duration)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--music-offset", type=float, default=d.get("music_offset", 0.0), help="seconds to skip into the track")
    ap.add_argument("--music-lufs", type=float, default=d.get("music_lufs", -30.0), help="music level before ducking")
    ap.add_argument("--fade-in", type=float, default=d.get("fade_in", 2.0))
    ap.add_argument("--fade-out", type=float, default=d.get("fade_out", 3.0))
    ap.add_argument("--tail", type=float, default=d.get("tail", 2.5), help="seconds the music runs past the last word, fading out over the start of Bumper Out")
    ap.add_argument("--duck-threshold", type=float, default=d.get("duck_threshold", 0.03))
    ap.add_argument("--duck-ratio", type=float, default=d.get("duck_ratio", 6.0))
    ap.add_argument("--duck-release", type=float, default=d.get("duck_release_ms", 600))
    a = ap.parse_args()

    L = dur(a.vo) + a.tail  # music runs past the VO end so the fade never sits under the last sentence
    if dur(a.music) - a.music_offset < L:
        sys.exit(f"Music is shorter than the VO section ({dur(a.music):.1f}s < {L:.1f}s). Pick a longer track.")
    ms = int(round(a.start * 1000))
    # Fixed gain from a measurement pass. (loudnorm's 3 s look-ahead drops the last seconds of the bed.)
    src_lufs = loudness(a.music, a.music_offset, L)[0]
    gain_db = a.music_lufs - src_lufs
    fo = max(L - a.fade_out, L - a.tail - 0.5, 0)  # fade starts only after the last word
    fc = (
        f"[2:a]atrim={a.music_offset}:{a.music_offset + L},asetpts=PTS-STARTPTS,"
        f"volume={gain_db:.2f}dB,aformat=sample_rates=48000:channel_layouts=stereo,"
        f"afade=t=in:d={a.fade_in},afade=t=out:st={fo:.3f}:d={L - fo:.3f}[m];"
        f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:{L:.3f}[key];"
        f"[m][key]sidechaincompress=threshold={a.duck_threshold}:ratio={a.duck_ratio}:attack=30:release={a.duck_release}[duck];"
        f"[duck]adelay={ms}|{ms},apad[bed];"
        f"[0:a]aresample=48000:async=1:first_pts=0,aformat=sample_rates=48000:channel_layouts=stereo[main];"
        f"[main][bed]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[aout]"
    )
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", a.vo, "-i", a.music,
           "-filter_complex", fc, "-map", "0:v", "-map", "[aout]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    whole = loudness(a.out)
    vo_sec = loudness(a.out, a.start + 20, min(60, L - 25))
    print(json.dumps({"out": a.out, "music_window_s": [round(a.start, 2), round(a.start + L, 2)],
                      "integrated_LUFS": whole[0], "peak_dBFS": whole[1],
                      "vo_section_LUFS": vo_sec[0]}, indent=1))


if __name__ == "__main__":
    main()
