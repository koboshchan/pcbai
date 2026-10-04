#!/usr/bin/python3
from pathlib import Path
import sys,json,shutil,math
import pcbnew as p
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import successor100 as s;import motherboard_refs as refs;import shortrefs_motherboard_silk as silk
D=R/'motherboard_repair';out=D/'motherboard.kicad_pcb';base=p.LoadBoard(str(out));phys=refs.physical(base);ident=s.identity(base)
report=json.loads((D/'motherboard_drc.json').read_text());fixed=[]
for iteration in range(20):
 report=json.loads((D/'motherboard_drc.json').read_text());errors=[v for v in report['violations'] if v['severity']=='error']
 if not errors:break
 if any(v['type']!='starved_thermal' for v in errors):break
 target=errors[0]['items'][1]['uuid'];baseline=len(errors);raw=out.read_bytes();accepted=False
 for angle in [0,15,30,45,60,75,90]:
  b=p.LoadBoard(str(out));pad=next(q for f in b.GetFootprints() for q in f.Pads() if q.m_Uuid.AsString()==target);pad.SetThermalSpokeAngleDegrees(angle);p.SaveBoard(str(out),b);stats=s.drc(out,True)
  if stats['errors']<baseline and stats['opens']==len(report['unconnected_items']):
   fixed.append({'uuid':target,'thermal_angle':angle,'reason':'Legal thermal spoke rotation removes isolated-spoke failure without changing pad geometry'});accepted=True;break
  out.write_bytes(raw)
 if not accepted:
  # Stitch the isolated GND copper island to the opposite connected GND pour.
  b=p.LoadBoard(str(out));pad=next(q for f in b.GetFootprints() for q in f.Pads() if q.m_Uuid.AsString()==target);x=p.ToMM(pad.GetPosition().x);y=p.ToMM(pad.GetPosition().y)
  for radius in [.9,1.1,1.3,1.5,1.8,2.2]:
   for angle in range(0,360,30):
    b=p.LoadBoard(str(out));v=p.PCB_VIA(b);v.SetPosition(s.xy(x+radius*math.cos(math.radians(angle)),y+radius*math.sin(math.radians(angle))));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v);p.SaveBoard(str(out),b);stats=s.drc(out,True)
    if stats['errors']<baseline and stats['opens']==len(report['unconnected_items']):fixed.append({'uuid':target,'stitch':v.m_Uuid.AsString(),'radius':radius,'angle':angle});accepted=True;break
    out.write_bytes(raw)
   if accepted:break
 if not accepted:break
stats=s.drc(out,True);b=p.LoadBoard(str(out));protected=json.loads((D/'protected_before.json').read_text());stats.update(candidate=str(out),sha=s.sha(out),identity=s.identity(b)==ident,placement_unchanged=refs.physical(b)==phys,silk_clean=silk.audit(b)['clean'],protected_unchanged=all(s.sha(Path(f))==h for f,h in protected.items()),thermal_repairs=fixed,release_authorized=False);stats['strict_pass']=stats['errors']==0 and stats['opens']==0 and all(stats[k] for k in ['identity','placement_unchanged','silk_clean','protected_unchanged']);s.write(D/'RESULT.json',stats);print(json.dumps(stats),flush=True)
