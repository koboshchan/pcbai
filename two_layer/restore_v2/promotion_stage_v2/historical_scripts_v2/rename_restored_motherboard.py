#!/usr/bin/python3
"""Apply approved reversible reference-only rename to restored hybrid CAD."""
from pathlib import Path
import collections,hashlib,json,shutil,subprocess,math
import pcbnew as p
import silk_refs as s
import motherboard_refs as refs
from restore_manual_motherboard import frozen_files
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    prior=json.loads((ROOT/'manual_motherboard_restoration.json').read_text())
    assert sha(SOURCE)==prior['pcb_sha256'] and prior['placement_errors']==0
    backup=ROOT/'backups/restored_hybrid_longrefs_52e39b4';backup.mkdir(exist_ok=True)
    for name in (SOURCE.name,SOURCE.with_suffix('.kicad_pro').name,'manual_motherboard_restoration.json','manual_motherboard_placement_drc.json'):
        src=ROOT/name;dst=backup/name
        if dst.exists():assert sha(src)==sha(dst),'Immutable historical backup conflict'
        else:shutil.copy2(src,dst)
    frozen=frozen_files();b=p.LoadBoard(str(SOURCE));physical=refs.physical(b);assert not list(b.GetTracks())
    record=refs.rename(b);original=s.candidates
    def local_candidates(fp,ref,layer,height):
        for angle,x,y in original(fp,ref,layer,height):
            if math.dist((x,y),(p.ToMM(fp.GetPosition().x),p.ToMM(fp.GetPosition().y)))<=4.01:yield angle,x,y
    s.candidates=local_candidates
    silk=s.apply_silk(b);assert silk['clean'] and not silk['unplaced'],silk['unplaced']
    assert refs.physical(b)==physical
    association=[dict(reference=f.GetReference(),old_reference=refs.role(f),distance_mm=math.dist((p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)),(p.ToMM(f.Reference().GetPosition().x),p.ToMM(f.Reference().GetPosition().y)))) for f in b.GetFootprints()]
    assert max(x['distance_mm'] for x in association)<=4.01
    p.SaveBoard(str(SOURCE),b);reload=p.LoadBoard(str(SOURCE));assert refs.physical(reload)==physical and s.audit_silk(reload)['clean']
    drc=ROOT/'renamed_motherboard_placement_drc.json';subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(drc),str(SOURCE)],check=True)
    d=json.loads(drc.read_text());errors=sum(v.get('severity')=='error' for v in d['violations']);assert errors==0
    result=dict(prior);result.update(reference_mapping_sha256=sha(refs.MAP),reference_count=record['complete_reference_count'],component_uuid_pad_net_geometry_preserved=True,physical_identity_sha256=record['physical_identity_sha256'],silk=silk,association=association,placement_errors=errors,unconnected=len(d['unconnected_items']),pcb_sha256=sha(SOURCE),economic_exporter_active=True)
    assert frozen==frozen_files();(ROOT/'renamed_motherboard_restoration.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('reference_count','placement_errors','unconnected','pcb_sha256','component_uuid_pad_net_geometry_preserved')}),flush=True)
if __name__=='__main__':main()
