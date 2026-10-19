"""Build (or read back) the HPL CMS upload workbook.

  python3 build_cms.py build <data.json> <out.xlsx>     # JSON -> formatted workbook (+ checks)
  python3 build_cms.py dump  <in.xlsx>  <data.json>     # existing workbook -> JSON, to revise and rebuild

data.json:
{
  "credits": {"author": "...", "reviewer": "...", "video_tool": "Claude", "audio_tool": "NotebookLM"},
  "sheets": [
    {"name": "TC262 L1",
     "courses": {"KB1": {"design": "...", "description": "...", "text_core": "Konten ini berfokus pada penjelasan ..."}},
     "lus": [{"kb": "KB1", "modul": 1, "judul_modul": "...", "judul_video": "...", "caption_video": "...",
              "judul_audio": "...", "caption_audio": "...", "judul_artikel": "..."}]}
  ]
}
Captions in JSON are the content sentences only; the credit block is added here."""
import sys, json, re, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

COLS = [("No", 5), ("LU", 15), ("Course Design", 30), ("Course Description", 60), ("Learning Content Title", 30),
        ("Text Core", 60), ("Judul Modul", 30), ("Judul Video", 32), ("Caption Video", 60), ("Judul Audio", 32),
        ("Caption Audio", 60), ("Judul Artikel", 36)]
PREFIX = "Konten ini berfokus pada penjelasan "

def credit(tool, c):
    return (f"Produced with the support of Artificial Intelligence (AI) tools: {tool}.\n"
            f"Learning content created by {c['author']}.\nReviewed by {c['reviewer']}.")

def strip_credit(text):
    parts = (text or "").split("\n\n", 1)
    return parts[1].strip() if len(parts) == 2 and parts[0].startswith("Produced with") else (text or "").strip()

def check(d):
    warn = []
    for sh in d["sheets"]:
        seen = {}
        for kb, c in sh["courses"].items():
            if not c["text_core"].startswith(PREFIX):
                warn.append(f"{sh['name']} {kb}: Text Core harus diawali '{PREFIX.strip()}'")
        for lu in sh["lus"]:
            tag = f"{sh['name']} {lu['kb']} M{lu['modul']}"
            if lu["kb"] not in sh["courses"]:
                warn.append(f"{tag}: KB tidak ada di courses")
            if lu["judul_artikel"].strip().lower() == lu["judul_modul"].strip().lower():
                warn.append(f"{tag}: Judul Artikel sama dengan Judul Modul (harus beda)")
            for k in ("judul_video", "judul_audio", "judul_artikel"):
                v = lu[k].strip().lower()
                if v in seen:
                    warn.append(f"{tag}: {k} kembar dengan {seen[v]}")
                seen[v] = tag
            for k in ("caption_video", "caption_audio"):
                t = lu[k]
                if t.startswith("Produced with"):
                    warn.append(f"{tag}: {k} sudah berisi kredit; tulis isi caption saja")
                n = len(re.findall(r"[.!?](\s|$)", t))
                if not 1 <= n <= 3:
                    warn.append(f"{tag}: {k} sebaiknya 1–3 kalimat (sekarang {n})")
            if re.search(r"\[[^\]]+\]", " ".join(str(v) for v in lu.values())):
                warn.append(f"{tag}: ada tanda [..] tersisa")
    return warn

def build(data, out):
    d = json.load(open(data))
    for w in check(d):
        print("CEK:", w)
    c = d["credits"]
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    head = dict(font=Font(bold=True, color="FFFFFFFF"), fill=PatternFill("solid", fgColor="FF2796A3"),
                alignment=Alignment(horizontal="center", vertical="center", wrap_text=True))
    thin = Side(style="thin", color="FFBFBFBF"); box = Border(left=thin, right=thin, top=thin, bottom=thin)
    for sh in d["sheets"]:
        ws = wb.create_sheet(sh["name"][:31])
        for i, (h, wdt) in enumerate(COLS, 1):
            cell = ws.cell(1, i, h); cell.border = box
            for k, v in head.items(): setattr(cell, k, v)
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = wdt
        ws.row_dimensions[1].height = 30
        lus = sorted(sh["lus"], key=lambda u: (int(re.sub(r"\D", "", u["kb"])), int(u["modul"])))
        for r, lu in enumerate(lus, 2):
            co = sh["courses"][lu["kb"]]
            row = [r - 1, f"{lu['kb']} · Modul {lu['modul']}", co["design"], co["description"], lu["judul_modul"],
                   co["text_core"], lu["judul_modul"], lu["judul_video"],
                   credit(c.get("video_tool", "Claude"), c) + "\n\n" + lu["caption_video"].strip(),
                   lu["judul_audio"], credit(c.get("audio_tool", "NotebookLM"), c) + "\n\n" + lu["caption_audio"].strip(),
                   lu["judul_artikel"]]
            for i, v in enumerate(row, 1):
                cell = ws.cell(r, i, v); cell.border = box
                cell.alignment = Alignment(vertical="top", wrap_text=True, horizontal="center" if i == 1 else None)
            ws.row_dimensions[r].height = 144
        ws.freeze_panes = "C2"
    wb.save(out)
    print("tersimpan:", out, "|", ", ".join(f"{s['name']} ({len(s['lus'])} LU)" for s in d["sheets"]))

def dump(xlsx, out):
    wb = openpyxl.load_workbook(xlsx); res = {"credits": None, "sheets": []}
    for ws in wb:
        rows = list(ws.iter_rows(values_only=True)); H = [str(h) for h in rows[0]]; g = lambda r, n: r[H.index(n)]
        sh = {"name": ws.title, "courses": {}, "lus": []}
        for r in rows[1:]:
            if not g(r, "LU"): continue
            kb, m = re.search(r"(KB\s*\d+).*?(\d+)\s*$", g(r, "LU")).groups(); kb = kb.replace(" ", "")
            sh["courses"].setdefault(kb, {"design": g(r, "Course Design"), "description": g(r, "Course Description"),
                                          "text_core": g(r, "Text Core")})
            cv = g(r, "Caption Video") or ""
            if res["credits"] is None and cv.startswith("Produced with"):
                L = cv.split("\n")
                res["credits"] = {"author": re.sub(r"^Learning content created by |\.$", "", L[1]),
                                  "reviewer": re.sub(r"^Reviewed by |\.$", "", L[2]),
                                  "video_tool": re.sub(r"^.*tools: |\.$", "", L[0]),
                                  "audio_tool": re.sub(r"^.*tools: |\.$", "", (g(r, "Caption Audio") or "").split("\n")[0])}
            sh["lus"].append({"kb": kb, "modul": int(m), "judul_modul": g(r, "Judul Modul"), "judul_video": g(r, "Judul Video"),
                              "caption_video": strip_credit(cv), "judul_audio": g(r, "Judul Audio"),
                              "caption_audio": strip_credit(g(r, "Caption Audio")), "judul_artikel": g(r, "Judul Artikel")})
        res["sheets"].append(sh)
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1); print("tersimpan:", out)

if __name__ == "__main__":
    {"build": build, "dump": dump}[sys.argv[1]](*sys.argv[2:4])
