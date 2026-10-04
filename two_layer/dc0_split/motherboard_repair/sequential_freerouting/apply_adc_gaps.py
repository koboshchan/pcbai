from run import *
from finish import connect
import math
b=p.LoadBoard(str(D/'local_adc.kicad_pcb'));allitems=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]
def points(t):return[t.GetPosition()] if isinstance(t,(p.PAD,p.PCB_VIA)) else[t.GetStart(),t.GetEnd()]
for i in range(2):
 r=json.load(open(D/('ADC_GAP_'+str(i)+'.json')));pair=[next(t for t in allitems if t.m_Uuid.AsString()==it['uuid']) for it in r['pair']];ps=r['path_mm'];a=min(points(pair[0]),key=lambda q:math.hypot(p.ToMM(q.x)-ps[0][0],p.ToMM(q.y)-ps[0][1]));z=min(points(pair[1]),key=lambda q:math.hypot(p.ToMM(q.x)-ps[-1][0],p.ToMM(q.y)-ps[-1][1]));connect(b,'ADC_2',ps,a,z)
out=D/'repath.kicad_pcb';p.SaveBoard(str(out),b);print(s.drc(out,True),flush=True)
