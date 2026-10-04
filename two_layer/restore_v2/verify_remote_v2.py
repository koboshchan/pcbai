#!/usr/bin/python3
"""Read-only remote proof, input snapshot, strict placement DRC."""
from pathlib import Path
import hashlib,json,subprocess
import pcbnew as p
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
ROOT=Path(__file__).resolve().parent;H=ROOT.parent;R=H.parent
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
 kickoff=json.loads((ROOT/'kickoff_sha256.json').read_text());actual={name:sha(R/name) for name in kickoff if (R/name).exists()};frozen={name:sha(R/name) for name in kickoff if name.endswith('.kicad_pcb') and ('daughtercard' in name or '/' not in name)}
 assert all(kickoff[name]==digest for name,digest in frozen.items()),'Daughter/root drift against kickoff'
 (ROOT/'remote_authority_snapshot_v2.json').write_text(json.dumps({'current_authority_sha256':actual,'frozen_daughter_root_sha256':frozen,'historical_orphan_changes':{n:{'kickoff':kickoff[n],'current':s} for n,s in actual.items() if kickoff[n]!=s}},indent=2)+'\n')
 audit=json.loads((ROOT/'prepared_audit_v2.json').read_text());board=ROOT/'restored_shortrefs_v2.kicad_pcb';assert sha(board)==audit['candidate_sha256'];b=p.LoadBoard(str(board));assert json.loads(json.dumps(refs.physical(b)))==audit['physical_identity'] and silk.audit(b)['clean']
 drc=ROOT/'remote_placement_drc_v2.json';subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(drc),str(board)],check=True);d=json.loads(drc.read_text());assert not any(v.get('severity')=='error' for v in d['violations'])
 print(json.dumps({'remote_identity_verified':True,'silk_clean':True,'errors':0,'unconnected':len(d['unconnected_items']),'immutable_daughter_root_count':len(frozen)}),flush=True)
if __name__=='__main__':main()
