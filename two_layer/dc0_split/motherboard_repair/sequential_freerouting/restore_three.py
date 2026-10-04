from run import *
b=p.LoadBoard(str(D/'repath.kicad_pcb'));source=p.LoadBoard(str(src));rows=json.load(open(D/'SCOPED_PATHS.json'));ids=set(q for r in rows for q in r['blocking_items']);added=[]
for t in source.GetTracks():
 if t.m_Uuid.AsString() in ids and t.GetNetname() in ['IN_5','IN_9','IN_40']:
  q=t.Duplicate();q.SetUuid(t.m_Uuid);q.SetNet(b.FindNet(t.GetNetname()));b.Add(q);added.append(q)
out=D/'restored_three.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));print(s.drc(out,True),flush=True)
