"""Export exact unchanged-connectivity resistor netlist, stock map and old/new values."""
import collections,copy,csv,hashlib,json,math
from pathlib import Path
H=Path(__file__).resolve().parent;T=H.parent;OLD=T/'fixed_model'
parts=json.loads((H/'basic_catalog.json').read_text())['parts'];byvalue={p['ohms']:p for p in parts};values=sorted(byvalue)
def nearest(v):
 if v==0:return 0.
 return min((x for x in values if x>0),key=lambda x:abs(math.log(x/v)))
def number(v):return float(v.rstrip('RkM'))*(1000 if v.endswith('k') else 1e6 if v.endswith('M') else 1)
def refs(c):
 d={}
 for l in [1,2]:
  for row in c['layer'+str(l)]:
   j=row['neuron'];b='daughtercard1'+chr(97+j//4)+'_weights_l1' if l==1 else 'daughtercard3_weights_l2_wta'
   for e in row['inputs']:
    i=e['index'];r=(f'R1_{i}_{j%4}' if l==1 else f'R2_{i}_{j}') if e['source']=='input' else (f'Rb_N{j}' if l==1 else f'Rb_L2_{j}');d[(b,r)]=e['ohms']
   d[(b,f'Rf_N{j}' if l==1 else f'Rf_L2_{j}')]=row['rf_ohms'];d[(b,f'R_BAL_{l}_{j}')]=row['balance']['ohms']
 return d
if __name__=='__main__':
 old=json.loads((OLD/'circuit.json').read_text());new=json.loads((H/'circuit.json').read_text());a=refs(old);b=refs(new);assert a.keys()==b.keys()
 net=copy.deepcopy(json.loads((OLD/'desired_netlist.json').read_text()))
 for board,items in net.items():
  for e in items:
   if 'ohms' in e:e['ohms']=b[(board,e['ref'])]
 original=copy.deepcopy(net)
 # Include every non-neural resistor from current repaired manifests, without reading/writing CAD.
 motherboard=json.loads((T/'motherboard_adc_repaired_manifest.json').read_text())
 net['motherboard']=[]
 for ref,val,pads in motherboard['physical_components']:
  if not ref.startswith('R'):continue
  v=number(val);nv=nearest(v);a[('motherboard',ref)]=v;b[('motherboard',ref)]=nv;net['motherboard'].append({'ref':ref,'ohms':nv,'tolerance':.01,'pads':dict(pads)})
 m=json.loads((T/'audit_original_manifest.json').read_text());board='daughtercard2_relu_l1';net[board]=[]
 for f in m[board]['footprints']:
  ref=f['reference']
  if not ref.startswith('R'):continue
  assert ref.startswith(('R_FB_','R_IN_')),ref
  i=int(ref.split('_')[-1]);pads={p['number']:p['net'].replace(f'ACT_{i}',f'RECT_{i}') if ref.startswith('R_FB_') else p['net'] for p in f['pads']};a[(board,ref)]=10000.;b[(board,ref)]=10000.;net[board].append({'ref':ref,'ohms':10000.,'tolerance':.01,'pads':pads})
 mapping=[];changes=[];counts=collections.Counter(b.values())
 for (board,ref),v in sorted(b.items()):
  assert v in byvalue;part=byvalue[v];ov=a[(board,ref)];row={'board':board,'ref':ref,'old_ohms':ov,'new_ohms':v,'lcsc':part['lcsc'],'library':'Basic','stock':part['stock'],'footprint':'Resistor_SMD:R_0805_2012Metric','catalog_tolerance':part['tolerance']};mapping.append(row)
  if not math.isclose(v,ov,rel_tol=1e-9):changes.append(row)
 for row in mapping:assert row['stock']>=counts[row['new_ohms']]*1.1
 # Connectivity comparison excludes added coverage of pre-existing non-neural boards.
 oldnet=json.loads((OLD/'desired_netlist.json').read_text());oc=copy.deepcopy(oldnet);nc=copy.deepcopy(original)
 for d in [oc,nc]:
  for items in d.values():
   for e in items:e.pop('ohms',None)
 assert oc==nc
 (H/'desired_netlist.json').write_text(json.dumps(net,indent=2));(H/'value_map.json').write_text(json.dumps(mapping,indent=2));(H/'value_changes.json').write_text(json.dumps(changes,indent=2))
 with (H/'value_changes.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(mapping[0]));w.writeheader();w.writerows(changes)
 bom=[dict(byvalue[v],quantity=counts[v]) for v in sorted(counts)]
 (H/'basic_resistor_bom.json').write_text(json.dumps(bom,indent=2));summary={'resistor_count':len(mapping),'unique_values':len(counts),'extended_resistors':0,'changed_resistors':len(changes),'exact_original_neural_pad_connectivity_preserved':True,'original_neural_component_count':len(refs(old)),'fixed_model_circuit_sha256':hashlib.sha256((OLD/'circuit.json').read_bytes()).hexdigest(),'fee_saved_USD_user_assumption':62*3,'nonneural_change_note':'R_REG_MINLOAD820ohm is Extended. Nearest Basic680ohm draws7.353mA and36.765mW at5V, within selected125mW resistor rating; regulator thermal increase12.554mW at15Vin. No steady-state classifier transfer change assumed. Requalify rail regulation/thermal in hardware.'}
 (H/'export_audit.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
