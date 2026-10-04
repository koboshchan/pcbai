import scoped_search as a
from run import *
a.step=.08;a.N=1251
b=p.LoadBoard(str(D/'repath.kicad_pcb'));v=json.load(open(D/'repath_drc.json'))['unconnected_items'][0];allitems=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];pair=[next(t for t in allitems if t.m_Uuid.AsString()==it['uuid']) for it in v['items']];r=a.plan(b,'ADC_2',pair=pair);r['pair']=v['items'];write('LAST_ADC_PATH.json',r)
