#!/usr/bin/python3
"""DRC-gated copper-only repair. Every rejected batch is discarded, never excluded."""
from pathlib import Path
import pcbnew as p
import route_v2 as route
import repair_ground_v2 as ground
import json,sys,math
source=Path(sys.argv[1]).resolve(); work=source.parent/'copper_stitch_conflict_v2';work.mkdir(exist_ok=False)
pro=source.with_suffix('.kicad_pro').read_text(); b=p.LoadBoard(str(source)); identity=ground.fixed(b)
def save(board,name):
 path=work/(name+'.kicad_pcb');p.SaveBoard(str(path),board);path.with_suffix('.kicad_pro').write_text(pro);return path
# Remove only router copper implicated in actual edge-clearance failures.
d=json.loads(source.with_name(source.stem+'_drc.json').read_text());bad={i['uuid'] for v in d['violations'] if v['severity']=='error' for i in v['items']}
removed=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in bad:removed.append(t.m_Uuid.AsString());b.RemoveNative(t)
current=save(b,'clean_edges');d,stats=route.drc(current);assert stats['errors']==0,stats
history=[{'stage':'edge_remove','removed':removed,**stats}]
print(json.dumps(history[-1]),flush=True)
def pos(pt):return (p.ToMM(pt.x),p.ToMM(pt.y))
def vec(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
def lookup(board):
 return {i.m_Uuid.AsString():i for i in list(board.GetTracks())+[pad for fp in board.GetFootprints() for pad in fp.Pads()]}
def available(item):
 if isinstance(item,p.PCB_VIA):return (p.F_Cu,p.B_Cu)
 if isinstance(item,p.PAD):return tuple(l for l in (p.F_Cu,p.B_Cu) if item.IsOnLayer(l))
 return (item.GetLayer(),)
for roundno in range(3):
 improved=False
 for pattern in range(10):
  board=p.LoadBoard(str(current)); index=lookup(board);added={};groups={}
  opens=sorted(d['unconnected_items'],key=lambda o:math.dist(tuple(o['items'][0]['pos'].values()),tuple(o['items'][1]['pos'].values())))
  for n,op in enumerate(opens):
   aa,bb=op['items'];a=index.get(aa['uuid']);z=index.get(bb['uuid'])
   if a is None or z is None or a.GetNetCode()!=z.GetNetCode():continue
   start=(aa['pos']['x'],aa['pos']['y']);end=(bb['pos']['x'],bb['pos']['y']);layer=(p.F_Cu,p.B_Cu)[pattern%2]
   code=a.GetNetCode();parts=[]
   def track(x,y):
    if x==y:return
    t=p.PCB_TRACK(board);t.SetStart(vec(x));t.SetEnd(vec(y));t.SetWidth(p.FromMM(.2));t.SetLayer(layer);t.SetNetCode(code);board.Add(t);parts.append(t)
   shape=pattern//2
   if shape==0:points=[start,end]
   elif shape==1:points=[start,(start[0],end[1]),end]
   elif shape==2:points=[start,(end[0],start[1]),end]
   elif shape==3:
    mx=(start[0]+end[0])/2;points=[start,(mx,start[1]),(mx,end[1]),end]
   else:
    my=(start[1]+end[1])/2;points=[start,(start[0],my),(end[0],my),end]
   for x,y in zip(points,points[1:]):track(x,y)
   for item,xy in ((a,start),(z,end)):
    if layer not in available(item):
     v=p.PCB_VIA(board);v.SetPosition(vec(xy));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(code);board.Add(v);parts.append(v)
   groups[n]=parts
   for t in parts:added[t.m_Uuid.AsString()]=n
  path=save(board,f'trial_{roundno}_{pattern}');trial,tstats=route.drc(path)
  # Reject whole paths touching any actual error; re-audit after every rejection.
  for prune in range(140):
   violations=[v for v in trial['violations'] if v['severity']=='error']
   if not violations:break
   reject=set()
   for violation in violations:
    involved={added[i['uuid']] for i in violation['items'] if i['uuid'] in added}
    if not involved:continue
    # For conflicts between entirely new paths, discard just the longer path.
    if len(involved)>1 and all(i['uuid'] in added for i in violation['items']):
     def length(g):return sum(p.ToMM(t.GetLength()) for t in groups[g] if isinstance(t,p.PCB_TRACK))
     reject.add(max(involved,key=length))
    else:reject.update(involved)
   if not reject:raise RuntimeError('Original copper acquired error without rejectable additions')
   for g in reject:
    for t in groups.pop(g,[]):board.RemoveNative(t);added.pop(t.m_Uuid.AsString(),None)
   path=save(board,f'trial_{roundno}_{pattern}');trial,tstats=route.drc(path)
  assert tstats['errors']==0,tstats
  assert ground.fixed(board)==identity
  if tstats['unconnected']<stats['unconnected']:
   current=path;d=trial;stats=tstats;improved=True
   history.append({'round':roundno,'pattern':pattern,'accepted_paths':len(groups),'candidate':str(current),**stats});print(json.dumps(history[-1]),flush=True)
  if stats['unconnected']==0:break
 if not improved or stats['unconnected']==0:break
result={'candidate':str(current),'candidate_sha256':route.sha(current),'identity_verified':ground.fixed(p.LoadBoard(str(current)))==identity,'silk_clean':route.silk.audit(p.LoadBoard(str(current)))['clean'],'release_authorized':False,'history':history,**stats}
(work/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
