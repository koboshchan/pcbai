#!/usr/bin/python3
"""Independently reconstruct model's physical resistor terminals and validate PCB.
Run with kat-box KiCad10. Audits optional routed boards without modifying any CAD.
"""
from pathlib import Path
import argparse,json,hashlib,math
import pcbnew as p
H=Path(__file__).resolve().parent
CH=[('1','2','3'),('7','6','5'),('8','9','10'),('14','13','12')]
def resistance(text):
 text=text.strip();factor=1
 if text[-1].lower() in ('k','m'):factor={'k':1000,'m':1e6}[text[-1].lower()];text=text[:-1]
 return float(text)*factor

def audit(routed=False):
 model=json.loads((H/'fixed_model/circuit.json').read_text());boards={};all_errors=[]
 originals=json.loads((H/'audit_original_manifest.json').read_text())
 for name,v in originals.items():
  path=H.parent/(name+'.kicad_pcb');assert hashlib.sha256(path.read_bytes()).hexdigest()==v['file_sha256'],('root original changed',name)
 for layer,groups in [(1,[range(i*4,i*4+4) for i in range(4)]),(2,[range(10)])]:
  for group in groups:
   name='daughtercard1'+chr(97+group[0]//4)+'_weights_l1' if layer==1 else 'daughtercard3_weights_l2_wta'
   suffix='_differential_repaired.kicad_pcb' if routed else '_differential_repaired_unrouted.kicad_pcb'
   path=H/(name+suffix);b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()};errors=[];desired={};channels=[]
   def fail(check,message):
    if not check:errors.append(message)
   fail(len(fs)==len(list(b.GetFootprints())),'duplicate references')
   def pads(ref):return {x.GetNumber():x.GetNetname() for x in fs[ref].Pads()}
   for j in group:
    row=model['layer'+str(layer)][j];pos=f'POS_N{j}' if layer==1 else f'POS_L2_{j}';inv=f'INV_N{j}' if layer==1 else f'INV_L2_{j}';out=f'V_SUM_{j}' if layer==1 else f'SCORE_{j}'
    for e in row['inputs']:
     if e['source']=='input':ref=f'R1_{e["index"]}_{j%4}' if layer==1 else f'R2_{e["index"]}_{j}';source=f'IN_{e["index"]}' if layer==1 else f'ACT_{e["index"]}'
     else:ref=f'Rb_N{j}' if layer==1 else f'Rb_L2_{j}';source='+5V_REF'
     desired[ref]=(e['ohms'],{'1':source,'2':pos if e['leg']=='positive' else inv})
    desired[f'Rf_N{j}' if layer==1 else f'Rf_L2_{j}']=(row['rf_ohms'],{'1':inv,'2':out})
    if row['balance']:
     bal=row['balance'];desired[f'R_BAL_{layer}_{j}']=(bal['ohms'],{'1':pos if bal['leg']=='positive' else inv,'2':'GND'})
    matches=[]
    for ref,f in fs.items():
     if f.GetValue()=='TL074':
      q=pads(ref)
      for o,n,s in CH:
       if q.get(n)==inv:
        matches.append((ref,o,n,s));fail(q.get(o)==out and q.get(s)==pos,f'{ref} channel{j} opamp terminals');fail(q.get('4')=='+15V' and q.get('11')=='-15V',f'{ref} rails')
    fail(len(matches)==1,f'neuron{j} channel count {len(matches)}');channels.extend(matches)
   for ref,(r,terminals) in desired.items():
    if ref not in fs:errors.append(f'missing {ref}');continue
    fail(pads(ref)==terminals,f'{ref} pad nets differ');fail(math.isclose(resistance(fs[ref].GetValue()),r,rel_tol=1e-9),f'{ref} resistance differs')
   for ref in fs:
    if ref.startswith(('R1_','R2_','Rf_','Rb_','R_BAL_')):fail(ref in desired,f'undeclared extra resistor {ref}')
    fail(not ref.startswith(('D_WTA','D_LED','R_LED')),f'obsolete direct score load {ref}')
    for pad in fs[ref].Pads():fail(pad.GetNetname() not in ('+12V','-12V','-5V_REF'),f'{ref} obsolete power net {pad.GetNetname()}') if not ref.startswith('J_STRADDLE') else None
   fail(b.GetCopperLayerCount()==2,'copper layers !=2')
   source_header=next(f for f in originals[name]['footprints'] if f['reference']=='J_STRADDLE_EDGE')
   fail(pads('J_STRADDLE_EDGE')=={x['number']:x['net'].replace('+12V','+15V').replace('-12V','-15V') for x in source_header['pads']},'76pin straddle pinmap changed')
   boards[name]={'pcb':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'neural_resistors':len(desired),'neuron_channels':len(channels),'errors':errors,'model_pad_agreement':not errors}
   all_errors.extend((name,e) for e in errors)
 result={'source_model_sha256':hashlib.sha256((H/'fixed_model/circuit.json').read_bytes()).hexdigest(),'routed':routed,'root_originals_unchanged':True,'boards':boards,'all_neural_pad_maps_match':not all_errors,'fabrication_ready':False,'limitations':'Only physical weighted amplifier topology and resistor values; routing/DRC, ReLU/motherboard power, dynamic opamp limits and assembly parts require separate gates.'}
 path=H/('final_model_routed_audit.json' if routed else 'final_model_unrouted_audit.json');path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='boards'},indent=2))
 if all_errors:raise AssertionError(all_errors)
 return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--routed',action='store_true');audit(a.parse_args().routed)
