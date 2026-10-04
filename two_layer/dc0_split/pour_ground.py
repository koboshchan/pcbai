#!/usr/bin/python3
from pathlib import Path
import pcbnew as p,json,subprocess,shutil
import motherboard_refs as refs
R=Path(__file__).resolve().parent
def fill_drc(f):
 out=f.with_name(f.stem+'_drc.json');r=subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','-o',str(out),str(f)],capture_output=True,text=True);f.with_name(f.stem+'_drc.log').write_text(r.stdout+r.stderr);return json.loads(out.read_text())
def apply(source):
 source=Path(source);b=p.LoadBoard(str(source));identity=refs.physical(b);height=40 if source.stem.startswith('DC0') else 100
 for z in list(b.Zones()):b.Delete(z)
 for layer in [p.F_Cu,p.B_Cu]:
  z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('GND'));z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(p.FromMM(.3));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS);o=z.Outline();o.NewOutline()
  for x,y in [(.55,.55),(99.45,.55),(99.45,height-.55),(.55,height-.55)]:o.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
 created={}
 for x in [10,30,50,70,90]:
  for y in ([15.7,36.5] if height==40 else [15.7,26,40,60,80,90]):
   v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v);created[v.m_Uuid.AsString()]=v
 target=source.with_name(source.stem+'_ground.kicad_pcb');p.SaveBoard(str(target),b)
 for ext in ['.kicad_pro','.kicad_dru']:
  if source.with_suffix(ext).exists():shutil.copyfile(source.with_suffix(ext),target.with_suffix(ext))
 report=fill_drc(target);reject={i['uuid'] for v in report['violations'] if v['severity']=='error' for i in v['items']} & created.keys()
 for uuid in reject:b.Delete(created[uuid])
 p.SaveBoard(str(target),b);report=fill_drc(target);loaded=p.LoadBoard(str(target));assert refs.physical(loaded)==identity
 final={'candidate':str(target),'GND_zones':2,'island_removal':'always','zone_outline_inset_mm':.55,'zone_clearance_mm':.2,'thermal_gap_mm':.3,'thermal_spoke_mm':.3,'GND_stitches_added':len(created)-len(reject),'rejected_vias':len(reject),'errors':sum(v['severity']=='error' for v in report['violations']),'unconnected':len(report['unconnected_items']),'release_authorized':False};target.with_name(target.stem+'_ground_audit.json').write_text(json.dumps(final,indent=2));return target
if __name__=='__main__':
 import sys
 print(apply(sys.argv[1]))
