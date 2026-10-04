#!/usr/bin/env python3
"""Inspect original emulator, weights and KiCad manifest without changing originals."""
from pathlib import Path
import importlib.util,json,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'two_layer'
raw=json.loads((OUT/'audit_original_manifest.json').read_text())
spec=importlib.util.spec_from_file_location('original_emulator',ROOT/'emulate_pcb_hardware.py');emu=importlib.util.module_from_spec(spec);spec.loader.exec_module(emu)
result={'python':sys.executable,'dataset_exists':(ROOT/'mnist_cache/mnist_8x8_test.npz').exists(),'negative_weight_examples':[],'parser_differences':[],'adc_dividers':[]}
for name,m in raw.items():
    parsed={f['reference']:f for f in emu.parse_kicad_pcb_footprints(ROOT/(name+'.kicad_pcb'))}
    for f in m['footprints']:
        expected={p['number']:p['net'] for p in f['pads'] if p['number']}
        observed=parsed.get(f['reference'],{}).get('pads',{})
        # Empty pad nets are omitted by emulator; retain them separately.
        differences={n:{'pcbnew':net,'emulator':observed.get(n)} for n,net in expected.items() if net and net!=observed.get(n)}
        extras={n:net for n,net in observed.items() if n not in expected}
        if differences or extras:result['parser_differences'].append({'board':name,'reference':f['reference'],'differences':differences,'extra_pads':extras})
for layer in [1,2]:
    weights=json.loads((ROOT/f'weights_layer{layer}.json').read_text())
    count=0; examples=[]
    for neuron in weights['weights']:
        for inp in neuron['inputs']:
            if inp['polarity']=='negative' and inp['is_populated']:
                count+=1
                if layer==1:
                    n=inp['neuron_idx'];board=f'daughtercard1{"abcd"[n//4]}_weights_l1';ref=f'R1_{inp["input_idx"]}_{n%4}'
                else:
                    board='daughtercard3_weights_l2_wta';ref=f'R2_{inp["hidden_idx"]}_{inp["class_idx"]}'
                f=next((f for f in raw[board]['footprints'] if f['reference']==ref),None)
                if len(examples)<5:examples.append({'board':board,'reference':ref,'weight':inp,'footprint':f})
    result[f'layer{layer}_populated_negative_count']=count;result['negative_weight_examples']+=examples
mb={f['reference']:f for f in raw['motherboard']['footprints']}
for c in range(10):
    top=mb[f'R_TOP_{c}'];bot=mb[f'R_BOT_{c}'];rt=emu.parse_resistor_value_ohms(top['value']);rb=emu.parse_resistor_value_ohms(bot['value']);ratio=rb/(rt+rb)
    result['adc_dividers'].append({'class':c,'top':top,'bottom':bot,'ratio':ratio,'raw_at_plus10_5V':ratio*10.5,'raw_at_minus10_5V':ratio*-10.5})
proc=subprocess.run([sys.executable,str(ROOT/'emulate_pcb_hardware.py'),'--benchmark'],text=True,capture_output=True)
result['benchmark']={'command':[sys.executable,str(ROOT/'emulate_pcb_hardware.py'),'--benchmark'],'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}
(OUT/'audit_emulator_findings.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
