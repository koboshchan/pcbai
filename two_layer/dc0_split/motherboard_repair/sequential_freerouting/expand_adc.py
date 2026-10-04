from run import *
b=p.LoadBoard(str(D/'local_adc.kicad_pcb'));rep=json.load(open(D/'swap_adc_drc.json'));baseline=json.load(open(D/'baseline_copper.json'));ids={it['uuid'] for v in rep['violations'] if v['severity']=='error' for it in v['items'] if it['uuid'] in baseline};ret=[];changes={}
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ids:changes[t.m_Uuid.AsString()]=baseline[t.m_Uuid.AsString()];ret.append(t);b.Remove(t)
write('EXPANDED_LOCAL_BLOCKERS.json',{'evidence_report':'swap_adc_drc.json','reason':'exact crossing/short clearance obstruction of scoped ADC two-layer corridor; only five evidenced original segments released','released_items':changes});p.SaveBoard(str(D/'expanded_adc.kicad_pcb'),b)
