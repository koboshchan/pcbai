#!/usr/bin/python3
"""Repair only connected copper vertices at rectangle edges, then strict audit."""
from pathlib import Path
import pcbnew as p
import route_v2 as route
import repair_ground_v2 as ground
import json,sys
ROOT=Path(__file__).resolve().parent
source=Path(sys.argv[1]).resolve(); target=source.with_name(source.stem+'_edge_fixed_v2.kicad_pcb')
assert not target.exists()
b=p.LoadBoard(str(source)); identity=ground.fixed(b)
tracks=list(b.GetTracks()); moved={}
# Clamp entire endpoint groups, including touching same-net vias, conservatively.
for t in tracks:
 radius=p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())/2
 for pt in ([t.GetPosition()] if isinstance(t,p.PCB_VIA) else [t.GetStart(),t.GetEnd()]):
  x,y=p.ToMM(pt.x),p.ToMM(pt.y); margin=.5+radius+.01
  nx,ny=max(margin,min(100-margin,x)),max(margin,min(100-margin,y))
  if (nx,ny)!=(x,y):
   key=(t.GetNetCode(),pt.x,pt.y); old=moved.get(key,(x,y))
   moved[key]=(max(old[0],nx) if x<50 else min(old[0],nx),max(old[1],ny) if y<50 else min(old[1],ny))
for t in tracks:
 for getter,setter in ([('GetPosition','SetPosition')] if isinstance(t,p.PCB_VIA) else [('GetStart','SetStart'),('GetEnd','SetEnd')]):
  pt=getattr(t,getter)();q=moved.get((t.GetNetCode(),pt.x,pt.y))
  if q:getattr(t,setter)(p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1])))
assert ground.fixed(b)==identity
p.SaveBoard(str(target),b);target.with_suffix('.kicad_pro').write_text(source.with_suffix('.kicad_pro').read_text())
d,stats=route.drc(target)
result={'candidate':str(target),'moved_endpoint_groups':len(moved),'identity_verified':True,'release_authorized':False,**stats}
target.with_name(target.stem+'_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
