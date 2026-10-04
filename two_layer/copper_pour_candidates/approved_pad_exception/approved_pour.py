#!/usr/bin/python3
"""Apply explicit approved straddle pad-only edge rules to isolated copies.
Requires exact reference plus a reviewed 76-pad manifest; no wildcard selection.
Original helper reused read-only. Output remains non-authoritative.
"""
import sys,json,shutil
from pathlib import Path
import pcbnew as p
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pour_ground import apply,sha,identity,drc

def rules_for(source,reference):
    b=p.LoadBoard(str(source)); fs=[f for f in b.GetFootprints() if f.GetReference()==reference]
    assert len(fs)==1
    f=fs[0]; pads=list(f.Pads()); assert len(pads)==76
    assert str(f.GetFPID().GetLibItemName())=='PinHeader_2x38_Straddle_P2.54mm'
    assert set(x.GetNumber() for x in pads)=={row+str(i) for row in 'AB' for i in range(1,39)}
    manifest={'reference':reference,'footprint_uuid':f.m_Uuid.AsString(),'library_id':str(f.GetFPID()),'pads':[]}
    text='(version 1)\n(rule "Global all copper edge 0.5mm" (constraint edge_clearance (min 0.5mm)))\n'
    for x in pads:
        number=x.GetNumber(); uid=x.m_Uuid.AsString()
        condition=f"A.Type == 'Pad' && A.memberOfFootprint('{reference}') && A.Pad_Number == '{number}'"
        text+=f'(rule "Approved straddle {number} {uid}" (condition "{condition}") (constraint edge_clearance (min 0.4mm)))\n'
        manifest['pads'].append({'number':number,'uuid':uid,'position_mm':[p.ToMM(x.GetPosition().x),p.ToMM(x.GetPosition().y)],'size_mm':[p.ToMM(x.GetSize().x),p.ToMM(x.GetSize().y)],'condition':condition,'minimum_mm':.4})
    return text,manifest

def run(name):
    root=Path(__file__).resolve().parent; previous=root.parent; folder=root/name; folder.mkdir(parents=True,exist_ok=True)
    source=previous/name/'source.kicad_pcb'; project=previous/name/'source.kicad_pro'; snapshot=folder/'source.kicad_pcb'
    original_board_sha=sha(source); original_project_sha=sha(project)
    shutil.copy2(source,snapshot); shutil.copy2(project,snapshot.with_suffix('.kicad_pro'))
    text,manifest=rules_for(snapshot,'J_STRADDLE_EDGE')
    snapshot.with_suffix('.kicad_dru').write_text(text)
    (folder/'pad_exception_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result=apply(snapshot,folder/'ground_candidate.kicad_pcb',snapshot.with_suffix('.kicad_pro'),True)
    final=p.LoadBoard(str(folder/'ground_candidate.kicad_pcb')); texts=[]
    for f in final.GetFootprints():
        for t in list(f.GetFields())+list(f.GraphicalItems()):
            if hasattr(t,'GetTextHeight') and t.GetLayer() in (p.F_SilkS,p.B_SilkS) and t.IsVisible() and t.GetText():texts.append(t)
    for t in final.GetDrawings():
        if hasattr(t,'GetTextHeight') and t.GetLayer() in (p.F_SilkS,p.B_SilkS) and t.IsVisible() and t.GetText():texts.append(t)
    result.update(board=name,silk_min_height_mm=min(p.ToMM(t.GetTextHeight()) for t in texts),silk_min_thickness_mm=min(p.ToMM(t.GetTextThickness()) for t in texts),prior_source_unchanged=sha(source)==original_board_sha,prior_project_unchanged=sha(project)==original_project_sha,project_sha256=sha(folder/'ground_candidate.kicad_pro'),rules_sha256=sha(folder/'ground_candidate.kicad_dru'))
    assert result['prior_source_unchanged'] and result['prior_project_unchanged'] and result['silk_min_height_mm']>=.8 and result['silk_min_thickness_mm']>=.12
    result['accepted']=result['errors']==0 and result['opens']==0
    return result
if __name__=='__main__':
    names=['daughtercard1'+x+'_weights_l1_differential' for x in 'abcd']+['daughtercard2_relu_l1_buffered','daughtercard3_weights_l2_wta_differential']
    results=[]; root=Path(__file__).resolve().parent
    for name in names:
        r=run(name);results.append(r);(root/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n');print(name,r['errors'],r['opens'],flush=True)
