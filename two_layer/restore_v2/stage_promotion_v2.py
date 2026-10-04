#!/usr/bin/python3
"""Stage motherboard-only source and identity remapping, never live mutations."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent
H=ROOT.parent
OUT=ROOT/'promotion_stage_v2'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def convert(value,mapping):
 if isinstance(value,str):return mapping.get(value,value)
 if isinstance(value,list):return [convert(v,mapping) for v in value]
 if isinstance(value,dict):return {mapping.get(k,k):convert(v,mapping) for k,v in value.items()}
 return value

def main():
 OUT.mkdir(exist_ok=True);mapping=json.loads((ROOT/'old_to_new_refs.json').read_text())['old_to_new'];plan={}
 # Preserve old-generators as historical explicitly. Routing/restoration entrypoints cannot
 # accidentally recreate or overwrite the accepted final authoritative board.
 retired=('economic_motherboard_long_route.py','restored_hybrid_route.py','restore_manual_motherboard.py','rename_restored_motherboard.py','launch_restored_hybrid.py','economic_motherboard.py','economic_motherboard_caps.py','repair_motherboard_final.py','repair_motherboard_power.py')
 for name in retired:
  src=H/name
  if not src.exists():continue
  historical=OUT/'historical_scripts_v2'/name;historical.parent.mkdir(exist_ok=True);historical.write_bytes(src.read_bytes())
  (OUT/name).write_text('#!/usr/bin/python3\n"""Retired historical placement/routing entrypoint. Final restore_v2 owns CAD."""\nraise RuntimeError("Retired motherboard entrypoint, use isolated restore_v2; historical source retained in backups/restore_v2_promotion/historical_scripts_v2")\n')
  plan[name]={'prior_sha256':sha(src),'staged_sha256':sha(OUT/name),'action':'retire_historical_generator'}
 for name in ('motherboard_adc_repaired_manifest.json','adc_physical_audit.json','approved_ahct_sourcing.json'):
  src=H/name
  if not src.exists():continue
  data=convert(json.loads(src.read_text()),mapping)
  if name=='approved_ahct_sourcing.json':data.update(assembly='MANUAL_TOP',manual=True,jlc_assembly_excluded=True,assembly_exclusion_reason='Lucas purchases and solders all eight top C126402 AHCTs; motherboard JLC Economic assembles bottom SMD only',saved_CAD_field_update='APPLIED_TO_UUID_ANCHORED_RESTORED_BOARD')
  (OUT/name).write_text(json.dumps(data,indent=2)+'\n');plan[name]={'prior_sha256':sha(src),'staged_sha256':sha(OUT/name),'action':'reference_role_remap'}
 # UUID-role module stays available to audited readers, unchanged except map location.
 for name in ('motherboard_refs.py','shortrefs_motherboard_silk.py','old_to_new_refs.json'):
  src=ROOT/name;(OUT/name).write_bytes(src.read_bytes());prior=H/name
  plan[name]={'prior_sha256':sha(prior) if prior.exists() else None,'staged_sha256':sha(OUT/name),'action':'promote_uuid_role_authority'}
 src=H/'export_sourcing_inventory.py';text=src.read_text();text=text.replace("H/'restored_hybrid_shortrefs_run/final_audit.json'","H/'restore_v2/route_run_v2/final_audit_v2.json'")
 assert 'motherboard_refs.role(f)' in text
 (OUT/src.name).write_text(text);plan[src.name]={'prior_sha256':sha(src),'staged_sha256':sha(OUT/src.name),'action':'active_hybrid_exporter'}
 (ROOT/'promotion_plan_v2.json').write_text(json.dumps(plan,indent=2)+'\n')
 print(json.dumps({'staged':len(plan),'live_files_mutated':0}))
if __name__=='__main__':main()
