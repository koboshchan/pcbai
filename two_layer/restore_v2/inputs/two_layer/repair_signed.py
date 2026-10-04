#!/usr/bin/python3
"""Physical local signed-group inverter prototype, all board editing on kat-box.
Uses existing quantized JSON only to exercise topology, NOT final trained values.
L1 negative weights first invert, finalSUM is negative desired preactivation.
L2 positive weights first invert, finalSCORE is positive desired score.
Intermediate saturation and output loading require hardware-aware retraining.
"""
from pathlib import Path
import json
import pcbnew as p
from repair_adc import net,clone,mm,configure
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent
CHANNELS=[('1','2','3'),('7','6','5'),('8','9','10'),('14','13','12')]

def setpads(board,fp,assign):
    for pad in fp.Pads():
        pad.SetNet(net(board,assign.get(pad.GetNumber(),'')))

def clean(board):
    for t in list(board.GetTracks()):board.Delete(t)
    for z in list(board.Zones()):board.Delete(z)
    board.SetCopperLayerCount(2)

def amplifier(board,template,ref,x,y,channels):
    fp=p.Cast_to_FOOTPRINT(template.Duplicate(False))
    configure(fp,ref,'TL074',x,y)
    assign={'4':'+12V','11':'-12V'}
    for pins,cs in zip(CHANNELS,channels):
        out,minus,plus=pins
        if cs is None:
            # Stable unity follower with GND input; NEVER tie output to ground.
            assign.update({out:f'NC_{ref}_{out}',minus:f'NC_{ref}_{out}',plus:'GND'})
        else:assign.update(dict(zip(pins,cs)))
    setpads(board,fp,assign);board.Add(fp)
    cap=next(f for f in board.GetFootprints() if f.GetReference().startswith('C_U') and f.GetValue()=='0.1uF')
    clone(board,cap,f'C_{ref}P','0.1uF',x-6,y-7,{'1':'+12V','2':'GND'})
    clone(board,cap,f'C_{ref}N','0.1uF',x+6,y-7,{'1':'-12V','2':'GND'})
    return fp

def l1():
    weights=json.loads((SOURCE/'weights_layer1.json').read_text())
    records={x['neuron_idx']:x for x in weights['weights']}
    audits={}
    for c,letter in enumerate('abcd'):
        name=f'daughtercard1{letter}_weights_l1'
        board=p.LoadBoard(str(SOURCE/(name+'.kicad_pcb')));clean(board)
        parts={f.GetReference():f for f in board.GetFootprints()}
        resistor=next(f for f in parts.values() if f.GetReference().startswith('Rf'))
        ic=parts['U1']
        amplifier(board,ic,'U_SIGN',75,65,[(f'NEG_GROUP_{n}',f'NEG_INV_{n}','GND') for n in range(c*4,c*4+4)])
        for k,n in enumerate(range(c*4,c*4+4)):
            bias=parts[f'Rb_N{n}']
            setpads(board,bias,{'1':f'INV_N{n}','2':'+5V_REF' if records[n]['bias_float']>=0 else '-5V_REF'})
            # Scale only first group, restore by final group resistor ratio.
            clone(board,resistor,f'R_SIGN_FB_{n}','1.2k',69,55+k*5,{'1':f'NEG_GROUP_{n}','2':f'NEG_INV_{n}'})
            clone(board,resistor,f'R_SIGN_IN_{n}','1.2k',81,55+k*5,{'1':f'NEG_GROUP_{n}','2':f'INV_N{n}'})
            for w in records[n]['inputs']:
                f=parts[f"R1_{w['input_idx']}_{n%4}"]
                setpads(board,f,{'1':f"IN_{w['input_idx']}",'2':f'NEG_INV_{n}' if w['polarity']=='negative' else f'INV_N{n}'})
        path=ROOT/(name+'_signed_prototype_unrouted.kicad_pcb')
        p.SaveBoard(str(path),board);p.LoadBoard(str(path))
        audits[name]={'prototype':str(path),'first_feedback_ohms':1200,'final_group_ohms':1200,'not_final_trained':True,'channels':[c*4+i for i in range(4)]}
    return audits

def l2():
    name='daughtercard3_weights_l2_wta'
    weights=json.loads((SOURCE/'weights_layer2.json').read_text())
    board=p.LoadBoard(str(SOURCE/(name+'.kicad_pcb')));clean(board)
    parts={f.GetReference():f for f in board.GetFootprints()}
    resistor=next(f for f in parts.values() if f.GetReference().startswith('Rf'))
    for chip in range(3):
        amplifier(board,parts['U1'],f'U_SIGN{chip+1}',14+chip*24,80,[(f'POS_GROUP_{n}',f'POS_INV_{n}','GND') if n<10 else None for n in range(chip*4,chip*4+4)])
    # Original unused U3 channels improperly short output toGND; correct.
    for pad in parts['U3'].Pads():
        if pad.GetNumber() in ['8','9']:pad.SetNet(net(board,'NC_U3_8'))
        if pad.GetNumber() in ['13','14']:pad.SetNet(net(board,'NC_U3_14'))
    for rec in weights['weights']:
        n=rec['class_idx']
        clone(board,resistor,f'R_SIGN_FB_{n}','1.2k',8+n*9,67,{'1':f'POS_GROUP_{n}','2':f'POS_INV_{n}'})
        clone(board,resistor,f'R_SIGN_IN_{n}','1.2k',8+n*9,71,{'1':f'POS_GROUP_{n}','2':f'INV_L2_{n}'})
        for w in rec['inputs']:
            f=parts.get(f"R2_{w['hidden_idx']}_{n}")
            if f is None:continue
            setpads(board,f,{'1':f"ACT_{w['hidden_idx']}",'2':f'POS_INV_{n}' if w['polarity']=='positive' else f'INV_L2_{n}'})
    path=ROOT/(name+'_signed_prototype_unrouted.kicad_pcb')
    p.SaveBoard(str(path),board);p.LoadBoard(str(path))
    return {name:{'prototype':str(path),'first_feedback_ohms':1200,'final_group_ohms':1200,'not_final_trained':True,'channels':list(range(10))}}

def main():
    audits=l1();audits.update(l2())
    (ROOT/'signed_prototype_manifest.json').write_text(json.dumps(audits,indent=2)+'\n')
    print(json.dumps(audits,indent=2))
if __name__=='__main__':main()
