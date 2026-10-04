#!/usr/bin/python3
"""Route restored hybrid geometry. Never use or promote Economic checkpoints."""
from pathlib import Path
import collections, hashlib, importlib.util, json, os, signal, subprocess, time
import pcbnew as p
import route_repaired as route
import silk_refs
from restore_manual_motherboard import frozen_files
ROOT=Path(__file__).resolve().parent
RUN=ROOT/'restored_hybrid_route_run'
SOURCE=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('archived_route_proofs',ROOT/'backups/retired_economic_long_route/economic_motherboard_long_route.py')
proofs=importlib.util.module_from_spec(spec);spec.loader.exec_module(proofs);proofs.RUN=RUN
# Actual text geometry, as used for the restoration search.
_rect=silk_refs.rect
def glyph_rect(item):
    if isinstance(item,p.PCB_FIELD):
        bb=item.GetEffectiveTextShape().BBox()
        return tuple(p.ToMM(v) for v in (bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()))
    return _rect(item)
silk_refs.rect=glyph_rect

def main():
    signal.signal(signal.SIGHUP,signal.SIG_IGN)
    RUN.mkdir(exist_ok=True)
    restoration=json.loads((ROOT/'manual_motherboard_restoration.json').read_text())
    assert restoration['placements_exactly_restored'] and restoration['placement_errors']==0 and restoration['silk']['clean']
    assert restoration['economic_exporter_active'] and sha(SOURCE)==restoration['pcb_sha256']
    frozen=frozen_files();b=p.LoadBoard(str(SOURCE));original=proofs.freeze(b);identity=route.checksum(b)
    assert b.GetCopperLayerCount()==2 and not list(b.GetTracks())
    # Edge bounding boxes include the .15 mm drawing stroke. Check the actual contour coordinates.
    edges=[g for g in b.GetDrawings() if g.GetLayer()==p.Edge_Cuts]
    xs=[p.ToMM(q.x) for g in edges for q in (g.GetStart(),g.GetEnd())];ys=[p.ToMM(q.y) for g in edges for q in (g.GetStart(),g.GetEnd())]
    assert max(xs)-min(xs)==100 and max(ys)-min(ys)==100
    import motherboard_refs as refs
    fps=refs.indexed(b)
    assert sha(refs.MAP)==restoration['reference_mapping_sha256']
    assert all(fps[f'{prefix}{i}'].GetLayer()==p.F_Cu for prefix in ('U_SR','C_SR') for i in range(1,9))
    pro=json.loads(SOURCE.with_suffix('.kicad_pro').read_text());rules=pro['board']['design_settings']['rules']
    assert rules['min_clearance']>=.2 and rules['min_track_width']>=.2 and rules['min_via_diameter']>=.6 and rules['min_through_hole_diameter']>=.3
    assert not pro['board']['design_settings'].get('drc_exclusions',[])
    dsn=RUN/'fresh48.dsn';ses=RUN/'fresh48.ses';candidate=RUN/'fresh48.kicad_pcb'
    assert not ses.exists() and not candidate.exists(),'Candidate path already exists'
    proof=proofs.export_proof(b,dsn);assert proof['source_segments']==0 and proof['source_vias']==0
    jar=Path('/tmp/freerouting_actual48.jar');assert sha(jar)=='19d06499ff6424368d4861c2ede43849944d9cb62bf673cae7f5039ee6620c6d'
    start=time.time();result={'source_sha256':sha(SOURCE),'resume_proof':proof,'router_sha256':sha(jar),'actual_pass_limit':48,'release_authorized':False,'pid':os.getpid(),'frozen_files':frozen}
    (RUN/'started.json').write_text(json.dumps(result,indent=2)+'\n')
    try:
        subprocess.run(['java','-Xmx10g','-jar',str(jar),'-de',str(dsn),'-do',str(ses),'--gui.enabled=false','-mt','1'],timeout=21600,check=True)
        assert ses.exists() and ses.stat().st_size>100 and p.ImportSpecctraSES(b,str(ses))
        assert identity==route.checksum(b) and original==proofs.freeze(b)
        for t in b.GetTracks():
            if isinstance(t,p.PCB_VIA):assert t.GetWidth(p.F_Cu)>=p.FromMM(.6) and t.GetDrillValue()>=p.FromMM(.3)
            else:assert t.GetWidth()>=p.FromMM(.2) and t.GetLayer() in (p.F_Cu,p.B_Cu)
        p.SaveBoard(str(candidate),b);candidate.with_suffix('.kicad_pro').write_text(SOURCE.with_suffix('.kicad_pro').read_text())
        drc=RUN/'fresh48_drc.json'
        q=subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','-o',str(drc),str(candidate)],capture_output=True,text=True)
        (RUN/'fresh48_drc.log').write_text(q.stdout+q.stderr)
        d=json.loads(drc.read_text());reloaded=p.LoadBoard(str(candidate))
        assert original==proofs.freeze(reloaded) and identity==route.checksum(reloaded) and frozen==frozen_files() and sha(SOURCE)==result['source_sha256']
        from hybrid_silk import audit_silk
        silk=audit_silk(reloaded);assert silk['clean'],silk
        result.update(pipeline_completed=True,errors=sum(v.get('severity')=='error' for v in d['violations']),unconnected=len(d.get('unconnected_items',[])),warnings=sum(v.get('severity')=='warning' for v in d['violations']),categories=dict(collections.Counter(v['type'] for v in d['violations'])),silk=silk,candidate_sha256=sha(candidate),frozen_identity_verified=True)
    except Exception as e:
        result.update(pipeline_completed=False,error=repr(e));raise
    finally:
        result['seconds']=time.time()-start;(RUN/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
