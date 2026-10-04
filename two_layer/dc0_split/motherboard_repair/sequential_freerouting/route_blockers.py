from run import *
b=p.LoadBoard(str(D/'manual_paths.kicad_pcb'));raw=p.LoadBoard(str(D/'scoped_raw.kicad_pcb'));sesids={t.m_Uuid.AsString() for t in raw.GetTracks()};ret=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in sesids:ret.append(t);b.Remove(t)
for net,x,y,nx,ny in [('IN_58',87.36,64.96,87.36,65.12),('IN_58',85.52,34.,85.44,34.08)]:
 old=s.xy(x,y);new=s.xy(nx,ny)
 for t in b.GetTracks():
  if t.GetNetname()!=net:continue
  if isinstance(t,p.PCB_VIA):
   if (t.GetPosition()-old).EuclideanNorm()<300:t.SetPosition(new)
  else:
   if (t.GetStart()-old).EuclideanNorm()<300:t.SetStart(new)
   if (t.GetEnd()-old).EuclideanNorm()<300:t.SetEnd(new)
start=D/'blockers_start.kicad_pcb';p.SaveBoard(str(start),b)
zones=list(b.Zones())
for z in zones:b.Remove(z)
dsn=D/'blockers.dsn';assert p.ExportSpecctraDSN(b,str(dsn));text=dsn.read_text();i=text.rfind('(wiring');head,tail=text[:i],text[i:];tail,n=re.subn(r'\(type\s+\w+\)','(type fix)',tail);dsn.write_text(head+tail);write('BLOCKERS_FIXED.json',{'scopes':n,'all_remaining_fixed':True})
with (D/'blockers_router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual48.jar','-de',str(dsn),'-do',str(D/'blockers.ses'),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True)
