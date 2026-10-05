"""Metadata-only migration. Electrical resistor manifest remains byte-identical."""
import json
from pathlib import Path
H=Path(__file__).resolve().parent
for name in ['circuit.json','trained_circuit.json']:
 p=H/name;d=json.loads(p.read_text());old_layers=json.dumps([d['layer1'],d['layer2']],sort_keys=True)
 def replace(v):
  if isinstance(v,str):return v.replace('74HCT595D','74AHCT595D').replace('74HCT595','74AHCT595').replace('HCT595','AHCT595') if 'AHCT595' not in v else v
  if isinstance(v,list):return [replace(x) for x in v]
  if isinstance(v,dict):return {k:replace(x) for k,x in v.items()}
  return v
 d=replace(d);d['input']='64 grayscale6bit Nexperia74AHCT595D SO16 C554704 BCM PWM outputs with10k/1uF RC;3.3V logic input'
 d['shared_5V_rail']={'source':'onboard L7805CV TO220 C111887, +15V to +5V linear regulator','range_V':[4.75,5.25],'loads':['AHCT595 VCC/PWM high','all +5V_REF bias resistors in both layers'],'sensitivity':'commonrail_sensitivity.json','nominal_driver_ohms_assumption':50,'not_hardware_qualification':True}
 assert json.dumps([d['layer1'],d['layer2']],sort_keys=True)==old_layers
 p.write_text(json.dumps(d,indent=2)+'\n')
p=H/'metrics.json';d=json.loads(p.read_text());mc=json.loads((H/'cuda_mc.json').read_text());d['mc']={k:mc[k] for k in ['board_realizations','examples_each','seed','min','mean','max','std','p05']};d['mc'].update(status='completed historical nominal5V fixed50ohm driver CUDA1000',source='cuda_mc.json',rail_driver_corner_MC='not performed');d['commonrail_sensitivity']='commonrail_sensitivity.json';p.write_text(json.dumps(d,indent=2)+'\n')
p=H/'RESULT.md';s=p.read_text().replace('74HCT595','74AHCT595').replace('HCT sourceimpedance','AHCT sourceimpedance');p.write_text(s)
