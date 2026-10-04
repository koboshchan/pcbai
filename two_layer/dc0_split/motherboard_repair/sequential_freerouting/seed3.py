from run import *
from import_locked import scopes
b=p.LoadBoard(str(D/'expanded_adc.kicad_pcb'));base=json.load(open(D/'baseline_copper.json'));retain=[];new=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() not in base:new.append(t);b.Remove(t)
p.SaveBoard(str(D/'seed3_start.kicad_pcb'),b)
zones=list(b.Zones())
for z in zones:b.Remove(z)
assert p.ExportSpecctraDSN(b,str(D/'seed3_fixed.dsn'));text=(D/'seed3_fixed.dsn').read_text();i=text.rfind('(wiring');head,tail=text[:i],text[i:];tail=re.sub(r'\(type\s+\w+\)','(type fix)',tail)
for t in list(b.GetTracks()):retain.append(t);b.Remove(t)
for t in new:b.Add(t)
assert p.ExportSpecctraDSN(b,str(D/'seed3_new.dsn'));nt=(D/'seed3_new.dsn').read_text();j=nt.rfind('(wiring');segments='\n'.join(scopes(nt[j:],'wire')+scopes(nt[j:],'via'))
segments=re.sub(r'\(type\s+\w+\)','(type route)',segments);idx=tail.rfind(')');idx=tail[:idx].rfind(')');combined=tail[:idx]+segments+'\n'+tail[idx:];dsn=D/'seed3.dsn';dsn.write_text(head+combined)
write('SEED3_FIXED_AUDIT.json',{'exported_original_scopes_fixed':True,'fixed_scopes':len(scopes(tail,'wire'))+len(scopes(tail,'via')),'only_new_generated_copper_unfixed':True,'expanded_blocker_evidence':'EXPANDED_LOCAL_BLOCKERS.json'})
with (D/'seed3_router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual48.jar','-de',str(dsn),'-do',str(D/'seed3.ses'),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True)
imp=p.LoadBoard(str(src));assert p.ImportSpecctraSES(imp,str(D/'seed3.ses'));p.SaveBoard(str(D/'seed3_raw.kicad_pcb'),imp);b=p.LoadBoard(str(D/'seed3_start.kicad_pcb'))
for t in imp.GetTracks():
 q=t.Duplicate();q.SetUuid(p.KIID());q.SetNet(b.FindNet(t.GetNetname()));b.Add(q)
out=D/'repath.kicad_pcb';p.SaveBoard(str(out),b);print(s.drc(out,True),flush=True)
