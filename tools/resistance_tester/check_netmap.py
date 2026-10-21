#!/usr/bin/python3
"""Independent pcbnew readback + exported schematic XML + fixed Pico pinout audit."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
R=Path(__file__).resolve().parent
b=p.LoadBoard(str(R/'fingerprint.kicad_pcb'))
actual={(f.GetReference(),a.GetNumber()):a.GetNetname() for f in b.GetFootprints() for a in f.Pads()}
xml=ET.parse(R/'evidence/schematic.xml')
sch={}
for n in xml.findall('./nets/net'):
 name=n.get('name').removeprefix('/')
 for nd in n.findall('node'):sch[(nd.get('ref'),nd.get('pin'))]=name
# Fixed published Pico physical-pin mapping, independent of build script/manifest.
physical={1:0,2:1,4:2,5:3,6:4,7:5,9:6,10:7,11:8,12:9,14:10,15:11,16:12,17:13,19:14,20:15,21:16,22:17,24:18,25:19,26:20,27:21,29:22,31:26,32:27,34:28}
gpios=[0,1,2,3,4,5,6,7,8,9,28,27,26,22,21,20,19,18,17,16]
expected={}
for phys,gpio in physical.items():
 expected[('J1' if phys<=20 else 'J2',str(phys if phys<=20 else phys-20))]=('GP' if gpio in gpios else 'SPARE_GP')+str(gpio)
for phys in [3,8,13,18,23,28,33,38]:
 expected[('J1' if phys<=20 else 'J2',str(phys if phys<=20 else phys-20))]='GND'
for phys,n in {30:'PICO_RUN_NC',35:'PICO_ADC_VREF_NC',36:'PICO_3V3_NC',37:'PICO_3V3_EN_NC',39:'PICO_VSYS_NC',40:'PICO_VBUS_NC'}.items():expected['J2',str(phys-20)]=n
for i,gpio in enumerate(gpios,1):
 expected['J3' if i<=10 else 'J4',str(i if i<=10 else i-10)]='T'+str(i)
 for pin,n in {'1':'T'+str(i) if i<=10 else 'GP'+str(gpio),'2':'GP'+str(gpio) if i<=10 else 'T'+str(i)}.items():expected['R'+str(i),pin]=n
 expected['C'+str(i),'1']='T'+str(i);expected['C'+str(i),'2']='GND'
assert actual==expected,[(k,expected.get(k),actual.get(k)) for k in set(actual)|set(expected) if actual.get(k)!=expected.get(k)]
assert sch==expected,[(k,expected.get(k),sch.get(k)) for k in set(sch)|set(expected) if sch.get(k)!=expected.get(k)]
assert all(t.GetLayer()==p.B_Cu and t.GetClass()!='PCB_VIA' for t in b.GetTracks())
assert all(f.GetLayer()==p.B_Cu for f in b.GetFootprints() if f.GetReference().startswith('C'))
assert len(list(b.GetFootprints()))==44
# Verify socket mechanical orientation, not just net naming.
fps={f.GetReference():f for f in b.GetFootprints()}
xy=lambda ref,pin:fps[ref].FindPadByNumber(str(pin)).GetPosition()
assert abs(p.ToMM(xy('J2',20).x-xy('J1',1).x)-17.78)<1e-5
assert xy('J2',20).y==xy('J1',1).y
assert xy('J2',1).y==xy('J1',20).y
xs=[];ys=[]
for s in b.GetDrawings():
 if s.GetLayer()==p.Edge_Cuts:
  for v in [s.GetStart(),s.GetEnd()]:xs.append(p.ToMM(v.x));ys.append(p.ToMM(v.y))
assert max(xs)-min(xs)==100 and max(ys)-min(ys)==70
report=dict(expected_connections=len(expected),pcb_matches=True,schematic_matches=True,outline_mm=[100,70],front_tracks=0,vias=0,wire_links=0,capacitors_bottom=20,mechanical_socket_spacing_mm=17.78)
(R/'evidence/netmap.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
