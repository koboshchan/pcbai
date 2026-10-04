from run import *
from finish import connect
import math
b=p.LoadBoard(str(D/'via_fixed.kicad_pcb'));allitems=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];manifest=[]
def points(t):return[t.GetPosition()] if isinstance(t,(p.PAD,p.PCB_VIA)) else[t.GetStart(),t.GetEnd()]
for net in ['IN_5','IN_9','IN_40','+5V_REF']:
 r=json.load(open(D/('PAIR_'+net.replace('+','P')+'.json')));assert not r['blocking_items'];pair=[next(t for t in allitems if t.m_Uuid.AsString()==it['uuid']) for it in r['pair']];ps=r['path_mm'];a=min(points(pair[0]),key=lambda q:math.hypot(p.ToMM(q.x)-ps[0][0],p.ToMM(q.y)-ps[0][1]));z=min(points(pair[1]),key=lambda q:math.hypot(p.ToMM(q.x)-ps[-1][0],p.ToMM(q.y)-ps[-1][1]));connect(b,net,ps,a,z);manifest.append(r)
out=D/'repath.kicad_pcb';p.SaveBoard(str(out),b);write('PAIRS_MANIFEST.json',manifest);print(s.drc(out,True),flush=True)
