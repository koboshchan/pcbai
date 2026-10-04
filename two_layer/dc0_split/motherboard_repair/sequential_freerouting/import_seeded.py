from run import *
imp=p.LoadBoard(str(src));assert p.ImportSpecctraSES(imp,str(D/'seeded.ses'));p.SaveBoard(str(D/'seeded_raw.kicad_pcb'),imp);b=p.LoadBoard(str(src));ids=set(q for r in json.load(open(D/'SCOPED_PATHS.json')) for q in r['blocking_items']);ret=[];added=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ids:ret.append(t);b.Remove(t)
for t in imp.GetTracks():
 new=t.Duplicate();new.SetUuid(p.KIID());new.SetNet(b.FindNet(t.GetNetname()));b.Add(new);added.append(new)
out=D/'repath.kicad_pcb';p.SaveBoard(str(out),b);print(s.drc(out,True),flush=True)
