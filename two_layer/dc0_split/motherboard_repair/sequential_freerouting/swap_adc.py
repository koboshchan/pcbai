from run import *
b=p.LoadBoard(str(D/'restored_three.kicad_pcb'));changes=[]
for t in list(b.GetTracks()):
 if t.GetNetname()!='ADC_2' or isinstance(t,p.PCB_VIA):continue
 x,y=p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)
 if t.GetLayer()==p.F_Cu and 23.7<x<26.1 and 56.4<y<57.3:t.SetLayer(p.B_Cu);changes.append(t.m_Uuid.AsString())
 if t.GetLayer()==p.B_Cu and 20.6<x<23.85 and 56.7<y<58.2 and t.m_Uuid.AsString() not in changes:t.SetLayer(p.F_Cu);changes.append(t.m_Uuid.AsString())
v=p.PCB_VIA(b);v.SetPosition(s.xy(20.64,58.16));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('ADC_2'));b.Add(v)
out=D/'swap_adc.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));print(s.drc(out,True),flush=True)
