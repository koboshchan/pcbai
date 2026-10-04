#!/usr/bin/python3
"""Recess exposed solder lands from routed edge without moving straddle header.
This is not a card-edge finger/socket conversion. Connector fit requires checking
actual purchased straddle header pin reach against the0.4mm land setback.
"""
from pathlib import Path
import argparse,json
import pcbnew as p
from route_repaired import checksum
from repair_adc import mm
ROOT=Path(__file__).resolve().parent

def apply(path):
    path=Path(path);board=p.LoadBoard(str(path));identity=checksum(board)
    header=next(fp for fp in board.GetFootprints() if fp.GetReference()=='J_STRADDLE_EDGE')
    assert abs(p.ToMM(header.GetPosition().y)-100)<1e-6
    records=[]
    for pad in header.Pads():
        assert pad.GetShape() in (p.PAD_SHAPE_RECT,p.PAD_SHAPE_ROUNDRECT)
        pos=pad.GetPosition();size=pad.GetSize()
        oldmax=p.ToMM(pos.y+size.y//2);oldmin=p.ToMM(pos.y-size.y//2)
        # Preserve inward land end and pin pitch. Move only the cut-facing end.
        # Accept original lands or prior0.5mm recess and preserve their inward end.
        if abs(oldmax-99.6)<1e-6:continue
        assert any(abs(oldmax-x)<1e-6 for x in [100,99.5]),(pad.GetNumber(),oldmax)
        newmax=99.6
        newsize=mm(newmax-oldmin)
        pad.SetSize(p.VECTOR2I(size.x,newsize))
        pad.SetPosition(p.VECTOR2I(pos.x,mm((newmax+oldmin)/2)))
        records.append({'pad':pad.GetNumber(),'inner_y_mm':oldmin,'old_tip_mm':oldmax,'new_tip_mm':newmax,'land_height_mm':p.ToMM(newsize)})
    assert checksum(board)==identity
    p.SaveBoard(str(path),board)
    reloaded=p.LoadBoard(str(path));assert checksum(reloaded)==identity
    report={'board':str(path),'modified_lands':len(records),'edge_setback_mm':.4,'electrical_identity_unchanged':True,'header_position_unchanged':True,'mechanical_pin_reach_requires_validation':True,'lands':records}
    path.with_name(path.stem+'_straddle_recess.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='lands'}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('boards',nargs='+');args=parser.parse_args()
    for path in args.boards:apply(path)
