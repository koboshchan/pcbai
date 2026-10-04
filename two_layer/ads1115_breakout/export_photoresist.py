#!/usr/bin/env python3
"""Vector, exact-scale mirrored negative F.Cu photographic mask on Letter."""
from pathlib import Path
import json
import pcbnew as p
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
ROOT=Path(__file__).resolve().parent
b=p.LoadBoard(str(ROOT/'ads1115_breakout.kicad_pcb'))
assert not any(t.GetLayer()==p.B_Cu for t in b.GetTracks())
assert not any(isinstance(t,p.PCB_VIA) for t in b.GetTracks())
assert not b.Zones(), 'Exporter expects no copper zones'
out=ROOT/'ads1115_photoresist_letter_mirrored_negative.pdf'
c=canvas.Canvas(str(out),pagesize=letter,pageCompression=1)
c.setTitle('ADS1115 photoresist mask - Letter 1:1 mirrored negative F.Cu')
c.setFillColorRGB(0,0,0);c.rect(0,0,*letter,fill=1,stroke=0)
c.saveState()
# Exact mm units. Mirror about board vertical axis, center 50x70 on Letter.
c.translate((letter[0]+50*mm)/2,(letter[1]+70*mm)/2)
c.scale(-mm,-mm)
c.setFillColorRGB(1,1,1);c.setStrokeColorRGB(1,1,1);c.setLineCap(1);c.setLineJoin(1)
for t in b.GetTracks():
    assert t.GetLayer()==p.F_Cu
    a=t.GetStart();d=t.GetEnd();c.setLineWidth(p.ToMM(t.GetWidth()))
    c.line(p.ToMM(a.x),p.ToMM(a.y),p.ToMM(d.x),p.ToMM(d.y))
centers=[]
for f in b.GetFootprints():
    for a in f.Pads():
        q=a.GetPosition();x=p.ToMM(q.x);y=p.ToMM(q.y)
        if a.IsOnLayer(p.F_Cu) and a.GetAttribute()!=p.PAD_ATTRIB_NPTH:
            w=p.ToMM(a.GetSize().x);h=p.ToMM(a.GetSize().y)
            c.saveState();c.translate(x,y);c.rotate(a.GetOrientationDegrees())
            if a.GetShape()==p.PAD_SHAPE_CIRCLE:c.circle(0,0,w/2,fill=1,stroke=0)
            elif a.GetShape()==p.PAD_SHAPE_RECT:c.rect(-w/2,-h/2,w,h,fill=1,stroke=0)
            else:raise ValueError(f'Unsupported pad shape {f.GetReference()}')
            c.restoreState()
        if a.GetDrillSize().x:centers.append((x,y,a.IsOnLayer(p.F_Cu) and a.GetAttribute()!=p.PAD_ATTRIB_NPTH))
# Small black drill-centering dots inside white copper; NPTH holes remain black.
c.setFillColorRGB(0,0,0)
for x,y,copper in centers:
    if copper:c.circle(x,y,.15,fill=1,stroke=0)
# Short external white corner marks leave the entire board border electrically black.
c.setStrokeColorRGB(1,1,1);c.setLineWidth(.1)
for x,y,sx,sy in [(0,0,-1,-1),(50,0,1,-1),(0,70,-1,1),(50,70,1,1)]:
    c.line(x+sx*.5,y,x+sx*3,y);c.line(x,y+sy*.5,x,y+sy*3)
c.restoreState()
c.showPage();c.save()
(ROOT/'photoresist_export.json').write_text(json.dumps({'page_points':[612,792],'page_inches':[8.5,11],'scale':1,'board_mm':[50,70],'layer':'F.Cu','mirrored':True,'negative':True,'copper':'white','background':'black','drill_centering_dot_mm':.3,'outline':'external corner marks','filename':out.name},indent=2)+'\n')
print(out)
