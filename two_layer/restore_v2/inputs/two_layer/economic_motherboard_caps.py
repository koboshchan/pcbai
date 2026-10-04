#!/usr/bin/python3
"""Approved eight-cap bottom relocation from immutable current placement backup."""
from pathlib import Path
import json,hashlib,shutil,math,collections,subprocess
import pcbnew as p
import silk_refs as s
from economic_motherboard import identity
ROOT=Path(__file__).resolve().parent
PCB=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def xy(q):return (p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y))
def distance(a,b):return math.dist(xy(a),xy(b))
def frozen(b):
 return {f.GetReference():(xy(f),f.GetOrientationDegrees(),f.GetLayer(),f.GetValue()) for f in b.GetFootprints()}
def main():
 backup=ROOT/'backups/economic_motherboard_before_caps_bottom';backup.mkdir(parents=True,exist_ok=True)
 for name in (PCB.name,'economic_motherboard_placement.json','economic_motherboard_placement_drc.json','ECONOMIC_MOTHERBOARD_REPORT.md'):
  src=ROOT/name
  if src.exists() and not (backup/name).exists():shutil.copy2(src,backup/name)
 b=p.LoadBoard(str(backup/PCB.name));assert not list(b.GetTracks())
 before=identity(b);fixed=frozen(b);roots={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in ROOT.parent.glob('*.kicad_pcb')}
 fps={f.GetReference():f for f in b.GetFootprints()};caps=[fps[f'C_SR{i}'] for i in range(1,9)]
 for f in caps:
  assert f.GetLayer()==p.F_Cu;f.Flip(f.GetPosition(),False)
 moves=[]
 for i,f in enumerate(caps,1):
  sr=fps[f'U_SR{i}'];pins={q.GetNumber():q for q in sr.Pads()};vcc=pins['16'];gnd=pins['8']
  obstacles=[]
  for other in b.GetFootprints():
   if other not in caps and s.side(other)==p.B_SilkS:obstacles.append(s.expand(s.rect(other.Reference()),.2))
  for other in b.GetFootprints():
   if other in caps and other is not f:continue
   if other is f:continue
   for q in other.Pads():
    if q.IsOnLayer(p.B_Cu):obstacles.append(s.expand(s.rect(q),.25))
  # Keep the capacitor out of the SO16 body; same-side body collision is not a pad short.
  sx,sy=xy(sr);body=(sx-2.1,sy-5,sx+2.1,sy+5)
  best=None
  for angle in (0,90,180,270):
   f.SetOrientationDegrees(angle)
   vx,vy=xy(vcc)
   for dx in range(-24,25):
    for dy in range(-24,25):
     x,y=vx+dx*.25,vy+dy*.25
     f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
     boxes=[s.rect(q) for q in f.Pads()]
     bound=(min(r[0] for r in boxes),min(r[1] for r in boxes),max(r[2] for r in boxes),max(r[3] for r in boxes))
     if not s.inside(s.expand(bound,.3),(.3,.3,99.7,99.7)) or s.intersects(s.expand(bound,.3),body):continue
     if any(s.intersects(r,o) for r in boxes for o in obstacles):continue
     pads={q.GetNumber():q for q in f.Pads()};cost=3*distance(pads['1'],vcc)+distance(pads['2'],gnd)
     item=(cost,angle,x,y)
     if best is None or item<best:best=item
  assert best is not None
  _,angle,x,y=best;f.SetOrientationDegrees(angle);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
  pads={q.GetNumber():q for q in f.Pads()}
  moves.append({'reference':f.GetReference(),'before_xy_mm':fixed[f.GetReference()][0],'after_xy_mm':xy(f),'angle_deg':angle,'cap_pad1_to_U_SR_pin16_mm':distance(pads['1'],vcc),'cap_pad2_to_U_SR_pin8_mm':distance(pads['2'],gnd),'distance_type':'straight-line pad-centre distance, not routed loop length'})
 assert identity(b)==before
 assert all(frozen(b)[r]==v for r,v in fixed.items() if r not in {f.GetReference() for f in caps})
 # Preserve previously audited references, only re-place the eight changed fields.
 pads=s.side_pads(b);obs={layer:s.SpatialBoxes() for layer in (p.F_SilkS,p.B_SilkS)}
 for layer in obs:
  for _,box in pads[layer]:obs[layer].add(s.expand(box,.2))
 for f in b.GetFootprints():
  if f not in caps:obs[s.side(f)].add(s.expand(s.rect(f.Reference()),.15))
 for f in caps:
  ref=f.Reference();layer=p.B_SilkS;x,y=xy(f);found=False
  candidates=list(s.candidates(f,ref,layer,.8))
  candidates.extend((a,px*.5,py*.5) for px,py in sorted(((xx,yy) for xx in range(2,198) for yy in range(2,60)),key=lambda z:(z[0]*.5-x)**2+(z[1]*.5-y)**2) for a in (0,90))
  for angle,px,py in candidates:
   s.configure(ref,layer,.8,angle,px,py);box=s.rect(ref)
   if s.inside(box,(.25,.25,99.75,99.75)) and not obs[layer].overlaps(box):obs[layer].add(s.expand(box,.15));found=True;break
  assert found
 audit=s.audit_silk(b);assert audit['clean'],audit
 p.SaveBoard(str(PCB),b)
 drc=ROOT/'economic_motherboard_placement_drc.json'
 subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(drc),str(PCB)],check=True)
 d=json.loads(drc.read_text());errors=[v for v in d['violations'] if v.get('severity')=='error']
 report=json.loads((backup/'economic_motherboard_placement.json').read_text());bottom=[];manual=[];other=[]
 for f in b.GetFootprints():
  row={'reference':f.GetReference(),'value':f.GetValue(),'footprint':f.GetFPID().GetUniStringLibId()}
  if list(f.Pads()) and all(q.GetAttribute()==p.PAD_ATTRIB_SMD for q in f.Pads()):(bottom if f.GetLayer()==p.B_Cu else manual).append(row)
  else:other.append(row)
 assert len(bottom)==153 and len(manual)==60
 report.update(bottom_JLC_SMD=sorted(bottom,key=lambda r:r['reference']),top_manual_SMD=sorted(manual,key=lambda r:r['reference']),manual_THT_or_mechanical=sorted(other,key=lambda r:r['reference']),bypass_capacitor_moves=moves,only_eight_caps_changed_since_approved_bottom_placement=True,silk=audit,placement_errors=len(errors),unconnected=len(d.get('unconnected_items',[])),drc_categories=dict(collections.Counter(v['type'] for v in d['violations'])),pcb_sha256=hashlib.sha256(PCB.read_bytes()).hexdigest(),root_sha256=roots,release_authorized=False)
 assert roots=={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in ROOT.parent.glob('*.kicad_pcb')}
 (ROOT/'economic_motherboard_placement.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'sha':report['pcb_sha256'],'errors':errors,'silk':audit,'moves':moves}),flush=True)
 assert not errors
if __name__=='__main__':main()
