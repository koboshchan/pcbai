import scoped_search as a
from run import *
a.step=.04;a.N=2501
b=p.LoadBoard(str(D/'local_adc.kicad_pcb'));d=json.load(open(D/'local_adc_drc.json'));v=d['unconnected_items'][int(sys.argv[1])];allitems=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];pair=[next(t for t in allitems if t.m_Uuid.AsString()==it['uuid']) for it in v['items']];r=a.plan(b,'ADC_2',pair=pair);r['pair']=v['items'];write('ADC_GAP_'+sys.argv[1]+'.json',r)
