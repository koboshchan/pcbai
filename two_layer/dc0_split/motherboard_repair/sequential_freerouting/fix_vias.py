from run import *
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
import math
b=p.LoadBoard(str(D/'repath.kicad_pcb'));d=json.load(open(D/'repath_drc.json'));bad={it['uuid'] for v in d['violations'] if v['severity']=='error' and v['type']=='clearance' for it in v['items'] if it['description'].startswith('Via [IN_58]')};manifest=[]
def xy(q):return(p.ToMM(q.x),p.ToMM(q.y))
for via in list(b.GetTracks()):
 if via.m_Uuid.AsString() not in bad:continue
 orig=via.GetPosition();neighbors=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()==via.GetNetname() and ((t.GetStart()-orig).EuclideanNorm()<300 or (t.GetEnd()-orig).EuclideanNorm()<300)];obs=[[],[]]
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetNetname()==via.GetNetname():continue
   for layer,k in [(p.F_Cu,0),(p.B_Cu,1)]:
    if not pad.IsOnLayer(layer):continue
    poly=pad.GetEffectivePolygon(layer)
    for i in range(poly.OutlineCount()):
     o=poly.COutline(i);obs[k].append(Polygon([xy(o.CPoint(j)) for j in range(o.PointCount())]))
 for t in b.GetTracks():
  if t.GetNetname()==via.GetNetname():continue
  shape=Point(xy(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2,resolution=24) if isinstance(t,p.PCB_VIA) else LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2,resolution=24)
  for layer,k in [(p.F_Cu,0),(p.B_Cu,1)]:
   if t.IsOnLayer(layer):obs[k].append(shape)
 obs=[unary_union(x) for x in obs];ox,oy=xy(orig);cands=sorted([(i*i+j*j,i,j) for i in range(-40,41) for j in range(-40,41)]);found=None
 for _,i,j in cands:
  point=Point(ox+i*.02,oy+j*.02)
  if min(point.distance(o) for o in obs)<.505:continue
  ok=True
  for t in neighbors:
   q=t.GetEnd() if (t.GetStart()-orig).EuclideanNorm()<300 else t.GetStart();seg=LineString([point.coords[0],xy(q)]);k=0 if t.GetLayer()==p.F_Cu else 1
   if seg.distance(obs[k])<p.ToMM(t.GetWidth())/2+.205:ok=False;break
  if ok:found=s.xy(*point.coords[0]);break
 if found is None:raise RuntimeError('No local via position within0.8mm meets actual pad and copper constraints')
 via.SetPosition(found)
 for t in neighbors:
  if (t.GetStart()-orig).EuclideanNorm()<300:t.SetStart(found)
  if (t.GetEnd()-orig).EuclideanNorm()<300:t.SetEnd(found)
 manifest.append({'uuid':via.m_Uuid.AsString(),'before':xy(orig),'after':xy(found)})
out=D/'via_fixed.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));write('VIA_LOCAL_MOVES.json',manifest);print(s.drc(out,True),flush=True)
