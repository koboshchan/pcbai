#!/usr/bin/python3
"""Optional legal GND-plane repair of a completed isolated router candidate."""
from pathlib import Path
import hashlib,json,subprocess,sys
import pcbnew as p
import route_v2 as route
import shortrefs_motherboard_silk as silk
ROOT=Path(__file__).resolve().parent;RUN=ROOT/'route_run_v2'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def fixed(b):
 data=route.frozen(b);data.pop('zones');return data
def main():
 source=Path(sys.argv[1]).resolve();assert source.parent==RUN and source.exists()
 target=source.with_name(source.stem+'_ground_planes_v2.kicad_pcb');assert not target.exists()
 b=p.LoadBoard(str(source));identity=fixed(b);assert not b.GetAreaCount()
 edges=[g for g in route.s.board_drawings(b) if g.GetLayer()==p.Edge_Cuts]
 xs=[q.x for g in edges for q in (g.GetStart(),g.GetEnd())];ys=[q.y for g in edges for q in (g.GetStart(),g.GetEnd())]
 x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys);assert x1-x0==y1-y0==p.FromMM(100)
 ground=b.GetNetsByName()['GND'].GetNetCode()
 for layer in (p.F_Cu,p.B_Cu):
  z=p.ZONE(b);z.SetLayer(layer);z.SetNetCode(ground);z.SetLocalClearance(p.FromMM(.2));z.SetThermalReliefGap(p.FromMM(.3));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL)
  outline=z.Outline();outline.NewOutline()
  for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):outline.Append(x,y)
  b.Add(z)
 assert fixed(b)==identity
 p.SaveBoard(str(target),b);target.with_suffix('.kicad_pro').write_text(source.with_suffix('.kicad_pro').read_text())
 out=target.with_name(target.stem+'_drc.json');q=subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','-o',str(out),str(target)],capture_output=True,text=True)
 target.with_name(target.stem+'_drc.log').write_text(q.stdout+q.stderr);d=json.loads(out.read_text());stats={'errors':sum(v.get('severity')=='error' for v in d['violations']),'unconnected':len(d.get('unconnected_items',[]))}
 loaded=p.LoadBoard(str(target));assert fixed(loaded)==identity and silk.audit(loaded)['clean'];assert loaded.GetAreaCount()==2
 result={'source_sha256':sha(source),'candidate':str(target),'candidate_sha256':sha(target),'physical_geometry_fields_identity_verified':True,'silk_clean':True,'zones_added':2,'zone_net':'GND','zone_clearance_mm':.2,'thermal_gap_mm':.3,'thermal_spoke_mm':.3,'zone_min_thickness_mm':.2,'rules_unchanged':True,'release_authorized':False,**stats}
 target.with_name(target.stem+'_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
