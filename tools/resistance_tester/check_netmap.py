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
# Ports 1..20 (J3 pins 1-10 then J4 pins 1-10) -> GPIO. Independent of build_board.py.
gpios=[19,17,15,13,11,9,7,5,3,1,18,16,14,12,10,8,6,4,2,0]
expected={}
for phys,gpio in physical.items():
 expected[('J1' if phys<=20 else 'J2',str(phys if phys<=20 else phys-20))]=('GP' if gpio in gpios else 'SPARE_GP')+str(gpio)
for phys in [3,8,13,18,23,28,33,38]:
 expected[('J1' if phys<=20 else 'J2',str(phys if phys<=20 else phys-20))]='GND'
for phys,n in {30:'PICO_RUN_NC',35:'PICO_ADC_VREF_NC',36:'PICO_3V3_NC',37:'PICO_3V3_EN_NC',39:'PICO_VSYS_NC',40:'PICO_VBUS_NC'}.items():expected['J2',str(phys-20)]=n
for i,gpio in enumerate(gpios,1):
 expected['J3' if i<=10 else 'J4',str(i if i<=10 else i-10)]='T'+str(i)
 lane=(i-1)*2 if i<=10 else (i-11)*2+1
 expected['R'+str(lane+1),'1']='GP'+str(gpio);expected['R'+str(lane+1),'2']='T'+str(i)
 expected['C'+str(lane+1),'1']='T'+str(i);expected['C'+str(lane+1),'2']='GND'
assert actual==expected,[(k,expected.get(k),actual.get(k)) for k in set(actual)|set(expected) if actual.get(k)!=expected.get(k)]
assert sch==expected,[(k,expected.get(k),sch.get(k)) for k in set(sch)|set(expected) if sch.get(k)!=expected.get(k)]
assert all(t.GetLayer()==p.B_Cu and t.GetClass()!='PCB_VIA' for t in b.GetTracks())
assert all(f.GetLayer()==p.B_Cu for f in b.GetFootprints() if f.GetReference().startswith(('C','R')))
assert len(list(b.GetFootprints()))==44
assert all(z.GetFirstLayer()==p.B_Cu for z in b.Zones())
smd=[f for f in b.GetFootprints() if f.GetReference().startswith(('R','C'))]
headers=[f for f in b.GetFootprints() if f.GetReference().startswith('J')]
assert len(smd)==40 and len(headers)==4
assert all(a.GetAttribute()==p.PAD_ATTRIB_SMD and a.IsOnLayer(p.B_Cu) and not a.IsOnLayer(p.F_Cu) for f in smd for a in f.Pads())
assert all(a.GetAttribute()==p.PAD_ATTRIB_PTH for f in headers for a in f.Pads())
assert sum(len(list(f.Pads())) for f in headers)==60
assert all(str(f.GetFPID().GetLibItemName()).endswith('R_0805_2012Metric') for f in smd if f.GetReference().startswith('R'))
assert all(str(f.GetFPID().GetLibItemName()).endswith('C_0805_2012Metric') for f in smd if f.GetReference().startswith('C'))
# Verify socket mechanical orientation, not just net naming.
fps={f.GetReference():f for f in b.GetFootprints()}
xy=lambda ref,pin:fps[ref].FindPadByNumber(str(pin)).GetPosition()
X=lambda ref,pin:p.ToMM(xy(ref,pin).x);Y=lambda ref,pin:p.ToMM(xy(ref,pin).y)
assert abs(X('J1',1)-X('J2',1)-17.78)<1e-5 and abs(X('J1',1)-25.78)<1e-5   # Pico rows 17.78 apart
assert abs(Y('J1',20)-Y('J2',1))<1e-5 and abs(Y('J1',1)-Y('J2',20))<1e-5   # pin20/21 same end, USB end at +Y
assert Y('J1',1)>Y('J1',20)                                                  # Pico rotated 180: pin 1 at the USB (+Y) end
assert abs(X('J3',1)-X('J4',1)-2.54)<1e-5 and all(abs(Y('J3',i)-Y('J4',i))<1e-5 for i in range(1,11))  # 2x10, 2.54 pitch
assert X('J4',1)>X('J1',1)+50 and Y('J3',2)-Y('J3',1)>0                    # DUT at high X = bottom-view LEFT; pin1 on top
xs=[];ys=[]
for s in b.GetDrawings():
 if s.GetLayer()==p.Edge_Cuts:
  for v in [s.GetStart(),s.GetEnd()]:xs.append(p.ToMM(v.x));ys.append(p.ToMM(v.y))
assert max(xs)-min(xs)==100 and max(ys)-min(ys)==70
report=dict(expected_connections=len(expected),pcb_matches=True,schematic_matches=True,outline_mm=[100,70],front_tracks=0,vias=0,wire_links=0,capacitors_bottom=20,resistors_bottom_0805=20,smd_pads_bottom_only=80,through_hole_footprints=4,through_hole_pads=60,mechanical_socket_spacing_mm=17.78,dut_block_pitch_mm=2.54,zones=len(list(b.Zones())),zone_layers=[b.GetLayerName(zz.GetFirstLayer()) for zz in b.Zones()])
(R/'evidence/netmap.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
