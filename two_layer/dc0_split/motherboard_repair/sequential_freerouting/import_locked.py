#!/usr/bin/python3
from run import *
import math

def scopes(text,name):
 out=[]
 for m in re.finditer(r'\('+name+r'\s',text):
  depth=0;quote=False
  for j in range(m.start(),len(text)):
   c=text[j]
   if c=='"':quote=not quote
   if quote:continue
   if c=='(':depth+=1
   if c==')':
    depth-=1
    if depth==0:out.append(text[m.start():j+1]);break
 return out

def dsnaudit():
 text=(D/'locked.dsn').read_text();text=text[text.rfind('(wiring'):];segments=[];vias=[]
 for w in scopes(text,'wire'):
  assert '(type fix)' in w
  a=re.search(r'\(path\s+(\S+)\s+([\d.]+)\s+([^()]+)\)',w);assert a,w
  net=re.search(r'\(net\s+([^()]+)\)',w).group(1).strip().strip('"');nums=list(map(float,a[3].split()));pts=list(zip(nums[::2],nums[1::2]))
  for u,v in zip(pts,pts[1:]):segments.append((net,a[1],float(a[2]),u,v))
 for w in scopes(text,'via'):
  assert '(type fix)' in w
  a=re.match(r'\(via\s+"([^"]+)"\s+([\d.-]+)\s+([\d.-]+)',w);assert a;net=re.search(r'\(net\s+([^()]+)\)',w).group(1).strip().strip('"');vias.append((net,float(a[2]),float(a[3])))
 def dist(q,u,v):
  dx=v[0]-u[0];dy=v[1]-u[1];den=dx*dx+dy*dy
  t=max(0,min(1,((q[0]-u[0])*dx+(q[1]-u[1])*dy)/den)) if den else 0
  return math.hypot(q[0]-u[0]-t*dx,q[1]-u[1]-t*dy)
 b=p.LoadBoard(str(src));miss=[]
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):
   q=t.GetPosition();found=any(net==t.GetNetname() and math.hypot(x-q.x/1000,y+q.y/1000)<.3 for net,x,y in vias)
  else:
   u=t.GetStart();v=t.GetEnd();points=[(u.x/1000,-u.y/1000),(v.x/1000,-v.y/1000),((u.x+v.x)/2000,-(u.y+v.y)/2000)]
   found=all(any(net==t.GetNetname() and layer==b.GetLayerName(t.GetLayer()) and abs(width-t.GetWidth()/1000)<.2 and dist(q,a,c)<.3 for net,layer,width,a,c in segments) for q in points)
  if not found:miss.append(t.m_Uuid.AsString())
 assert not miss,miss
 write('DSN_GEOMETRY_AUDIT.json',{'baseline_items':len(b.GetTracks()),'exported_segments':len(segments),'exported_vias':len(vias),'all_source_copper_represented_fixed':True,'missing':miss,'tolerance_um':.3})

def main():
 dsnaudit();b=p.LoadBoard(str(src));phys=refs.physical(b);ids=s.identity(b);orig=copper(b);imp=p.LoadBoard(str(src));assert p.ImportSpecctraSES(imp,str(D/'locked.ses'));p.SaveBoard(str(D/'ses_raw.kicad_pcb'),imp)
 base=list(b.GetTracks());added=[]
 def covered(t):
  if isinstance(t,p.PCB_VIA):return any(isinstance(u,p.PCB_VIA) and u.GetNetname()==t.GetNetname() and math.hypot(u.GetPosition().x-t.GetPosition().x,u.GetPosition().y-t.GetPosition().y)<300 for u in base)
  a=t.GetStart();c=t.GetEnd();dx=c.x-a.x;dy=c.y-a.y;length=math.hypot(dx,dy)
  if not length:return True
  ints=[]
  for u in base:
   if isinstance(u,p.PCB_VIA) or u.GetNetname()!=t.GetNetname() or u.GetLayer()!=t.GetLayer() or u.GetWidth()!=t.GetWidth():continue
   e=u.GetStart();f=u.GetEnd()
   if max(abs((q.x-a.x)*dy-(q.y-a.y)*dx)/length for q in [e,f])>300:continue
   ts=sorted(((q.x-a.x)*dx+(q.y-a.y)*dy)/(length*length) for q in [e,f]);ints.append(ts)
  end=0
  for l,r in sorted(ints):
   if l>end+300/length:break
   end=max(end,r)
  return end>=1-300/length
 for t in imp.GetTracks():
  if t.GetNetname() not in ['ADC_2','IN_58'] or covered(t):continue
  new=t.Duplicate(False);new.m_Uuid=p.KIID();b.Add(new);added.append(new.m_Uuid.AsString())
 assert all(copper(b)[k]==v for k,v in orig.items());assert refs.physical(b)==phys and s.identity(b)==ids
 out=D/'pre_crb.kicad_pcb';p.SaveBoard(str(out),b);stats=s.drc(out,True);loaded=p.LoadBoard(str(out));stats.update(sha=s.sha(out),candidate=str(out),identity=s.identity(loaded)==ids,physical_identity=refs.physical(loaded)==phys,silk_clean=silk.audit(loaded)['clean'],existing_copper_preserved=all(copper(loaded).get(k)==v for k,v in orig.items()),added_copper=added,protected_unchanged=all(s.sha(Path(f))==h for f,h in json.loads((D/'protected_before.json').read_text()).items()))
 stats['strict_pass']=stats['errors']==stats['opens']==0 and all(stats[k] for k in ['identity','physical_identity','silk_clean','existing_copper_preserved','protected_unchanged']);write('PRE_CRB_AUDIT.json',stats);print(json.dumps(stats))
if __name__=='__main__':main()
