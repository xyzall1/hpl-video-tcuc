"""Collect inputs for the CMS workbook.

  python3 collect.py kb <TC-229> <level>                 # key behaviours from the Direktori Kompetensi (Dirkom)
  python3 collect.py addie <design.xlsx> <level>         # course names + topic (module) titles from an ADDIE workbook
  python3 collect.py folder <section_dir> [--no-transcribe] [--out=<dir>]
                                                         # per section: video/audio/article files, article heading,
                                                         # transcripts (npx hyperframes transcribe) -> JSON report

Dirkom data is not bundled (internal document). It is read from env DIRKOM_JSON or from the
instructional-design-addie skill (references/competencies.json) in the usual install locations."""
import sys, os, re, json, glob, subprocess

LEVELS = {1: "Fundamental", 2: "Developing", 3: "Intermediate", 4: "Advanced", 5: "Mastery"}
VERBS = [(r"^Mampu menjelaskan\s+", ""), (r"^Menerapkan\s+", "penerapan "), (r"^Membuat\s+", "cara membuat "),
         (r"^(Mengidentifikasi|Menganalisis|Merancang|Melakukan|Menjalankan|Memformulasikan|Memberikan|"
          r"Mengintegrasikan|Mengembangkan|Menyelaraskan)\s+", lambda m: "cara " + m.group(1).lower() + " ")]

def dirkom_path():
    cands = [os.environ.get("DIRKOM_JSON", "")] + [os.path.expanduser(p) for p in (
        "~/.claude/skills/instructional-design-addie/references/competencies.json",
        "~/.codex/skills/instructional-design-addie/references/competencies.json",
        "~/Documents/tcuc-studio/skills/instructional-design-addie/references/competencies.json")]
    for p in cands:
        if p and os.path.exists(p): return p
    sys.exit("Data Dirkom tidak ditemukan. Set DIRKOM_JSON ke competencies.json dari skill instructional-design-addie.")

def kb_phrase(kb):
    """KB sentence -> phrase that follows 'pembahasan mengenai'."""
    s = kb.strip()
    for pat, rep in VERBS:
        if re.match(pat, s): return re.sub(pat, rep, s, count=1)
    return s[0].lower() + s[1:]

def cmd_kb(code, level):
    code = code.upper().replace("TC", "TC-").replace("--", "-") if not re.match(r"[A-Z]+-\d+", code.upper()) else code.upper()
    data = json.load(open(dirkom_path()))
    c = next((x for x in data if x["code"] == code), None)
    if not c: sys.exit(f"{code} tidak ada di Dirkom")
    kbs = c["levels"].get(str(level), [])
    out = {"code": c["code"], "competency": c["name"], "level": LEVELS[int(level)],
           "kb": [{"kb": f"KB{i}", "text": t, "phrase": kb_phrase(t)} for i, t in enumerate(kbs, 1)]}
    print(json.dumps(out, ensure_ascii=False, indent=1))

def cmd_addie(xlsx, level):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    ws = next(w for w in wb if "Design-Topik" in w.title)
    rows = list(ws.iter_rows(values_only=True)); H = [str(h or "") for h in rows[0]]
    g = lambda r, n: r[H.index(n)]
    courses = {}
    for r in rows[1:]:
        if not r[0] or not str(r[0]).startswith(str(level)): continue
        kb = "KB" + str(int(str(g(r, "Kode course")).split("-C")[-1]))
        courses.setdefault(kb, {"course_code": g(r, "Kode course"), "name": g(r, "Judul course"), "topics": []})
        courses[kb]["topics"].append({"modul": int(g(r, "No")), "title": g(r, "Judul topik")})
    print(json.dumps(courses, ensure_ascii=False, indent=1))

BOILER = re.compile(r"(?i)^(telkom corporate university|school of|modul pembelajaran|[a-e]\.\s|identitas modul|daftar isi)")

def module_title(path):
    """Module title and competency code. Order: identity-table row 'Judul/Nama Modul', first non-boilerplate
    title line, then the file name ('…_Modul3_Evaluasi_dan_Business_Case' -> 'Evaluasi dan Business Case')."""
    title, code, text = None, None, ""
    try:
        if path.lower().endswith(".docx"):
            import docx
            d = docx.Document(path)
            for t in d.tables:
                for r in t.rows:
                    cells = [c.text.strip() for c in r.cells]
                    if len(cells) >= 2:
                        if re.match(r"(?i)(judul|nama) modul", cells[0]): title = title or cells[1]
                        if re.match(r"(?i)kode kompetensi", cells[0]): code = code or cells[1]
                    text += " ".join(cells) + "\n"
            text = "\n".join(p.text for p in d.paragraphs) + "\n" + text
        elif path.lower().endswith(".pptx"):
            from pptx import Presentation
            for sl in Presentation(path).slides[:3]:
                for sh in sl.shapes:
                    if sh.has_text_frame: text += sh.text_frame.text + "\n"
        elif path.lower().endswith(".pdf"):
            text = subprocess.run(["pdftotext", "-l", "2", path, "-"], capture_output=True, text=True).stdout
    except Exception as e:
        return {"title": None, "code": None, "note": f"gagal dibaca: {e}"}
    m = re.search(r"\b(TC|LC)-?\s?(\d{3})\b", (code or "") + " " + text + " " + os.path.basename(path))
    code = f"{m.group(1)}-{m.group(2)}" if m else None
    if not title:
        fm = re.search(r"(?i)modul[\s_-]*\d+[\s_-]+(.+)$", os.path.splitext(os.path.basename(path))[0])
        if fm: title = fm.group(1).replace("_", " ").strip()
    if not title:
        title = next((l.strip() for l in text.splitlines() if l.strip() and not BOILER.match(l.strip())), None)
    return {"title": title, "code": code}

def heading(docx_path):
    import docx
    d = docx.Document(docx_path)
    for p in d.paragraphs:
        if p.text.strip(): return p.text.strip()

def transcribe(path, out):
    os.makedirs(out, exist_ok=True)
    subprocess.run(["npx", "--yes", "hyperframes", "transcribe", path, "-d", out, "-m", "small", "-l", "id"],
                   capture_output=True)
    f = os.path.join(out, "transcript.json")
    if not os.path.exists(f): return None
    d = json.load(open(f)); w = d if isinstance(d, list) else d.get("words", d.get("segments", []))
    return " ".join((x.get("text") or x.get("word") or "").strip() for x in w)

def cmd_folder(path, *opts):
    o = dict(a[2:].split("=", 1) if "=" in a else (a[2:], True) for a in opts)
    out = o.get("out", "/tmp/hpl-cms-transcripts")
    files = sorted(glob.glob(os.path.join(path, "*")))
    pick = lambda exts: [f for f in files if f.lower().endswith(exts)]
    rep = {"folder": path, "modul": [], "video": [], "audio": [], "artikel": []}
    is_mod = lambda f: "modul" in os.path.basename(f).lower() and "artikel" not in os.path.basename(f).lower()
    stem = lambda f: re.sub(r"\s*\(\d+\)$", "", re.sub(r"^\d+\s*", "", os.path.splitext(os.path.basename(f))[0])).replace("_", " ").strip()
    for f in pick((".mp4", ".mov", ".m4v")):
        rep["video"].append({"file": f, "title_from_name": stem(f),
                             "transcript": None if o.get("no-transcribe") else transcribe(f, os.path.join(out, "v_" + stem(f)[:40]))})
    for f in pick((".mp3", ".m4a", ".wav")):
        rep["audio"].append({"file": f, "title_from_name": stem(f),
                             "transcript": None if o.get("no-transcribe") else transcribe(f, os.path.join(out, "a_" + stem(f)[:40]))})
    for f in pick((".pptx", ".pdf", ".docx")):
        if is_mod(f) or f.lower().endswith((".pptx", ".pdf")):
            rep["modul"].append({"file": f, **module_title(f)})
        else:
            rep["artikel"].append({"file": f, "heading": heading(f)})
    if not rep["modul"]:
        rep["modul_note"] = "Tidak ada file modul: tanyakan judul modul ke user (jangan ambil dari artikel)."
    print(json.dumps(rep, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    {"kb": cmd_kb, "addie": cmd_addie, "folder": cmd_folder}[sys.argv[1]](*sys.argv[2:])
