"""Verify B-side mounting, post-flip pin positions, and pin-to-net mapping."""
from pathlib import Path
import json
import pcbnew as p
root=Path(__file__).resolve().parent;b=p.LoadBoard(str(root/'ads1115_breakout.kicad_pcb'))
audit=[]
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref not in ['JAD','JI2C','JAR','JM1','JM2','JM3','C1']:continue
 assert f.GetLayer()==p.B_Cu
 pins={a.GetNumber():a for a in f.Pads()}
 if ref=='JAD':
  for i in range(1,13):
   a=pins[str(i)];q=a.GetPosition()
   assert abs(p.ToMM(q.x)-10.5)<1e-5 and abs(p.ToMM(q.y)-(45.94-(i-1)*2.54))<1e-5
   assert a.GetNetname()==(f'ADC_{i-1}' if i<11 else 'GND')
  # Horizontal right-angle socket has been flipped top/bottom on B:
  # its courtyard bounds remain left of its pins, not to their right.
  c=f.GetBoundingBox();assert p.ToMM(c.GetX())<10.5
 if ref.startswith('JM'):
  k=int(ref[-1])-1
  expected={1:'3V3',2:'GND',3:'SCL',4:'SDA',5:['GND','3V3','SDA'][k]}
  for j in range(4):expected[7+j]=f'ADC_{4*k+j}' if 4*k+j<10 else 'GND'
  for i,n in expected.items():assert pins[str(i)].GetNetname()==n
 if ref=='JI2C':assert [pins[str(i)].GetNetname()for i in range(1,5)]==['3V3','GND','SDA','SCL']
 if ref=='JAR':assert [pins[str(i)].GetNetname()for i in range(1,3)]==['3V3','GND']
 audit.append({'reference':ref,'component_side':'B','orientation_degrees':f.GetOrientationDegrees(),'pins':[{'pin':a.GetNumber(),'net':a.GetNetname(),'x_mm':p.ToMM(a.GetPosition().x),'y_mm':p.ToMM(a.GetPosition().y)}for a in f.Pads()]})
(root/'B_side_mount_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print('All seven THT footprints on B; JAD pin order, outward housing, and module nets verified')
