"""HPL thumbnail 16:9 (1920x1080), recreated from Thumbnail_HPL_16x9.pptx (six colour families: amber, cyan, blue, violet, emerald, rose).
Backgrounds are the deck's own images; ornaments use the deck's exact geometry and colours.
usage: python3 make_thumb.py out.png <level> <ornament> "<title>" ["<LABEL>"] [--size=cover|course|content] [--format=square] [--palette=kuning|tosca|biru|ungu|hijau|pink]
  level    : fundamental | developing | intermediate   (background brightness)
  ornament : hexagon | orbit
  size     : cover 46pt, course 40pt, content 32pt (deck values; 1pt = 2px at 1920 wide)"""
import sys,os,subprocess,shutil,tempfile,html,base64,math
args=[a for a in sys.argv[1:] if not a.startswith("--")]; opts=dict(a[2:].split("=") for a in sys.argv[1:] if a.startswith("--") and "=" in a)
out,level,orn,title=args[:4]; label=args[4] if len(args)>4 else ""
size=opts.get("size","content" if not label else "course")
HERE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
# level -> background (Fundamental = second-brightest, Intermediate = darkest, per user; Developing = brightest)
SQ=opts.get("format")=="square"
# user-facing colour names (Indonesian) -> deck colour family
ALIAS={"kuning":"amber","oranye":"amber","tosca":"cyan","biru muda":"cyan","biru":"blue","ungu":"violet","hijau":"emerald","pink":"rose","merah muda":"rose"}
PAL=opts.get("palette","kuning").strip().lower(); PAL=ALIAS.get(PAL,PAL)
# colour families from the decks: (ornament fill, ornament stroke = label colour)
COLORS={"amber":("#FBBF24","#FCD34D"),"cyan":("#22D3EE","#67E8F9"),"blue":("#60A5FA","#93C5FD"),
        "violet":("#A78BFA","#C4B5FD"),"emerald":("#34D399","#6EE7B7"),"rose":("#FB7185","#FDA4AF")}
if PAL not in COLORS: sys.exit("warna tidak dikenal; pilih: kuning, tosca, biru, ungu, hijau, pink")
BG=("sq_" if SQ else "")+PAL+"_"+{"fundamental":"mid","developing":"bright","intermediate":"dark"}[level]+".jpg"
W_,H_=(1080,1080) if SQ else (1920,1080)
TSZ={"cover":92,"course":80,"content":64}[size]
# Arial Bold is not redistributed in the repo: use the bundled copy if present, else the macOS system font
FONT=next((f for f in (os.path.join(HERE,"fonts/ArialBold.ttf"),"/System/Library/Fonts/Supplemental/Arial Bold.ttf","/Library/Fonts/Arial Bold.ttf") if os.path.exists(f)),None)
if not FONT: sys.exit("Arial Bold tidak ditemukan; taruh file-nya di fonts/ArialBold.ttf")
def b64(p): return base64.b64encode(open(p,"rb").read()).decode()
F,S=COLORS[PAL]
def hexagon(x,y,w,h,a,lw):  # PowerPoint prst=hexagon, adj 25000 -> inset = 0.25*min(w,h)
    i=0.25*min(w,h); pts=[(x,y+h/2),(x+i,y),(x+w-i,y),(x+w,y+h/2),(x+w-i,y+h),(x+i,y+h)]
    return f'<polygon points="{" ".join(f"{px:.1f},{py:.1f}" for px,py in pts)}" fill="{F}" fill-opacity="{a}" stroke="{S}" stroke-width="{lw}"/>'
def diamond(x,y,w,h,a,lw):
    return f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" fill="{F}" fill-opacity="{a}" stroke="{S}" stroke-width="{lw}"/>'
def donut(x,y,d,a,lw):  # prst=donut adj 25000 -> ring thickness 0.25*d
    cx,cy,R=x+d/2,y+d/2,d/2; r=R-0.25*d
    return f'<path d="M{cx-R},{cy} a{R},{R} 0 1,0 {2*R},0 a{R},{R} 0 1,0 {-2*R},0 Z M{cx-r},{cy} a{r},{r} 0 1,1 {2*r},0 a{r},{r} 0 1,1 {-2*r},0 Z" fill="{F}" fill-opacity="{a}" fill-rule="evenodd" stroke="{S}" stroke-width="{lw}"/>'
def cube(x,y,s,a,lw):  # prst=cube adj 25000 -> depth 0.25*s
    d=0.25*s
    return (f'<polygon points="{x},{y+d} {x+d},{y} {x+s},{y} {x+s-d},{y+d}" fill="{F}" fill-opacity="{min(1,a+.1)}" stroke="{S}" stroke-width="{lw}"/>'
            f'<polygon points="{x+s-d},{y+d} {x+s},{y} {x+s},{y+s-d} {x+s-d},{y+s}" fill="{F}" fill-opacity="{a-.18}" stroke="{S}" stroke-width="{lw}"/>'
            f'<rect x="{x}" y="{y+d}" width="{s-d}" height="{s-d}" fill="{F}" fill-opacity="{a}" stroke="{S}" stroke-width="{lw}"/>')
def ell(x,y,d,a,lw): return f'<circle cx="{x+d/2}" cy="{y+d/2}" r="{d/2}" fill="{F}" fill-opacity="{a}" stroke="{S}" stroke-width="{lw}"/>'
pt=lambda emu: emu/12700*2  # line width EMU -> px
# ornaments: exact shape lists extracted from the decks (ornaments.json), drawn with PowerPoint preset geometry
import json
ORN_ALIAS={"hexagon":"heksagon","layers":"tumpukan","kartu":"grafik"}
orn=ORN_ALIAS.get(orn,orn)
ORN=json.load(open(os.path.join(HERE,"ornaments.json")))
if orn not in ORN: sys.exit("ornamen tidak dikenal; pilih: "+", ".join(sorted(ORN)))
def geom(t):
    x,y,w,h,a=t["x"],t["y"],t["w"],t["h"],t["adj"]; ss=min(w,h); P=lambda pts:"M"+" L".join(f"{px:.1f},{py:.1f}" for px,py in pts)+" Z"
    k=t["prst"]; A=lambda n,d: a.get(n,d)/100000
    if k=="ellipse": return [f"M{x},{y+h/2} a{w/2},{h/2} 0 1,0 {w},0 a{w/2},{h/2} 0 1,0 {-w},0 Z"]
    if k=="diamond": return [P([(x+w/2,y),(x+w,y+h/2),(x+w/2,y+h),(x,y+h/2)])]
    if k=="hexagon": i=A("adj",25000)*ss; return [P([(x,y+h/2),(x+i,y),(x+w-i,y),(x+w,y+h/2),(x+w-i,y+h),(x+i,y+h)])]
    if k=="triangle": return [P([(x+w*A("adj",50000),y),(x+w,y+h),(x,y+h)])]
    if k=="trapezoid": i=A("adj",25000)*ss; return [P([(x+i,y),(x+w-i,y),(x+w,y+h),(x,y+h)])]
    if k=="chevron": d=A("adj",50000)*ss; return [P([(x,y),(x+w-d,y),(x+w,y+h/2),(x+w-d,y+h),(x,y+h),(x+d,y+h/2)])]
    if k=="roundRect":
        r=A("adj",16667)*ss
        return [f"M{x+r},{y} H{x+w-r} A{r},{r} 0 0 1 {x+w},{y+r} V{y+h-r} A{r},{r} 0 0 1 {x+w-r},{y+h} H{x+r} A{r},{r} 0 0 1 {x},{y+h-r} V{y+r} A{r},{r} 0 0 1 {x+r},{y} Z"]
    if k=="donut":
        R1,R2=w/2,h/2; d=A("adj",25000)*ss; r1,r2=R1-d,R2-d; cx,cy=x+w/2,y+h/2
        return [f"M{cx-R1},{cy} a{R1},{R2} 0 1,0 {2*R1},0 a{R1},{R2} 0 1,0 {-2*R1},0 Z M{cx-r1},{cy} a{r1},{r2} 0 1,1 {2*r1},0 a{r1},{r2} 0 1,1 {-2*r1},0 Z"]
    if k=="pie":
        a1,a2=a.get("adj1",0)/60000,a.get("adj2",16200000)/60000; cx,cy,rx,ry=x+w/2,y+h/2,w/2,h/2
        sweep=(a2-a1)%360; pt=lambda g:(cx+rx*math.cos(math.radians(g)),cy+ry*math.sin(math.radians(g)))
        (sx,sy),(ex,ey)=pt(a1),pt(a2)
        return [f"M{cx},{cy} L{sx:.1f},{sy:.1f} A{rx},{ry} 0 {1 if sweep>180 else 0} 1 {ex:.1f},{ey:.1f} Z"]
    if k=="cube":
        d=A("adj",25000)*ss
        return [P([(x,y+d),(x+d,y),(x+w,y),(x+w-d,y+d)]),P([(x+w-d,y+d),(x+w,y),(x+w,y+h-d),(x+w-d,y+h)]),P([(x,y+d),(x+w-d,y+d),(x+w-d,y+h),(x,y+h)])]
    if k=="can":
        e=A("adj",25000)*ss/2; rx=w/2
        body=f"M{x},{y+e} V{y+h-e} A{rx},{e} 0 0 0 {x+w},{y+h-e} V{y+e} A{rx},{e} 0 0 1 {x},{y+e} Z"
        top=f"M{x},{y+e} a{rx},{e} 0 1,0 {w},0 a{rx},{e} 0 1,0 {-w},0 Z"
        return [body,top]
    sys.exit("bentuk belum didukung: "+k)
SHADE={"cube":(.10,-.18,0),"can":(0,.10)}   # PowerPoint lightens/darkens 3-D faces
svg=""
for t in ORN[orn]["square" if SQ else "wide"]["shapes"]:
    cx,cy=t["x"]+t["w"]/2,t["y"]+t["h"]/2
    tr=(f' transform="rotate({t["rot"]} {cx} {cy})' if t["rot"] else ' transform="')+(f' translate({2*cx} 0) scale(-1 1)' if t["flipH"] else "")+(f' translate(0 {2*cy}) scale(1 -1)' if t["flipV"] else "")+'"'
    col={"F":F,"S":S,None:"none"}[t["fill"]]
    for i,dp in enumerate(geom(t)):
        al=max(0,min(1,t["alpha"]+SHADE.get(t["prst"],(0,0,0))[i]))
        svg+=f'<path d="{dp}" fill="{col}" fill-opacity="{al:.2f}" fill-rule="evenodd" stroke="{S}" stroke-width="{t["lw"]:.2f}"{tr}/>'

lab=f'<div class="lab">{html.escape(label)}</div>' if label else ""
page=f'''<!doctype html><html><head><meta charset="UTF-8"><meta name="viewport" content="width={W_}, height={H_}"><title>thumb</title><style>
@font-face{{font-family:"ArialB";src:url(data:font/ttf;base64,{b64(FONT)})}}
html,body{{margin:0}}
#root{{position:relative;width:{W_}px;height:{H_}px;overflow:hidden;background:url(data:image/jpeg;base64,{b64(os.path.join(HERE,"bg",BG))}) center/cover}}
svg{{position:absolute;inset:0}}
/* text box: x122 y166 w914 h749, anchored middle; deck shadow blur 14pt, dist 2pt down, black 42% */
.box{{position:absolute;left:122px;top:166px;width:914px;height:749px;display:flex;flex-direction:column;justify-content:center;font-family:"ArialB",Arial,sans-serif;font-weight:700;filter:drop-shadow(0 3px 3px rgba(0,0,0,.45)) drop-shadow(0 4px 14px rgba(0,0,0,.35))}}
.lab{{font-size:26px;letter-spacing:6.4px;color:{S};margin-bottom:24px;text-transform:uppercase;white-space:nowrap}}
.box.sq{{left:104px;top:713px;width:873px;height:266px;align-items:center;text-align:center}}
.box.sq h1{{font-size:46px;line-height:1.3}}
h1{{margin:0;font-size:{TSZ}px;line-height:1.3;color:#fff;font-weight:700}}
</style></head><body><div id="root" data-composition-id="main" data-start="0" data-width="{W_}" data-height="{H_}" data-duration="1" data-fps="30">
<svg width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}">{svg}</svg><div class="box{' sq' if SQ else ''}">{lab}<h1>{" ".join(f'<span style="white-space:nowrap">{html.escape(w)}</span>' if "-" in w else html.escape(w) for w in title.split(" "))}</h1></div></div>
<script>window.__timelines={{main:{{duration:()=>1,seek(){{}},play(){{}},pause(){{}}}}}};</script></body></html>'''
d=tempfile.mkdtemp(); open(os.path.join(d,"index.html"),"w").write(page)
subprocess.run(["npx","hyperframes","snapshot","--no-end","--describe","false","-o","shot","--at","0.5"],cwd=d,capture_output=True)
shutil.copy(os.path.join(d,"shot","frame-00-at-0.5s.png"),out); print(out)
