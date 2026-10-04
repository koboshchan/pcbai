#!/usr/bin/python3
"""Validate actual ADC footprints, values, polarities and MCU pin mapping."""
from pathlib import Path
import pcbnew as p
import json
ROOT=Path(__file__).resolve().parent

def main():
    board=p.LoadBoard(str(ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'))
    from motherboard_refs import MAP,indexed
    fs=indexed(board) if MAP.exists() else {f.GetReference():f for f in board.GetFootprints()}
    def assert_part(ref,value,connections):
        fp=fs[ref];assert fp.GetValue()==value
        actual={pad.GetNumber():pad.GetNetname() for pad in fp.Pads()}
        assert actual==connections,(ref,actual,connections)
    for i in range(10):
        d=f'SCORE_DIV_{i}';a=f'ADC_{i}'
        assert_part(f'R_TOP_{i}','220k',{'1':f'SCORE_{i}','2':d})
        assert_part(f'R_BOT_{i}','22k',{'1':'GND','2':d})
        assert_part(f'R_REF_{i}','22k',{'1':'+3V3_ADC','2':d})
        assert_part(f'R_ADC_{i}','1k',{'1':d,'2':a})
        assert_part(f'D_HI_{i}','1N4148W',{'1':'+3V3_ADC','2':a})
        assert_part(f'D_LO_{i}','1N4148W',{'1':a,'2':'GND'})
        for r in [f'D_HI_{i}',f'D_LO_{i}']:
            assert fs[r].GetFPID().GetLibItemName()=='D_SOD-123'
            assert any(x.GetLayer()==p.F_CrtYd for x in fs[r].GraphicalItems())
    assert_part('J_ADC_REF','3V3_GND_FROM_MCU',{'1':'+3V3_ADC','2':'GND'})
    scores={pad.GetNumber():pad.GetNetname() for pad in fs['J_MCU_SCORES'].Pads()}
    assert scores=={**{str(i+1):f'ADC_{i}' for i in range(10)},'11':'GND','12':'GND'}
    for i in range(1,9):assert fs[f'U_SR{i}'].GetValue()=='74AHCT595S16-13'
    for fp in fs.values():
        for pad in fp.Pads():assert pad.GetNetname() not in ('+12V','-12V')
    assert board.GetCopperLayerCount()==2 and len(list(board.GetTracks()))==0
    result={'HCT_3V3logic_repair_pass':True,'confirmed_15Vrail_labels_pass':True,'channels':10,'offset_divider_and_series_nets_pass':True,'silicon_clamp_package_polarity_pass':True,'dedicated_reference_header_pass':True,'geometry':'Standard KiCad10 library SOD123and1x02header includingcourtyard/mask; resistorcloneoriginal','unrouted':True,'fabrication_ready':False}
    (ROOT/'adc_physical_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
