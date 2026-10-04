from run import *
import math
from scoped_search import plan
from finish import connect
b=p.LoadBoard(str(D/'manual_paths.kicad_pcb'));base=json.load(open(D/'baseline_copper.json'))
for t in list(b.GetTracks()):
 if t.GetNetname() in ['ADC_2','IN_58'] and t.m_Uuid.AsString() not in base:b.Remove(t)
p.SaveBoard(str(D/'repath_start.kicad_pcb'),b);b=p.LoadBoard(str(D/'repath_start.kicad_pcb'))
for net,ref,num in [('ADC_2','JAD','3'),('IN_58','JS3','B27')]:
 r=plan(b,net,ref,num);print(r['blocking_items'],flush=True)
 if r['blocking_items']:raise RuntimeError('hard fixed path unavailable, further local geometry refinement needed')
 pad=next(q for f in b.GetFootprints() if f.GetReference()==ref for q in f.Pads() if q.GetNumber()==num);v=r['path_mm'][-1];opts=[]
 for t in b.GetTracks():
  if t.GetNetname()!=net:continue
  for q in ([t.GetPosition()] if isinstance(t,p.PCB_VIA) else [t.GetStart(),t.GetEnd()]):
   if t.IsOnLayer(p.F_Cu if v[2]==0 else p.B_Cu):opts.append((math.hypot(p.ToMM(q.x)-v[0],p.ToMM(q.y)-v[1]),q))
 end=min(opts,key=lambda a:a[0])[1];connect(b,net,r['path_mm'],pad.GetPosition(),end);p.SaveBoard(str(D/'repath.kicad_pcb'),b);write('REPATH_'+net+'.json',r)
shutil.copyfile(D/'pre_crb.kicad_pro',D/'repath.kicad_pro');print(s.drc(D/'repath.kicad_pcb',True),flush=True)
