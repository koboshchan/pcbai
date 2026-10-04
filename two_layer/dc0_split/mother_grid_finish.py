#!/usr/bin/python3
from pathlib import Path
import sys,json,math,heapq,shutil
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
import pcbnew as p
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import successor100 as s;import motherboard_refs as refs
D=R/'motherboard_repair';out=D/'motherboard.kicad_pcb';step=.05;N=2001

def point(pos):return (p.ToMM(pos.x)/step,p.ToMM(pos.y)/step)
def search(b,net,a,c,extra):
 ims=[Image.new('1',(N,N)),Image.new('1',(N,N))];dr=[ImageDraw.Draw(i) for i in ims]
 def disk(layer,xy,r):
  x,y=xy;r/=step;dr[layer].ellipse((math.floor(x-r),math.floor(y-r),math.ceil(x+r),math.ceil(y+r)),fill=1)
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetNetname()==net:continue
   sz=pad.GetSize();r=max(p.ToMM(sz.x),p.ToMM(sz.y))/2+.2+.1+extra
   for layer,k in [(p.F_Cu,0),(p.B_Cu,1)]:
    if pad.IsOnLayer(layer):disk(k,point(pad.GetPosition()),r)
 for t in b.GetTracks():
  if t.GetNetname()==net:continue
  if isinstance(t,p.PCB_VIA):
   for k in [0,1]:disk(k,point(t.GetPosition()),p.ToMM(t.GetWidth())/2+.2+.1+extra)
  else:
   k=0 if t.GetLayer()==p.F_Cu else 1;rad=p.ToMM(t.GetWidth())/2+.2+.1+extra;xy=point(t.GetStart());zz=point(t.GetEnd());dr[k].line([xy,zz],fill=1,width=math.ceil(rad*2/step));disk(k,xy,rad);disk(k,zz,rad)
 masks=[np.array(i,dtype=bool) for i in ims]
 for m in masks:e=math.ceil(.8/step);m[:e,:]=True;m[-e:,:]=True;m[:,:e]=True;m[:,-e:]=True
 vias=(distance_transform_edt(~masks[0])>=math.ceil(.25/step))&(distance_transform_edt(~masks[1])>=math.ceil(.25/step))
 start=tuple([round(a[0]/step),round(a[1]/step),a[2]]);end=tuple([round(c[0]/step),round(c[1]/step),c[2]])
 print('grid',net,start,end,'blocked',masks[start[2]][start[1],start[0]],masks[end[2]][end[1],end[0]],flush=True)
 def h(q):return math.hypot(q[0]-end[0],q[1]-end[1])+ (0 if q[2]==end[2] else 12)
 queue=[(h(start),0,start)];cost={start:0};parent={};done=set();moves=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)]
 while queue:
  _,g,q=heapq.heappop(queue)
  if q in done:continue
  done.add(q)
  if q==end:
   path=[q]
   while path[-1]!=start:path.append(parent[path[-1]])
   return path[::-1]
  x,y,l=q;options=[]
  for dx,dy,w in moves:
   xx=x+dx;yy=y+dy
   if not(0<=xx<N and 0<=yy<N) or masks[l][yy,xx]:continue
   if dx and dy and (masks[l][y,xx] or masks[l][yy,x]):continue
   options.append(((xx,yy,l),w))
  if vias[y,x]:options.append(((x,y,1-l),20))
  for v,w in options:
   ng=g+w
   if ng<cost.get(v,float('inf')):cost[v]=ng;parent[v]=q;heapq.heappush(queue,(ng+h(v),ng,v))
  if len(done)>1800000:break
 print('no path visited',len(done),flush=True)
 return None

def add(b,net,path,a,c):
 points=[(a[0],a[1],a[2])]+[(x*step,y*step,l) for x,y,l in path]+[(c[0],c[1],c[2])]
 # Collapse straight grid runs.
 simple=[points[0]]
 for i in range(1,len(points)-1):
  u,v,w=points[i-1],points[i],points[i+1]
  if u[2]==v[2]==w[2] and abs((v[0]-u[0])*(w[1]-v[1])-(v[1]-u[1])*(w[0]-v[0]))<1e-7:continue
  simple.append(v)
 simple.append(points[-1]);nn=b.FindNet(net)
 for u,v in zip(simple,simple[1:]):
  if u[2]!=v[2]:
   via=p.PCB_VIA(b);via.SetPosition(s.xy(u[0],u[1]));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(nn);b.Add(via)
  elif math.hypot(u[0]-v[0],u[1]-v[1])>1e-7:
   t=p.PCB_TRACK(b);t.SetStart(s.xy(u[0],u[1]));t.SetEnd(s.xy(v[0],v[1]));t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu if u[2]==0 else p.B_Cu);t.SetNet(nn);b.Add(t)

repairs=[]
for iteration in range(10):
 stats=s.drc(out,True);report=json.loads((D/'motherboard_drc.json').read_text());opens=report['unconnected_items']
 if not opens:break
 raw=out.read_bytes();accepted=False
 for gap in opens:
  b=p.LoadBoard(str(out));items={q.m_Uuid.AsString():q for f in b.GetFootprints() for q in f.Pads()};items.update({t.m_Uuid.AsString():t for t in b.GetTracks()});u,v=[items[i['uuid']] for i in gap['items']];net=u.GetNetname()
  def ends(item):
   pos=item.GetPosition() if not isinstance(item,p.PCB_TRACK) or isinstance(item,p.PCB_VIA) else item.GetStart();xy=(p.ToMM(pos.x),p.ToMM(pos.y))
   layers=[k for ll,k in [(p.F_Cu,0),(p.B_Cu,1)] if item.IsOnLayer(ll)]
   return [xy+(l,) for l in layers]
  for extra in [.03,.08]:
   for a in ends(u):
    for c in ends(v):
     path=search(b,net,a,c,extra)
     if path is None:continue
     trial=p.LoadBoard(str(out));add(trial,net,path,a,c);p.SaveBoard(str(out),trial);st=s.drc(out,True)
     if st['errors']==0 and st['opens']<stats['opens']:
      repairs.append({'net':net,'from':a,'to':c,'nodes':len(path),'stats':st});print(repairs[-1],flush=True);accepted=True;break
     print('reject',net,st,flush=True);out.write_bytes(raw)
    if accepted:break
   if accepted:break
  if accepted:break
 if not accepted:break
s.write(D/'GRID_REPAIR.json',repairs)
import subprocess
subprocess.run(['/usr/bin/python3',str(R/'mother_thermal_finish.py')],check=True)
