#!/usr/bin/env python3
"""Independent filled-copper/track audit. Extract with KiCad Python, check with Shapely."""
import json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
if '--extract' in sys.argv:
 import pcbnew as k
 b=k.LoadBoard(str(R/'fingerprint.kicad_pcb'))
 def point(v):return [k.ToMM(v.x),k.ToMM(v.y)]
 def ring(c):return [point(c.CPoint(i)) for i in range(c.PointCount())]
 def polys(s):
  return [dict(shell=ring(s.COutline(i)),holes=[ring(s.CHole(i,h)) for h in range(s.HoleCount(i))]) for i in range(s.OutlineCount())]
 items=[]
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.IsOnLayer(k.B_Cu):
    items.append(dict(kind='pad',ref=f.GetReference()+'.'+p.GetNumber(),net=p.GetNetname(),polys=polys(p.GetEffectivePolygon(k.B_Cu))))
 for z in b.Zones():items.append(dict(kind='zone',net=z.GetNetname(),polys=polys(z.GetFilledPolysList(k.B_Cu))))
 tracks=[]
 for t in b.GetTracks():
  assert t.GetClass()=='PCB_TRACK' and t.GetLayer()==k.B_Cu
  tracks.append(dict(kind='track',net=t.GetNetname(),a=point(t.GetStart()),b=point(t.GetEnd()),width=k.ToMM(t.GetWidth())))
 data=dict(board_sha256=hashlib.sha256((R/'fingerprint.kicad_pcb').read_bytes()).hexdigest(),items=items,tracks=tracks)
 (R/'evidence/copper-geometry.json').write_text(json.dumps(data))
 print('extracted',len(items),len(tracks))
else:
 from shapely.geometry import Polygon,LineString,Point,box
 from shapely.ops import unary_union
 d=json.loads((R/'evidence/copper-geometry.json').read_text())
 assert d['board_sha256']==hashlib.sha256((R/'fingerprint.kicad_pcb').read_bytes()).hexdigest()
 tracks=d['tracks'];g=[]
 for it in d['items']:
  s=unary_union([Polygon(x['shell'],x['holes']).buffer(0) for x in it['polys']])
  g.append((it,s))
 for it in tracks:g.append((it,LineString([it['a'],it['b']]).buffer(it['width']/2,resolution=64)))
 limits=[]
 for it,s in g:
  if s.is_empty:continue
  x,y,X,Y=s.bounds
  limits.append((min(x,y,100-X,70-Y),it['kind'],it.get('ref'),it['net']))
 worst=min(limits)
 assert worst[0]>=.5, worst
 assert all(abs(t['width']-.3)<1e-8 for t in tracks)
 assert not any(t['net']=='GND' for t in tracks)
 dangling=[]
 for t in tracks:
  for end in ['a','b']:
   p=Point(t[end])
   if not any(it is not t and it['net']==t['net'] and s.distance(p)<.00001 for it,s in g):dangling.append([t['net'],t[end]])
 assert not dangling,dangling
 nets={}
 for it,s in g:nets.setdefault(it['net'],[]).append(s)
 nets={n:unary_union(s) for n,s in nets.items()}
 clearances=[]
 names=sorted(nets)
 for i,n in enumerate(names):
  for m in names[i+1:]:clearances.append((nets[n].distance(nets[m]),n,m))
 clearance=min(clearances)
 assert clearance[0]>=.299,clearance
 out=dict(board_sha256=d['board_sha256'],outline_mm=[100,70],track_count=len(tracks),all_tracks_mm=.3,min_measured_net_clearance_mm=clearance[0],closest_nets=list(clearance[1:]),required_clearance_mm=.3,minimum_copper_edge_mm=worst[0],limiting_copper=list(worst[1:]),required_edge_clearance_mm=.5,dangling_track_endpoints=dangling,explicit_ground_tracks=0,ground_u_escape_removed=True,filled_ground_islands=sum(len(it['polys']) for it in d['items'] if it['kind']=='zone'))
 (R/'evidence/copper-audit.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2))
