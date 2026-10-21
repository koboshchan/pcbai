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
def tr(a,z,n,w=.3):
 if a==z:return
 t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetLayer(p.B_Cu);t.SetWidth(p.FromMM(w));t.SetNet(net(n));b.Add(t)
def path(points,n):
 for a,z in zip(points,points[1:]):tr(a,z,n)
for a,z in zip([(0,0),(100,0),(100,70),(0,70)],[(100,0),(100,70),(0,70),(0,0)]):
 s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetLayer(p.Edge_Cuts);s.SetStart(v(*a));s.SetEnd(v(*z));s.SetWidth(p.FromMM(.05));b.Add(s)

# ---- Bottom-view layout: DUT 2x13 at bottom-view LEFT (= high X in this top-view frame), Pico at bottom-view RIGHT (low X).
# TOP/component view, mounted from above; no flip/mirror. Pico is rotated 180 deg (USB end toward +Y). J1 = Pico pins 1-20 at inner column x=32.78, J2 = pins 21-40 at outer column x=15.
GPIO_LANES=[28,27,26,22,21,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0]  # lane 0 = top ... lane 25 = bottom
PIN_OF={28:('J2',14),27:('J2',12),26:('J2',11),22:('J2',9),21:('J2',7),20:('J2',6),19:('J2',5),18:('J2',4),17:('J2',2),16:('J2',1),15:('J1',20),14:('J1',19),13:('J1',17),12:('J1',16),11:('J1',15),10:('J1',14),
        9:('J1',12),8:('J1',11),7:('J1',10),6:('J1',9),5:('J1',7),4:('J1',6),3:('J1',5),2:('J1',4),1:('J1',2),0:('J1',1)}
phys_gpio={1:0,2:1,4:2,5:3,6:4,7:5,9:6,10:7,11:8,12:9,14:10,15:11,16:12,17:13,19:14,20:15,21:16,22:17,24:18,25:19,26:20,27:21,29:22,31:26,32:27,34:28}
used={g for g in GPIO_LANES}
ns1={};ns2={}
for ph,g in phys_gpio.items():
 n=('GP' if g in used else 'SPARE_GP')+str(g)
 (ns1 if ph<=20 else ns2)[str(ph if ph<=20 else ph-20)]=n
for ph in [3,8,13,18]:ns1[str(ph)]='GND'
for ph in [23,28,33,38]:ns2[str(ph-20)]='GND'
for ph,n in {30:'PICO_RUN_NC',35:'PICO_ADC_VREF_NC',36:'PICO_3V3_NC',37:'PICO_3V3_EN_NC',39:'PICO_VSYS_NC',40:'PICO_VBUS_NC'}.items():ns2[str(ph-20)]=n
XI,XO=32.78,15.0;YT=16.0
j1=add('J1','PICO_LEFT_PHYS1_20','Connector_PinSocket_2.54mm','PinSocket_1x20_P2.54mm_Vertical',XI,YT+19*2.54,ns1);j1.SetOrientationDegrees(180)
j2=add('J2','PICO_RIGHT_PHYS21_40','Connector_PinSocket_2.54mm','PinSocket_1x20_P2.54mm_Vertical',XO,YT,ns2)
YD0=20.0
for f in (j1,j2):
 for it in list(f.GraphicalItems()):
  if it.GetLayer()==p.F_SilkS:f.Remove(it)  # shared Pico assembly projection replaces conflicting socket silk
 f.SetFPID(p.LIB_ID('','Pico_1x20_female_oval_1.7x1.4'))
 for pad in f.Pads():pad.SetSize(v(1.7,1.4));pad.SetShape(p.PAD_SHAPE_RECT if pad.GetNumber()=='1' else p.PAD_SHAPE_OVAL)
# J3 = DUT outer column (bottom-view leftmost) ports 1-13, J4 = inner column ports 14-26, both pin1 at top.
j3=add('J3','DUT1_13_FEMALE','Connector_PinSocket_2.54mm','PinSocket_1x13_P2.54mm_Vertical',97.54,YD0,{str(i):'T'+str(i) for i in range(1,14)})
j4=add('J4','DUT14_26_FEMALE','Connector_PinSocket_2.54mm','PinSocket_1x13_P2.54mm_Vertical',95.0,YD0,{str(i):'T'+str(i+13) for i in range(1,14)})
J={'J1':j1,'J2':j2,'J3':j3,'J4':j4}
# Two adjacent 1x13 strips form a 2x13 block: replace their individual silk/courtyard (which would overlap) with one shared silk box
# and abutting, non-overlapping courtyards (J4 inner half / J3 outer half). No DRC check is disabled.
for f in (j3,j4):
 for pad in f.Pads():pad.SetSize(v(1.7,1.4));pad.SetShape(p.PAD_SHAPE_RECT if pad.GetNumber()=='1' else p.PAD_SHAPE_OVAL)  # 1 mm drill, .2 mm vertical annular ring permits .4 mm routing clearance
for f,(xa,xb) in ((j3,(96.27,98.91)),(j4,(93.63,96.26))):
 f.SetFPID(p.LIB_ID('','PinSocket_1x13_P2.54mm_Vertical_2x13_block_modified'))
 for it in list(f.GraphicalItems()):
  if it.GetLayer() in (p.F_SilkS,p.F_CrtYd):f.Remove(it)
 sh=p.PCB_SHAPE(f);sh.SetShape(p.SHAPE_T_RECT);sh.SetLayer(p.F_CrtYd);sh.SetStart(v(xa,YD0-1.4));sh.SetEnd(v(xb,YD0+12*2.54+1.4));sh.SetWidth(p.FromMM(.05));f.Add(sh)
bx=p.PCB_SHAPE(b);bx.SetShape(p.SHAPE_T_RECT);bx.SetLayer(p.F_SilkS);bx.SetStart(v(93.5,YD0-1.8));bx.SetEnd(v(99.1,YD0+12*2.54+1.8));bx.SetWidth(p.FromMM(.15));b.Add(bx)
def poly(pts,n):
 path([v(*q) for q in pts],n)
mapping=[];lane_port={}
TOPY=[0.8+1.45*k for k in range(10)]
for k,g in enumerate(GPIO_LANES):
 gn='GP'+str(g);jn,pin=PIN_OF[g];pp=pt(J[jn],pin);px,py_=p.ToMM(pp.x),p.ToMM(pp.y)
 m=k//2
 port=(m+1) if k%2==0 else (14+m)
 tn='T'+str(port);lane_port[k]=port
 yc=2.5+2.56*k; yd=YD0-1.27+1.27*k
 ak=34+1.15*(25-k)
 if k<10:
  y0=TOPY[k]
  if k==9: pre=[(px,py_),(px+1.5,py_),(px+1.5,y0)]
  else:
   lx=0.8+1.45*k; pre=[(px,py_),(lx,py_),(lx,y0)]
 else:
  y0=py_;pre=[(px,py_)]
 dy=yc-y0
 R_X=72.0;ex=ak+dy
 r=add('R'+str(k+1),'4.7k 1% 1/8W','Resistor_SMD','R_0805_2012Metric',R_X,yc,{},True)
 r.SetOrientationDegrees(0)
 assert r.FindPadByNumber('1').GetPosition().x<r.FindPadByNumber('2').GetPosition().x
 pads=[r.FindPadByNumber('1'),r.FindPadByNumber('2')];pads[0].SetNet(net(gn));pads[1].SetNet(net(tn))
 poly(pre+[(ak,y0),(ex,yc),(p.ToMM(pads[0].GetPosition().x),yc)],gn)
 cx=76.0 if k%2==0 else 78.5
 c=add('C'+str(k+1),'100nF X7R 10%','Capacitor_SMD','C_0805_2012Metric',cx,yc+0.95,{},True)
 c.SetPosition(v(cx,yc+1.28));c.SetOrientationDegrees(0)
 c.FindPadByNumber('2').SetNet(net(tn));c.FindPadByNumber('1').SetNet(net('GND'))
 cp=[c.FindPadByNumber('2'),c.FindPadByNumber('1')]
 pc=cp[0].GetPosition();poly([(p.ToMM(pc.x),yc),(p.ToMM(pc.x),p.ToMM(pc.y))],tn)
 # GND is connected by the refilled .3 mm-clearance pour; no redundant escape stub.
 # node trace: R right pad -> cap pad1 -> compress start
 ac=81.0;dd=yd-yc;xdut=95.0
 tail=[(p.ToMM(pads[1].GetPosition().x),yc),(ac,yc),(ac+0.7*abs(dd),yd)]
 if k%2==0: tail+= [(96.27,yd),(97.54,yd+1.27)]
 else: tail+=[(xdut,yd)]
 poly(tail,tn)
 mapping.append(dict(test=port,gpio=g,lane=k,pico_physical=(pin if jn=='J1' else pin+20),header='J3' if k%2==0 else 'J4',pin=m+1))
# fix recorded nets for parts built with deferred nets
for q in parts:
 if q['ref'] in ('J1','J2'):q['footprint']='Pico_1x20_female_oval_1.7x1.4 (embedded, rectangular pin 1)'
 if q['ref'] in('J3','J4'):q['footprint']='PinSocket_1x13_P2.54mm_Vertical_2x13_block_modified (embedded, shared 2x13 silk box, abutting courtyards)'
 f=[x for x in b.GetFootprints() if x.GetReference()==q['ref']][0]
 q['nets']={a.GetNumber():a.GetNetname() for a in f.Pads() if a.GetNetname()}
for txt,x,y,size in [('UNPOWERED DUT ONLY',45,68.6,1.3),('USB END',23.89,68,1),('1',92.4,YD0,1),('TOP: PICO LEFT / DUT RIGHT',47,0.9,0.8)]:
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.15));t.SetLayer(p.F_SilkS);b.Add(t)
# Assembly guide only: actual 21x51 mm Pico projection on TOP silkscreen,
# centered between socket rows. USB points +Y; sockets remain F.Cu/THT.
# This is NOT a physical Pico body nor any extra copper.
for xa,ya,xb,yb in [(13.39,14.63,34.39,65.63),(20.1,62.0,27.68,66.3)]:
 sh=p.PCB_SHAPE(b);sh.SetShape(p.SHAPE_T_RECT);sh.SetLayer(p.F_SilkS)
 sh.SetStart(v(xa,ya));sh.SetEnd(v(xb,yb));sh.SetWidth(p.FromMM(.15));b.Add(sh)
for txt,x,y,size in [('PICO TOP',23.89,40,1.1),('1',30.1,64.26,.8),('20',30.1,16,.8),('21',17.7,16,.8),('40',17.7,64.26,.8),('J4',95,17,.8),('J3',97.54,17,.8)]:
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.12));t.SetLayer(p.F_SilkS);b.Add(t)
z_=p.ZONE(b);z_.SetLayer(p.B_Cu);z_.SetNet(net('GND'))
ol=z_.Outline();ol.NewOutline()
for q in [(0.6,0.6),(99.4,0.6),(99.4,69.4),(0.6,69.4)]:ol.Append(p.FromMM(q[0]),p.FromMM(q[1]))
z_.SetLocalClearance(p.FromMM(.3));z_.SetMinThickness(p.FromMM(.3));z_.SetPadConnection(p.ZONE_CONNECTION_FULL)
z_.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS);b.Add(z_)
ds=b.GetDesignSettings();ds.m_MinClearance=p.FromMM(.3);ds.m_TrackMinWidth=p.FromMM(.3)
template=json.loads((ROOT/'fingerprint.kicad_pro').read_text())
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'fingerprint.kicad_pcb'),b)
# Use shipped library models so the archive renders without system model packages.
board_path=ROOT/'fingerprint.kicad_pcb'
board_path.write_text(board_path.read_text().replace('${KICAD10_3DMODEL_DIR}','${KIPRJMOD}/models'))
template['board']['design_settings']['rules']['min_clearance']=.3
template['board']['design_settings']['rules']['min_track_width']=.3
template['net_settings']['classes'][0]['clearance']=.3
template['net_settings']['classes'][0]['track_width']=.3
template['board']['design_settings']['drc_exclusions']=[]
(ROOT/'fingerprint.kicad_pro').write_text(json.dumps(template,indent=2)+'\n')
mapping.sort(key=lambda m:m['test'])
(ROOT/'manifest.json').write_text(json.dumps(dict(components=parts,layout='bottom-view: DUT 2x13 at left, Pico at right; B.Cu GND pour',assembly_side='TOP (F.Cu footprints, through-hole pins soldered on B.Cu)',pico_usb_direction_top='+Y (toward board bottom)',top_dut_left_column='J4 ports 14..26 top-to-bottom',top_dut_right_column='J3 ports 1..13 top-to-bottom',port_count=26,unordered_pairs=325,directed_pairs=650,reference_count=26,repeats=8,scan_rows=5408,min_trace_mm=.3,min_clearance_mm=.3,gpio_map=mapping,series_ohms=4700,cap_farads=1e-7,jumpers=0),indent=2)+'\n')
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
