#!/usr/bin/python3
from run import *
from scoped_search import plan
import math
# Repair private candidate by exact DRC endpoints, all remaining baseline copper fixed.
def connect(b,net,pts,start,end):
 pts[0]=[p.ToMM(start.x),p.ToMM(start.y),pts[0][2]];pts[-1]=[p.ToMM(end.x),p.ToMM(end.y),pts[-1][2]];simple=[pts[0]]
 for i in range(1,len(pts)-1):
  u,v,w=pts[i-1:i+2]
  if u[2]==v[2]==w[2] and abs((v[0]-u[0])*(w[1]-v[1])-(v[1]-u[1])*(w[0]-v[0]))<1e-8:continue
  simple.append(v)
 simple.append(pts[-1])
 for u,v in zip(simple,simple[1:]):
  if u[2]!=v[2]:
   t=p.PCB_VIA(b);t.SetPosition(s.xy(*u[:2]));t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
  else:
   if math.dist(u[:2],v[:2])<1e-8:continue
   t=p.PCB_TRACK(b);t.SetStart(s.xy(*u[:2]));t.SetEnd(s.xy(*v[:2]));t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu if u[2]==0 else p.B_Cu)
  t.SetNet(b.FindNet(net));b.Add(t)
if __name__=='__main__':
 out=D/'manual_paths.kicad_pcb';b=p.LoadBoard(str(out));d=json.load(open(D/'manual_paths_drc.json'));moves=[]
 # Relocate only two newly added vias and attached new track endpoints by 0.08mm, away from pads.
 for x,y,dx,dy in [(87.36,64.96,.08,0),(85.44,33.92,.08,.08)]:
  old=s.xy(x,y);new=s.xy(x+dx,y+dy)
  for t in b.GetTracks():
   if t.GetNetname()!='IN_58':continue
   if isinstance(t,p.PCB_VIA):
    if t.GetPosition()==old:t.SetPosition(new);moves.append(t.m_Uuid.AsString())
   else:
    if t.GetStart()==old:t.SetStart(new)
    if t.GetEnd()==old:t.SetEnd(new)
 p.SaveBoard(str(out),b);print(s.drc(out,True),flush=True)
 # Merge only SES routes on the blocker nets, then check exact strict report.
 raw=p.LoadBoard(str(D/'scoped_raw.kicad_pcb'));b=p.LoadBoard(str(out))
 for t in raw.GetTracks():
  if t.GetNetname()=='GND':continue
  new=t.Duplicate();b.Add(new)
 p.SaveBoard(str(out),b);print(s.drc(out,True),flush=True)
