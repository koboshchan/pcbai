from run import *
b=p.LoadBoard(str(D/'repath.kicad_pcb'));source=p.LoadBoard(str(src));ids=json.load(open(D/'EXPANDED_LOCAL_BLOCKERS.json'))['released_items'];ret=[]
for t in source.GetTracks():
 if t.m_Uuid.AsString() in ids and t.GetNetname() in ['IN_8','IN_39']:
  q=t.Duplicate();q.SetUuid(t.m_Uuid);q.SetNet(b.FindNet(t.GetNetname()));b.Add(q);ret.append(q)
out=D/'restore89.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));print(s.drc(out,True),flush=True)
