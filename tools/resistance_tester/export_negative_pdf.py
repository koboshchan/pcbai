#!/usr/bin/env python3
"""Center the KiCad non-mirrored, unit-scale negative SVG on US Letter, without fitting."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import cairosvg,fitz
R=Path(__file__).resolve().parent
source=R/'evidence/bcu-negative.svg'
out=Path('/home/kit/out/resistance-tester/rt-negative-letter-v2.pdf')
root=ET.parse(source).getroot()
assert root.get('viewBox').startswith('0.0000 0.0000 ')
assert not any('scale(-' in e.get('transform','') for e in root.iter())
root.set('width','215.9mm');root.set('height','279.4mm')
root.set('viewBox','-57.95 -104.7 215.9 279.4')
svg=ET.tostring(root)
(R/'evidence/bcu-negative-letter.svg').write_bytes(svg)
cairosvg.svg2pdf(bytestring=svg,write_to=str(out))
doc=fitz.open(out);page=doc[0];mm=72/25.4
assert len(doc)==1 and abs(page.rect.width-612)<.0001 and abs(page.rect.height-792)<.0001
# Independently inspect actual PDF paths for two rectangular pin-1 pads.
# Their absolute X positions disambiguate non-mirroring and their centers prove scale/translation.
drawings=page.get_drawings()
pads=[]
for x in [95,97.54]:
 target=fitz.Rect((x-.85+57.95)*mm,(20-.7+104.7)*mm,(x+.85+57.95)*mm,(20+.7+104.7)*mm)
 matches=[d for d in drawings if d['fill']==(1,1,1) and all(abs(a-b)<.002 for a,b in zip(d['rect'],target))]
 assert len(matches)==1,(x,len(matches))
 pads.append(matches[0]['rect'])
pitch=(pads[1].x0-pads[0].x0)/mm
assert abs(pitch-2.54)<.0001
# Raster sample actual PDF, not the SVG, for negative polarity and non-mirrored signal track.
pix=page.get_pixmap(matrix=fitz.Matrix(4,4),alpha=False)
def rgb(x,y):
 px=round((x+57.95)*mm*4);py=round((y+104.7)*mm*4)
 return pix.pixel(px,py)
assert min(rgb(.8,20))>245 # GP28 vertical signal copper
assert max(rgb(.1,20))<10 # etched margin black
assert max(rgb(95,20))<10 # true drill center black
assert min(rgb(95.65,20))>245 # surrounding copper annulus white
# Inspect whole page and a high-resolution crop without rescaling source PDF.
page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(str(R/'evidence/negative-letter-preview.png'))
clip=fitz.Rect(57.95*mm,104.7*mm,157.95*mm,174.7*mm)
page.get_pixmap(matrix=fitz.Matrix(5,5),clip=clip,alpha=False).save(str(R/'evidence/negative-copper-detail.png'))
report=dict(pdf=str(out),pdf_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),source_svg_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),page_points=[page.rect.width,page.rect.height],page_mm=[215.9,279.4],board_mm=[100,70],board_top_left_on_page_mm=[57.95,104.7],scale=1,mirrored=False,polarity='white/transparent copper on opaque black; drill centers black',measured_pdf_header_pitch_mm=pitch,pdf_anchor_pads='J4.1 x95 then J3.1 x97.54; y20; rectangular 1.7x1.4mm',pdf_raster_samples={str(p):rgb(*p) for p in [(.8,20),(.1,20),(95,20),(95.65,20)]},print_instruction='US Letter, Actual Size / 100%; no Fit/Shrink, no mirror')
(R/'evidence/negative-letter-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
