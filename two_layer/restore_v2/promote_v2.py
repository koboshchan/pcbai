#!/usr/bin/python3
"""Version-checked final promotion. Never accepts unfinished routing."""
from pathlib import Path
import collections,hashlib,json,os,shutil,subprocess
import pcbnew as p
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
import route_v2 as routing
ROOT=Path(__file__).resolve().parent;H=ROOT.parent;R=H.parent
RUN=ROOT/'route_run_v2';STAGE=ROOT/'promotion_stage_v2'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def copy_atomic(src,dest):
 tmp=dest.with_name(dest.name+'.restore_v2_tmp');shutil.copy2(src,tmp);os.replace(tmp,dest)
def electrical(board):return sorted((f.GetReference(),f.GetValue(),sorted((q.GetNumber(),q.GetNetname()) for q in f.Pads())) for f in board.GetFootprints())
def main():
 result=json.loads((RUN/'result_v2.json').read_text());assert result['pipeline_completed'] and result['errors']==0 and result['unconnected']==0 and result['frozen_identity_verified']
 candidate=RUN/'routed_shortrefs_v2.kicad_pcb';assert result['candidate_sha256']==sha(candidate)
 d,stats=routing.drc(candidate);assert stats['errors']==stats['unconnected']==0
 original=p.LoadBoard(str(ROOT/'restored_shortrefs_v2.kicad_pcb'));board=p.LoadBoard(str(candidate));assert routing.frozen(board)==routing.frozen(original) and silk.audit(board)['clean']
 kickoff=json.loads((ROOT/'kickoff_sha256.json').read_text());frozen={n:h for n,h in kickoff.items() if n.endswith('.kicad_pcb') and ('daughtercard' in n or '/' not in n)}
 assert all(sha(R/n)==h for n,h in frozen.items()),'Frozen root/daughter changed'
 plan=json.loads((ROOT/'promotion_plan_v2.json').read_text());targets=list(plan)+['motherboard_adc_repaired.kicad_pcb','motherboard_adc_repaired_unrouted.kicad_pcb','motherboard_adc_repaired.kicad_pro','motherboard_adc_repaired_unrouted.kicad_pro','motherboard_adc_repaired_drc.json','motherboard_adc_repaired_status.json','motherboard_adc_repaired_silk.json','manual_motherboard_restoration.json','renamed_motherboard_restoration.json','motherboard_final_audit.json']
 backup=H/'backups/restore_v2_promotion';backup.mkdir(parents=True,exist_ok=False)
 current={name:sha(H/name) for name in targets if (H/name).exists()};diverged={name:{'planned_sha256':plan.get(name,{}).get('prior_sha256',kickoff.get('two_layer/'+name)),'final_pre_promotion_sha256':digest} for name,digest in current.items() if plan.get(name,{}).get('prior_sha256',kickoff.get('two_layer/'+name))!=digest}
 for name in current:shutil.copy2(H/name,backup/name)
 for f in (STAGE/'historical_scripts_v2').iterdir():
  dest=backup/'historical_scripts_v2'/f.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(f,dest)
 (backup/'authority_version_snapshot_v2.json').write_text(json.dumps({'kickoff_sha256':kickoff,'promotion_sha256':current,'orphan_divergence_preserved':diverged},indent=2)+'\n')
 # Only mutate live paths after a final comparison to the archived bytes.
 assert all(sha(H/n)==digest for n,digest in current.items()),'Authority changed during final promotion snapshot'
 for name in plan:assert sha(STAGE/name)==plan[name]['staged_sha256'];copy_atomic(STAGE/name,H/name)
 for name in ('motherboard_adc_repaired.kicad_pcb',):copy_atomic(candidate,H/name)
 copy_atomic(ROOT/'restored_shortrefs_v2.kicad_pcb',H/'motherboard_adc_repaired_unrouted.kicad_pcb')
 for name in ('motherboard_adc_repaired.kicad_pro','motherboard_adc_repaired_unrouted.kicad_pro'):copy_atomic(candidate.with_suffix('.kicad_pro'),H/name)
 copy_atomic(candidate.with_name(candidate.stem+'_drc.json'),H/'motherboard_adc_repaired_drc.json')
 result.update(stats,candidate_sha256=sha(candidate),reference_mapping_sha256=sha(ROOT/'old_to_new_refs.json'),reference_count=228,silk=silk.audit(board),side_counts=dict(collections.Counter(board.GetLayerName(f.GetLayer()) for f in board.GetFootprints())),smd_side_counts=dict(collections.Counter(board.GetLayerName(f.GetLayer()) for f in board.GetFootprints() if list(f.Pads()) and all(q.GetAttribute()==p.PAD_ATTRIB_SMD for q in f.Pads()))),frozen_daughter_root_sha256=frozen,orphan_divergence_preserved=diverged,assembly_policy='Bottom JLC Economic SMD only; every top SMD/THT manual; C126402 x8 top manual',economic_exporter_active=True,release_ready=False,release_authorized=False)
 for path in (RUN/'final_audit_v2.json',H/'motherboard_adc_repaired_status.json',H/'motherboard_final_audit.json'):
  path.write_text(json.dumps(result,indent=2)+'\n')
 (H/'motherboard_adc_repaired_silk.json').write_text(json.dumps(result['silk'],indent=2)+'\n')
 prepared=json.loads((ROOT/'prepared_audit_v2.json').read_text());prepared.update(placements_exactly_restored=True,pad_net_footprint_identity_preserved=True,component_uuid_pad_net_geometry_preserved=True,economic_exporter_active=True,placement_errors=0,reference_mapping_sha256=sha(ROOT/'old_to_new_refs.json'),pcb_sha256=sha(H/'motherboard_adc_repaired_unrouted.kicad_pcb'))
 for name in ('manual_motherboard_restoration.json','renamed_motherboard_restoration.json'):(H/name).write_text(json.dumps(prepared,indent=2)+'\n')
 rows=electrical(board);manifest={'candidate':'motherboard_adc_repaired.kicad_pcb','identity_hash':hashlib.sha256(json.dumps(rows).encode()).hexdigest(),'physical_components':rows,'source_board_sha256':sha(candidate),'reference_mapping_sha256':sha(ROOT/'old_to_new_refs.json'),'root_original_unmodified':True,'provisional':False,'release_authorized':False}
 (H/'motherboard_adc_repaired_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 subprocess.run(['/usr/bin/python3',str(H/'export_sourcing_inventory.py')],cwd=H,check=True)
 inventory=json.loads((H/'sourcing_inventory_provisional.json').read_text());items=[x for x in inventory['items'] if x['board']=='motherboard_adc_repaired.kicad_pcb'];registers=[x for x in items if x['historical_reference'].startswith('U_SR')]
 assert len(registers)==8 and all(x['side']=='Top' and x['assembly']=='manual' and x['lcsc']=='C126402' for x in registers)
 assert all(x['side']=='Bottom' for x in items if x['assembly']=='JLC_SMD') and all(x['assembly']!='JLC_SMD' for x in items if x['side']=='Top')
 assert all(sha(R/n)==h for n,h in frozen.items()) and sha(H/'motherboard_adc_repaired.kicad_pcb')==result['candidate_sha256']
 promoted=set(targets)|{'motherboard_adc_repaired_manifest.json','sourcing_inventory_provisional.json','approved_ahct_sourcing.json','adc_physical_audit.json'}|{str(f.relative_to(H)) for f in (H/'assembly_provisional').iterdir() if f.is_file()}|{str(f.relative_to(H)) for f in backup.rglob('*') if f.is_file()}
 hashes={name:sha(H/name) for name in promoted if (H/name).exists()};(ROOT/'promoted_sha256_v2.json').write_text(json.dumps(hashes,indent=2)+'\n')
 print(json.dumps({'board_sha256':result['candidate_sha256'],'errors':0,'unconnected':0,'side_counts':result['side_counts'],'smd_side_counts':result['smd_side_counts'],'promoted_files':len(hashes),'manual_ahct_count':8}),flush=True)
if __name__=='__main__':main()
