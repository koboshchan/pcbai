from run import *
b=p.LoadBoard(str(D/'restored_three.kicad_pcb'));d=json.load(open(D/'restored_three_drc.json'));ids={it['uuid'] for v in d['violations'] if v['severity']=='error' for it in v['items'] if it['description'].startswith('Track [ADC_2]')};ret=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ids:ret.append(t);b.Remove(t)
out=D/'local_adc.kicad_pcb';p.SaveBoard(str(out),b);shutil.copyfile(D/'pre_crb.kicad_pro',out.with_suffix('.kicad_pro'));print(s.drc(out,True),flush=True)
