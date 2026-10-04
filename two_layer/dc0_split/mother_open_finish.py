#!/usr/bin/python3
from pathlib import Path
import sys,json,shutil,subprocess,re
import pcbnew as p
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import successor100 as s;import motherboard_refs as refs;import shortrefs_motherboard_silk as silk
D=R/'motherboard_repair';out=D/'motherboard.kicad_pcb';b=p.LoadBoard(str(out));phys=refs.physical(b);ident=s.identity(b);shutil.copyfile(out,D/'pre_open_repair.kicad_pcb')
# Re-route only two incomplete signal nets, freeing their partial protected routes.
removed=[]
tracks=[t for t in b.GetTracks()]
zones=[z for z in b.Zones()]
for t in tracks:
 if t.GetNetname() in ['ADC_2','IN_58']:removed.append(t.m_Uuid.AsString());b.Remove(t)
for z in zones:b.Remove(z)
dsn=D/'signal_repair.dsn';assert p.ExportSpecctraDSN(b,str(dsn));text=dsn.read_text();guards=''
for n,(x1,y1,x2,y2) in enumerate([(-10000,-110000,500,10000),(99500,-110000,110000,10000),(-10000,-500,110000,10000),(-10000,-110000,110000,-99500)]):
 for layer in ['F.Cu','B.Cu']:guards+=f'    (keepout edge_guard_{n}_{layer} (rect {layer} {x1} {y1} {x2} {y2}))\n'
dsn.write_text(text.replace('    (via ',guards+'    (via ',1))
with (D/'signal_router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual48.jar','-de',str(dsn),'-do',str(D/'signal_repair.ses'),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=14400)
assert p.ImportSpecctraSES(b,str(D/'signal_repair.ses'))
for f in b.GetFootprints():
 old=phys[f.m_Uuid.AsString()];new=f.GetPosition();assert abs(new.x-old['position'][0])<=1 and abs(new.y-old['position'][1])<=1;f.SetPosition(p.VECTOR2I(*old['position']))
assert refs.physical(b)==phys and s.identity(b)==ident
zb=p.LoadBoard(str(D/'pre_open_repair.kicad_pcb'))
for z in zb.Zones():b.Add(z.Duplicate(False))
p.SaveBoard(str(out),b);stats=s.drc(out,True);s.write(D/'SIGNAL_REPAIR.json',{'removed_partial_tracks':removed,'stats':stats});print(stats,flush=True)
subprocess.run(['/usr/bin/python3',str(R/'mother_thermal_finish.py')],check=True)
