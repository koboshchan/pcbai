from run import *
from finish import connect
import math
b=p.LoadBoard(str(D/'repath.kicad_pcb'));r=json.load(open(D/'LAST_ADC_PATH.json'));allitems=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];pair=[next(t for t in allitems if t.m_Uuid.AsString()==it['uuid']) for it in r['pair']];base=json.load(open(D/'baseline_copper.json'));released={};ret=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in r['blocking_items']:released[t.m_Uuid.AsString()]=base.get(t.m_Uuid.AsString());ret.append(t);b.Remove(t)
def points(t):return[t.GetPosition()] if isinstance(t,(p.PAD,p.PCB_VIA)) else[t.GetStart(),t.GetEnd()]
ps=r['path_mm'];a=min(points(pair[0]),key=lambda q:math.hypot(p.ToMM(q.x)-ps[0][0],p.ToMM(q.y)-ps[0][1]));z=min(points(pair[1]),key=lambda q:math.hypot(p.ToMM(q.x)-ps[-1][0],p.ToMM(q.y)-ps[-1][1]));connect(b,'ADC_2',ps,a,z);out=D/'last_adc.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));write('LAST_LOCAL_BLOCKERS.json',{'evidence':'LAST_ADC_PATH.json','released_items':released});print(s.drc(out,True),flush=True)
