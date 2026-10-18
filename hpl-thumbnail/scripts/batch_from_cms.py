"""Render every HPL thumbnail for one level from a CMS workbook sheet.
usage: python3 batch_from_cms.py <cms.xlsx> <sheet> <level> <code> <competency> <out_dir> [--palette=kuning|tosca|biru|ungu|hijau|pink] [--ornament=<nama>] [--audio-ornament=<nama>] [--jobs=4]
  level      : fundamental | developing | intermediate
  code       : file prefix, e.g. TC262_L1
  competency : competency name for the cover and course labels, e.g. "Strategic Media Planning"
CMS columns (header row 1): LU ("KB1 · Modul 1"), Course Design, Judul Video, Judul Audio, Judul Artikel.
Output: <code>_00_Cover Kompetensi - ..., <code>_0n_Cover Course n - ..., <code>_KBk_Mm_{Video,Artikel,Audio} - <judul>.png"""
import sys,os,re,subprocess,openpyxl
from concurrent.futures import ThreadPoolExecutor
args=[a for a in sys.argv[1:] if not a.startswith("--")]; opts=dict(a[2:].split("=",1) for a in sys.argv[1:] if a.startswith("--"))
xlsx,sheet,level,code,comp,out=args
orn=opts.get("ornament","heksagon"); aorn=opts.get("audio-ornament",orn)   # one ornament per competency; audio uses its 1:1 version
MT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"make_thumb.py")
os.makedirs(out,exist_ok=True)
clean=lambda t: re.sub(r"\s+"," ",re.sub(r'[:/?\\*"<>|]',"",str(t))).strip()
ws=openpyxl.load_workbook(xlsx,data_only=True)[sheet]
rows=list(ws.iter_rows(values_only=True)); H=[str(h).strip() if h else "" for h in rows[0]]
col=lambda name: H.index(name)
jobs=[]; P=lambda n: os.path.join(out,f"{code}_{n}.png")
jobs.append([P(f"00_Cover Kompetensi - {clean(comp)} ({level.title()})"),level,orn,comp,level.upper(),"--size=cover"])
courses=[]
for r in rows[1:]:
    lu=r[col("LU")]
    if not lu: continue
    kb=re.search(r"KB\s*(\d+)",lu).group(1); m=re.search(r"Modul\s*(\d+)",lu).group(1)
    cd=r[col("Course Design")]
    if cd and cd not in courses:
        courses.append(cd); n=len(courses)
        jobs.append([P(f"0{n}_Cover Course {n} - {clean(cd)}"),level,orn,cd,f"COURSE {n} – {comp.upper()}","--size=course"])
    for kind,c in (("Video","Judul Video"),("Artikel","Judul Artikel")):
        if r[col(c)]: jobs.append([P(f"KB{kb}_M{m}_{kind} - {clean(r[col(c)])}"),level,orn,r[col(c)],"--size=content"])
    if r[col("Judul Audio")]: jobs.append([P(f"KB{kb}_M{m}_Audio - {clean(r[col('Judul Audio')])}"),level,aorn,r[col("Judul Audio")],"--format=square"])
def run(j):
    p=subprocess.run(["python3",MT,*j,"--palette="+opts.get("palette","kuning")],capture_output=True,text=True)
    return j[0],p.returncode==0 and os.path.exists(j[0]),p.stderr[-300:]
with ThreadPoolExecutor(int(opts.get("jobs",4))) as ex:
    for f,ok,err in ex.map(run,jobs): print("OK  " if ok else "FAIL",os.path.basename(f),"" if ok else err)
# contact sheet
from PIL import Image
fs=sorted(j[0] for j in jobs if os.path.exists(j[0])); W=480
c=Image.new("RGB",(W*4+30,280*((len(fs)+3)//4)),"white")
for i,f in enumerate(fs):
    im=Image.open(f); im=im.resize((W,270) if im.width!=im.height else (270,270))
    c.paste(im,((i%4)*(W+10)+(W-im.width)//2,(i//4)*280))
cs=os.path.join(out,f"../{code}_contact_sheet.jpg"); c.save(cs,quality=85); print("contact sheet:",os.path.abspath(cs))
