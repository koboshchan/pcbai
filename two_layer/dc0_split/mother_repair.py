#!/usr/bin/python3
from pathlib import Path
import pcbnew as p, sys,json,shutil,hashlib,subprocess,collections
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R));import successor100 as s;import motherboard_refs as refs;import shortrefs_motherboard_silk as silk
D=R/'motherboard_repair';D.mkdir(exist_ok=True)
source=R/'successor100/motherboard_routed.kicad_pcb'
protected=s.protected();protected[str(source)]=s.sha(source);dc=R/'successor100/DC0_routed.kicad_pcb';protected[str(dc)]=s.sha(dc)
assert s.sha(source)=='cb85e3b510f840965050c5aa1c9874f7896faf1ece7ef54abdf6eca3011cf12e'
assert s.sha(dc)=='1196b0d47c1c553b22a4061d3ac7e1c41cbf3d4a35dd5b7f1d4cda102bfdb34a'
s.write(D/'protected_before.json',protected)
base=p.LoadBoard(str(source));physical=refs.physical(base);ident=s.identity(base)
for ext in ['.kicad_pro','.kicad_dru']:
 src=source.with_suffix(ext)
 if not src.exists():src=R/'successor100'/('motherboard'+ext)
 if src.exists():shutil.copyfile(src,D/('motherboard'+ext))
best=None
for gap,width in [(.2,.2),(.2,.25),(.25,.2),(.3,.2),(.3,.25),(.35,.2),(.4,.2),(.2,.3)]:
 b=p.LoadBoard(str(source))
 for z in b.Zones():z.SetThermalReliefGap(p.FromMM(gap));z.SetThermalReliefSpokeWidth(p.FromMM(width))
 out=D/'motherboard.kicad_pcb';p.SaveBoard(str(out),b);stats=s.drc(out,True)
 print(gap,width,stats,flush=True)
 score=stats['errors']*100+stats['opens']
 if best is None or score<best[0]:best=(score,gap,width);shutil.copyfile(out,D/'best.kicad_pcb');shutil.copyfile(out.with_name('motherboard_drc.json'),D/'best_drc.json')
 if stats['errors']==0:break
shutil.copyfile(D/'best.kicad_pcb',D/'motherboard.kicad_pcb')
b=p.LoadBoard(str(D/'motherboard.kicad_pcb'));assert refs.physical(b)==physical and s.identity(b)==ident
for z in list(b.Zones()):b.Delete(z)
dsn=D/'motherboard.dsn';assert p.ExportSpecctraDSN(b,str(dsn))
text=dsn.read_text();guards=''
for n,(x1,y1,x2,y2) in enumerate([(-10000,-110000,500,10000),(99500,-110000,110000,10000),(-10000,-500,110000,10000),(-10000,-110000,110000,-99500)]):
 for layer in ['F.Cu','B.Cu']:guards+=f'    (keepout edge_guard_{n}_{layer} (rect {layer} {x1} {y1} {x2} {y2}))\n'
dsn.write_text(text.replace('    (via ',guards+'    (via ',1))
with (D/'router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual4.jar','-de',str(dsn),'-do',str(D/'motherboard.ses'),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=7200)
assert p.ImportSpecctraSES(b,str(D/'motherboard.ses'))
for f in b.GetFootprints():
 old=physical[f.m_Uuid.AsString()];new=f.GetPosition();assert abs(new.x-old['position'][0])<=1 and abs(new.y-old['position'][1])<=1;f.SetPosition(p.VECTOR2I(*old['position']))
assert refs.physical(b)==physical and s.identity(b)==ident
# Restore the same thermal GND zones without changing any pad properties.
zoneboard=p.LoadBoard(str(D/'best.kicad_pcb'))
for z in zoneboard.Zones():b.Add(z.Duplicate(False))
out=D/'motherboard.kicad_pcb';p.SaveBoard(str(out),b);stats=s.drc(out,True)
loaded=p.LoadBoard(str(out));stats.update(candidate=str(out),sha=s.sha(out),identity=s.identity(loaded)==ident,placement_unchanged=refs.physical(loaded)==physical,silk_clean=silk.audit(loaded)['clean'],thermal_gap_mm=best[1],thermal_spoke_mm=best[2],release_authorized=False)
stats['protected_unchanged']=all(s.sha(Path(f))==v for f,v in protected.items());stats['strict_pass']=stats['errors']==0 and stats['opens']==0 and all(stats[k] for k in ['identity','placement_unchanged','silk_clean','protected_unchanged']);s.write(D/'RESULT.json',stats);print(json.dumps(stats),flush=True)
