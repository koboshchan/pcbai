#!/usr/bin/python3
"""Idempotent grayscale/power integration onto placed repaired motherboard.
Run only with remote KiCad10 system Python. No routing or original edits.
"""
from pathlib import Path
import json,re,subprocess
import pcbnew as p
ROOT=Path(__file__).resolve().parent
PCB=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def net(b,n):
 if n not in b.GetNetsByName():b.Add(p.NETINFO_ITEM(b,n))
 return b.GetNetsByName()[n]
def pads(f):return {q.GetNumber():q.GetNetname() for q in f.Pads()}
def main():
 b=p.LoadBoard(str(PCB));assert b.GetCopperLayerCount()==2 and not list(b.GetTracks())
 old={f.GetReference():f for f in b.GetFootprints()}
 slots={r:(pads(f),f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees()) for r,f in old.items() if r.startswith('J_SLOT')}
 adc={r:pads(f) for r,f in old.items() if r.startswith(('R_TOP_','R_BOT_','R_REF_','R_ADC_','D_HI_','D_LO_'))}
 for f in list(b.GetFootprints()):
  if f.GetReference().startswith(('R_PWM_','C_PWM_','C_BULK_','C_RAIL_')) or f.GetReference() in ('J_PWR_IN','J_REF_IN','R_PWR5'):b.Delete(f)
 def add(lib,item,ref,value,x,y,nets,bottom=False,properties=None):
  f=p.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty',item);assert f is not None
  f.SetUuid(p.KIID());f.SetReference(ref);f.SetValue(value);f.Value().SetVisible(False)
  f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
  b.Add(f)
  if bottom:f.Flip(f.GetPosition(),False)
  for q in f.Pads():q.SetNet(net(b,nets[q.GetNumber()]))
  if ref in ('J_PWR_IN','J_REF_IN'):f.SetOrientationDegrees(90)
  if properties:f.SetLibDescription(f.GetLibDescription()+'; '+json.dumps(properties,sort_keys=True))
  return f
 mapping=[]
 for f in b.GetFootprints():
  if f.GetReference().startswith('U_SR'):
   assert f.GetValue() in ('74HCT595D','74AHCT595D','74AHCT595S16-13')
   f.SetValue('74AHCT595S16-13')
   f.SetLibDescription('Diodes 74AHCT595S16-13; SOIC-16; LCSC C126402; JLC assembled; 5V supply, TTL-compatible 3.3V MCU inputs')
   for q in f.Pads():
    m=re.fullmatch(r'(?:RAW_)?IN_(\d+)',q.GetNetname())
    if m:
     i=int(m.group(1));q.SetNet(net(b,f'RAW_IN_{i}'));mapping.append({'pixel':i,'driver':f.GetReference(),'driver_pad':q.GetNumber()})
 assert sorted(x['pixel'] for x in mapping)==list(range(64))
 for i in range(64):
  x=8+5.5*(i%16);y=36.8+11*(i//16)
  add('Resistor_SMD','R_0805_2012Metric',f'R_PWM_{i}','10k',x,y,{'1':f'RAW_IN_{i}','2':f'IN_{i}'},True,{'Tolerance':'5%'})
  add('Capacitor_SMD','C_0805_2012Metric',f'C_PWM_{i}','1uF',x,y+2.2,{'1':f'IN_{i}','2':'GND'},True,{'Voltage':'50V','Dielectric':'X7R','Tolerance':'10%','Note':'Effective capacitance under DC bias must be qualified'})
 add('Connector_PinHeader_2.54mm','PinHeader_1x03_P2.54mm_Vertical','J_PWR_IN','+15V_GND_-15V',72,96,{'1':'+15V','2':'GND','3':'-15V'})
 add('Connector_PinHeader_2.54mm','PinHeader_1x02_P2.54mm_Vertical','J_REF_IN','EXTERNAL_ACCURATE_5V_REF',57,95,{'1':'+5V_REF','2':'GND'})
 for suffix,x,ns in [('P',8,{'1':'+15V','2':'GND'}),('N',92,{'1':'GND','2':'-15V'})]:
  add('Capacitor_SMD','CP_Elec_8x10',f'C_BULK_{suffix}','100uF',x,17 if suffix=='P' else 23,ns,True,{'Voltage':'50V','MPN':'EEE-FK1H101P','Tolerance':'20%','Source':'https://rmscomponents.com.au/shop/passive-components/capacitors/100uf-50v-20-105c-8x10-2mm-smd-electrolytic-capacitor-panasonic-eee-fk-series'})
  add('Capacitor_SMD','C_0805_2012Metric',f'C_RAIL_{suffix}','0.1uF',x if suffix=='P' else 84,25,ns,True,{'Voltage':'50V','Dielectric':'X7R'})
 for f in b.GetFootprints():
  if f.GetReference().startswith('C_SR'):f.SetLibDescription('Logic decoupling capacitor, Voltage=50V, X7R')
 now={f.GetReference():f for f in b.GetFootprints()}
 assert slots=={r:(pads(now[r]),now[r].GetPosition().x,now[r].GetPosition().y,now[r].GetOrientationDegrees()) for r in slots}
 assert adc=={r:pads(now[r]) for r in adc}
 assert pads(now['J_MCU_SPI'])['1']=='+5V' and 'R_PWR5' not in now
 p.SaveBoard(str(PCB),b);b=p.LoadBoard(str(PCB));now={f.GetReference():f for f in b.GetFootprints()}
 for item in mapping:
  i=item['pixel'];assert pads(now[item['driver']])[item['driver_pad']]==f'RAW_IN_{i}'
  assert pads(now[f'R_PWM_{i}'])=={'1':f'RAW_IN_{i}','2':f'IN_{i}'}
  assert pads(now[f'C_PWM_{i}'])=={'1':f'IN_{i}','2':'GND'}
 assert pads(now['J_PWR_IN'])=={'1':'+15V','2':'GND','3':'-15V'}
 assert pads(now['C_BULK_N'])=={'1':'GND','2':'-15V'}
 assert pads(now['C_BULK_P'])=={'1':'+15V','2':'GND'}
 drc=ROOT/'motherboard_final_placement_drc.json'
 subprocess.run(['kicad-cli','pcb','drc','--format','json','--all-track-errors','-o',str(drc),str(PCB)],check=True)
 d=json.loads(drc.read_text());errors=[v for v in d['violations'] if v.get('severity')=='error'];counts={}
 for v in d['violations']:counts[v['type']]=counts.get(v['type'],0)+1
 report={'board':PCB.name,'pad_net_audit_passed':True,'slot_bus_and_positions_preserved':True,'adc_preserved':True,'filters':sorted(mapping,key=lambda x:x['pixel']),'filter_resistance_ohm':10000,'filter_capacitance_F':1e-6,'filter_resistor_tolerance':0.05,'filter_capacitor_nominal_tolerance':0.1,'capacitor_dc_bias_qualification_pending':True,'input_source_model_note':'10k filter plus actual driver source impedance; no buffers','power_input':pads(now['J_PWR_IN']),'reference_input':pads(now['J_REF_IN']),'logic_5V':'External J_MCU_SPI pin1; no connection to +5V_REF','negative_reference':'Backplane preserved but not sourced; final model must not use','bulk_caps':{'positive':pads(now['C_BULK_P']),'negative':pads(now['C_BULK_N']),'value':'100uF50V','footprint':'CP_Elec_8x10','mpn':'EEE-FK1H101P'},'drc_counts':counts,'drc_error_count':len(errors),'unconnected_count':len(d.get('unconnected_items',[])),'fabrication_ready':False}
 (ROOT/'motherboard_final_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='filters'}));assert not errors,'Placement DRC errors, inspect report'
if __name__=='__main__':main()
