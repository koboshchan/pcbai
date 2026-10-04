from run import *
from import_locked import scopes
b=p.LoadBoard(str(D/'reset_adc.kicad_pcb'));base=json.load(open(D/'baseline_copper.json'));retain=[];new=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() not in base:new.append(t);b.Remove(t)
p.SaveBoard(str(D/'seed4_start.kicad_pcb'),b);zones=list(b.Zones())
for z in zones:b.Remove(z)
assert p.ExportSpecctraDSN(b,str(D/'seed4_fixed.dsn'));text=(D/'seed4_fixed.dsn').read_text();i=text.rfind('(wiring');head,tail=text[:i],text[i:];tail=re.sub(r'\(type\s+\w+\)','(type fix)',tail)
for t in list(b.GetTracks()):retain.append(t);b.Remove(t)
for t in new:b.Add(t)
assert p.ExportSpecctraDSN(b,str(D/'seed4_new.dsn'));nt=(D/'seed4_new.dsn').read_text();j=nt.rfind('(wiring');segments='\n'.join(scopes(nt[j:],'wire')+scopes(nt[j:],'via'));segments=re.sub(r'\(type\s+\w+\)','(type route)',segments);idx=tail.rfind(')');idx=tail[:idx].rfind(')');dsn=D/'seed4.dsn';dsn.write_text(head+tail[:idx]+segments+'\n'+tail[idx:])
with (D/'seed4_router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual48.jar','-de',str(dsn),'-do',str(D/'seed4.ses'),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True)
imp=p.LoadBoard(str(src));assert p.ImportSpecctraSES(imp,str(D/'seed4.ses'));p.SaveBoard(str(D/'seed4_raw.kicad_pcb'),imp);b=p.LoadBoard(str(D/'seed4_start.kicad_pcb'))
for t in imp.GetTracks():
 q=t.Duplicate();q.SetUuid(p.KIID());q.SetNet(b.FindNet(t.GetNetname()));b.Add(q)
out=D/'repath.kicad_pcb';p.SaveBoard(str(out),b);print(s.drc(out,True),flush=True)
