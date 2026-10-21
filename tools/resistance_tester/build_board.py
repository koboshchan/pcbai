#!/usr/bin/python3
"""Deterministic KiCad PCB and independently exportable schematic generation."""
import json,csv,uuid
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
b=p.BOARD(); parts=[]; nets={}
def v(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def net(n):
 if n not in nets:
  nets[n]=p.NETINFO_ITEM(b,n);b.Add(nets[n])
 return nets[n]
def add(ref,val,lib,fp,x,y,ns,bottom=False):
 f=p.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty',fp)
 f.SetFPID(p.LIB_ID(lib,fp));f.SetReference(ref);f.SetValue(val); f.SetPosition(v(x,y));b.Add(f)
 if bottom:f.Flip(f.GetPosition(),False)
 for pad in f.Pads():
  n=ns.get(pad.GetNumber())
  if n:pad.SetNet(net(n))
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 parts.append(dict(ref=ref,value=val,footprint=lib+':'+fp,nets=ns))
 return f
def pt(f,pin):return f.FindPadByNumber(str(pin)).GetPosition()
def tr(a,z,n,w=.35):
 if a==z:return
 t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetLayer(p.B_Cu);t.SetWidth(p.FromMM(w));t.SetNet(net(n));b.Add(t)
def path(points,n):
 for a,z in zip(points,points[1:]):tr(a,z,n)
for a,z in zip([(0,0),(100,0),(100,70),(0,70)],[(100,0),(100,70),(0,70),(0,0)]):
 s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetLayer(p.Edge_Cuts);s.SetStart(v(*a));s.SetEnd(v(*z));s.SetWidth(p.FromMM(.05));b.Add(s)
left=[(1,0),(2,1),(4,2),(5,3),(6,4),(7,5),(9,6),(10,7),(11,8),(12,9)]
ns1={str(a):'GP'+str(g) for a,g in left}
for a in [3,8,13,18]:ns1[str(a)]='GND'
for a,g in [(14,10),(15,11),(16,12),(17,13),(19,14),(20,15)]:ns1[str(a)]='SPARE_GP'+str(g)
# J2 pin1 is Pico physical21, bottom end; pin20 is physical40 at USB end.
right=[(14,28),(12,27),(11,26),(9,22),(7,21),(6,20),(5,19),(4,18),(2,17),(1,16)]
ns2={str(a):'GP'+str(g) for a,g in right}
for a in [3,8,13,18]:ns2[str(a)]='GND'
for a,n in {10:'PICO_RUN_NC',15:'PICO_ADC_VREF_NC',16:'PICO_3V3_NC',17:'PICO_3V3_EN_NC',19:'PICO_VSYS_NC',20:'PICO_VBUS_NC'}.items():ns2[str(a)]=n
# both sockets upright same pin ordering in footprints; J2 rotated180 makes pin1 bottom.
j1=add('J1','PICO_LEFT_PHYS1_20','Connector_PinSocket_2.54mm','PinSocket_1x20_P2.54mm_Vertical',40,10,ns1)
j2=add('J2','PICO_RIGHT_PHYS21_40','Connector_PinSocket_2.54mm','PinSocket_1x20_P2.54mm_Vertical',57.78,58.26,ns2)
j2.SetOrientationDegrees(180)
j3=add('J3','DUT1_10_FEMALE','Connector_PinSocket_2.54mm','PinSocket_1x10_P2.54mm_Vertical',10,10,{str(i):'T'+str(i) for i in range(1,11)})
j4=add('J4','DUT11_20_FEMALE','Connector_PinSocket_2.54mm','PinSocket_1x10_P2.54mm_Vertical',90,30,{str(i):'T'+str(i+10) for i in range(1,11)})
mapping=[]
for side,channels,jp,jd in [('L',left,j1,j3),('R',right,j2,j4)]:
 for k,(pin,gpio) in enumerate(channels):
  i=k+1+(0 if side=='L' else 10); y=p.ToMM(pt(jp,pin).y); tn='T'+str(i);gn='GP'+str(gpio)
  # Narrow ground trunk passes between the standard 0805 pads under the body.
  x=29 if side=='L' else 71
  r=add('R'+str(i),'4.7k 1% 1/8W','Resistor_SMD','R_0805_2012Metric',x,y,
        {'1':tn if side=='L' else gn,'2':gn if side=='L' else tn},True)
  r.SetOrientationDegrees(0)
  cx=24.5 if side=='L' else 75.5
  c=add('C'+str(i),'100nF X7R 10%','Capacitor_SMD','C_0805_2012Metric',cx,y+1.27,{'1':tn,'2':'GND'},True)
  # Flip then orient so node pad points outward, ground pad inward.
  c.SetOrientationDegrees(0 if side=='L' else 180)
  rpnode=pt(r,1 if side=='L' else 2);rpgpio=pt(r,2 if side=='L' else 1)
  tr(pt(jp,pin),rpgpio,gn)
  # fanout through two-segment monotone channel, no unassigned copper.
  tr(pt(c,1),pt(jd,k+1),tn)
  path([rpnode,v(p.ToMM(pt(c,1).x),y),pt(c,1)],tn)
  tr(pt(c,2),v(29 if side=='L' else 71,y+1.27),'GND',.25)
  mapping.append(dict(test=i,gpio=gpio,pico_physical=pin if side=='L' else pin+20,header='J3' if side=='L' else 'J4',pin=k+1))
for x,end in [(29,53.18),(71,59.53)]:tr(v(x,5),v(x,end),'GND',.25)
tr(v(29,5),v(71,5),'GND',.5)
for pin in [3,8,13,18]:
 tr(pt(j1,pin),v(29,p.ToMM(pt(j1,pin).y)),'GND')
 tr(pt(j2,pin),v(71,p.ToMM(pt(j2,pin).y)),'GND')
for txt,x,y,size in [('UNPOWERED DUT ONLY',50,65,1.3),('PICO USB',49,7,1),('1',7,10,1),('11',94,30,1),('RC FINGERPRINT v1',50,68,1)]:
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.15));t.SetLayer(p.F_SilkS);b.Add(t)
ds=b.GetDesignSettings();ds.m_MinClearance=p.FromMM(.25);ds.m_TrackMinWidth=p.FromMM(.25)
template=json.loads((ROOT/'fingerprint.kicad_pro').read_text())
p.SaveBoard(str(ROOT/'fingerprint.kicad_pcb'),b)
# Use shipped library models so the archive renders without system model packages.
board_path=ROOT/'fingerprint.kicad_pcb'
board_path.write_text(board_path.read_text().replace('${KICAD10_3DMODEL_DIR}','${KIPRJMOD}/models'))
template['board']['design_settings']['rules']['min_clearance']=.25
template['board']['design_settings']['rules']['min_track_width']=.25
template['net_settings']['classes'][0]['clearance']=.25
template['net_settings']['classes'][0]['track_width']=.35
template['board']['design_settings']['drc_exclusions']=[]
(ROOT/'fingerprint.kicad_pro').write_text(json.dumps(template,indent=2)+'\n')
(ROOT/'manifest.json').write_text(json.dumps(dict(components=parts,gpio_map=mapping,series_ohms=4700,cap_farads=1e-7,jumpers=0),indent=2)+'\n')
with (ROOT/'BOM.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','Value','Footprint','Side'])
 for c in parts:w.writerow([c['ref'],c['value'],c['footprint'],'Bottom' if c['ref'].startswith(('C','R')) else 'Top'])
# Exact embedded passive pin symbols, all pads represented, unique net labels.
q=lambda s:json.dumps(str(s));u=lambda:str(uuid.uuid4())
root=u();libs=[];items=[]
for idx,c in enumerate(parts):
 name=c['ref'];pins=c['nets'];x=20+(idx%8)*65;y=15+(idx//8)*68;h=max(8,len(pins)*2.54+2)
 common=f'(property "Reference" {q(name)} (at 0 5 0) (effects (font (size 1.27 1.27)))) (property "Value" {q(c["value"])} (at 0 2.5 0) (effects (font (size 1.27 1.27))))'
 pp=[f'(pin passive line (at -10.16 {-2.54*(j+1):.4f} 0) (length 5.08) (name {q(pin)} (effects (font (size 1 1)))) (number {q(pin)} (effects (font (size 1 1)))))' for j,pin in enumerate(pins)]
 libs.append(f'(symbol "Fingerprint:{name}" (pin_names (offset .5)) (in_bom yes) (on_board yes) {common} (symbol "{name}_0_1" (rectangle (start -5.08 0) (end 5.08 {-h}) (stroke (width .25) (type default)) (fill (type background)))) (symbol "{name}_1_1" '+ ' '.join(pp)+'))')
 props=f'(property "Reference" {q(name)} (at {x} {y-5} 0) (effects (font (size 1.27 1.27)))) (property "Value" {q(c["value"])} (at {x} {y-2.5} 0) (effects (font (size 1.27 1.27)))) (property "Footprint" {q(c["footprint"])} (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))'
 items.append(f'(symbol (lib_id "Fingerprint:{name}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}") {props} '+' '.join(f'(pin {q(pin)} (uuid "{u()}"))' for pin in pins)+f' (instances (project "fingerprint" (path "/{root}" (reference {q(name)}) (unit 1)))))')
 for j,(pin,n) in enumerate(pins.items()):
  items.append(f'(label {q(n)} (at {x-10.16} {y+2.54*(j+1):.4f} 180) (effects (font (size 1 1)) (justify right bottom)) (uuid "{u()}"))')
(ROOT/'fingerprint.kicad_sch').write_text(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root}") (paper "A1") (lib_symbols '+' '.join(libs)+')\n'+'\n'.join(items)+')\n')
print('Generated',len(parts),'parts,',len(mapping),'channels, 0 jumper wires')

(ROOT/'fp-lib-table').write_text('(fp_lib_table '+ ' '.join('(lib (name "'+lib+'")(type "KiCad")(uri "'+str(Path('/usr/share/kicad/footprints')/(lib+'.pretty'))+'")(options "")(descr ""))' for lib in ['Resistor_SMD','Capacitor_SMD','Connector_PinSocket_2.54mm'])+')\n')
