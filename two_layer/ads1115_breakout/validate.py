#!/usr/bin/env python3
from pathlib import Path
import json, hashlib
import pcbnew as p
import pymupdf
ROOT=Path(__file__).resolve().parent
board=ROOT/'ads1115_breakout.kicad_pcb';b=p.LoadBoard(str(board));b.BuildConnectivity()
r=json.loads((ROOT/'drc.json').read_text());assert not r['unconnected_items'];assert not [v for v in r['violations'] if v['severity']=='error']
box=b.GetBoardEdgesBoundingBox();assert abs(p.ToMM(box.GetWidth())-50)<.1 and abs(p.ToMM(box.GetHeight())-70)<.1
assert not b.Zones()
widths=[]
for t in b.GetTracks():
 assert not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu
 w=p.ToMM(t.GetWidth());widths.append(w);assert w>=.3
 if t.GetNetname() in ['3V3','GND']:assert w>=.8
for f in b.GetFootprints():
 for pad in f.Pads():
  if pad.GetAttribute()!=p.PAD_ATTRIB_NPTH:
   assert pad.FlashLayer(p.F_Cu) and not pad.FlashLayer(p.B_Cu)
   assert min(p.ToMM(pad.GetSize().x),p.ToMM(pad.GetSize().y))>=1.8
   if pad.GetAttribute()==p.PAD_ATTRIB_PTH:assert .9<=p.ToMM(pad.GetDrillSize().x)<=1.0
back=(ROOT/'gerbers/ads1115_breakout-B_Cu.gbl').read_text()
assert 'D03*' not in back and 'D01*' not in back, 'B.Cu has conductive drawing commands'
front=(ROOT/'gerbers/ads1115_breakout-F_Cu.gtl').read_text();assert front.count('D03*')==50+2*len(json.loads((ROOT/'connectivity.json').read_text())['jumpers'])
pdf=pymupdf.open(ROOT/'ads1115_photoresist_letter_mirrored_negative.pdf');pg=pdf[0]
assert len(pdf)==1 and tuple(pg.rect)==(0,0,612,792)
pix=pg.get_pixmap(matrix=pymupdf.Matrix(4,4),colorspace=pymupdf.csGRAY);u=72/25.4
sample=lambda x,y:pix.pixel(round(x*4),round(y*4))[0]
x=(612+50*u)/2-10.5*u;y=(792-70*u)/2+45.94*u
assert sample(20,20)==0 and sample(x,y)==0 and sample(x+.5*u,y)>240
result={'board_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),'errors':0,'unconnected':0,'warnings':len(r['violations']),'tracks':len(widths),'widths_mm':sorted(set(widths)),'jumpers':len(json.loads((ROOT/'connectivity.json').read_text())['jumpers']),'page_points':[612,792],'pdf_polarity_verified':True,'unit_scale_points_per_mm':u,'board_dimension_points':[50*u,70*u]}
(ROOT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
