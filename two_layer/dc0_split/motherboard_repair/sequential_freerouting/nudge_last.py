from run import *
b=p.LoadBoard(str(D/'repath.kicad_pcb'));base=json.load(open(D/'baseline_copper.json'));moves={}
def shift(q):
 x,y=p.ToMM(q.x),p.ToMM(q.y);dx=dy=0
 if 1.5<x<6.5 and 89.3<y<89.5:dy=.12
 if 19.7<x<20.6 and 97<y<97.6:dy=.1
 if 19.3<x<19.5 and 51.5<y<53:dx=.1
 return s.xy(x+dx,y+dy)
for t in b.GetTracks():
 if t.GetNetname()!='ADC_2' or t.m_Uuid.AsString() in base:continue
 if isinstance(t,p.PCB_VIA):t.SetPosition(shift(t.GetPosition()))
 else:t.SetStart(shift(t.GetStart()));t.SetEnd(shift(t.GetEnd()))
out=D/'nudge_last.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));print(s.drc(out,True),flush=True)
