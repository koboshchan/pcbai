import json, csv, math, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import transforms

from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("OVERLAY_DIR", str(ROOT / "out/overlay")))
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(OUT)
G = json.load(open("geom.json"))
BOMDIR = str(ROOT / "boards/bom")
SHA = {'DC0_v2':'899da15d','DC1':'b5d0b202','DC2':'04167d23','DC3_v2':'d7c2393f','motherboard_v2':'4932b44c'}

def load_csv(name):
    rows = {}
    for r in csv.DictReader(open(f'{BOMDIR}/{name}.csv')):
        key = r['reference']
        rows[key] = r
    return rows

SETS = [('DC0_v2','DC0_v2','DC0 v2'), ('DC1','DC1a','DC1 variant a'), ('DC1','DC1b','DC1 variant b'),
        ('DC1','DC1c','DC1 variant c'), ('DC1','DC1d','DC1 variant d'), ('DC2','DC2','DC2'),
        ('DC3_v2','DC3_v2','DC3 v2'), ('motherboard_v2','motherboard_v2','Motherboard v2')]
BODGE0 = ((18.25,44.27),(18.25,55.27))
PW, PH = 11, 8.5
FS = 5.6  # pt
PT_MM = 0.3528

def pad_patch(p, mir, X0, X1, color, alpha, ax=None):
    x = X0+X1-p['x'] if mir else p['x']
    rot = -p['rot'] if mir else p['rot']
    w, h = p['w'], p['h']
    if p['shape'] == 0 and abs(w-h) < 1e-3:  # circle
        return Circle((x,p['y']), w/2, fc=color, ec='none', alpha=alpha)
    r = Rectangle((x-w/2, p['y']-h/2), w, h, fc=color, ec='none', alpha=alpha)
    # kicad y down + angle CCW on screen; with inverted y axis, rotation sign flips
    r.set_transform(transforms.Affine2D().rotate_deg_around(x, p['y'], -rot) + ax.transData)
    return r

def xf(geom, cw):
    X0,Y0,X1,Y1 = geom['bbox']
    if cw: P=lambda x,y:(Y1-y, x-X0); dr=-90
    else:  P=lambda x,y:(y-Y0, X1-x); dr=90
    g={'bbox':[0,0,Y1-Y0,X1-X0]}
    g['tracks']=[]
    for t in geom['tracks']:
        if t[0]=='seg':
            a=P(t[2],t[3]); b=P(t[4],t[5]); g['tracks'].append(['seg',t[1],a[0],a[1],b[0],b[1],t[6]])
    g['fps']=[]
    for f in geom['fps']:
        f2=dict(f); a=P(f['bbox'][0],f['bbox'][1]); b=P(f['bbox'][2],f['bbox'][3])
        f2['bbox']=[min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])]
        f2['pads']=[]
        for p in f['pads']:
            p2=dict(p); p2['x'],p2['y']=P(p['x'],p['y']); p2['rot']=p['rot']+dr; f2['pads'].append(p2)
        g['fps'].append(f2)
    bod=tuple(P(*q) for q in BODGE0)
    return g, bod

def draw_page(pdf, title, sub, geom, rows, side, view, mir, pngpath=None, scale_note=''):
    X0, Y0, X1, Y1 = geom['bbox']
    vx0, vy0, vx1, vy1 = view
    fig = plt.figure(figsize=(PW,PH))
    ax = fig.add_axes([0.035, 0.05, 0.75, 0.86])
    bw, bh = vx1-vx0, vy1-vy0
    # equal aspect
    axw, axh = 0.75*PW, 0.86*PH
    s = min(axw/bw, axh/bh)  # in/mm
    cx, cy = (vx0+vx1)/2, (vy0+vy1)/2
    hw, hh = axw/s/2, axh/s/2
    if mir:
        cx = X0+X1-cx
    ax.set_xlim(cx-hw, cx+hw); ax.set_ylim(cy+hh, cy-hh)
    ax.set_axis_off()
    XL, XR = cx-hw, cx+hw; YT, YB = cy-hh, cy+hh
    fs_mm = FS*PT_MM/25.4/s*25.4  # board mm per text height
    fs_mm = FS/72/s
    # outline
    ax.add_patch(Rectangle((X0,Y0), X1-X0, Y1-Y0, fc='#f6f3e8', ec='#c9b26b', lw=1.2, zorder=-5))
    lay = 'F.Cu' if side=='F' else 'B.Cu'
    for t in geom['tracks']:
        if t[0]=='seg' and t[1]==lay:
            xs = [X0+X1-t[2], X0+X1-t[4]] if mir else [t[2], t[4]]
            ax.plot(xs, [t[3], t[5]], color='#d9d2bd', lw=t[6]*s*72, solid_capstyle='round', zorder=0)
    labels = []
    occupied = []
    for f in geom['fps']:
        r = rows.get(f['ref'])
        excluded = r is None
        status = 'EXCL' if excluded else r['status']
        onside = (f['side']==side)
        for p in f['pads']:
            if not (p['front'] if side=='F' else p['back']): continue
            if p['th'] and not onside:
                col, al = '#b8b3a6', 0.6
            elif not onside:
                continue
            elif status=='FIT': col, al = '#c7a14a', 0.95
            elif status=='DNP': col, al = '#c9c6bd', 0.7
            else: col, al = '#b8b3a6', 0.6
            pp = pad_patch(p, mir, X0, X1, col, al, ax); pp.set_zorder(1); ax.add_patch(pp)
            if p['th']:
                x = X0+X1-p['x'] if mir else p['x']
                ax.add_patch(Circle((x,p['y']), min(p['w'],p['h'])*0.28, fc='white', ec='none', zorder=2))
        if not onside or excluded: continue
        bx = [f['bbox'][0], f['bbox'][2]]
        if mir: bx = sorted([X0+X1-bx[0], X0+X1-bx[1]])
        fx = (bx[0]+bx[1])/2; fy = (f['bbox'][1]+f['bbox'][3])/2
        if not (vx0-2 <= (X0+X1-fx if mir else fx) <= vx1+2 and vy0-2 <= fy <= vy1+2): continue
        if status=='FIT':
            ax.add_patch(Rectangle((bx[0], f['bbox'][1]), bx[1]-bx[0], f['bbox'][3]-f['bbox'][1], fc='none', ec='#8a6d1f', lw=0.35, zorder=2))
        if status=='DNP':
            x0b,x1b,y0b,y1b = bx[0],bx[1],f['bbox'][1],f['bbox'][3]
            ax.plot([x0b,x1b],[y0b,y1b],color='#a9a59a',lw=0.4,zorder=3); ax.plot([x0b,x1b],[y1b,y0b],color='#a9a59a',lw=0.4,zorder=3)
            continue
        labels.append((f, r, status, fx, fy))
    # place labels: FIT first
    labels.sort(key=lambda l: (l[2]!='FIT', l[3], l[4]))
    th = fs_mm*1.25
    def box(x,y,w,h): return (x-w/2,y-h/2,x+w/2,y+h/2)
    def hit(b):
        for o in occupied:
            if b[0]<o[2] and b[2]>o[0] and b[1]<o[3] and b[3]>o[1]: return True
        return False
    for f, r, status, fx, fy in labels:
        val = r['value'] if r['source_value'] in ('POPULATION','') else r['source_value']
        if status=='DNP': val = 'DNP'
        if len(val) > 18:
            import textwrap
            val = '\n'.join(textwrap.wrap(val.replace('_',' _'), 16, break_long_words=True)).replace(' _','_')
        nl = val.count('\n')+1
        w = max(len(x) for x in val.split('\n'))*fs_mm*0.62+fs_mm*0.6
        h = th*nl
        cand = [(0,0)]
        for d in (1.0,1.6,2.3,3.2,4.2,5.5):
            for a in range(0,360,30):
                cand.append((d*h*math.cos(math.radians(a))*1.8, d*h*math.sin(math.radians(a))))
        for dx,dy in cand:
            px = min(max(fx+dx, XL+w/2), XR-w/2); py = min(max(fy+dy, YT+h/2+th), YB-h/2-th)
            b = box(px, py, w, h)
            if not hit(b): break
        dx, dy = px-fx, py-fy
        occupied.append(b)
        lx, ly = fx+dx, fy+dy
        if (dx,dy)!=(0,0):
            ax.plot([fx,lx],[fy,ly], color='#b3261e' if status=='FIT' else '#999', lw=0.4, zorder=4)
            ax.add_patch(Circle((fx,fy), fs_mm*0.12, fc='#b3261e' if status=='FIT' else '#999', zorder=4))
        if status=='FIT':
            ax.text(lx, ly, val, fontsize=FS, ha='center', va='center', color='#111', zorder=6, family='DejaVu Sans', clip_on=True,
                    fontweight='bold', bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='#8a6d1f', lw=0.3, alpha=0.92))
        else:
            ax.text(lx, ly, val, fontsize=FS*0.8, ha='center', va='center', color='#9a978f', zorder=5,
                    bbox=dict(boxstyle='round,pad=0.08', fc='#f0eee8', ec='none', alpha=0.8))
        if status=='FIT':
            ax.text(lx, ly+h*0.95, f['ref'], fontsize=FS*0.62, ha='center', va='center', color='#555', zorder=5, clip_on=True)
    if BODGE_ON[0] and side=='B':
        (ax_, ay_), (bx_, by_) = BODGE[0]
        xa = X0+X1-ax_ if mir else ax_; xb = X0+X1-bx_ if mir else bx_
        ax.plot([xa,xb],[ay_,by_], color='#e00000', lw=2.4, zorder=8)
        inv = lambda x,y: XL<=x<=XR and YT<=y<=YB
        for xx,yy,t in ((xa,ay_,'JS1 B7'),(xb,by_,'JS2 B7')):
            if not inv(xx,yy): continue
            ax.add_patch(Circle((xx,yy),0.7,fc='none',ec='#e00000',lw=1.4,zorder=8))
            ax.text(xx,yy-1.6,t,ha='center',va='bottom',color='#e00000',fontsize=7,fontweight='bold',zorder=9,clip_on=True,
                    bbox=dict(fc='white',ec='#e00000',lw=0.5,pad=1))
        mx_ = min(max((xa+xb)/2, XL+14), XR-14); my_=(ay_+by_)/2
        if inv(mx_, my_) or inv(xa,ay_) or inv(xb,by_):
            ax.text(mx_,my_+1.6,'BODGE WIRE (mandatory)' if abs(xb-xa)>8 else 'BODGE',ha='center',va='top',color='#e00000',fontsize=7.5,fontweight='bold',zorder=9,clip_on=True,
                    bbox=dict(fc='white',ec='none',alpha=0.85,pad=0.5))
    # header / sidebar
    fig.text(0.035,0.955,title,fontsize=15,fontweight='bold',color='#222')
    fig.text(0.035,0.928,sub,fontsize=8.5,color='#555')
    side_txt = 'TOP (F)\nviewed from above' if side=='F' else 'BACK (B), MIRRORED\nviewed from below'
    fig.text(0.80,0.975,side_txt,fontsize=9,va='top',fontweight='bold',color='#8a6d1f' if side=='F' else '#1f4e8a')
    sx = 0.80; y = 0.88
    leg = [('#c7a14a','Fitted pad, bold value label'),('#c9c6bd','DNP: dim + grey X, leave empty'),('#b8b3a6','THT from other side / no part')]
    for c,t in leg:
        fig.patches.append(Rectangle((sx,y),0.015,0.015,fc=c,transform=fig.transFigure,figure=fig)); fig.text(sx+0.022,y+0.002,t,fontsize=7); y-=0.03
    fig.text(sx,y,'Small grey text = reference.\nRed leader = label moved off part.\nCoords exact from KiCad source (mm).',fontsize=6.5,color='#444',va='top'); y-=0.08
    # mini map
    mm_ax = fig.add_axes([0.80,0.10,0.18,0.18*PW/PH*(Y1-Y0)/(X1-X0)])
    mm_ax.add_patch(Rectangle((X0,Y0),X1-X0,Y1-Y0,fc='#eee',ec='#999'))
    if mir: mx0 = X0+X1-vx1; mx1 = X0+X1-vx0
    else: mx0, mx1 = vx0, vx1
    mm_ax.add_patch(Rectangle((mx0,vy0),mx1-mx0,vy1-vy0,fc='#c7a14a55',ec='#8a6d1f'))
    mm_ax.set_xlim(X0-1,X1+1); mm_ax.set_ylim(Y1+1,Y0-1); mm_ax.set_aspect('equal'); mm_ax.set_xticks([]); mm_ax.set_yticks([])
    mm_ax.set_title('tile location'+(' (mirrored)' if mir else ''),fontsize=6.5)
    fig.text(0.80,0.06,scale_note,fontsize=6.5,color='#444')
    pdf.savefig(fig)
    if pngpath: fig.savefig(pngpath, dpi=160)
    plt.close(fig)

BODGE_ON = [False]
BODGE=[None]
os.makedirs('png_rot', exist_ok=True)
pages = []
with PdfPages('pcbai_value_overlay_rot90.pdf') as pdf:
    # cover
    fig = plt.figure(figsize=(PW,PH))
    fig.text(0.06,0.86,'pcbai value overlay assembly guide (rotated 90 CW)',fontsize=24,fontweight='bold')
    notes = ['Values shown directly on footprints, exact source precision (not rounded purchase values).',
             'Each board side: full overview page, then 2x2 zoomed tiles (50 x 50 mm each) for printing.',
             'DC1: four population variants a/b/c/d on identical bare PCB. Only fitted parts get values; DNP dimmed.',
             'DC3: DNP sites dimmed. Back sides are MIRRORED (as seen when you flip the board over).',
             'Motherboard: MANDATORY red bodge wire JS1 B7 (18.25, 44.27) to JS2 B7 (18.25, 55.27), back side.',
             'DC0: source value 74AHCT595S16-13; the part actually ordered is 74HCT595 (5V-tolerant HCT, works as drop-in).',
             'Board geometry rotated 90 degrees clockwise vs KiCad view; all text kept upright. Back = mirrored, then rotated.',
             'Source hashes: ' + ', '.join(f'{k} {v}' for k,v in SHA.items())]
    for i,n in enumerate(notes): fig.text(0.06,0.76-i*0.06,n,fontsize=10.5)
    pdf.savefig(fig); plt.close(fig)
    for gk, ck, name in SETS:
        geom0 = G[gk]; rows = load_csv(ck)
        BODGE_ON[0] = gk=='motherboard_v2'
        X0,Y0,X1,Y1 = geom0['bbox']
        nfit = sum(1 for r in rows.values() if r['status']=='FIT'); ndnp = sum(1 for r in rows.values() if r['status']=='DNP')
        sides = ['F'] + (['B'] if any(r['side']=='B' for r in rows.values()) or BODGE_ON[0] else [])
        for side in sides:
            mir = side=='B'
            geom, BODGE[0] = xf(geom0, not mir)
            X0,Y0,X1,Y1 = geom['bbox']
            sub = f'source sha {SHA[gk]}  |  {nfit} fitted' + (f', {ndnp} DNP' if ndnp else '') + f'  |  board {X1-X0:.2f} x {Y1-Y0:.2f} mm (rotated 90 CW)'
            tag = f'{ck}_{"top" if side=="F" else "back"}'
            draw_page(pdf, f'{name}  {"TOP" if side=="F" else "BACK"}  overview', sub, geom, rows, side, (X0,Y0,X1,Y1), mir, f'png_rot/{tag}_overview.png', 'Overview, for orientation; use tiles to read.')
            mx, my = (X0+X1)/2, (Y0+Y1)/2
            ov = 3
            tiles = [('top-left',(X0-1,Y0-1,mx+ov,my+ov)),('top-right',(mx-ov,Y0-1,X1+1,my+ov)),('bottom-left',(X0-1,my-ov,mx+ov,Y1+1)),('bottom-right',(mx-ov,my-ov,X1+1,Y1+1))]
            for tn, v in tiles:
                if mir: tn = tn.replace('left','L_').replace('right','left').replace('L_','right')
                draw_page(pdf, f'{name}  {"TOP" if side=="F" else "BACK"}  tile {tn}', sub, geom, rows, side, v, mir, f'png_rot/{tag}_{tn}.png', 'Rotated 90 CW view.' if not mir else 'Mirrored (seen from below), rotated 90 CW.')
print('done')
