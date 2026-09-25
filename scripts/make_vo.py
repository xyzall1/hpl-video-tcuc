#!/usr/bin/env python3
"""Generate VO from a script with ElevenLabs (per sentence, with timestamps) and join with breathing pauses.

Outputs <out-dir>/vo.wav (+ vo.mp3 copy) and <out-dir>/timing.json (see references/assemble-config.md for the schema).
API key: env ELEVENLABS_API_KEY or ~/.config/elevenlabs/key. Never printed.
"""
import argparse, base64, json, os, re, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from timing_lib import split_cues, strip_tags, load_config  # noqa: E402


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        p = Path.home() / ".config/elevenlabs/key"
        if p.exists():
            k = p.read_text().strip()
    if not k:
        sys.exit("ELEVENLABS_API_KEY is not set (or ~/.config/elevenlabs/key). Set it in your shell profile and retry.")
    return k


def parse_script(text):
    """Blank line = paragraph. Returns list of (paragraph_index, sentence_with_tags)."""
    out = []
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    for pi, p in enumerate(paras):
        p = " ".join(p.split())
        # split after . ? ! (optionally followed by closing quote) + space
        for s in re.split(r"(?:(?<=[.?!…])|(?<=[.?!…][”\"']))\s+(?=[\[“\"A-Z0-9])", p):
            if strip_tags(s).strip():
                out.append((pi, s.strip()))
    return out


def tts(text, voice, model, fmt, settings, prev_text=None, next_text=None):
    body = {"text": text, "model_id": model, "voice_settings": settings}
    if not model.startswith("eleven_v3"):  # request stitching is not supported on v3
        if prev_text: body["previous_text"] = prev_text
        if next_text: body["next_text"] = next_text
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format={fmt}",
        data=json.dumps(body).encode(), method="POST",
        headers={"xi-api-key": api_key(), "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs error {e.code}: {e.read().decode()[:500]}")


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).decode())


def main():
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--voice-id", default=cfg["elevenlabs"].get("voice_id"))
    ap.add_argument("--model", default=cfg["elevenlabs"]["model_id"])
    ap.add_argument("--pause-sentence", type=float, default=cfg["pauses"]["sentence"])
    ap.add_argument("--pause-paragraph", type=float, default=cfg["pauses"]["paragraph"])
    a = ap.parse_args()
    if not a.voice_id:
        sys.exit("No voice id: pass --voice-id or set elevenlabs.voice_id in config.json")

    out = Path(a.out_dir); seg_dir = out / "segments"; seg_dir.mkdir(parents=True, exist_ok=True)
    sents = parse_script(Path(a.script).read_text(encoding="utf-8"))
    settings = cfg["elevenlabs"]["voice_settings"]
    fmt = "mp3_44100_128"
    lead, tail = cfg["pauses"]["lead_in"], cfg["pauses"]["tail"]

    timeline, concat, t = [], [], lead
    sil = lambda d, i: _silence(seg_dir / f"sil_{i:03d}.wav", d)
    concat.append(sil(lead, 0))
    for i, (pi, s) in enumerate(sents):
        seg = seg_dir / f"s_{i:03d}.mp3"
        meta = seg_dir / f"s_{i:03d}.json"
        if not seg.exists():  # resumable: re-running skips finished sentences
            prev = strip_tags(sents[i - 1][1]) if i else None
            nxt = strip_tags(sents[i + 1][1]) if i + 1 < len(sents) else None
            r = tts(s, a.voice_id, a.model, fmt, settings, prev, nxt)
            seg.write_bytes(base64.b64decode(r["audio_base64"]))
            meta.write_text(json.dumps(r.get("alignment") or r.get("normalized_alignment")))
            print(f"[{i+1}/{len(sents)}] {strip_tags(s)[:60]}", flush=True)
        al = json.loads(meta.read_text())
        wav = seg.with_suffix(".wav")  # decode to PCM so joins and durations are sample-exact
        subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(seg), "-ar", "44100", "-ac", "1", str(wav)])
        d = dur(wav)
        # speech bounds inside the clip from character alignment
        st = al["character_start_times_seconds"]; en = al["character_end_times_seconds"]
        s0, s1 = (st[0], en[-1]) if st else (0.0, d)
        timeline.append({"text": strip_tags(s), "paragraph": pi, "start": round(t + s0, 3), "end": round(t + min(s1, d), 3),
                         "chars": al["characters"], "char_starts": [round(t + x, 3) for x in st]})
        concat.append(str(wav))
        t += d
        if i + 1 < len(sents):
            gap = a.pause_paragraph if sents[i + 1][0] != pi else a.pause_sentence
            concat.append(sil(gap, i + 1)); t += gap
    concat.append(sil(tail, 999)); t += tail

    lst = seg_dir / "concat.txt"
    lst.write_text("".join(f"file '{Path(c).resolve()}'\n" for c in concat))
    subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                           "-c:a", "pcm_s16le", str(out / "vo.wav")])  # assembly uses the WAV (sample-exact)
    subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(out / "vo.wav"),
                           "-c:a", "libmp3lame", "-b:a", "192k", str(out / "vo.mp3")])  # for listening / sharing
    total = dur(out / "vo.wav")
    cues = split_cues(timeline, cfg["subtitle"]["max_chars"])
    for s in timeline:
        s.pop("chars"); s.pop("char_starts")
    json.dump({"source": "elevenlabs", "duration": round(total, 3), "sentences": timeline, "cues": cues},
              open(out / "timing.json", "w"), ensure_ascii=False, indent=1)
    print(f"vo.wav {total:.2f}s, {len(timeline)} sentences, {len(cues)} cues -> {out}")


def _silence(path, d):
    subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                           "-t", f"{max(d, 0.01):.3f}", "-c:a", "pcm_s16le", str(path)])
    return str(path)


if __name__ == "__main__":
    main()
