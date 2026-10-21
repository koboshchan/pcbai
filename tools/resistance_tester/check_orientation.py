#!/usr/bin/python3
"""Independent TOP assembly check. No import of board generator or netmap checker."""
import ast,csv,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as k
R=Path(__file__).resolve().parent
SOURCE="https://pip-assets.raspberrypi.com/categories/610-raspberry-pi-pico/documents/RP-008307-DS-2-pico-datasheet.pdf?disposition=inline"
# Transcribed from official Fig 2, read alongside Fig 4 component-side pin numbers.
names=("GP0 GP1 GND GP2 GP3 GP4 GP5 GND GP6 GP7 GP8 GP9 GND GP10 GP11 GP12 GP13 GND GP14 GP15 "
       "GP16 GP17 GND GP18 GP19 GP20 GP21 GND GP22 RUN GP26 GP27 AGND GP28 ADC_VREF 3V3 3V3_EN GND VSYS VBUS").split()
assert len(names)==40
b=k.LoadBoard(str(R/'fingerprint.kicad_pcb'))
fp={f.GetReference():f for f in b.GetFootprints()}
sch={}
for n in ET.parse(R/'evidence/schematic.xml').findall('./nets/net'):
 for q in n.findall('node'):sch[q.get('ref'),q.get('pin')]=n.get('name').removeprefix('/')
def xy(p):
 return [round(k.ToMM(p.GetPosition().x),6),round(k.ToMM(p.GetPosition().y),6)]
def actual(ref,pin):
 return fp[ref].FindPadByNumber(str(pin))
for ref in ('J1','J2','J3','J4'):
 assert fp[ref].GetLayer()==k.F_Cu,(ref,'not TOP')
 assert all(p.GetAttribute()==k.PAD_ATTRIB_PTH for p in fp[ref].Pads())
rows=[];coord_by_gpio={}
for ph,name in enumerate(names,1):
 # USB-UP top diagram: 1..20 left downward, 21..40 right upward.
 # Rotate 180 (x,y)->(-x,-y), then translate center=(23.89,40.13).
 # This places USB DOWN, 1..20 RIGHT upward and 21..40 LEFT downward.
 x0=-8.89 if ph<=20 else 8.89
 y0=-24.13+(ph-1)*2.54 if ph<=20 else 24.13-(ph-21)*2.54
 expected=[round(23.89-x0,6),round(40.13-y0,6)]
 ref='J1' if ph<=20 else 'J2';pin=ph if ph<=20 else ph-20
 p=actual(ref,pin)
 net='GND' if name in ('GND','AGND') else (name if name.startswith('GP') else 'PICO_'+name+'_NC')
 assert all(abs(a-z)<.00001 for a,z in zip(xy(p),expected)),(ph,xy(p),expected)
 assert p.GetNetname()==net and sch[ref,str(pin)]==net,(ph,name,p.GetNetname())
 rows.append(dict(pico_physical=ph,official_signal=name,header=ref,local_pad=pin,x_mm=expected[0],y_mm=expected[1],pcb_net=net))
 if name.startswith('GP'):coord_by_gpio[int(name[2:])]=rows[-1]
tree=ast.parse((R/'firmware/main.py').read_text())
fw=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GPIO' for t in n.targets))
m=json.loads((R/'manifest.json').read_text())
assert set(fw)==set(coord_by_gpio) and len(fw)==26
dut=[]
for port in range(1,27):
 # TOP: left J4, right J3, both local pin 1 at smallest Y.
 ref='J3' if port<=13 else 'J4';pin=port if port<=13 else port-13
 expected=[97.54 if ref=='J3' else 95.0,round(20+(pin-1)*2.54,6)]
 p=actual(ref,pin);assert all(abs(a-z)<.00001 for a,z in zip(xy(p),expected))
 assert p.GetNetname()=='T'+str(port)==sch[ref,str(pin)]
 entry=next(q for q in m['gpio_map'] if q['test']==port)
 g=fw[port-1];ph=coord_by_gpio[g]['pico_physical']
 assert (entry['gpio'],entry['pico_physical'],entry['header'],entry['pin'])==(g,ph,ref,pin)
 # Check resistor endpoint itself, not solely a manifest claim.
 matches=[]
 for f in b.GetFootprints():
  if f.GetReference().startswith('R'):
   ns={p.GetNetname() for p in f.Pads()}
   if ns=={'GP'+str(g),'T'+str(port)}:matches.append(f.GetReference())
 assert len(matches)==1,(port,matches)
 dut.append(dict(port=port,header=ref,local_pad=pin,x_mm=expected[0],y_mm=expected[1],gpio=g,pico_physical=ph,series_resistor=matches[0]))
report=dict(verified=True,mapping_correct_no_copper_or_firmware_change=True,source_url=SOURCE,source_figures=[2,3,4],source_pdf_pages=[5,7,8],official_usb_up_top_corners={'top_left':1,'bottom_left':20,'bottom_right':21,'top_right':40},transform='rotation 180 degrees ONLY, then translate center to (23.89,40.13); no reflection',
assembly='All four female headers and Pico above TOP/non-copper side, tails soldered B.Cu',
top_view='Pico LEFT, USB DOWN (+Y); DUT RIGHT, J4 left column ports14..26, J3 right column ports1..13; both downward',
bottom_view='DUT LEFT, Pico RIGHT',pico_pins=rows,dut_contacts=dut,
pcb_sha256=hashlib.sha256((R/'fingerprint.kicad_pcb').read_bytes()).hexdigest())
(R/'evidence/top-orientation.json').write_text(json.dumps(report,indent=2)+'\n')
with (R/'evidence/top-orientation-pins.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print('TOP mount verified: 40 physical Pico pins + 26 DUT contacts; rotation only, no mirror; PCB/schematic/firmware/manifest agree')
