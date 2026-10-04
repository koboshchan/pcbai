from run import *
from import_locked import scopes
b=p.LoadBoard(str(D/'via_fixed.kicad_pcb'));base=json.load(open(D/'baseline_copper.json'));retain=[];new=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() not in base:new.append(t);b.Remove(t)
p.SaveBoard(str(D/'seeded_start.kicad_pcb'),b)
zones=list(b.Zones())
for z in zones:b.Remove(z)
assert p.ExportSpecctraDSN(b,str(D/'seeded_fixed.dsn'));text=(D/'seeded_fixed.dsn').read_text();i=text.rfind('(wiring');head,tail=text[:i],text[i:];tail=re.sub(r'\(type\s+\w+\)','(type fix)',tail)
for t in list(b.GetTracks()):retain.append(t);b.Remove(t)
for t in new:b.Add(t)
assert p.ExportSpecctraDSN(b,str(D/'seeded_new.dsn'));nt=(D/'seeded_new.dsn').read_text();j=nt.rfind('(wiring');segments='\n'.join(scopes(nt[j:],'wire')+scopes(nt[j:],'via'));print('newscopes',len(segments),flush=True)
# New copper is explicitly route-unfixed; immutable original copper remains type fix.
segments=re.sub(r'\(type\s+\w+\)','(type route)',segments);idx=tail.rfind(')');idx=tail[:idx].rfind(')');combined=tail[:idx]+segments+'\n'+tail[idx:];dsn=D/'seeded.dsn';dsn.write_text(head+combined)
with (D/'seeded_router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual48.jar','-de',str(dsn),'-do',str(D/'seeded.ses'),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True)
