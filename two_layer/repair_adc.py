#!/usr/bin/python3
"""Create isolated ADC offset/clamp circuit from current motherboard on kat-box.
Not fabrication output. Powered range is audited separately; silicon diodes do
not promise absolute-voltage limits or prevention of power-off rail backfeed.
"""
from pathlib import Path
import json
import pcbnew as p
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent

def layers(*ids):
    result=p.LSET()
    for item in ids: result.AddLayer(item)
    return result

def mm(x): return p.FromMM(x)
def net(board,name):
    ns=board.GetNetsByName()
    if name not in ns:
        board.Add(p.NETINFO_ITEM(board,name))
    return board.GetNetsByName()[name]
def configure(fp,ref,value,x,y):
    fp.SetReference(ref);fp.SetValue(value);fp.SetUuid(p.KIID())
    fp.SetPosition(p.VECTOR2I(mm(x),mm(y)))
    fp.SetOrientationDegrees(0)
    fp.Reference().SetVisible(True);fp.Value().SetVisible(False)
    return fp
def clone(board,template,ref,value,x,y,nets):
    fp=configure(p.Cast_to_FOOTPRINT(template.Duplicate(False)),ref,value,x,y)
    for pad in fp.Pads():
        if pad.GetNumber() in nets:pad.SetNet(net(board,nets[pad.GetNumber()]))
    board.Add(fp)
    return fp

def build():
    board=p.LoadBoard(str(SOURCE/'motherboard.kicad_pcb'))
    for t in list(board.GetTracks()):board.Delete(t)
    for z in list(board.Zones()):board.Delete(z)
    board.SetCopperLayerCount(2)
    parts={f.GetReference():f for f in board.GetFootprints()}
    rt=parts['R_TOP_0']; diode_source=p.LoadBoard(str(SOURCE/'daughtercard2_relu_l1.kicad_pcb'))
    dt=next(f for f in diode_source.GetFootprints() if f.GetReference().startswith('D'))
    # Rebuild diode geometry explicitly for known stock SOD-123 K=1,A=2.
    dt=p.FOOTPRINT(board);dt.SetLayer(p.F_Cu)
    dt.SetFPID(p.LIB_ID('Diode_SMD','D_SOD-123'))
    for n,x in [('1',-1.65),('2',1.65)]:
        pad=p.PAD(dt);pad.SetNumber(n);pad.SetAttribute(p.PAD_ATTRIB_SMD)
        pad.SetShape(p.PAD_SHAPE_RECT);pad.SetSize(p.VECTOR2I(mm(.9),mm(1.2)))
        pad.SetPosition(p.VECTOR2I(mm(x),0));pad.SetLayerSet(layers(p.F_Cu,p.F_Mask,p.F_Paste));dt.Add(pad)
    # Dedicated MCU 3.3V/GND header, not an invented existing rail.
    header=p.FOOTPRINT(board);header.SetLayer(p.F_Cu)
    configure(header,'J_ADC_REF','3V3_GND_FROM_MCU',94,15)
    for n,x,nname in [('1',0,'+3V3_ADC'),('2',2.54,'GND')]:
        pad=p.PAD(header);pad.SetNumber(n);pad.SetAttribute(p.PAD_ATTRIB_PTH)
        pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(p.VECTOR2I(mm(1.7),mm(1.7)))
        pad.SetDrillSize(p.VECTOR2I(mm(1),mm(1)))
        pad.SetPosition(p.VECTOR2I(mm(94+x),mm(15)))
        pad.SetLayerSet(p.LSET.AllCuMask());pad.SetNet(net(board,nname));header.Add(pad)
    board.Add(header)
    manifest=[]
    for i in range(10):
        x=7+i*9.4
        # Provisional placement only. Integrated routing/layout will relocate.
        top=parts[f'R_TOP_{i}'];top.SetValue('220k')
        bot=parts[f'R_BOT_{i}'];bot.SetValue('22k')
        top.SetPosition(p.VECTOR2I(mm(x),mm(8)));bot.SetPosition(p.VECTOR2I(mm(x),mm(11)))
        clone(board,rt,f'R_REF_{i}','22k',x,14,{'1':'+3V3_ADC','2':f'SCORE_DIV_{i}'})
        clone(board,rt,f'R_ADC_{i}','1k',x,17,{'1':f'SCORE_DIV_{i}','2':f'ADC_{i}'})
        clone(board,dt,f'D_HI_{i}','1N4148W',x,20,{'1':'+3V3_ADC','2':f'ADC_{i}'})
        clone(board,dt,f'D_LO_{i}','1N4148W',x,24,{'1':f'ADC_{i}','2':'GND'})
        for pad in parts['J_MCU_SCORES'].Pads():
            if pad.GetNumber()==str(i+1):pad.SetNet(net(board,f'ADC_{i}'))
        manifest.append({'channel':i,'score_series_ohm':220000,'ref_ohm':22000,'ground_ohm':22000,'adc_series_ohm':1000,'reference_net':'+3V3_ADC','adc_net':f'ADC_{i}','diodes':{'high_K':'+3V3_ADC','high_A':f'ADC_{i}','low_K':f'ADC_{i}','low_A':'GND'}})
    path=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
    p.SaveBoard(str(path),board)
    p.LoadBoard(str(path))
    (ROOT/'adc_netlist_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(path)
if __name__=='__main__':build()
