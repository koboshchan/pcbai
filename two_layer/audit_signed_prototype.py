#!/usr/bin/python3
"""Check physical sign path, amp pins and resistor nets in prototypes."""
from pathlib import Path
import json
import pcbnew as p
ROOT=Path(__file__).resolve().parent
CH=[('1','2','3'),('7','6','5'),('8','9','10'),('14','13','12')]
def pads(f):return {x.GetNumber():x.GetNetname() for x in f.Pads()}
def check():
    count=0
    for layer,letters in [(1,'abcd'),(2,'x')]:
        raw=json.loads((ROOT.parent/f'weights_layer{layer}.json').read_text())
        for c,letter in enumerate(letters):
            name=f'daughtercard1{letter}_weights_l1' if layer==1 else 'daughtercard3_weights_l2_wta'
            b=p.LoadBoard(str(ROOT/(name+'_signed_prototype_unrouted.kicad_pcb')))
            fs={f.GetReference():f for f in b.GetFootprints()}
            assert b.GetCopperLayerCount()==2 and len(list(b.GetTracks()))==0
            for rec in raw['weights']:
                n=rec['neuron_idx' if layer==1 else 'class_idx']
                if layer==1 and n//4!=c:continue
                group=f'NEG_INV_{n}' if layer==1 else f'POS_INV_{n}'
                inv=f'INV_N{n}' if layer==1 else f'INV_L2_{n}'
                gout=f'NEG_GROUP_{n}' if layer==1 else f'POS_GROUP_{n}'
                for w in rec['inputs']:
                    i=w['input_idx' if layer==1 else 'hidden_idx']
                    ref=f'R1_{i}_{n%4}' if layer==1 else f'R2_{i}_{n}'
                    assert ref in fs,ref
                    indirect=w['polarity']==('negative' if layer==1 else 'positive')
                    assert pads(fs[ref])=={'1':f'IN_{i}' if layer==1 else f'ACT_{i}','2':group if indirect else inv},ref
                    count+=1
                assert set(pads(fs[f'R_SIGN_FB_{n}']).values())=={gout,group}
                assert set(pads(fs[f'R_SIGN_IN_{n}']).values())=={gout,inv}
                amp='U_SIGN' if layer==1 else f'U_SIGN{n//4+1}'
                out,minus,plus=CH[n%4]
                pa=pads(fs[amp]);assert [pa[out],pa[minus],pa[plus]]==[gout,group,'GND']
                assert pa['4']=='+12V' and pa['11']=='-12V'
            for f in fs.values():
                if f.GetValue()=='TL074':
                    pa=pads(f)
                    for out,_,_ in CH:assert pa[out] not in ['GND','+12V','-12V'],(name,f.GetReference(),out)
    report={'tested_populated_weight_paths':count,'correct_physical_sign_groups':True,'two_layer_unrouted_prototypes':5,'saturation_loading_accuracy_not_validated':True,'fabrication_ready':False}
    (ROOT/'signed_prototype_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':check()
