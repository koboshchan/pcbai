#!/usr/bin/python3
from pathlib import Path
import pcbnew as p,json,hashlib,collections,shutil
R=Path(__file__).resolve().parent;P=R.parent;S=P/'restore_v2/restored_shortrefs_v2.kicad_pcb'
mm=p.FromMM
def pos(x,y):return p.VECTOR2I(mm(x),mm(y))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def members(b):return {f.GetReference():{'uuid':f.m_Uuid.AsString(),'value':f.GetValue(),'footprint':f.GetFPID().GetLibItemName().wx_str(),'pads':sorted((q.GetNumber(),q.GetNetname()) for q in f.Pads())} for f in b.GetFootprints()}
def header(b,ref,daughter):
 f=p.FOOTPRINT(b);f.SetReference(ref);f.SetValue('2x38_2.54mm_GENERIC_MANUAL_STRADDLE' if daughter else '2x38_2.54mm_GENERIC_MANUAL_SOCKET');b.Add(f);f.SetPosition(pos(50,40 if daughter else 10))
 for n in range(1,77):
  q=p.PAD(f);q.SetNumber(str(n));q.SetShape(p.PAD_SHAPE_RECT if n==1 else p.PAD_SHAPE_OVAL);x=3.01+((n-1)//2)*2.54
  if daughter:
   q.SetAttribute(p.PAD_ATTRIB_SMD);q.SetSize(pos(1.7,2.2));q.SetPosition(pos(x,38.5));ls=p.LSET();ls.AddLayer(p.F_Cu if n%2 else p.B_Cu);ls.AddLayer(p.F_Mask if n%2 else p.B_Mask);q.SetLayerSet(ls)
  else:
   q.SetAttribute(p.PAD_ATTRIB_PTH);q.SetSize(pos(1.6,1.6));q.SetDrillSize(pos(1,1));q.SetLayerSet(p.LSET.AllCuMask());q.SetPosition(pos(x,8.73 if n%2 else 11.27))
  q.SetNet(b.FindNet(pinmap[str(n)]));f.Add(q)
 return f
pinmap={str(n+1):'IN_'+str(n) for n in range(64)};pinmap.update({str(n):v for n,v in enumerate(['SPI_MOSI','SPI_SCK','SPI_LATCH','SPI_OE','+5V','GND','+5V','GND','GND','GND','GND','GND'],65)})
def main():
 R.mkdir(exist_ok=True);sources=sorted(P.glob('*.kicad_pcb'))+sorted(P.glob('*.kicad_pro'))+[S,S.with_suffix('.kicad_pro')]
 snapshot={str(f.relative_to(P)):sha(f) for f in sources};(R/'source_sha256.json').write_text(json.dumps(snapshot,indent=2))
 b=p.LoadBoard(str(S));d=p.LoadBoard(str(S));original=members(b)
 moving={'U'+str(i) for i in range(1,9)}|{'C'+str(i) for i in range(1,9)}|{'RP'+str(i) for i in range(64)}|{'CP'+str(i) for i in range(64)}
 assert len(moving)==144 and moving<=original.keys();assert 'JD0' not in original and 'J0' not in original
 left=collections.defaultdict(set);right=collections.defaultdict(set)
 for f in b.GetFootprints():
  for q in f.Pads():
   if q.GetNetname():(right if f.GetReference() in moving else left)[q.GetNetname()].add((f.GetReference(),q.GetNumber()))
 boundary=set(left)&set(right);assert boundary==set(pinmap.values()),boundary^set(pinmap.values())
 for f in list(b.GetFootprints()):
  if f.GetReference() in moving:b.Delete(f)
 for f in list(d.GetFootprints()):
  if f.GetReference() not in moving:d.Delete(f)
 for board in [b,d]:
  for t in list(board.GetTracks()):board.Remove(t)
  for z in list(board.Zones()):board.Remove(z)
 for g in list(d.GetDrawings()):d.Remove(g)
 for a,c in [((0,0),(100,0)),((100,0),(100,40)),((100,40),(0,40)),((0,40),(0,0))]:
  g=p.PCB_SHAPE(d);g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(pos(*a));g.SetEnd(pos(*c));g.SetLayer(p.Edge_Cuts);g.SetWidth(mm(.05));d.Add(g)
 for f in d.GetFootprints():
  r=f.GetReference()
  if f.GetLayer()==p.B_Cu:f.Flip(f.GetPosition(),False)
  f.SetOrientationDegrees(0)
  if r.startswith('U'):i=int(r[1:])-1;x=8.7+i*11.8;y=7.3
  elif r.startswith('RP') or r.startswith('CP'):
   n=int(r[2:]);bank=n//8;k=n%8;x=3.5+bank*12+(k%4)*3.0;y=(18 if k<4 else 28)+(5.0 if r.startswith('CP') else 0);f.SetOrientationDegrees(90)
  else:i=int(r[1:])-1;x=8.7+i*11.8;y=13.9
  f.SetPosition(pos(x,y))
 header(b,'JD0',False);header(d,'J0',True)
 joint={**{k:v for k,v in members(b).items() if k!='JD0'},**{k:v for k,v in members(d).items() if k!='J0'}};assert joint==original,[(k,original[k],joint.get(k)) for k in original if original[k]!=joint.get(k)][:2]
 for board,name in [(b,'motherboard'),(d,'DC0')]:
  import shortrefs_motherboard_silk as silk
  report=silk.apply(board);(R/(name+'_silk.json')).write_text(json.dumps(report,indent=2));assert report['clean'],report['unplaced']
  p.SaveBoard(str(R/(name+'.kicad_pcb')),board);shutil.copyfile(S.with_suffix('.kicad_pro'),R/(name+'.kicad_pro'))
 (R/'DC0.kicad_dru').write_text('(version 1)\n'+''.join('(rule "DC0 J0 pad '+str(n)+' only" (condition "A.Type == \'Pad\' && A.memberOfFootprint(\'J0\') && A.Pad_Number == \''+str(n)+'\'") (constraint edge_clearance (min 0.4mm)))\n'.replace("== ' ","== '") for n in range(1,77)))
 (R/'straddle_exception_manifest.json').write_text(json.dumps({'reference':'J0','global_edge_mm':.5,'pad_only_edge_mm':.4,'pads':[{'number':q.GetNumber(),'uuid':q.m_Uuid.AsString(),'layer':d.GetLayerName(q.GetLayer()),'edge_setback_mm':.4} for f in d.GetFootprints() if f.GetReference()=='J0' for q in f.Pads()]},indent=2))
 (R/'split_identity.json').write_text(json.dumps({'verified':True,'boundary_nets':sorted(boundary),'pinmap':pinmap,'original_parts':228,'mother_parts':84,'dc0_parts':144,'DC0_dimensions_mm':[100,40],'header_pitch_mm':2.54,'header_span_mm':37*2.54,'mother_header_center_mm':[50,10],'source_sha_unchanged':all(sha(P/k)==v for k,v in snapshot.items()),'release_authorized':False},indent=2))
if __name__=='__main__':main()
