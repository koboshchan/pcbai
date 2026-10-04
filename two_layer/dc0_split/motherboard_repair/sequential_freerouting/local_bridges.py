from run import *
b=p.LoadBoard(str(D/'manual_paths.kicad_pcb'));moves=[('IN_58',87.36,64.96,87.36,65.12),('IN_58',85.52,34.,85.44,34.08),('IN_5',15.1083,61.0597,15.1083,60.7)]
for net,x,y,nx,ny in moves:
 old=s.xy(x,y);new=s.xy(nx,ny)
 for t in b.GetTracks():
  if t.GetNetname()!=net:continue
  if isinstance(t,p.PCB_VIA):
   if (t.GetPosition()-old).EuclideanNorm()<300:t.SetPosition(new)
  else:
   if (t.GetStart()-old).EuclideanNorm()<300:t.SetStart(new)
   if (t.GetEnd()-old).EuclideanNorm()<300:t.SetEnd(new)
ids=['7e568b0f-12ec-4141-a9d1-07dac36192fd','bd2bfc63-6d7c-49f4-92f6-d0ed38fc1ed0','965bd8ce-9a21-48ae-a7a8-6a20133e5e87'];changes=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() not in ids:continue
 old=t.GetLayer();t.SetLayer(p.B_Cu if old==p.F_Cu else p.F_Cu)
 for point in [t.GetStart(),t.GetEnd()]:
  via=p.PCB_VIA(b);via.SetPosition(point);via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetViaType(p.VIATYPE_THROUGH);via.SetNet(t.GetNet());b.Add(via)
 changes.append(t.m_Uuid.AsString())
out=D/'bridges.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));print(s.drc(out,True),flush=True)
