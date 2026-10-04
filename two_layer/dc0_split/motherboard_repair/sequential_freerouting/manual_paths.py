#!/usr/bin/python3
from run import *
import math

def main():
 rows=json.load(open(D/'SCOPED_PATHS.json'));ids=set(q for r in rows for q in r['blocking_items']);b=p.LoadBoard(str(src));tracks=list(b.GetTracks());removed=[]
 for t in tracks:
  if t.m_Uuid.AsString() in ids:removed.append(copper(b)[t.m_Uuid.AsString()]);b.Remove(t)
 for row in rows:
  pts=row['path_mm'];ref,num=('JAD','3') if row['net']=='ADC_2' else ('JS3','B27');pad=next(q for f in b.GetFootprints() if f.GetReference()==ref for q in f.Pads() if q.GetNumber()==num);pts[0]=[p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y),pts[0][2]]
  last=pts[-1];opts=[]
  for t in b.GetTracks():
   if t.GetNetname()!=row['net']:continue
   for q in ([t.GetPosition()] if isinstance(t,p.PCB_VIA) else [t.GetStart(),t.GetEnd()]):
    if t.IsOnLayer(p.F_Cu if last[2]==0 else p.B_Cu):opts.append((math.hypot(p.ToMM(q.x)-last[0],p.ToMM(q.y)-last[1]),q))
  _,q=min(opts,key=lambda a:a[0]);pts[-1]=[p.ToMM(q.x),p.ToMM(q.y),last[2]];simple=[pts[0]]
  for i in range(1,len(pts)-1):
   u,v,w=pts[i-1:i+2]
   if u[2]==v[2]==w[2] and abs((v[0]-u[0])*(w[1]-v[1])-(v[1]-u[1])*(w[0]-v[0]))<1e-8:continue
   simple.append(v)
  simple.append(pts[-1]);net=b.FindNet(row['net'])
  for u,v in zip(simple,simple[1:]):
   if u[2]!=v[2]:
    t=p.PCB_VIA(b);t.SetPosition(s.xy(*u[:2]));t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
   else:
    if math.dist(u[:2],v[:2])<1e-8:continue
    t=p.PCB_TRACK(b);t.SetStart(s.xy(*u[:2]));t.SetEnd(s.xy(*v[:2]));t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu if u[2]==0 else p.B_Cu)
   t.SetNet(net);b.Add(t)
 out=D/'manual_paths.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));stats=s.drc(out,True);write('MANUAL_PATHS_AUDIT.json',stats);print(stats,flush=True)
if __name__=='__main__':main()
