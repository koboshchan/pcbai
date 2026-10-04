from run import *
imp=p.LoadBoard(str(D/'blockers_start.kicad_pcb'));assert p.ImportSpecctraSES(imp,str(D/'blockers.ses'));p.SaveBoard(str(D/'blockers_raw.kicad_pcb'),imp)
b=p.LoadBoard(str(D/'blockers_start.kicad_pcb'));newitems=[]
for t in imp.GetTracks():
 new=t.Duplicate();new.SetUuid(p.KIID());new.SetNet(b.FindNet(t.GetNetname()));b.Add(new);newitems.append(new)
out=D/'repath.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));print(s.drc(out,True),flush=True)
