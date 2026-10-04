from run import *
b=p.LoadBoard(str(D/'restore89.kicad_pcb'));base=json.load(open(D/'baseline_copper.json'));ret=[]
for t in list(b.GetTracks()):
 if t.GetNetname()=='ADC_2' and t.m_Uuid.AsString() not in base:ret.append(t);b.Remove(t)
p.SaveBoard(str(D/'reset_adc.kicad_pcb'),b)
