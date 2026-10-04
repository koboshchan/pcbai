#!/usr/bin/python3
"""Independent saved-file geometry invariants for relocated DC3."""
import json,hashlib
from pathlib import Path
import pcbnew as p
from route_repaired import checksum
from silk_refs import audit_silk
from dc3_spacing import drawing_adapter,fixed,NAME,ROOT
import silk_refs
work=ROOT/'dc3_spacing_candidate';meta=json.loads((work/'placement.json').read_text())
a=p.LoadBoard(str(Path(meta['backup'])/(NAME+'.kicad_pcb')));b=p.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
def snapshot(board):
    result={}
    for f in board.GetFootprints():
        pos=f.GetPosition()
        result[f.GetReference()]={'position':(pos.x,pos.y),'angle':f.GetOrientationDegrees(),'layer':f.GetLayer(),'value':f.GetValue(),'pads':sorted((x.GetNumber(),x.GetPosition().x-pos.x,x.GetPosition().y-pos.y,x.GetSize().x,x.GetSize().y,x.GetDrillSize().x,x.GetDrillSize().y,x.GetShape(),x.GetAttribute(),x.GetLayerSet().FmtBin(),x.GetNetname(),x.GetOrientationDegrees()) for x in f.Pads())}
    return result
old,new=snapshot(a),snapshot(b);moves={m['reference']:m for m in meta['moves']};issues=[]
for ref,before in old.items():
    after=new[ref]
    if {k:v for k,v in before.items() if k!='position'}!={k:v for k,v in after.items() if k!='position'}:issues.append([ref,'nonplacement_geometry_changed'])
    if ref not in moves and before['position']!=after['position']:issues.append([ref,'unapproved_move'])
    if ref in moves and after['position']!=tuple(p.FromMM(x) for x in moves[ref]['after_mm']):issues.append([ref,'incorrect_target'])
assert set(old)==set(new)
assert fixed(a)==fixed(b) and checksum(a)==checksum(b)
# Exact top-level outline serialization invariant.
import re
def outlines(path):return re.findall(r'\n\t\(gr_[^\n]+.*?\n\t\)',path.read_text(),re.S)
assert outlines(Path(meta['backup'])/(NAME+'.kicad_pcb'))==outlines(ROOT/(NAME+'.kicad_pcb'))
drawings=drawing_adapter(b,(ROOT/(NAME+'.kicad_pcb')).read_text());silk_refs.board_drawings=lambda board:drawings
silk=audit_silk(b);assert silk['clean']
assert all(hashlib.sha256((ROOT.parent/n).read_bytes()).hexdigest()==h for n,h in meta['root_original_sha256'].items())
result={'passed':not issues,'issues':issues,'components':len(new),'moved':len(moves),'header_exact':True,'pad_shapes_sizes_drills_localpositions_layers_nets_identical':True,'outline_exact':True,'electrical_identical':True,'two_copper_layers':b.GetCopperLayerCount()==2,'root_originals_unchanged':True,'saved_file_silk':silk,'fabrication_ready':False}
(work/'geometry_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert not issues
