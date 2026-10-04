#!/usr/bin/python3
"""DC3-only reproducible spacing candidate; no published writes."""
import sys,json,hashlib,shutil,datetime,re
from pathlib import Path
import pcbnew as p
from route_repaired import electrical,checksum
import silk_refs
from silk_refs import apply_silk

def drawing_adapter(board,source):
    # KiCad10 Debian lacks DRAWINGS iteration. Resolve actual serialized
    # top-level drawing UUIDs instead, never omit decorative silk silently.
    blocks=re.findall(r'\n\t\((gr_[^\n]+.*?\n\t\))',source,re.S)
    ids=[]
    for block in blocks:
        match=re.search(r'\(uuid "([^"]+)"\)',block)
        assert match,'Drawing UUID missing'
        ids.append(match.group(1))
    result=[]
    for uid in ids:
        ptr=p.Cast_to_PCB_SHAPE(board.ResolveItem(p.KIID(uid)))
        if not hasattr(ptr,'GetLayer'):
            obj=p.PCB_SHAPE.__new__(p.PCB_SHAPE);obj.this=ptr;obj.thisown=False
            ptr=obj
        result.append(ptr)
    return result
ROOT=Path(__file__).resolve().parent
NAME='daughtercard3_weights_l2_wta_differential_repaired'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fixed(b):
    f=next(f for f in b.GetFootprints() if f.GetReference()=='J_STRADDLE_EDGE')
    return [(a.GetNumber(),a.GetPosition().x,a.GetPosition().y,a.GetSize().x,a.GetSize().y,a.GetShape(),a.GetLayerSet().FmtBin()) for a in f.Pads()]
def main():
    src=ROOT/(NAME+'.kicad_pcb');pro=src.with_suffix('.kicad_pro')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=ROOT/'backups'/('DC3_before_spacing_'+stamp);backup.mkdir(parents=True)
    for f in (src,pro):shutil.copy2(f,backup/f.name)
    work=ROOT/'dc3_spacing_candidate';work.mkdir(exist_ok=True)
    board=p.LoadBoard(str(src));before=checksum(board);header=fixed(board)
    roots={f.name:sha(f) for f in ROOT.parent.glob('*.kicad_pcb')}
    moves=[]
    for f in board.GetFootprints():
        m=re.fullmatch(r'R2_(7|8|9)_(\d+)',f.GetReference())
        if m:
            col,row=map(int,m.groups());old=[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)]
            new=[85+(col-7)*5,20+row*6]
            f.SetPosition(p.VECTOR2I(p.FromMM(new[0]),p.FromMM(new[1])))
            moves.append({'reference':f.GetReference(),'before_mm':old,'after_mm':new})
    assert checksum(board)==before and fixed(board)==header
    # All nets share the relocated weight matrix. Full DC3 reroute avoids
    # dangling disconnected remnants and preserves other five boards entirely.
    for t in list(board.GetTracks()):board.Delete(t)
    drawings=drawing_adapter(board,src.read_text())
    silk_refs.board_drawings=lambda b: drawings
    audit=apply_silk(board)
    target=work/'dc3.kicad_pcb';p.SaveBoard(str(target),board)
    project=json.loads(pro.read_text());ds=project['board']['design_settings'];ds['drc_exclusions']=[]
    target.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
    shutil.copy2(target,work/'dc3_unrouted.kicad_pcb');shutil.copy2(target.with_suffix('.kicad_pro'),work/'dc3_unrouted.kicad_pro')
    report={'backup':str(backup),'published_sha256':sha(src),'electrical_hash':before,'frozen_header':header,'root_original_sha256':roots,'moves':moves,'silk':audit,'release_ready':False,'routing_scope':'Full DC3 only, shared matrix nets; unaffected boards untouched'}
    (work/'placement.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'unplaced':audit['unplaced'],'clean':audit['clean'],'moved':len(moves),'backup':str(backup)}),flush=True)
    if audit['unplaced'] or not audit['clean']:return
    assert p.ExportSpecctraDSN(board,str(work/'dc3.dsn'))
def finish():
    import subprocess,collections
    work=ROOT/'dc3_spacing_candidate';target=work/'dc3.kicad_pcb'
    meta=json.loads((work/'placement.json').read_text())
    if len(sys.argv)>1 and sys.argv[1]=='finish_stitched':
        board=p.LoadBoard(str(target));assert (work/'stitch_pass.json').exists()
    else:
        board=p.LoadBoard(str(work/'dc3_unrouted.kicad_pcb'))
        assert p.ImportSpecctraSES(board,str(work/'dc3.ses'))
    assert checksum(board)==meta['electrical_hash']
    assert fixed(board)==[tuple(x) for x in meta['frozen_header']]
    assert board.GetCopperLayerCount()==2
    drawings=drawing_adapter(board,(work/'dc3_unrouted.kicad_pcb').read_text())
    silk_refs.board_drawings=lambda b:drawings
    silk=silk_refs.audit_silk(board);assert silk['clean']
    p.SaveBoard(str(target),board)
    subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','--output',str(work/'final_drc.json'),str(target)],check=False)
    drc=json.loads((work/'final_drc.json').read_text());counts=collections.Counter(x['type'] for x in drc['violations'])
    errors=sum(x['severity']=='error' for x in drc['violations']);opens=len(drc['unconnected_items'])
    passed=errors==0 and opens==0 and counts['silk_overlap']==0 and counts['silk_over_copper']==0
    final={'errors':errors,'unconnected':opens,'categories':dict(counts),'silk':silk,'passed':passed,'release_ready':False,'routed_sha256':sha(target),'electrical_hash':checksum(board),'header_identical':True}
    (work/'final.json').write_text(json.dumps(final,indent=2)+'\n');print(json.dumps(final,indent=2))
    assert all(sha(ROOT.parent/name)==h for name,h in meta['root_original_sha256'].items())
    assert sha(ROOT/(NAME+'.kicad_pcb'))==meta['published_sha256'],'Published source changed during route'
    if not passed:return
    # Stage sibling file and replace only this DC3 board after passing gates.
    for name,source in ((NAME+'.kicad_pcb',target),(NAME+'_unrouted.kicad_pcb',work/'dc3_unrouted.kicad_pcb')):
        dest=ROOT/name;tmp=dest.with_suffix('.spacing.tmp');shutil.copy2(source,tmp);tmp.replace(dest)
    for suffix,source in (('_drc.json','final_drc.json'),('_spacing_audit.json','final.json'),('_silk.json','placement.json')):
        if suffix=='_silk.json':
            (ROOT/(NAME+suffix)).write_text(json.dumps(meta['silk'],indent=2)+'\n')
        else:shutil.copy2(work/source,ROOT/(NAME+suffix))
    print('PROMOTED_DC3_ONLY',flush=True)
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1].startswith('finish'):finish()
    else:main()
