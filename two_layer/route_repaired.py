#!/usr/bin/python3
"""Route explicit repaired candidates, never infer them from root originals.
Run ONLY on kat-box after authoritative trained/netlist manifest is finalized.
No fabrication exports for provisional, incomplete, or failing candidates.
"""
from pathlib import Path
import argparse,collections,json,subprocess,hashlib,re
import pcbnew as p
from repair_adc import mm
ROOT=Path(__file__).resolve().parent

def electrical(board):
    return sorted((f.GetReference(),f.GetValue(),sorted((a.GetNumber(),a.GetNetname()) for a in f.Pads())) for f in board.GetFootprints())

def checksum(board):
    return hashlib.sha256(json.dumps(electrical(board)).encode()).hexdigest()

def prepare(path):
    path=Path(path).resolve()
    assert path.parent==ROOT and path.name.endswith('_repaired_unrouted.kicad_pcb'), 'Final repaired input naming required'
    board=p.LoadBoard(str(path)); assert board.GetCopperLayerCount()==2
    assert len(list(board.GetTracks()))==0,'Candidate must be unrouted'
    stem=path.name.replace('_repaired_unrouted.kicad_pcb','')
    source_stem=stem
    for suffix in ('_adc','_differential','_buffered'):
        if source_stem.endswith(suffix):source_stem=source_stem[:-len(suffix)]
    source_project=ROOT.parent/(source_stem+'.kicad_pro')
    project=json.loads(source_project.read_text())
    ds=project['board']['design_settings'];ds['drc_exclusions']=[]
    ds['rules'].update(min_clearance=.2,min_track_width=.2,min_via_diameter=.6,min_through_hole_diameter=.3,min_via_annular_width=.15,min_copper_edge_clearance=.3,min_silk_clearance=.15,min_text_height=.8,min_text_thickness=.12)
    project['net_settings']['classes'][0].update(clearance=.2,track_width=.25,via_diameter=.6,via_drill=.3)
    path.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
    dsn=ROOT/(stem+'_repaired.dsn')
    assert p.ExportSpecctraDSN(board,str(dsn))
    text=dsn.read_text()
    # Routing rules only. Never rewrite component pad geometry or every 'width'.
    text=re.sub(r'(\(rule\s*\(width\s+)[\d.]+',r'\g<1>250',text)
    text=re.sub(r'(\(clearance\s+)[\d.]+',r'\g<1>200',text)
    dsn.write_text(text)
    manifest={'candidate':path.name,'identity_hash':checksum(board),'physical_components':electrical(board),'root_original_unmodified':True,'provisional':True,'release_authorized':False}
    (ROOT/(stem+'_repaired_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    return dsn

def finish(path,ses):
    path=Path(path).resolve();board=p.LoadBoard(str(path));expected=checksum(board)
    assert p.ImportSpecctraSES(board,str(ses)),'No usable session import'
    assert checksum(board)==expected,'Router changed physical nets/components'
    assert board.GetCopperLayerCount()==2
    for item in board.GetTracks():
        if isinstance(item,p.PCB_VIA):
            assert item.GetWidth()>=mm(.6) and item.GetDrillValue()>=mm(.3)
        else:
            assert item.GetLayer() in [p.F_Cu,p.B_Cu] and item.GetWidth()>=mm(.2)
    # Keep initial copper checkpoint prior to optional silkscreen helper.
    stem=path.name.replace('_repaired_unrouted.kicad_pcb','')
    checkpoint=ROOT/(stem+'_repaired_routed_copper.kicad_pcb')
    p.SaveBoard(str(checkpoint),board)
    from silk_refs import apply_silk
    silk=apply_silk(board)
    assert checksum(board)==expected,'Silk stage changed physical nets/components'
    audit=ROOT/(stem+'_repaired_silk.json');audit.write_text(json.dumps(silk,indent=2)+'\n')
    # B.Cu GND plane will be added only once board-specific connector clearance
    # and ground pour geometry are verified; no blindly hardcoded100mm polygon.
    target=ROOT/(stem+'_repaired.kicad_pcb');p.SaveBoard(str(target),board)
    reloaded=p.LoadBoard(str(target));assert checksum(reloaded)==expected
    pro=path.with_suffix('.kicad_pro');target.with_suffix('.kicad_pro').write_text(pro.read_text())
    report=ROOT/(stem+'_repaired_drc.json')
    result=subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','--output',str(report),str(target)],capture_output=True,text=True)
    target.with_suffix('.drc.log').write_text(result.stdout+result.stderr)
    assert report.exists(),'DRC failed without output'
    data=json.loads(report.read_text())
    errors=sum(x.get('severity')=='error' for x in data.get('violations',[]))
    unconnected=len(data.get('unconnected_items',[]))
    # A zero/zero route is necessary, not sufficient: provisional identity,
    # model/CAD agreement, silk, layer/edge/mechanical gates still block release.
    summary={'candidate':target.name,'errors':errors,'unconnected':unconnected,'warnings':sum(x.get('severity')=='warning' for x in data.get('violations',[])),'categories':dict(collections.Counter(x['type'] for x in data.get('violations',[]))),'silk':silk,'release_ready':False,'reason':'Pending authoritative trained netlist/model agreement and mechanical/silk validation'}
    (ROOT/(stem+'_repaired_status.json')).write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','finish']);parser.add_argument('board');parser.add_argument('--ses');args=parser.parse_args()
    if args.action=='prepare':print(prepare(args.board))
    else:
        assert args.ses
        finish(args.board,args.ses)
