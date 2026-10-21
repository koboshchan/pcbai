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

# ---- Bottom-view layout: DUT 2x10 at bottom-view LEFT (= high X in this top-view frame), Pico at bottom-view RIGHT (low X).
# Pico is rotated 180 deg (USB end toward +Y). J1 = Pico pins 1-20 at inner column x=25.78, J2 = pins 21-40 at outer column x=8.
GPIO_LANES=[19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0]  # lane 0 = top ... lane 19 = bottom
PIN_OF={19:('J2',5),18:('J2',4),17:('J2',2),16:('J2',1),15:('J1',20),14:('J1',19),13:('J1',17),12:('J1',16),11:('J1',15),10:('J1',14),
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
XI,XO=25.78,8.0;YT=8.0
j1=add('J1','PICO_LEFT_PHYS1_20','Connector_PinSocket_2.54mm','PinSocket_1x20_P2.54mm_Vertical',XI,YT+19*2.54,ns1);j1.SetOrientationDegrees(180)
j2=add('J2','PICO_RIGHT_PHYS21_40','Connector_PinSocket_2.54mm','PinSocket_1x20_P2.54mm_Vertical',XO,YT,ns2)
YD0=26.205
# J3 = DUT outer column (bottom-view leftmost) ports 1-10, J4 = inner column ports 11-20, both pin1 at top.
j3=add('J3','DUT1_10_FEMALE','Connector_PinSocket_2.54mm','PinSocket_1x10_P2.54mm_Vertical',92.54,YD0,{str(i):'T'+str(i) for i in range(1,11)})
j4=add('J4','DUT11_20_FEMALE','Connector_PinSocket_2.54mm','PinSocket_1x10_P2.54mm_Vertical',90.0,YD0,{str(i):'T'+str(i+10) for i in range(1,11)})
J={'J1':j1,'J2':j2,'J3':j3,'J4':j4}
# Two adjacent 1x10 strips form a 2x10 block: replace their individual silk/courtyard (which would overlap) with one shared silk box
# and abutting, non-overlapping courtyards (J4 inner half / J3 outer half). No DRC check is disabled.
for f,(xa,xb) in ((j3,(91.27,93.91)),(j4,(88.63,91.26))):
 f.SetFPID(p.LIB_ID('','PinSocket_1x10_P2.54mm_Vertical_2x10_block_modified'))
 for it in list(f.GraphicalItems()):
  if it.GetLayer() in (p.F_SilkS,p.F_CrtYd):f.Remove(it)
 sh=p.PCB_SHAPE(f);sh.SetShape(p.SHAPE_T_RECT);sh.SetLayer(p.F_CrtYd);sh.SetStart(v(xa,YD0-1.4));sh.SetEnd(v(xb,YD0+9*2.54+1.4));sh.SetWidth(p.FromMM(.05));f.Add(sh)
bx=p.PCB_SHAPE(b);bx.SetShape(p.SHAPE_T_RECT);bx.SetLayer(p.F_SilkS);bx.SetStart(v(88.5,YD0-1.8));bx.SetEnd(v(94.1,YD0+9*2.54+1.8));bx.SetWidth(p.FromMM(.15));b.Add(bx)
W=0.3
def poly(pts,n):
 path([v(*q) for q in pts],n)
mapping=[];lane_port={}
TOPY=[1.9,3.3,4.7,6.1]
for k,g in enumerate(GPIO_LANES):
 gn='GP'+str(g);jn,pin=PIN_OF[g];pp=pt(J[jn],pin);px,py_=p.ToMM(pp.x),p.ToMM(pp.y)
 m=k//2
 port=(m+1) if k%2==0 else (11+m)
 tn='T'+str(port);lane_port[k]=port
 yc=8.5+3.0*k; yd=YD0-1.27+1.27*k
 ak=29+0.9*(19-k)
 if k<4:
  y0=TOPY[k]
  if k==3: pre=[(px,py_),(px,y0)]
  else:
   lx={2:5.5,1:3.7,0:1.9}[k]; pre=[(px,py_),(lx,py_),(lx,y0)]
 else:
  y0=py_;pre=[(px,py_)]
 dy=yc-y0
 R_X=58.0;ex=ak+dy
 r=add('R'+str(k+1),'4.7k 1% 1/8W','Resistor_SMD','R_0805_2012Metric',R_X,yc,{},True)
 r.SetOrientationDegrees(0)
 assert r.FindPadByNumber('1').GetPosition().x<r.FindPadByNumber('2').GetPosition().x
 pads=[r.FindPadByNumber('1'),r.FindPadByNumber('2')];pads[0].SetNet(net(gn));pads[1].SetNet(net(tn))
 poly(pre+[(ak,y0),(ex,yc),(p.ToMM(pads[0].GetPosition().x),yc)],gn)
 cx=62.0 if k%2==0 else 64.5
 c=add('C'+str(k+1),'100nF X7R 10%','Capacitor_SMD','C_0805_2012Metric',cx,yc+0.95,{},True)
 c.SetOrientationDegrees(90)
 if c.FindPadByNumber('1').GetPosition().y>c.FindPadByNumber('2').GetPosition().y:c.SetOrientationDegrees(270)
 assert c.FindPadByNumber('1').GetPosition().y<c.FindPadByNumber('2').GetPosition().y
 c.FindPadByNumber('1').SetNet(net(tn));c.FindPadByNumber('2').SetNet(net('GND'));cp=[c.FindPadByNumber('1'),c.FindPadByNumber('2')]
 for q in parts[-2:]:pass
 # node trace: R right pad -> cap pad1 -> compress start
 ac=67.5;dd=yd-yc;xdut=90.0
 tail=[(p.ToMM(pads[1].GetPosition().x),yc),(ac,yc),(ac+abs(dd),yd)]
 if k%2==0: tail+= [(91.27,yd),(92.54,yd+1.27)]
 else: tail+=[(xdut,yd)]
 poly(tail,tn)
 mapping.append(dict(test=port,gpio=g,lane=k,pico_physical=(pin if jn=='J1' else pin+20),header='J3' if k%2==0 else 'J4',pin=m+1))
for pm in parts[-0:]:pass
# fix recorded nets for parts built with deferred nets
for q in parts:
 if q['ref'] in('J3','J4'):q['footprint']='PinSocket_1x10_P2.54mm_Vertical_2x10_block_modified (embedded, shared 2x10 silk box, abutting courtyards)'
 f=[x for x in b.GetFootprints() if x.GetReference()==q['ref']][0]
 q['nets']={a.GetNumber():a.GetNetname() for a in f.Pads() if a.GetNetname()}
for txt,x,y,size in [('UNPOWERED DUT ONLY',45,68.6,1.3),('PICO USB',17,64,1),('1',87.4,YD0,1),('BOTTOM VIEW: DUT LEFT, PICO RIGHT',47,0.9,0.8)]:
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.15));t.SetLayer(p.F_SilkS);b.Add(t)
z_=p.ZONE(b);z_.SetLayer(p.B_Cu);z_.SetNet(net('GND'))
ol=z_.Outline();ol.NewOutline()
for q in [(0.6,0.6),(99.4,0.6),(99.4,69.4),(0.6,69.4)]:ol.Append(p.FromMM(q[0]),p.FromMM(q[1]))
z_.SetLocalClearance(p.FromMM(.25));z_.SetMinThickness(p.FromMM(.25));z_.SetPadConnection(p.ZONE_CONNECTION_FULL)
z_.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS);b.Add(z_)
ds=b.GetDesignSettings();ds.m_MinClearance=p.FromMM(.25);ds.m_TrackMinWidth=p.FromMM(.25)
template=json.loads((ROOT/'fingerprint.kicad_pro').read_text())
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'fingerprint.kicad_pcb'),b)
# Use shipped library models so the archive renders without system model packages.
board_path=ROOT/'fingerprint.kicad_pcb'
board_path.write_text(board_path.read_text().replace('${KICAD10_3DMODEL_DIR}','${KIPRJMOD}/models'))
template['board']['design_settings']['rules']['min_clearance']=.25
template['board']['design_settings']['rules']['min_track_width']=.25
template['net_settings']['classes'][0]['clearance']=.25
template['net_settings']['classes'][0]['track_width']=.35
template['board']['design_settings']['drc_exclusions']=[]
(ROOT/'fingerprint.kicad_pro').write_text(json.dumps(template,indent=2)+'\n')
mapping.sort(key=lambda m:m['test'])
(ROOT/'manifest.json').write_text(json.dumps(dict(components=parts,layout='bottom-view: DUT 2x10 at left, Pico at right; B.Cu GND pour',gpio_map=mapping,series_ohms=4700,cap_farads=1e-7,jumpers=0),indent=2)+'\n')
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
