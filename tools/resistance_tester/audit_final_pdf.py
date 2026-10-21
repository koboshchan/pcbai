#!/usr/bin/env python3
"""Audit the actual delivered PDF against a fresh, independent KiCad copper projection.

Run audit_copper.py --extract in KiCad 10 first, and refresh
pdf-projection-extract.json (actual through-hole drill centers/sizes).
Raster comparison uses absolute page coordinates, never registration/fitting.
"""
import json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parent
E=R/'evidence'
if '--extract' in sys.argv:
 import pcbnew as k
 b=k.LoadBoard(str(R/'fingerprint.kicad_pcb'))
 aux=dict(board_sha256=hashlib.sha256((R/'fingerprint.kicad_pcb').read_bytes()).hexdigest(),
  kicad_version=k.Version(),drills=[dict(ref=f.GetReference()+'.'+p.GetNumber(),
  xy=[k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y)],
  size=[k.ToMM(p.GetDrillSize().x),k.ToMM(p.GetDrillSize().y)])
  for f in b.GetFootprints() for p in f.Pads() if p.GetDrillSize().x])
 old=R/'old.kicad_pcb'
 if old.exists():
  previous=k.LoadBoard(str(old))
  aux['old_board_sha256']=hashlib.sha256(old.read_bytes()).hexdigest()
  aux['removed_ground_tracks']=[dict(a=[k.ToMM(t.GetStart().x),k.ToMM(t.GetStart().y)],
   b=[k.ToMM(t.GetEnd().x),k.ToMM(t.GetEnd().y)]) for t in previous.GetTracks() if t.GetNetname()=='GND']
 (E/'pdf-projection-extract.json').write_text(json.dumps(aux,indent=2)+'\n')
 sys.exit(0)
import pymupdf as fitz
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
pdf=Path('/home/kit/out/resistance-tester/rt-negative-letter-v2.pdf')
geom=json.loads((E/'copper-geometry.json').read_text())
aux=json.loads((E/'pdf-projection-extract.json').read_text())
assert aux['board_sha256']==geom['board_sha256']
assert geom['board_sha256']==hashlib.sha256((R/'fingerprint.kicad_pcb').read_bytes()).hexdigest()
mm=72/25.4; dpi=1200; ppm=dpi/25.4
offset=np.array([57.95,104.7])
def pt(xy):return fitz.Point(*((np.asarray(xy)+offset)*mm))
doc=fitz.open(pdf);page=doc[0]
assert len(doc)==1 and abs(page.rect.width-612)<1e-5 and abs(page.rect.height-792)<1e-5
ref=fitz.open();p=ref.new_page(width=612,height=792)
p.draw_rect(p.rect,color=None,fill=(0,0,0))
# Filled pad/zone polygons independently extracted from actual PCB, not SVG/PDF.
for it in geom['items']:
 for poly in it['polys']:
  sh=p.new_shape()
  for ring in [poly['shell']]+poly['holes']:
   points=[pt(v) for v in ring];sh.draw_polyline(points+[points[0]])
  sh.finish(color=None,fill=(1,1,1),even_odd=True);sh.commit()
for t in geom['tracks']:
 sh=p.new_shape();sh.draw_line(pt(t['a']),pt(t['b']))
 sh.finish(color=(1,1,1),width=t['width']*mm,lineCap=1,closePath=False);sh.commit()
for d in aux['drills']:
 x,y=d['xy'];dx,dy=np.array(d['size'])/2
 p.draw_oval(fitz.Rect(pt([x-dx,y-dy]),pt([x+dx,y+dy])),color=None,fill=(0,0,0))
clip=fitz.Rect(pt([0,0]),pt([100,70]))
def raster(pg):
 pix=pg.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),clip=clip,colorspace=fitz.csGRAY,alpha=False)
 return pix,np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width)
pix,a=raster(page);rp,b=raster(p)
assert (pix.x,pix.y,pix.width,pix.height)==(rp.x,rp.y,rp.width,rp.height)
A=a>=128;B=b>=128
# Only forgive sub-0.03 mm boundary tessellation/raster differences.
# This is tighter than a single 0.3 mm trace by more than an order of magnitude.
distB=ndi.distance_transform_edt(~B)
distA=ndi.distance_transform_edt(~A)
extra=A & ~B;missing=B & ~A
extra_max=float(distB[extra].max(initial=0)/ppm)
missing_max=float(distA[missing].max(initial=0)/ppm)
assert extra_max<=.03 and missing_max<=.03,(extra_max,missing_max)
# Actual clear pixel extents relative to the exact page board rectangle.
yy,xx=np.nonzero(A)
x=(xx+pix.x+.5)/ppm-offset[0];y=(yy+pix.y+.5)/ppm-offset[1]
edges=[float(x.min()),float(y.min()),float(100-x.max()),float(70-y.max())]
lower=min(edges)-.5/ppm
assert lower>=.5,edges
mirror_mismatch=float(np.count_nonzero(A!=np.fliplr(B))/A.size)
normal_mismatch=float(np.count_nonzero(A!=B)/A.size)
assert mirror_mismatch>normal_mismatch*10
# Preserve labeled final PDF preview; coordinates are physical PCB mm.
preview=Image.fromarray(a).convert('RGB');dr=ImageDraw.Draw(preview)
for x0 in range(0,101,10):
 px=round((x0+offset[0])*ppm-pix.x)
 dr.line((px,0,px,preview.height),fill=(80,80,255),width=2)
 dr.text((px+3,3),str(x0),fill=(255,0,0),stroke_width=1)
for y0 in range(0,71,10):
 py=round((y0+offset[1])*ppm-pix.y)
 dr.line((0,py,preview.width,py),fill=(80,80,255),width=2)
 dr.text((3,py+3),str(y0),fill=(255,0,0),stroke_width=1)
preview.resize((2000,1400)).save(E/'final-pdf-coordinate-preview.png')
diff=np.zeros((*A.shape,3),dtype=np.uint8);diff[B]=(180,180,180)
diff[extra]=(255,0,0);diff[missing]=(0,80,255)
Image.fromarray(diff).resize((2000,1400)).save(E/'final-pdf-projection-diff.png')
# Component inventory guards against an added isolated tab or missing connection.
la,na=ndi.label(A);lb,nb=ndi.label(B)
sa=np.sort(np.bincount(la.ravel())[1:]);sb=np.sort(np.bincount(lb.ravel())[1:])
assert na==nb,(na,nb)
# Direct FINAL-PDF electrical continuity checks at the two disputed features.
def actual_component(x,y):
 ix=round((x+offset[0])*ppm-pix.x-.5)
 iy=round((y+offset[1])*ppm-pix.y-.5)
 return int(la[iy,ix])
def connected(points):
 ids=[actual_component(*xy) for xy in points]
 assert ids[0]>0 and len(set(ids))==1,(points,ids)
 return dict(points_mm=points,pdf_copper_component=ids[0])
# The apparent bottom-right U/tab is the signal-side C26 pad and its short feed.
tab=connected([[72.9125,66.5],[79.45,66.5],[79.45,67.78],[95.65,50.48]])
# The apparent left edge exit bends UP 0.8 mm inside the board.
side=connected([[15.65,49.02],[.8,49.02],[.8,.8],[71.0875,2.5]])
features=dict(
 lower_right_tab=dict(net='T26',part='C26.2',pad_bbox_mm=[78.95,67.055,79.95,68.505],
 pad_to_bottom_edge_mm=1.495,feed_mm=[[79.45,66.5],[79.45,67.78]],
 identity='functional capacitor signal pad, connected in actual PDF to R26.2 and J4.13, not a dangling GND escape',continuity=tab),
 left_side_exit=dict(net='GP28',part='J2.14 to R1.1',turn_mm=[.8,49.02],
 trace_leftmost_mm=.65,identity='white signal turns upward inside board; adjacent black isolation opens to etched border, not copper touching edge',continuity=side))
out=dict(pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
 board_sha256=geom['board_sha256'],dpi=dpi,page_points=[612,792],
 board_bbox_page_mm=[57.95,104.7,157.95,174.7],
 compared_pixels=int(A.size),registration='absolute page coordinates; no fitted translation, rotation, scaling or mirroring',
 copper_polarity='white/clear copper; black drill holes and etched gaps',
 edge_clearance_pixel_centers_mm=dict(zip(['left','top','right','bottom'],edges)),
 conservative_min_edge_clearance_mm=lower,nonmirrored_xor_fraction=normal_mismatch,
 mirrored_xor_fraction=mirror_mismatch,extra_clear_pixel_max_distance_from_expected_copper_mm=extra_max,
 missing_clear_pixel_max_distance_from_actual_pdf_copper_mm=missing_max,
 boundary_tolerance_mm=.03,actual_pdf_copper_components=int(na),pcb_projection_copper_components=int(nb),
 removed_old_GND_tracks=aux.get('removed_ground_tracks',[]),identified_disputed_features=features,
 conclusion='Actual PDF matches independently extracted FINAL PCB copper, including drill subtraction, within 0.03 mm boundary raster/tessellation tolerance; no added trace/tab, missing connection or edge contact.')
(E/'final-pdf-projection-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
