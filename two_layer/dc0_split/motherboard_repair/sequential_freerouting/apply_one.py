from run import *
import math
from finish import connect
net=sys.argv[1];inp=Path(sys.argv[2]);out=Path(sys.argv[3]);b=p.LoadBoard(str(inp));r=json.load(open(D/('REPATH_'+net+'.json')));assert not r['blocking_items'];ref,num=('JAD','3') if net=='ADC_2' else ('JS3','B27');pad=next(q for f in b.GetFootprints() if f.GetReference()==ref for q in f.Pads() if q.GetNumber()==num);v=r['path_mm'][-1];opts=[]
for t in b.GetTracks():
 if t.GetNetname()!=net:continue
 for q in ([t.GetPosition()] if isinstance(t,p.PCB_VIA) else [t.GetStart(),t.GetEnd()]):
  if t.IsOnLayer(p.F_Cu if v[2]==0 else p.B_Cu):opts.append((math.hypot(p.ToMM(q.x)-v[0],p.ToMM(q.y)-v[1]),q))
end=min(opts,key=lambda a:a[0])[1];connect(b,net,r['path_mm'],pad.GetPosition(),end);p.SaveBoard(str(out),b)
