import csv,json,collections,re,os,html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,LongTable,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import landscape,letter
from reportlab.lib import colors
from pypdf import PdfReader,PdfWriter
(Path(__file__).resolve().parents[2]/'out').mkdir(exist_ok=True)
O=Path(os.environ.get('BOM_DIR',str(Path(__file__).resolve().parents[2]/'boards/bom'))); data=json.load(open(O/'bom_data.json')); boards=data['boards']; names=data['names']; W,H=landscape(letter)
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Small',fontName='Helvetica',fontSize=8,leading=10,spaceAfter=5));styles.add(ParagraphStyle(name='Tiny',fontName='Helvetica',fontSize=7,leading=9));styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=8.5,leading=10.5));styles.add(ParagraphStyle(name='Warn',fontName='Helvetica-Bold',fontSize=10,leading=14,backColor=colors.HexColor('#fff0cc'),borderPadding=7,spaceBefore=8,spaceAfter=10))
story=[];sections={}
def p(s,st='Small'):return Paragraph(html.escape(str(s)),styles[st])
def heading(s):story.append(p(s,'Heading2'))
def table(rows,widths,small=False):
 tab=LongTable([[p(c,'Tiny' if small else 'Cell') for c in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
 tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7ecf0')),('LINEBELOW',(0,0),(-1,0),.6,colors.black),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f6f7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]));story.append(tab)
def pkg(r):
 s=r['package']
 return {'R_0805_2012Metric':'0805 resistor','C_0805_2012Metric':'0805 capacitor','D_SOD-123':'SOD-123','SOIC-14_3.9x8.7mm_P1.27mm':'SOIC-14, 1.27 mm','SOIC-16_3.9x9.9mm_P1.27mm':'SOIC-16 / SOP-16, 1.27 mm','PinHeader_2x38_Straddle_P2.54mm':'2x38 straddle, 2.54 mm','Straddle2x38':'2x38 straddle, 2.54 mm','PinSocket_2x38_P2.54mm_Vertical':'2x38 socket, 2.54 mm','Socket2x38':'2x38 socket, 2.54 mm'}.get(s,s)
def groups(parts,tol=True):
 g=collections.Counter((r['value'],pkg(r),r['tolerance_percent'] if tol else '') for r in parts if r['status']=='FIT')
 return sorted(g.items(),key=lambda t:(t[0][1],t[0][0],t[0][2]))
def footer(c,d):
 c.saveState();c.setFont('Helvetica',7);c.setFillColor(colors.grey);c.drawString(32,18,'pcbai hand-soldering reference | exact fab sources, values unchanged');c.drawRightString(W-32,18,str(d.page));c.restoreState()
for name in names:
 d=boards[name];parts=d['parts'];fit=[r for r in parts if r['status']=='FIT'];dnp=[r for r in parts if r['status']=='DNP']
 if story:story.append(PageBreak())
 story.append(p('pcbai assembly reference' if name==names[0] else name,'Title'))
 if name==names[0]: heading(name)
 story.append(p(f"{len(d['layers'])} copper layers | {d['dimensions_mm'][0]:g} x {d['dimensions_mm'][1]:g} mm | {len(fit)} fitted items | {len(dnp)} DNP sites"))
 if name==names[0]:
  story.append(p('One complete working stack is DC0 + DC1a/b/c/d + DC2 + DC3 + motherboard. Quantities in this reference are for that stack, not all spare bare PCBs in the JLC batches. All assembly is by hand.'))
  story.append(p('Hardware on hand / ordered: mostly 5% 0805 resistors, TL074 SOIC-14, 74HCT595 SOP-16 (HCT, not HC), 100nF 0805 capacitors, and 1N4148W SOD-123 diodes. Board/CSV values below are preserved exactly, not rounded to purchased kit values. CSV tolerance requirements are shown where provided.'))
  story.append(p('DC0 board labels its eight shift registers 74AHCT595S16-13. The ordered HCT part is noted here but the BOM does not silently rename it. 0.1uF = 100nF. Straddle connectors are counted as connector items, not bare copper contacts.'))
 if name.startswith('DC1'):
  i='abcd'.index(name[-1]);story.append(p(f'Populate ONLY variant {name} for neurons N{i*4} through N{i*4+3}. Same bare 4-layer board for all four variants. CSV overrides universal footprint values at all 532 resistor sites. There are 112 extra sites DNP on every variant; total DNP is larger. DNP means leave open, never fit 0 ohms.'))
 if name=='DC3_v2':story.append(p('Universal DC3 has 217 DNP resistor sites. Keep those sites open. Populated values and DNP state are taken directly from this final board.'))
 if name=='motherboard_v2':
  story.append(p('MANDATORY BOTTOM BODGE WIRE: JS1 pad B7 to JS2 pad B7. Fit before powering the stack.','Warn'))
  story.append(p('72 top-mounted items, 9 back-mounted items. THT connectors on the top are soldered at their pins on the back. The two placement diagram pages follow this section.'))
 source=d['source']
 story.append(p('Verified source: '+source,'Tiny'));story.append(p('SHA-256 '+d['sha256'],'Tiny'))
 if 'population_csv' in d:story.append(p('Population: '+d['population_csv']+' | SHA-256 '+d['population_sha256'],'Tiny'))
 if name=='motherboard_v2':story.append(p('Provenance note: fab quote-details.json retained the pre-mask-fix hash 271faeaa... . The authoritative fixed source hash above matches mb-jd0-mask/verification.json. No older source was used.','Tiny'))
 holes=[r for r in d['excluded'] if r['reference'].startswith('H')];story.append(p('Mounting holes (excluded from parts totals): '+ '; '.join(f"{r['reference']} at ({r['x_mm']:g}, {r['y_mm']:g}) mm" for r in holes)+'.','Tiny'))
 heading('Grouped fitting summary')
 rows=[['Value','Package','Qty','CSV tolerance']]+[[k[0],k[1],str(n),k[2]+'%' if k[2] else '-'] for k,n in groups(parts)]
 table(rows,[280,330,40,78]);story.append(Spacer(1,10))
 for side in (['F','B'] if name=='motherboard_v2' else ['F']):
  selected=[r for r in fit if r['side']==side]
  heading(('TOP side' if side=='F' else 'BACK side') if name=='motherboard_v2' else 'Every populated component')
  table([['Ref','Value','Footprint / package','Side','Tol / status']]+[[r['reference'],r['value'],r['footprint'],r['side'],(r['tolerance_percent']+'%' if r['tolerance_percent'] else 'FIT')] for r in selected],[95,220,320,35,58])
 if dnp:
  heading('DNP component sites - leave pads open')
  story.append(p('Every reference below has value DNP, footprint R_0805_2012Metric (0805 resistor), side F. They are excluded from grouped fitted quantities and the combined shopping totals.'))
  assert all(r['package']=='R_0805_2012Metric' and r['side']=='F' for r in dnp)
  # Every reference is explicitly listed; compact blocks avoid hundreds of repetitive DNP rows.
  for i in range(0,len(dnp),60):story.append(p(', '.join(r['reference'] for r in dnp[i:i+60])+'.','Cell'));story.append(Spacer(1,8))
 if name=='motherboard_v2':
  story.append(PageBreak());story.append(p('Placement diagrams are inserted at this position.','Small'))
  # Marker page replaced with the two vector pages after building.
  sections['diagram_marker']=True
story.append(PageBreak());story.append(p('Combined fitting totals - one complete stack','Title'))
story.append(p('DC0 x1, DC1a x1, DC1b x1, DC1c x1, DC1d x1, DC2 x1, DC3 x1, motherboard x1. Excludes DNP, holes, spare bare PCBs and optional heatsinks. Add one insulated bottom bodge wire for JS1 B7 to JS2 B7. Values remain source values, not the purchased-kit rounded BOM.'))
allparts=[r for n in names for r in boards[n]['parts']]; g=groups(allparts,False)
with (O/'combined_totals.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Value','Package','Total_qty']);w.writerows((k[0],k[1],n) for k,n in g)
# Two side-by-side columns, all grouped totals on the final page.
mid=(len(g)+2)//3;left=g[:mid];right=g[mid:2*mid];third=g[2*mid:];rows=[['Value','Package','Qty']*3]
for i in range(mid):
 row=[]
 for arr in [left,right,third]:
  if i<len(arr):k,n=arr[i];row += [k[0],k[1],str(n)]
  else:row+=['','','']
 rows.append(row)
styles.add(ParagraphStyle(name='FinalCell',fontName='Helvetica',fontSize=6.5,leading=7.2))
t=Table([[p(c,'FinalCell') for c in row] for row in rows],colWidths=[100,115,27]*3);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7ecf0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1),('LINEBEFORE',(3,0),(3,-1),.5,colors.grey)]));story.append(t)
story.append(p(f"Total fitted items: {sum(r['status']=='FIT' for r in allparts)}. Includes 15 TL074s, 8 shift registers, 52 1N4148W diodes and 65 1uF capacitors. Connector functional labels remain separate source-value rows.",'Tiny'))
doc=SimpleDocTemplate(str(O/'bom_body.pdf'),pagesize=(W,H),leftMargin=32,rightMargin=32,topMargin=28,bottomMargin=32,title='pcbai per-board assembly BOM',author='Kat');doc.build(story,onFirstPage=footer,onLaterPages=footer)
r=PdfReader(O/'bom_body.pdf');w=PdfWriter();marker=[]
for i,page in enumerate(r.pages):
 if 'Placement diagrams are inserted' in (page.extract_text() or ''):
  marker.append(i)
  for dp in PdfReader(Path(__file__).resolve().parents[2]/'pdfs/motherboard_placement.pdf').pages:w.add_page(dp)
 else:w.add_page(page)
assert len(marker)==1
from io import BytesIO
from reportlab.pdfgen import canvas
for i,page in enumerate(w.pages):
 buf=BytesIO();c=canvas.Canvas(buf,pagesize=(W,H));c.setFillColor(colors.white);c.rect(W-65,12,40,16,fill=1,stroke=0);c.setFillColor(colors.grey);c.setFont('Helvetica',7);c.drawRightString(W-32,18,str(i+1));c.save();buf.seek(0);page.merge_page(PdfReader(buf).pages[0])
with open(Path(__file__).resolve().parents[2]/'out/pcbai_board_bom.pdf','wb') as f:w.write(f)
print('pages',len(w.pages),'groups',len(g),'marker',marker,'last page combined', 'Combined fitting totals' in (w.pages[-1].extract_text() or ''))
(O/'build_report.json').write_text(json.dumps({'pages':len(w.pages),'groups':len(g),'part_counts':{n:{'fitted':sum(r['status']=='FIT' for r in boards[n]['parts']),'dnp':sum(r['status']=='DNP' for r in boards[n]['parts'])} for n in names},'total_fitted':sum(r['status']=='FIT' for r in allparts),'diagram_marker':marker},indent=2))
