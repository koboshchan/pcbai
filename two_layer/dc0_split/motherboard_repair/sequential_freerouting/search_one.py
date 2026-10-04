from scoped_search import *
b=p.LoadBoard(str(D/'repath_start.kicad_pcb'));print(type(b),flush=True);r=plan(b,'ADC_2','JAD','3');write('REPATH_ADC_2.json',r)
