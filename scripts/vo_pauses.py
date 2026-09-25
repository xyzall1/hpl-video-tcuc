#!/usr/bin/env python3
"""Add breathing pauses to a supplied VO.

detect: snap each transcript line (Whisper "[mm:ss] text" report) to the nearest real silence and propose cuts.
apply : insert the pauses and write vo.wav/vo.mp3 + timing.json (same schema as make_vo.py).

cuts.json (edit before apply):
  {"vo": "...", "lines": [{"t": 1.75, "type": "S"|"P"|"-", "text": "Tabelnya presisi, ..."}, ...], "first_text": "..."}
  - each line = one spoken sentence/line starting at its cut `t` (original seconds); first line starts at 0
  - type: S = sentence pause, P = paragraph/topic pause, "-" = no pause (just a subtitle boundary)
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from timing_lib import load_config, split_cues  # noqa: E402


def silences(vo, noise="-30dB", d=0.08):
    err = subprocess.run(["ffmpeg", "-nostdin", "-i", vo, "-af", f"highpass=f=100,silencedetect=n={noise}:d={d}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en))


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).decode())


def read_transcript(path):
    lines = []
    for m in re.finditer(r"\[(\d+):(\d+)\]\s*(.+)", Path(path).read_text(encoding="utf-8")):
        lines.append((int(m.group(1)) * 60 + int(m.group(2)), m.group(3).strip()))
    return lines


def detect(a):
    gaps = silences(a.vo)
    lines = read_transcript(a.transcript)
    out = []
    for i, (sec, text) in enumerate(lines):
        if i == 0:
            continue
        # Whisper floors to the second: speech starts within [sec-0.4, sec+1.0)
        cand = [g for g in gaps if sec - 0.4 <= g[1] <= sec + 1.0]
        if cand:
            g = max(cand, key=lambda g: g[1] - g[0])
            t, gl = round((g[0] + g[1]) / 2, 2), g[1] - g[0]
        else:
            t, gl = float(sec), 0
        prev = lines[i - 1][1].rstrip()
        typ = "-" if prev.endswith(",") else ("P" if gl > 0.6 else "S")
        out.append({"t": t, "type": typ, "text": text, "gap": round(gl, 2), "whisper": sec})
    json.dump({"vo": str(Path(a.vo).resolve()), "first_text": lines[0][1] if lines else "", "lines": out},
              open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(out)} boundaries -> {a.out}. Review: mark topic changes P, '-' for mid-sentence, fix text.")


def apply(a):
    cfg = load_config()
    c = json.load(open(a.cuts))
    vo = a.vo or c["vo"]
    D = dur(vo)
    pause = {"S": cfg["pauses"]["sentence"], "P": cfg["pauses"]["paragraph"], "-": 0.0}
    rows = [{"t": 0.0, "type": "-", "text": c["first_text"]}] + c["lines"]
    out = Path(a.out_dir); seg = out / "segments"; seg.mkdir(parents=True, exist_ok=True)
    lead, tail = cfg["pauses"]["lead_in"], cfg["pauses"]["tail"]
    parts, t, sentences, para = [], lead, [], 0
    def sil(i, d):
        p = seg / f"sil_{i:03d}.wav"
        subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{max(d,0.01):.3f}", str(p)])
        return p
    parts.append(sil(0, lead))
    for i, r in enumerate(rows):
        a0 = r["t"]; a1 = rows[i + 1]["t"] if i + 1 < len(rows) else D
        if i and r["type"] == "P":
            para += 1
        p = seg / f"v_{i:03d}.wav"
        subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{a0:.3f}", "-t", f"{a1-a0:.3f}", "-i", vo,
                               "-ar", "44100", "-ac", "1", str(p)])
        d = dur(p)
        sentences.append({"text": r["text"], "paragraph": para, "start": round(t, 3), "end": round(t + d, 3), "src_start": a0})
        parts.append(p); t += d
        if i + 1 < len(rows):
            g = pause[rows[i + 1]["type"]]
            if g > 0:
                parts.append(sil(i + 1, g)); t += g
    parts.append(sil(999, tail))
    lst = seg / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "pcm_s16le", str(out / "vo.wav")])
    subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(out / "vo.wav"), "-b:a", "192k", str(out / "vo.mp3")])
    # a row's audio slice starts at the silence midpoint; shift subtitle to ~ speech onset
    for s in sentences:
        s["start"] = round(s["start"] + (0.12 if s["src_start"] > 0 else 0), 3)
    cues = split_cues(sentences, cfg["subtitle"]["max_chars"])
    total = dur(out / "vo.wav")
    json.dump({"source": "supplied", "duration": round(total, 3), "sentences": sentences, "cues": cues},
              open(out / "timing.json", "w"), ensure_ascii=False, indent=1)
    print(f"vo.wav {total:.2f}s (was {D:.2f}s), {len(sentences)} lines, {len(cues)} cues -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    d = sp.add_parser("detect"); d.add_argument("--vo", required=True); d.add_argument("--transcript", required=True); d.add_argument("--out", required=True)
    p = sp.add_parser("apply"); p.add_argument("--cuts", required=True); p.add_argument("--vo"); p.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    detect(a) if a.cmd == "detect" else apply(a)
