#!/usr/bin/python3
from run import *
import math,heapq,numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
step=.08;N=1251

def pt(q):return (p.ToMM(q.x)/step,p.ToMM(q.y)/step)
def image():return Image.new('1',(N,N))
def drawtrack(im,t,margin=0):
 dr=ImageDraw.Draw(im);r=(p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())/2+margin)/step
 a=pt(t.GetPosition()) if isinstance(t,p.PCB_VIA) else pt(t.GetStart());c=a if isinstance(t,p.PCB_VIA) else pt(t.GetEnd())
 dr.line([a,c],fill=1,width=max(1,math.ceil(2*r)))
 for x,y in [a,c]:dr.ellipse((x-r,y-r,x+r,y+r),fill=1)

def plan(b,net,ref=None,num=None,pair=None):
 ims=[image(),image()];trackims=[image(),image()];target=pair[0] if pair else next(q for f in b.GetFootprints() if f.GetReference()==ref for q in f.Pads() if q.GetNumber()==num)
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetNetname()==net:continue
   for layer,k in [(p.F_Cu,0),(p.B_Cu,1)]:
    if not pad.IsOnLayer(layer):continue
    poly=pad.GetEffectivePolygon(layer)
    for ii in range(poly.OutlineCount()):
     o=poly.COutline(ii);ImageDraw.Draw(ims[k]).polygon([pt(o.CPoint(j)) for j in range(o.PointCount())],fill=1)
 for t in b.GetTracks():
  if (t.GetNetname()==net and (not pair or t.m_Uuid==pair[1].m_Uuid)):continue
  for layer,k in [(p.F_Cu,0),(p.B_Cu,1)]:
   if t.IsOnLayer(layer):drawtrack(trackims[k],t)
 hard=[distance_transform_edt(~np.array(im,dtype=bool))*step for im in ims];soft=[distance_transform_edt(~np.array(im,dtype=bool))*step for im in trackims]
 blocked=[(d<.33)|(soft[k]<.36) for k,d in enumerate(hard)];softb=[d<.33 for d in soft];viapad=(hard[0]>.62)&(hard[1]>.62);viatrack=(soft[0]>.54)&(soft[1]>.54)
 def ends(t):
  poss=[t.GetPosition()] if isinstance(t,p.PCB_VIA) or isinstance(t,p.PAD) else [t.GetStart(),t.GetEnd()]
  return [(round(pt(q)[0]),round(pt(q)[1]),k) for q in poss for ll,k in [(p.F_Cu,0),(p.B_Cu,1)] if t.IsOnLayer(ll)]
 goals=set(q for t in b.GetTracks() if t.GetNetname()==net for q in ends(t))
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetNetname()==net and pad.m_Uuid!=target.m_Uuid:goals.update(ends(pad))
 goals={q for q in goals if not blocked[q[2]][q[1],q[0]]};ga=np.array([(x,y) for x,y,k in goals]);starts=ends(target)
 def h(q):return np.sqrt(((ga-np.array(q[:2]))**2).sum(axis=1)).min()
 costs={q:0 for q in starts};queue=[(h(q),0,q) for q in starts];heapq.heapify(queue);parents={};done=set();moves=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.4143),(1,-1,1.4143),(-1,1,1.4143),(-1,-1,1.4143)]
 while queue:
  _,g,q=heapq.heappop(queue)
  if q in done:continue
  done.add(q);x,y,k=q
  if q in goals:
   path=[q]
   while path[-1] in parents:path.append(parents[path[-1]])
   path.reverse();break
  opts=[]
  for dx,dy,w in moves:
   xx=x+dx;yy=y+dy
   if not(10<=xx<N-10 and 10<=yy<N-10) or blocked[k][yy,xx]:continue
   if dx and dy and (blocked[k][y,xx] or blocked[k][yy,x]):continue
   opts.append(((xx,yy,k),w*(1+50*softb[k][yy,xx])))
  if viapad[y,x] and soft[0][y,x]>.62 and soft[1][y,x]>.62:opts.append(((x,y,1-k),30+(0 if viatrack[y,x] else 500)))
  for z,w in opts:
   ng=g+w
   if ng<costs.get(z,1e99):costs[z]=ng;parents[z]=q;heapq.heappush(queue,(ng+h(z),ng,z))
 else:raise RuntimeError('fixed pads disconnect raster, requires exact verification')
 used=[np.zeros((N,N),bool),np.zeros((N,N),bool)]
 for x,y,k in path:used[k][y,x]=True
 crossed=[]
 for t in b.GetTracks():
  if (t.GetNetname()==net and (not pair or t.m_Uuid==pair[1].m_Uuid)):continue
  im=image();drawtrack(im,t,.33);mask=np.array(im,dtype=bool)
  if any(np.any(mask&used[k]) for layer,k in [(p.F_Cu,0),(p.B_Cu,1)] if t.IsOnLayer(layer)):crossed.append(t.m_Uuid.AsString())
 print(net,'path',len(path),'explored',len(done),'blocking items',len(crossed),flush=True)
 return {'net':net,'path_mm':[(x*step,y*step,k) for x,y,k in path],'blocking_items':crossed}
if __name__=='__main__':
 b=p.LoadBoard(str(src));results=[]
 for args in [('IN_58','JS3','B27'),('ADC_2','JAD','3')]:
  results.append(plan(b,*args));write('SCOPED_PATHS.json',results)
