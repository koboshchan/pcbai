#!/usr/bin/env python3
from pathlib import Path
import json
import pcbnew as p
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parent
b=p.LoadBoard(str(ROOT/'ads1115_breakout.kicad_pcb'))
g={};holes=[]
for t in b.GetTracks():
 a=t.GetStart();z=t.GetEnd();g.setdefault(t.GetNetname(),[]).append(LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))]).buffer(p.ToMM(t.GetWidth())/2,resolution=64))
for f in b.GetFootprints():
 for a in f.Pads():
  q=a.GetPosition();x=p.ToMM(q.x);y=p.ToMM(q.y)
  if a.GetAttribute()==p.PAD_ATTRIB_NPTH:
   holes.append(Point(x,y).buffer(p.ToMM(a.GetDrillSize().x)/2,resolution=64));continue
  if not a.IsOnLayer(p.F_Cu):continue
  w=p.ToMM(a.GetSize().x);h=p.ToMM(a.GetSize().y)
  shape=Point(x,y).buffer(w/2,resolution=64) if a.GetShape()==p.PAD_SHAPE_CIRCLE else box(x-w/2,y-h/2,x+w/2,y+h/2)
  n=a.GetNetname() or f'{f.GetReference()}:{a.GetNumber()}'
  g.setdefault(n,[]).append(shape)
g={n:unary_union(s)for n,s in g.items()};bounds=box(0,0,50,70).boundary
pairs=[(a,c,sa.distance(sc))for i,(a,sa) in enumerate(g.items())for c,sc in list(g.items())[i+1:]]
worst=min(pairs,key=lambda a:a[2]);edge=min((s.distance(bounds),n)for n,s in g.items());hc=min((s.distance(h),n)for n,s in g.items()for h in holes)
print('minimum different-net copper',worst,'edge',edge,'NPTH',hc)
assert worst[2]>=.4999 and edge[0]>=.4999
(ROOT/'geometry_clearance.json').write_text(json.dumps({'min_copper_clearance_mm':worst[2],'worst_nets':worst[:2],'min_edge_clearance_mm':edge[0],'min_NPTH_clearance_mm':hc[0],'method':'Shapely vector unions, pad circles and round-cap track polygons, resolution 64'},indent=2)+'\n')
