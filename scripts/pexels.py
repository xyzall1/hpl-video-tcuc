#!/usr/bin/env python3
"""Pexels stock search/download via the official API (https://www.pexels.com/api/).

search  : find landscape videos (or photos) for a storyboard beat; writes candidates JSON + a thumbnail contact sheet.
download: fetch the chosen item into the scene folder and append attribution to credits.txt.

Key: env PEXELS_API_KEY or ~/.config/pexels/key. Never printed.
"""
import argparse, json, os, sys, urllib.parse, urllib.request
from pathlib import Path

API = "https://api.pexels.com"


def key():
    k = os.environ.get("PEXELS_API_KEY")
    p = Path.home() / ".config/pexels/key"
    if not k and p.exists():
        k = p.read_text().strip()
    if not k:
        sys.exit("PEXELS_API_KEY is not set (or ~/.config/pexels/key).")
    return k


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": key(), "User-Agent": "hpl-video-tcuc"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Pexels error {e.code}: {e.read().decode()[:300]}")


def best_file(files, min_h=720, max_h=1080):
    """Prefer an HD landscape MP4 between 720p and 1080p (enough for a 720p export, light to download)."""
    mp4 = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width") and f.get("height")]
    land = [f for f in mp4 if f["width"] >= f["height"]] or mp4
    ok = [f for f in land if min_h <= f["height"] <= max_h]
    pool = ok or sorted(land, key=lambda f: f["height"], reverse=True)
    return max(pool, key=lambda f: f["height"]) if ok else pool[0]


def search(a):
    q = urllib.parse.quote(a.query)
    if a.kind == "video":
        d = get(f"{API}/videos/search?query={q}&orientation=landscape&size=medium&per_page={a.n}&locale={a.locale}")
        items = []
        for v in d.get("videos", []):
            if v["duration"] < a.min_dur:
                continue
            f = best_file(v["video_files"])
            items.append({"id": v["id"], "kind": "video", "duration": v["duration"], "w": f["width"], "h": f["height"],
                          "download": f["link"], "thumb": v["image"], "page": v["url"], "author": v["user"]["name"],
                          "author_url": v["user"]["url"]})
    else:
        d = get(f"{API}/v1/search?query={q}&orientation=landscape&size=medium&per_page={a.n}&locale={a.locale}")
        items = [{"id": p["id"], "kind": "photo", "w": p["width"], "h": p["height"], "download": p["src"]["large2x"],
                  "thumb": p["src"]["medium"], "page": p["url"], "author": p["photographer"], "author_url": p["photographer_url"],
                  "alt": p.get("alt", "")} for p in d.get("photos", [])]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"query": a.query, "kind": a.kind, "items": items}, open(out, "w"), indent=1)
    sheet = contact_sheet(items, out.with_suffix(".jpg"), a.query)
    for i, it in enumerate(items, 1):
        extra = f"{it['duration']}s {it['w']}x{it['h']}" if it["kind"] == "video" else f"{it['w']}x{it['h']}"
        print(f"{i}. id={it['id']} {extra} by {it['author']}  {it['page']}")
    print(f"-> {out}" + (f" | sheet {sheet}" if sheet else ""))


def contact_sheet(items, path, title):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    import io
    tw, th, cols = 384, 216, 3
    rows = (len(items) + cols - 1) // cols or 1
    sheet = Image.new("RGB", (cols * tw, rows * (th + 28)), "white")
    dr = ImageDraw.Draw(sheet)
    for i, it in enumerate(items):
        try:
            im = Image.open(io.BytesIO(urllib.request.urlopen(it["thumb"], timeout=30).read())).convert("RGB")
            im.thumbnail((tw, th)); x, y = (i % cols) * tw, (i // cols) * (th + 28)
            sheet.paste(im, (x + (tw - im.width) // 2, y))
            label = f"{i+1}. {it['duration']}s" if it["kind"] == "video" else f"{i+1}."
            dr.text((x + 6, y + th + 6), f"{label}  id {it['id']}", fill=(29, 43, 54))
        except Exception:
            pass
    sheet.save(path, quality=85)
    return path


def download(a):
    c = json.load(open(a.candidates))
    it = next((x for x in c["items"] if str(x["id"]) == str(a.id)), None)
    if not it:
        sys.exit(f"id {a.id} not in {a.candidates}")
    dest_dir = Path(a.dest); dest_dir.mkdir(parents=True, exist_ok=True)
    ext = ".mp4" if it["kind"] == "video" else ".jpg"
    name = a.name or f"pexels-{it['kind']}-{it['id']}"
    dest = dest_dir / f"{name}{ext}"
    if dest.exists():
        sys.exit(f"{dest} exists; choose another --name")
    req = urllib.request.Request(it["download"], headers={"User-Agent": "hpl-video-tcuc"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    with open(dest_dir / "credits.txt", "a", encoding="utf-8") as f:
        f.write(f"{dest.name}: {it['kind']} by {it['author']} on Pexels ({it['page']})\n")
    print(json.dumps({"file": str(dest), "kind": it["kind"], "duration": it.get("duration"), "w": it["w"], "h": it["h"], "credit": it["author"]}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("search"); s.add_argument("--query", required=True); s.add_argument("--kind", choices=["video", "photo"], default="video")
    s.add_argument("--n", type=int, default=6); s.add_argument("--min-dur", type=int, default=4); s.add_argument("--locale", default="en-US")
    s.add_argument("--out", required=True)
    d = sp.add_parser("download"); d.add_argument("--candidates", required=True); d.add_argument("--id", required=True)
    d.add_argument("--dest", required=True); d.add_argument("--name")
    a = ap.parse_args()
    search(a) if a.cmd == "search" else download(a)
