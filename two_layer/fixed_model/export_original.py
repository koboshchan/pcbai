import sys,json,importlib.util,numpy as np
from pathlib import Path
from model import synthesize
ROOT=Path(__file__).resolve().parents[2]
# E96 canonical IEC decade sequence from root source, no import dependencies.
import ast
source=ast.parse((ROOT/'train_mnist_hardware.py').read_text())
for node in source.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='E96_BASE_VALUES' for t in node.targets):base=ast.literal_eval(node.value.args[0])
e96=np.concatenate([np.array(base)*10**d for d in range(0,8)])
layers=[]
for name in ['weights_layer1.json','weights_layer2.json']:
 d=json.loads((ROOT/name).read_text());w=[];b=[]
 for row in d['weights']:
  w.append([float(e['weight_float']) for e in row['inputs']]);b.append(float(row['bias_float']))
 layers.append((np.array(w),np.array(b)))
# Hardware original L1 is inverting and DC2 is inverting; L2 should directly represent classifier scores.
out={'status':'PROVISIONAL existing trained weights mapped to repaired topology, pending binary retraining','input':'64 binary 74HC595 outputs, commanded 0 or 5V','rf_ohms':100000,'layer1':synthesize(-layers[0][0],-layers[0][1],e96),'layer2':synthesize(layers[1][0],layers[1][1],e96),'rails':'+/-15V replacing net labels +/-12V only if supply confirmed; swing simulation +/-10V conservative','rectifier':{'rin_ohms':10000,'rf_ohms':10000,'tolerance':.01,'diodes':'1N4148W SOD123','output':'RECT_k -> unity follower -> ACT_k','additional_TL074':4},'adc':{'score_to_mid_ohms':220000,'3V3_to_mid_ohms':22000,'GND_to_mid_ohms':22000,'mid_to_adc_ohms':1000,'divider_tolerance':.01,'diodes':'1N4148W SOD123, cathode 3V3 for upper clamp, anode GND for lower clamp','requires_3V3_header':True},'remove_or_disable':['all passive WTA diodes and common bus load','direct score LEDs, optional buffers required for indicators'],'equation':'out=(1+Rf*(Gn+Gbn))*Vplus-Rf*sum(gn*x); Vplus=sum(gp*x)/(Gp+Gbp)','balance':'one E96 1% resistor from selected leg to ground; rounded mismatch included explicitly','buffer_output_model_ohms':1,'input_source_model_ohms':50,'limitations':['HC595 source resistance model is assumed not measured, test 0/50/100ohm','static ideal opamp nodal model with clipping, not SPICE transient validation','rectifier raw output cannot drive mixed-sign L2 directly while off','no analog grayscale drive provided by original HC595','no unique analog winner LED claim']}
if '--trained' in sys.argv:
 out=json.loads(Path(__file__).with_name('trained_circuit.json').read_text())
 out['status']='authoritative binary MNIST trained component model, metrics.json'
Path(__file__).with_name('circuit.json').write_text(json.dumps(out,indent=2))
np.savez(Path(__file__).with_name('original_float.npz'),w1=layers[0][0],b1=layers[0][1],w2=layers[1][0],b2=layers[1][1])
# Authoritative desired component pad net topology, local refs. Existing neuron IC pad slots from actual manifest.
m=json.loads((ROOT/'two_layer/audit_original_manifest.json').read_text());boards={}
for l,n in [(1,16),(2,10)]:
 rows=out['layer'+str(l)]
 for j,row in enumerate(rows):
  board='daughtercard1'+chr(ord('a')+j//4)+'_weights_l1' if l==1 else 'daughtercard3_weights_l2_wta'
  p='POS_N'+str(j) if l==1 else 'POS_L2_'+str(j);v='INV_N'+str(j) if l==1 else 'INV_L2_'+str(j);o='V_SUM_'+str(j) if l==1 else 'SCORE_'+str(j)
  items=boards.setdefault(board,[])
  for e in row['inputs']:
   i=e['index'];src=('IN_'+str(i) if l==1 else 'ACT_'+str(i)) if e['source']=='input' else '+5V_REF'
   ref=f'R{l}_{i}_{j}' if e['source']=='input' else f'RB{l}_{j}'
   items.append({'ref':ref,'ohms':e['ohms'],'tolerance':e['tolerance'],'pads':{'1':src,'2':p if e['leg']=='positive' else v}})
  items.append({'ref':f'RF{l}_{j}','ohms':row['rf_ohms'],'tolerance':.01,'pads':{'1':v,'2':o}})
  if row['balance']:items.append({'ref':f'RBAL{l}_{j}','ohms':row['balance']['ohms'],'tolerance':.01,'pads':{'1':p if row['balance']['leg']=='positive' else v,'2':'GND'}})
  for fp in m[board]['footprints']:
   if fp['value']=='TL074':
    pads={a['number']:a['net'] for a in fp['pads']}
    for neg,pos in [('2','3'),('6','5'),('9','10'),('13','12')]:
     if pads.get(neg)==v:items.append({'ref':fp['reference'],'patch_pads':{neg:v,pos:p}})
Path(__file__).with_name('desired_netlist.json').write_text(json.dumps(boards,indent=2))
print('exported circuit and pad netlist')
