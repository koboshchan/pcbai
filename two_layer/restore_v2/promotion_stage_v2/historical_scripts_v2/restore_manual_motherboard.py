#!/usr/bin/python3
"""Restore authorized pre-Economic placement without moving a footprint."""
from pathlib import Path
import collections, hashlib, json, shutil, subprocess, math
import pcbnew as p
import silk_refs as s
from economic_motherboard import identity
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'backups/economic_motherboard_before_bottom/motherboard_adc_repaired_unrouted.kicad_pcb'
TARGET=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def placements(b):
 return {f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()) for f in b.GetFootprints()}
def frozen_files():
 files=list(ROOT.parent.glob('*.kicad_pcb'))+[ROOT/n for n in ('daughtercard_1a_adc_repaired.kicad_pcb','daughtercard_1b_adc_repaired.kicad_pcb','daughtercard_1c_adc_repaired.kicad_pcb','daughtercard_1d_adc_repaired.kicad_pcb','daughtercard_2_adc_repaired.kicad_pcb','daughtercard_3_adc_repaired.kicad_pcb')]
 return {str(f.relative_to(ROOT.parent)):sha(f) for f in files if f.exists()}
def main():
 backup=ROOT/'backups/economic_motherboard_authorized_reversal_79d137c';backup.mkdir(parents=True,exist_ok=True)
 names=['motherboard_adc_repaired.kicad_pcb','motherboard_adc_repaired_unrouted.kicad_pcb','motherboard_adc_repaired.kicad_pro','motherboard_adc_repaired_status.json','motherboard_adc_repaired_drc.json','motherboard_adc_repaired_silk.json','economic_motherboard_placement.json','economic_motherboard_placement_drc.json','economic_motherboard_route_run.json','ECONOMIC_MOTHERBOARD_REPORT.md']
 for name in names:
  src=ROOT/name;dest=backup/name
  if src.exists():
   if dest.exists():assert sha(src)==sha(dest),'Immutable saved Economic state changed'
   else:shutil.copy2(src,dest)
 saved={f.name:sha(f) for f in backup.iterdir() if f.is_file()}
 b=p.LoadBoard(str(SOURCE));original=placements(b);net_identity=identity(b);frozen=frozen_files();assert not list(b.GetTracks())
 fps={f.GetReference():f for f in b.GetFootprints()}
 assert all(fps[f'U_SR{i}'].GetLayer()==p.F_Cu and fps[f'C_SR{i}'].GetLayer()==p.F_Cu for i in range(1,9))
 assert all(fps[f'{prefix}_PWM_{i}'].GetLayer()==p.B_Cu for prefix in ('R','C') for i in range(64))
 for i in range(1,9):
  f=fps[f'U_SR{i}'];f.SetValue('74AHCT595S16-13');f.SetLibDescription('Diodes 74AHCT595S16-13; LCSC C126402; manual top-side sourcing/soldering by Lucas; excluded JLC bottom assembly; 5V TTL-compatible inputs')
 fps['C_REG_IN'].SetValue('1uF');fps['C_REG_IN'].SetLibDescription('Samsung CL21B105KBFNNNE; LCSC C28323; 1uF 50V X7R 0805; JLC bottom Economic assembly')
 original_candidates=s.candidates
 original_rect=s.rect
 def glyph_rect(item):
  if isinstance(item,p.PCB_FIELD):
   bb=item.GetEffectiveTextShape().BBox()
   return tuple(p.ToMM(v) for v in (bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()))
  return original_rect(item)
 s.rect=glyph_rect
 def local_pattern(fp,ref,layer,height):
  name=fp.GetReference();x=p.ToMM(fp.GetPosition().x);y=p.ToMM(fp.GetPosition().y)
  if name.startswith(('R_PWM_','C_PWM_')):
   # Interleaved vertical lanes, resistor right and capacitor left.
   # Both lie entirely between adjacent connector rows and near their own part.
   resistor=name.startswith('R_')
   yield 90,x+(2.122 if resistor else -2.151),y+(.7 if resistor else -1.5)
   for dx in (2.122,2.151,2.1593,2.16,2.13,2.14,2.15,2.17,2.18,2.19,2.2,2.1,2.05,2.25):
    for dy in (0,.05,-.05,.1,-.1):
     yield 90,x+(dx if resistor else -dx),y+(.7 if resistor else -1.5)+dy
   # Search every local channel, never displace the label to a remote bank.
   offsets=[(dx*.1,dy*.1) for dx in range(-40,41) for dy in range(-40,41) if dx*dx+dy*dy<=1600]
   offsets.sort(key=lambda q:q[0]*q[0]+q[1]*q[1])
   for dx,dy in offsets:
    for angle in (90,0):yield angle,x+dx,y+dy
  else:yield from original_candidates(fp,ref,layer,height)
 s.candidates=local_pattern
 from hybrid_silk import finish_local_search
 audit=finish_local_search(b,s.apply_silk(b))
 audit['method']='Actual KiCad stroked glyph shape bounding boxes for text, conservative pad boxes; unchanged 0.20 mm pad and 0.15 mm text clearance.'
 association=[]
 for f in b.GetFootprints():
  r=f.Reference();d=math.dist((p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)),(p.ToMM(r.GetPosition().x),p.ToMM(r.GetPosition().y)))
  association.append({'reference':f.GetReference(),'distance_mm':d,'angle_deg':r.GetTextAngle().AsDegrees()})
 assert placements(b)==original and identity(b)==net_identity
 result={'source_preEconomic_sha256':sha(SOURCE),'economic_saved_files':saved,'placements_exactly_restored':True,'pad_net_footprint_identity_preserved':True,'silk':audit,'association':association,'frozen_files':frozen,'assembly_policy':'JLC Economic bottom SMD; all top SMD and THT manual','top_AHCT_manual_sourcing':'C126402','economic_exporter_active':True,'release_authorized':False}
 (ROOT/'manual_motherboard_restoration.json').write_text(json.dumps(result,indent=2)+'\n')
 assert audit['clean'] and not audit['unplaced'],audit['unplaced']
 assert max(r['distance_mm'] for r in association if r['reference'].startswith(('R_PWM_','C_PWM_')))<=4.01
 p.SaveBoard(str(TARGET),b)
 shutil.copy2(ROOT/'motherboard_adc_repaired.kicad_pro',TARGET.with_suffix('.kicad_pro'))
 drc=ROOT/'manual_motherboard_placement_drc.json';subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(drc),str(TARGET)],check=True)
 d=json.loads(drc.read_text());errors=[v for v in d['violations'] if v.get('severity')=='error']
 result.update(placement_errors=len(errors),unconnected=len(d.get('unconnected_items',[])),pcb_sha256=sha(TARGET),side_counts=dict(collections.Counter(b.GetLayerName(f.GetLayer()) for f in b.GetFootprints())),smd_side_counts=dict(collections.Counter(b.GetLayerName(f.GetLayer()) for f in b.GetFootprints() if list(f.Pads()) and all(q.GetAttribute()==p.PAD_ATTRIB_SMD for q in f.Pads()))))
 assert not errors,errors
 assert frozen==frozen_files()
 (ROOT/'manual_motherboard_restoration.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('economic_saved_files','association','frozen_files','silk')}),flush=True)
if __name__=='__main__':main()
