#!/usr/bin/python3
"""Isolated buffered precision-rectifier repair, generated on kat-box only.
No root sources are changed. This is an unrouted prototype, never fab output.
"""
from pathlib import Path
import json
import pcbnew as p
from repair_adc import net, configure, clone, mm
from repair_signed import clean, setpads, CHANNELS
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent


def build():
    board=p.LoadBoard(str(SOURCE/'daughtercard2_relu_l1.kicad_pcb'))
    clean(board)
    parts={f.GetReference():f for f in board.GetFootprints()}
    diode=p.FootprintLoad('/usr/share/kicad/footprints/Diode_SMD.pretty','D_SOD-123')
    assert diode is not None
    cap=parts['C_U1P']
    amp=parts['U1']
    changes=[]
    for i in range(16):
        # Feedback stays on raw RECT, not buffered ACT. Header ACT is unchanged.
        for pad in parts[f'R_FB_{i}'].Pads():
            if pad.GetNetname()==f'ACT_{i}':pad.SetNet(net(board,f'RECT_{i}'))
        parts[f'R_FB_{i}'].SetValue('10k')
        parts[f'R_IN_{i}'].SetValue('10k')
        for kind,padnets in [('RECT',{'1':f'RECT_{i}','2':f'OP_OUT_{i}'}),('CLAMP',{'1':f'OP_OUT_{i}','2':f'INV_RELU_{i}'})]:
            old=parts[f'D_{kind}_{i}']
            xy=old.GetPosition()
            angle=old.GetOrientationDegrees()
            clone(board,diode,old.GetReference(),'1N4148W',p.ToMM(xy.x),p.ToMM(xy.y),padnets).SetOrientationDegrees(angle)
            board.Delete(old)
        changes.append({'channel':i,'raw':f'RECT_{i}','buffered':f'ACT_{i}','input_ohm':10000,'feedback_ohm':10000,'resistor_tolerance':.01,'diodes':'1N4148W SOD123'})
    # Provisional compact row below existing circuitry; placement/clearance is
    # intentionally not asserted until integrated routing and DRC are complete.
    for chip in range(4):
        ref=f'U_BUF{chip+1}'
        fp=p.Cast_to_FOOTPRINT(amp.Duplicate(False))
        x,y=13+chip*24,80
        configure(fp,ref,'TL074',x,y)
        assignment={'4':'+15V','11':'-15V'}
        for pins,i in zip(CHANNELS,range(chip*4,chip*4+4)):
            assignment.update(dict(zip(pins,[f'ACT_{i}',f'ACT_{i}',f'RECT_{i}'])))
        setpads(board,fp,assignment);board.Add(fp)
        clone(board,cap,f'C_{ref}P','0.1uF',x-6,y-7,{'1':'+15V','2':'GND'})
        clone(board,cap,f'C_{ref}N','0.1uF',x+6,y-7,{'1':'-15V','2':'GND'})
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() in ('+12V','-12V'):
                pad.SetNet(net(board,pad.GetNetname().replace('12V','15V')))
    path=ROOT/'daughtercard2_relu_l1_buffered_repaired_unrouted.kicad_pcb'
    p.SaveBoard(str(path),board)
    actual=p.LoadBoard(str(path))
    audit(actual)
    result={'status':'unrouted prototype, no DRC or fabrication release','board':str(path),'channels':changes,'added_opamps':16,'added_TL074':4,'rails':'+/-15V','root_untouched':True}
    (ROOT/'relu_repair_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


def audit(board):
    fps={fp.GetReference():fp for fp in board.GetFootprints()}
    assert len(fps)==91,len(fps)
    def pads(ref):return {pad.GetNumber():pad.GetNetname() for pad in fps[ref].Pads()}
    for i in range(16):
        assert set(pads(f'R_FB_{i}').values())=={f'RECT_{i}',f'INV_RELU_{i}'}
        assert set(pads(f'R_IN_{i}').values())=={f'V_SUM_{i}',f'INV_RELU_{i}'}
        assert pads(f'D_RECT_{i}')=={'1':f'RECT_{i}','2':f'OP_OUT_{i}'}
        assert pads(f'D_CLAMP_{i}')=={'1':f'OP_OUT_{i}','2':f'INV_RELU_{i}'}
        chip=i//4;out,minus,plus=CHANNELS[i%4];q=pads(f'U_BUF{chip+1}')
        assert q[out]==q[minus]==f'ACT_{i}' and q[plus]==f'RECT_{i}'
        assert q['4']=='+15V' and q['11']=='-15V'
        assert pads('J_STRADDLE_EDGE')[f'B{i+1}']==f'ACT_{i}'
    for fp in fps.values():
        for pad in fp.Pads():assert pad.GetNetname() not in ('+12V','-12V')
    assert board.GetCopperLayerCount()==2
    assert len(list(board.GetTracks()))==len(list(board.Zones()))==0

if __name__=='__main__':build()
