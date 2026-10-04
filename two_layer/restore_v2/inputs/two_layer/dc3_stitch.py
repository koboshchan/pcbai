#!/usr/bin/python3
"""Strictly gated remaining DC3 single-open stitching; no publication writes."""
from pathlib import Path
import pcbnew as p,json,subprocess,math
ROOT=Path(__file__).resolve().parent/'dc3_spacing_candidate'
source=ROOT/'dc3.kicad_pcb';b=p.LoadBoard(str(source))
net='POS_L2_6';start=(18.25,53.25)
ends=set()
for t in b.GetTracks():
    if t.GetNetname()==net:
        for pt in (t.GetStart(),t.GetEnd()):ends.add((p.ToMM(pt.x),p.ToMM(pt.y)))
ends=sorted(ends,key=lambda q:math.dist(start,q))
def pt(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
code=next(f.GetNetCode() for fp in b.GetFootprints() for f in fp.Pads() if f.GetNetname()==net)
for end in ends:
    if math.dist(start,end)<.1:continue
    for layer in (p.F_Cu,p.B_Cu):
        for bend in (None,(start[0],end[1]),(end[0],start[1])):
            board=p.LoadBoard(str(source));points=[start,end] if bend is None else [start,bend,end]
            for a,z in zip(points,points[1:]):
                if a==z:continue
                t=p.PCB_TRACK(board);t.SetStart(pt(a));t.SetEnd(pt(z));t.SetWidth(p.FromMM(.2));t.SetLayer(layer);t.SetNetCode(code);board.Add(t)
            if layer==p.B_Cu:
                for pos in (start,end):
                    v=p.PCB_VIA(board);v.SetPosition(pt(pos));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(code);board.Add(v)
            target=ROOT/'stitch.kicad_pcb';p.SaveBoard(str(target),board)
            target.with_suffix('.kicad_pro').write_text(source.with_suffix('.kicad_pro').read_text())
            subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','--output',str(ROOT/'stitch_drc.json'),str(target)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            d=json.loads((ROOT/'stitch_drc.json').read_text());errors=[x for x in d['violations'] if x['severity']=='error'];opens=d['unconnected_items']
            print(end,layer,bend,len(errors),len(opens),flush=True)
            if not errors and not opens:
                source.write_bytes(target.read_bytes());(ROOT/'stitch_pass.json').write_text(json.dumps({'start':start,'end':end,'layer':layer,'bend':bend,'errors':0,'unconnected':0},indent=2));raise SystemExit(0)
raise SystemExit('No strict clean stitch found')
