#!/usr/bin/python3
"""Exclusive isolated restoration, actual reference rename before any silk."""
from pathlib import Path
import collections,hashlib,json,subprocess
import pcbnew as p
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
import silk_refs as s
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'pre_economic_input_v2.kicad_pcb'
TARGET=ROOT/'restored_shortrefs_v2.kicad_pcb'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
 assert not (ROOT/'prepared_audit_v2.json').exists(),'Validated isolated input already prepared'
 project=json.loads(TARGET.with_suffix('.kicad_pro').read_text());settings=project['board']['design_settings'];rules=settings['rules']
 for key,minimum in {'min_clearance':.2,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_via_annular_width':.15,'min_silk_clearance':.15,'min_text_height':.8,'min_text_thickness':.12,'min_copper_edge_clearance':.3}.items():rules[key]=max(rules.get(key,0),minimum)
 assert not settings.get('drc_exclusions',[])
 for cls in project['net_settings']['classes']:
  for key,minimum in {'clearance':.2,'track_width':.25,'via_diameter':.6,'via_drill':.3}.items():cls[key]=max(cls.get(key,0),minimum)
 TARGET.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
 b=p.LoadBoard(str(SOURCE)); before=refs.physical(b);fps={f.GetReference():f for f in b.GetFootprints()}
 assert len(fps)==228 and not list(b.GetTracks()) and b.GetCopperLayerCount()==2
 assert all(fps[f'{pref}{i}'].GetLayer()==p.F_Cu for pref in ('U_SR','C_SR') for i in range(1,9))
 assert all(fps[f'{pref}_PWM_{i}'].GetLayer()==p.B_Cu for pref in ('R','C') for i in range(64))
 for i in range(1,9):
  f=fps[f'U_SR{i}'];f.SetValue('74AHCT595S16-13');f.SetLibDescription('Diodes 74AHCT595S16-13; LCSC C126402; top MANUAL sourced/soldered by Lucas; excluded JLC bottom assembly')
 fps['C_REG_IN'].SetValue('1uF');fps['C_REG_IN'].SetLibDescription('Samsung CL21B105KBFNNNE; LCSC C28323; 1uF 50V X7R 0805; JLC bottom assembly')
 approved=refs.physical(b)
 for uid,row in before.items():
  a=dict(row);z=dict(approved[uid]);a.pop('value');z.pop('value');assert a==z,'Sourcing modified geometry'
 mapping=refs.rename(b);assert len(mapping['old_to_new'])==228
 rect=s.rect
 def effective(item):
  if isinstance(item,p.PCB_FIELD):return silk.base.bbox(silk.base.glyph(item))
  return rect(item)
 s.rect=effective
 report=silk.apply(b)
 (ROOT/'prepare_silk_v2.json').write_text(json.dumps(report,indent=2)+'\n')
 assert not report['unplaced'] and report['clean'],{'unplaced':report['unplaced'],'violations':report['violations']}
 assert refs.physical(b)==approved
 p.SaveBoard(str(TARGET),b);TARGET.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n');loaded=p.LoadBoard(str(TARGET));assert refs.physical(loaded)==approved
 assert silk.audit(loaded)['clean']
 pro=json.loads(TARGET.with_suffix('.kicad_pro').read_text());rules=pro['board']['design_settings']['rules']
 assert rules['min_clearance']>=.2 and rules['min_track_width']>=.2 and rules['min_via_diameter']>=.6 and rules['min_through_hole_diameter']>=.3
 assert not pro['board']['design_settings'].get('drc_exclusions',[])
 drc=ROOT/'placement_drc_v2.json';subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(drc),str(TARGET)],check=True)
 d=json.loads(drc.read_text());errors=[v for v in d['violations'] if v.get('severity')=='error'];assert not errors,errors
 result={'source_sha256':sha(SOURCE),'candidate_sha256':sha(TARGET),'mapping_sha256':sha(refs.MAP),'reference_count':228,'physical_identity':approved,'frozen_identity_verified':True,'errors':len(errors),'unconnected':len(d['unconnected_items']),'silk':report,'side_counts':dict(collections.Counter(b.GetLayerName(f.GetLayer()) for f in b.GetFootprints())),'smd_side_counts':dict(collections.Counter(b.GetLayerName(f.GetLayer()) for f in b.GetFootprints() if list(f.Pads()) and all(q.GetAttribute()==p.PAD_ATTRIB_SMD for q in f.Pads()))),'release_authorized':False}
 (ROOT/'prepared_audit_v2.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ('candidate_sha256','reference_count','errors','unconnected','side_counts','smd_side_counts')}),flush=True)
if __name__=='__main__':main()
