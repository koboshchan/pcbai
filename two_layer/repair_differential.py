#!/usr/bin/python3
"""Generate physical differential summers from a worker circuit snapshot.
Run on kat-box only. Source originals untouched. No routing/export/accuracy claim.
"""
from pathlib import Path
import argparse, json, hashlib
import pcbnew as p
from repair_adc import clone, net
from repair_signed import clean, setpads, CHANNELS
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent

def value(r):
    return f'{r/1e6:g}M' if r>=1e6 else f'{r/1000:g}k' if r>=1000 else f'{r:g}'

def build(model):
    raw=Path(model).read_bytes();circuit=json.loads(raw)
    modelhash=hashlib.sha256(raw).hexdigest()
    records={}
    for layer,groups in [(1,[list(range(c*4,c*4+4)) for c in range(4)]),(2,[list(range(10))])]:
        for group in groups:
            name=f'daughtercard1{chr(97+group[0]//4)}_weights_l1' if layer==1 else 'daughtercard3_weights_l2_wta'
            board=p.LoadBoard(str(SOURCE/(name+'.kicad_pcb')));clean(board)
            parts={f.GetReference():f for f in board.GetFootprints()}
            resistor=next(f for ref,f in parts.items() if ref.startswith('Rf'))
            desired={}; opampmap={}
            if layer==2:
                for ref,fp in list(parts.items()):
                    if ref.startswith(('D_WTA_','D_LED_','R_LED_')) or ref=='R_WTA':
                        board.Delete(fp)
                        del parts[ref]
            for j in group:
                row=circuit[f'layer{layer}'][j]
                assert row['neuron']==j
                pos=f'POS_N{j}' if layer==1 else f'POS_L2_{j}'
                inv=f'INV_N{j}' if layer==1 else f'INV_L2_{j}'
                out=f'V_SUM_{j}' if layer==1 else f'SCORE_{j}'
                rf=f'Rf_N{j}' if layer==1 else f'Rf_L2_{j}'
                rb=f'Rb_N{j}' if layer==1 else f'Rb_L2_{j}'
                for e in row['inputs']:
                    i=e['index'];ref=f'R1_{i}_{j%4}' if layer==1 else f'R2_{i}_{j}'
                    src=f'IN_{i}' if layer==1 else f'ACT_{i}'
                    if e['source']!='input':ref=rb;src='+5V_REF'
                    assert ref not in desired
                    desired[ref]={'ohms':e['ohms'],'tolerance':e['tolerance'],'pads':{'1':src,'2':pos if e['leg']=='positive' else inv}}
                desired[rf]={'ohms':row['rf_ohms'],'tolerance':row['rf_tolerance'],'pads':{'1':inv,'2':out}}
                if row['balance']:
                    bal=row['balance'];desired[f'R_BAL_{layer}_{j}']={'ohms':bal['ohms'],'tolerance':bal['tolerance'],'pads':{'1':pos if bal['leg']=='positive' else inv,'2':'GND'}}
                # Find the actual channel, not a guessed global channel index.
                matches=[]
                for fp in parts.values():
                    if fp.GetValue()!='TL074':continue
                    q={pad.GetNumber():pad.GetNetname() for pad in fp.Pads()}
                    for output,minus,plus in CHANNELS:
                        if q[minus]==inv:
                            for pad in fp.Pads():
                                if pad.GetNumber()==plus:pad.SetNet(net(board,pos))
                            matches.append({'ref':fp.GetReference(),'output':output,'minus':minus,'plus':plus,'nets':[out,inv,pos]})
                assert len(matches)==1,(name,j,matches)
                opampmap[str(j)]=matches[0]
            # Remove omitted zero coefficients and old biases; never parallel feedback.
            for ref,fp in parts.items():
                if ref.startswith(('R1_','R2_','Rb_','Rf_')) and ref not in desired:board.Delete(fp)
            for index,(ref,entry) in enumerate(desired.items()):
                fp=parts.get(ref)
                if fp is None:
                    # Only newly populated coefficients/balances use staging row.
                    fp=clone(board,resistor,ref,value(entry['ohms']),7+(index%15)*6,84+(index//15%3)*4,entry['pads'])
                else:fp.SetValue(value(entry['ohms']));setpads(board,fp,entry['pads'])
                fp.SetLibDescription(f"Physical differential model; tolerance {entry['tolerance']:g}; model SHA256 {modelhash}")
            # Unused amplifier units require unity feedback, not grounded outputs.
            for fp in board.GetFootprints():
                if fp.GetReference().startswith('C'):
                    properties=dict(fp.GetProperties());properties['Voltage Rating']='50V';fp.SetProperties(properties)
                if fp.GetValue()=='TL074':
                    q={pad.GetNumber():pad.GetNetname() for pad in fp.Pads()}
                    for output,minus,plus in CHANNELS:
                        if q[output]=='GND' and q[minus]=='GND':
                            nc=f'NC_{fp.GetReference()}_{output}'
                            for pad in fp.Pads():
                                if pad.GetNumber() in (output,minus):pad.SetNet(net(board,nc))
                for pad in fp.Pads():
                    if pad.GetNetname() in ('+12V','-12V'):pad.SetNet(net(board,pad.GetNetname().replace('12V','15V')))
            target=ROOT/(name+'_differential_repaired_unrouted.kicad_pcb')
            p.SaveBoard(str(target),board)
            reloaded=p.LoadBoard(str(target));actual={f.GetReference():f for f in reloaded.GetFootprints()}
            assert len(actual)==len(list(reloaded.GetFootprints())), 'Duplicate references'
            for ref,entry in desired.items():
                assert {pad.GetNumber():pad.GetNetname() for pad in actual[ref].Pads()}==entry['pads'],ref
                assert actual[ref].GetValue()==value(entry['ohms'])
            for channel in opampmap.values():
                q={pad.GetNumber():pad.GetNetname() for pad in actual[channel['ref']].Pads()}
                assert [q[channel[k]] for k in ('output','minus','plus')]==channel['nets']
            records[name]={'board':str(target),'model_sha256':modelhash,'provisional':True,'model_status':circuit.get('status'),'components':desired,'channels':opampmap}
    (ROOT/'differential_repair_manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps({name:{'model_status':v['model_status'],'components':len(v['components']),'channels':len(v['channels'])} for name,v in records.items()},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--model',default=str(ROOT/'fixed_model/circuit.json'));args=parser.parse_args();build(args.model)
