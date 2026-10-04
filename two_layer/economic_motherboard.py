#!/usr/bin/python3
"""Minimal motherboard bottom-AHCT Economic assembly revision; no regeneration."""
from pathlib import Path
import hashlib,json,shutil,subprocess,collections
import pcbnew as p
from silk_refs import apply_silk
ROOT=Path(__file__).resolve().parent
PCB=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def identity(b):
 return sorted((f.GetReference(),f.GetFPID().GetUniStringLibId(),sorted((q.GetNumber(),q.GetNetname()) for q in f.Pads())) for f in b.GetFootprints())
def main():
 backup=ROOT/'backups/economic_motherboard_before_bottom';backup.mkdir(parents=True,exist_ok=True)
 if not (backup/PCB.name).exists():shutil.copy2(PCB,backup/PCB.name)
 else:pass # Immutable backup is source for reproducible retries.
 roots={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in ROOT.parent.glob('*.kicad_pcb')}
 b=p.LoadBoard(str(backup/PCB.name));before=identity(b);assert not list(b.GetTracks())
 fixed={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()) for f in b.GetFootprints() if not f.GetReference().startswith('U_SR')}
 sr=[]
 for f in b.GetFootprints():
  ref=f.GetReference()
  if ref.startswith('U_SR'):
   assert f.GetLayer()==p.F_Cu
   f.Flip(f.GetPosition(),False);f.SetValue('74AHCT595S16-13')
   f.SetLibDescription('Diodes 74AHCT595S16-13; LCSC C126402; JLC assembled bottom SMD; 5V TTL-compatible inputs')
   sr.append(ref)
  if ref=='C_REG_IN':
   f.SetValue('1uF');f.SetLibDescription('Samsung CL21B105KBFNNNE; LCSC C28323; JLC Basic; 1uF 50V X7R 0805')
 assert len(sr)==8 and identity(b)==before
 assert fixed=={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()) for f in b.GetFootprints() if f.GetReference() in fixed}
 rail=next(f for f in b.GetFootprints() if f.GetReference()=='C_RAIL_N')
 rail.SetPosition(p.VECTOR2I(p.FromMM(84),p.FromMM(28)))
 import silk_refs as s
 original=s.candidates
 def wider(fp,ref,layer,height):
  yield from original(fp,ref,layer,height)
  x,y=fp.GetPosition().x/1e6,fp.GetPosition().y/1e6
  points=sorted(((a*.75,c*.75) for a in range(2,132) for c in range(2,132)),key=lambda z:(z[0]-x)**2+(z[1]-y)**2)
  for px,py in points:
   for angle in (0,90):
    yield angle,px,py
 s.candidates=wider
 silk=apply_silk(b)
 p.SaveBoard(str(PCB),b)
 drc=ROOT/'economic_motherboard_placement_drc.json'
 subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(drc),str(PCB)],check=True)
 d=json.loads(drc.read_text());errors=[v for v in d['violations'] if v.get('severity')=='error']
 manual=[];bottom=[];th=[]
 for f in b.GetFootprints():
  row={'reference':f.GetReference(),'value':f.GetValue(),'footprint':f.GetFPID().GetUniStringLibId()}
  if list(f.Pads()) and all(q.GetAttribute()==p.PAD_ATTRIB_SMD for q in f.Pads()):
   (bottom if f.GetLayer()==p.B_Cu else manual).append(row)
  else:th.append(row)
 assert roots=={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in ROOT.parent.glob('*.kicad_pcb')}
 report={'pad_number_net_footprint_identity_preserved':True,'non_AHCT_placements_preserved_except_C_RAIL_N':True,'moved_conflicting_capacitor':{'reference':'C_RAIL_N','before_xy_mm':[84,25],'after_xy_mm':[84,28]},'silk_association_visual_review_pending':True,'root_sha256':roots,'flipped':sorted(sr),'bottom_JLC_SMD':sorted(bottom,key=lambda r:r['reference']),'top_manual_SMD':sorted(manual,key=lambda r:r['reference']),'manual_THT_or_mechanical':sorted(th,key=lambda r:r['reference']),'silk':silk,'placement_errors':len(errors),'unconnected':len(d.get('unconnected_items',[])),'drc_categories':dict(collections.Counter(v['type'] for v in d['violations'])),'pcb_sha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'release_authorized':False}
 (ROOT/'economic_motherboard_placement.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'errors':len(errors),'silk':silk,'bottom_SMD':len(bottom),'top_manual_SMD':len(manual),'manual_other':len(th)}),flush=True)
 assert not errors,'Review placement conflicts before routing'
 assert silk['clean'],'Silk conflicts must be fixed before routing'
if __name__=='__main__':main()
