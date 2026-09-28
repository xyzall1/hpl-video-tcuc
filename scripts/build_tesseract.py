#!/usr/bin/env python3
"""Assemble a learning video in Tesseract from assemble.json and export MP4.

Layout: bumper in -> [MG plate + scene images + subtitles + VO] -> bumper out.
All scene/cue times in assemble.json and timing.json are VO seconds (VO t=0 = end of bumper in).
"""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from timing_lib import load_config  # noqa: E402


def tsrct():
    cands = [os.environ.get("TSRCT"), str(Path.home() / "Library/Application Support/Tesseract/bin/tsrct"),
             str(Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "Tesseract/bin/tsrct"), shutil.which("tsrct")]
    for c in cands:
        if c and Path(c).exists():
            return c
    sys.exit("Tesseract CLI (tsrct) not found — install it per the tesseract-video skill's installation reference.")


def run(*args, capture=True):
    r = subprocess.run([TS, *args], capture_output=True, text=True, env={**os.environ, "TESSERACT_SKILL": "hpl-video-tcuc"})
    if r.returncode:
        sys.exit(f"tsrct {args[0]} {args[1] if len(args) > 1 else ''} failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout


def probe(path, entries):
    return subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entries, "-of", "csv=p=0:s=x", str(path)]).decode().strip()


def dur_ms(path):
    return int(round(float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).decode()) * 1000))


def hex_rgba(h):
    h = h.lstrip("#"); return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1]


def main(cfg_path):
    global TS
    TS = tsrct()
    cfg = load_config()
    A = json.load(open(cfg_path))
    base = Path(cfg_path).resolve().parent
    P = lambda p: str((base / p).resolve()) if p else None
    out_dir = Path(P(A.get("out_dir", ".")))
    name = A["name"]
    proj = out_dir / f"{name}.tsrct"
    if proj.exists():  # keep history instead of overwriting
        v = out_dir / "Versions"; v.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        shutil.move(str(proj), v / f"{name}_{stamp}.tsrct")
        if (out_dir / f"{name}.mp4").exists():
            shutil.move(str(out_dir / f"{name}.mp4"), v / f"{name}_{stamp}.mp4")
    work = out_dir / ".tesseract-work"; work.mkdir(parents=True, exist_ok=True)
    W, H = cfg["canvas"]
    sub = cfg["subtitle"]
    timing = json.load(open(P(A["timing"])))

    # ---- import
    run("project", "create", "--project", str(proj))
    bi, bo = P(A.get("bumper_in")), P(A.get("bumper_out"))
    BI = json.loads(run("project", "import-video", "--project", str(proj), "--file", bi, "--asset-id", "bumper-in"))["durationMs"] if bi else 0
    BO = json.loads(run("project", "import-video", "--project", str(proj), "--file", bo, "--asset-id", "bumper-out"))["durationMs"] if bo else 0
    MG = json.loads(run("project", "import-video", "--project", str(proj), "--file", P(A["mg"]), "--asset-id", "mg"))["durationMs"]
    run("project", "import-asset", "--project", str(proj), "--file", P(A["vo"]), "--asset-id", "vo", "--kind", "audio")
    VO = dur_ms(P(A["vo"]))
    scenes = []
    for i, s in enumerate(A.get("scenes", [])):
        aid = f"scene-{i+1}"
        f = P(s["file"])
        if f.lower().endswith((".mp4", ".mov", ".m4v")):
            r = json.loads(run("project", "import-video", "--project", str(proj), "--file", f, "--asset-id", aid))
            scenes.append({**s, "aid": aid, "kind": "Video", "w": r["width"], "h": r["height"], "src_ms": r["durationMs"]})
        else:
            run("project", "import-asset", "--project", str(proj), "--file", f, "--asset-id", aid, "--kind", "image")
            iw, ih = map(int, probe(f, "stream=width,height").split("x"))
            scenes.append({**s, "aid": aid, "kind": "Image", "w": iw, "h": ih})
    font = str(ROOT / sub["font"])
    run("project", "import-font", "--project", str(proj), "--file", font)

    O = BI                      # VO section start on the edit clock
    SECTION = max(MG, VO)
    BO_START = O + SECTION
    TOTAL = BO_START + BO
    ms = lambda s: int(round(s * 1000))
    ident = lambda: {"anchorPoint": [0, 0], "position": [0, 0], "scale": [100, 100], "rotation": 0, "opacity": 100}

    run("project", "checkout", "--project", str(proj), "--output", str(work / "editable.json"))
    doc = json.load(open(work / "editable.json"))
    doc["dimensions"] = {"width": W, "height": H}
    doc["duration"] = TOTAL / 1000
    layers, actions, lid = [], [], 1

    # ---- subtitles (topmost): text before its pill; Rect position = top-left corner
    try:
        from PIL import ImageFont
        F = ImageFont.truetype(font, sub["font_size"]); width = F.getlength
    except Exception:
        width = lambda t: len(t) * sub["font_size"] * 0.56
    ph, pad, cy = sub["pill_height"], sub["padding_x"], sub["center_y"]
    for i, c in enumerate(timing["cues"]):
        st, du = O + ms(c["start"]), ms(c["end"]) - ms(c["start"])
        if du <= 0:
            continue
        pw = int(width(c["text"]) + pad * 2); x0, y0 = int(W / 2 - pw / 2), cy - ph // 2
        layers.append({"type": "Text", "id": lid, "name": f"Sub {i+1:03d} text", "activeRange": {"start": st, "duration": du}, "transform": ident(),
            "sourceText": {"text": c["text"], "fontFamily": sub["font_family"], "fontStyle": sub["font_style"], "fontSize": sub["font_size"],
                           "fillColor": hex_rgba(sub["text_color"]), "justification": "center", "boxText": True,
                           "boxPosition": [x0, y0], "boxSize": [pw, ph], "verticalAlign": "center"}}); lid += 1
        layers.append({"type": "Rect", "id": lid, "name": f"Sub {i+1:03d} bg", "activeRange": {"start": st, "duration": du}, "transform": ident(),
            "rect": {"size": [pw, ph], "position": [x0, y0], "roundness": ph / 2, "fillColor": hex_rgba(sub["background"])}}); lid += 1

    # ---- scene images / extra footage: cover the canvas, crossfade, slow push-in
    fade = cfg["image_fade_ms"]
    for s in scenes:
        st = O + ms(s["start"]); du = ms(s["end"]) - ms(s["start"])
        cover = max(W / s["w"], H / s["h"]) * 100 * 1.005
        z0, z1 = cover, cover * 1.05
        L = {"type": s["kind"], "id": lid, "name": Path(s["file"]).stem, "activeRange": {"start": st, "duration": du},
             "transform": {"anchorPoint": [s["w"] / 2, s["h"] / 2], "position": [W / 2, H / 2], "scale": [z0, z0], "rotation": 0, "opacity": 100},
             "source": {"assetId": s["aid"], "fit": "contain"}}
        if s["kind"] == "Video":
            src = ms(s.get("src_start", 0))
            L.update({"sourceRange": {"start": src, "duration": min(du, s["src_ms"] - src)}, "sourceIntrinsicDuration": s["src_ms"],
                      "volume": s.get("volume", 0.0)})
        layers.append(L)
        k = s["aid"]
        actions.append({"type": "setFxPropertyKeyframes", "compositionId": "main", "property": {"layerId": lid, "propertyType": "opacity"}, "keyframes": [
            {"id": f"{k}-o0", "layerTime": 0, "value": {"type": "float", "value": 0}, "easing": {"type": "linear"}},
            {"id": f"{k}-o1", "layerTime": fade, "value": {"type": "float", "value": 100}, "easing": {"type": "linear"}},
            {"id": f"{k}-o2", "layerTime": du - fade, "value": {"type": "float", "value": 100}, "easing": {"type": "linear"}},
            {"id": f"{k}-o3", "layerTime": du - 1, "value": {"type": "float", "value": 0}, "easing": {"type": "linear"}}]})
        if s.get("push_in", True):
            for ax in ("scaleX", "scaleY"):  # vec2 'scale' is not an animatable property; split axes
                actions.append({"type": "setFxPropertyKeyframes", "compositionId": "main", "property": {"layerId": lid, "propertyType": ax}, "keyframes": [
                    {"id": f"{k}-{ax}0", "layerTime": 0, "value": {"type": "float", "value": z0}, "easing": {"type": "linear"}},
                    {"id": f"{k}-{ax}1", "layerTime": du, "value": {"type": "float", "value": z1}, "easing": {"type": "linear"}}]})
        lid += 1

    # ---- MG plate
    layers.append({"type": "Video", "id": lid, "name": "HyperFrames MG", "activeRange": {"start": O, "duration": MG},
                   "sourceRange": {"start": 0, "duration": MG}, "sourceIntrinsicDuration": MG, "transform": ident(),
                   "source": {"assetId": "mg", "fit": "contain"}}); lid += 1
    # ---- bumpers (audio kept, gain-trimmed: supplied bumpers are mastered hot)
    for aid, path, st, d in [("bumper-in", bi, 0, BI), ("bumper-out", bo, BO_START, BO)]:
        if not path:
            continue
        bw, bh = map(int, probe(path, "stream=width,height").split("x"))
        sc = min(W / bw, H / bh) * 100
        layers.append({"type": "Video", "id": lid, "name": aid, "activeRange": {"start": st, "duration": d}, "sourceRange": {"start": 0, "duration": d},
                       "sourceIntrinsicDuration": d, "volume": A.get("bumper_gain", cfg["bumper_gain"]),
                       "transform": {"anchorPoint": [0, 0], "position": [(W - bw * sc / 100) / 2, (H - bh * sc / 100) / 2], "scale": [sc, sc], "rotation": 0, "opacity": 100},
                       "source": {"assetId": aid, "fit": "contain"}}); lid += 1
    # ---- VO
    layers.append({"type": "Audio", "id": lid, "name": "VO", "activeRange": {"start": O, "duration": VO}, "sourceRange": {"start": 0, "duration": VO},
                   "sourceIntrinsicDuration": VO, "source": {"assetId": "vo"}, "volume": A.get("vo_gain", 1.0), "captionsEnabled": False})

    doc["composition"]["layers"] = layers
    json.dump(doc, open(work / "editable.json", "w"), ensure_ascii=False, indent=1)
    json.dump(actions, open(work / "edits.json", "w"))
    run("project", "commit", "--project", str(proj), "--file", str(work / "editable.json"))
    if actions:
        run("project", "apply", "--project", str(proj), "--actions", str(work / "edits.json"))

    mp4 = out_dir / f"{name}.mp4"
    run("export", "--project", str(proj), "--resolution", cfg["export"]["resolution"], "--fps", str(cfg["export"]["fps"]), "--output", str(mp4))
    (out_dir / "Previews").mkdir(exist_ok=True)
    run("filmstrip", "--project", str(proj), "--start-ms", "0", "--duration-ms", str(TOTAL - 500),
        "--interval-ms", str(max(4000, TOTAL // 24 // 1000 * 1000)), "--output", str(out_dir / "Previews/Filmstrip.png"))
    loud = subprocess.run(["ffmpeg", "-nostdin", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = [l.strip() for l in loud.splitlines() if l.strip().startswith(("I:", "Peak:"))][-2:]
    print(json.dumps({"project": str(proj), "video": str(mp4), "duration_s": TOTAL / 1000, "layers": len(layers),
                      "loudness": summary, "filmstrip": str(out_dir / "Previews/Filmstrip.png")}, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build_tesseract.py assemble.json")
    main(sys.argv[1])
