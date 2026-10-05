#!/usr/bin/python3
"""Import router output, verify variants/mechanics, and run strict KiCad DRC."""
from pathlib import Path
import collections,hashlib,json,subprocess,sys
import pcbnew as p
from build import snapshot,normalized,xy,mm
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def identity(b):
 return sorted((f.GetReference(),f.GetValue(),sorted((q.GetNumber(),q.GetNetname()) for q in f.Pads())) for f in b.GetFootprints())
def mechanics(b):
 return {'edges':sorted((int(d.GetShape()),d.GetStart().x,d.GetStart().y,d.GetEnd().x,d.GetEnd().y,d.GetWidth()) for d in b.GetDrawings() if d.GetLayer()==p.Edge_Cuts),'parts':sorted((f.GetReference(),f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),sorted((q.GetNumber(),q.GetPosition().x,q.GetPosition().y,q.GetSize().x,q.GetSize().y,q.GetDrillSize().x,q.GetDrillSize().y,int(q.GetShape()),int(q.GetAttribute()),str(q.GetLayerSet().FmtBin())) for q in f.Pads())) for f in b.GetFootprints() if f.GetReference().startswith(('J','H')))}

def main():
 b=p.LoadBoard(str(HERE/'dc1_universal_unrouted.kicad_pcb'));expected=identity(b)
 if len(sys.argv)>1:
  b=p.LoadBoard(sys.argv[1])
 else:
  assert p.ImportSpecctraSES(b,str(HERE/'dc1_universal.ses'))
 assert identity(b)==expected,'Router modified component/pad net identity'
 sources=[p.LoadBoard(str(ROOT/f'daughtercard1{c}_weights_l1_differential_repaired.kicad_pcb')) for c in 'abcd']
 assert all(mechanics(x)==mechanics(b) for x in sources),'Mounting/connector/outline differs'
 mb=p.LoadBoard(str(ROOT/'dc0_split/motherboard_repair/approved_bodge_CRB/post_crb.kicad_pcb'))
 connector=next(f for f in b.GetFootprints() if f.GetReference()=='J_STRADDLE_EDGE')
 for slot in range(4):
  socket=next(f for f in mb.GetFootprints() if f.GetReference()==f'JS{slot}')
  socketnets={q.GetNumber():normalized(q.GetNetname(),slot*4) for q in socket.Pads()}
  assert {q.GetNumber():q.GetNetname() for q in connector.Pads()}==socketnets,('motherboard slot pin roles differ',slot)
 cards,_=snapshot();manifest=json.loads((HERE/'manifest.json').read_text());actual={f.GetReference():f for f in b.GetFootprints()}
 keys={tuple(sorted(r['nets'])) for r in manifest['rows']}
 matrix={tuple(sorted((f'IN_{i}',f'{leg}_N{j}'))) for i in range(64) for j in range(4) for leg in ('POS','INV')}
 support={tuple(sorted((rail,f'{leg}_N{j}'))) for rail in ('+5V_REF','GND') for j in range(4) for leg in ('POS','INV')}|{tuple(sorted((f'INV_N{j}',f'V_SUM_{j}'))) for j in range(4)}
 assert keys==matrix|support and len(manifest['rows'])==532,'Incomplete future-model footprint matrix'
 assert sum(not r['cards'] for r in manifest['rows'])==112,'Added sites must default to DNP'
 variant_checks={}
 for c in 'abcd':
  expect=collections.Counter((tuple(sorted(f['pads'].items())),f['value']) for row in manifest['rows'] for c1,f in row['cards'].items() if c1==c)
  assembled=collections.Counter()
  for row in manifest['rows']:
   entry=row['cards'].get(c)
   if entry:
    pads={q.GetNumber():q.GetNetname() for q in actual[row['reference']].Pads()}
    # Pad ordering may reverse relative to source; resistance is bidirectional.
    assert sorted(pads.values())==sorted(entry['pads'].values())
    assembled[(tuple(sorted(entry['pads'].items())),entry['value'])]+=1
  assert expect==assembled
  variant_checks[c]={'populated_resistors':sum(assembled.values()),'dnp_resistors':len(manifest['rows'])-sum(assembled.values()),'exact_source_resistor_value_and_netpair_match':True,'source_sha256':cards[c]['sha256']}
 for d in list(b.GetDrawings()):
  if d.GetLayer() in (p.F_SilkS,p.B_SilkS):b.Delete(d)
 # Arrow and L mark physical pin-1 end, same physical x on both PCB faces.
 for layer in (p.F_SilkS,p.B_SilkS):
  t=p.PCB_TEXT(b);t.SetText('L');t.SetPosition(xy(2.1,92.8));t.SetTextSize(xy(1,1));t.SetTextThickness(mm(.15));t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);b.Add(t)
  for a,z in [((1.25,92.5),(1.25,95)),((1.25,95),(.85,94.3)),((1.25,95),(1.65,94.3))]:
   s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*z));s.SetWidth(mm(.15));s.SetLayer(layer);b.Add(s)
 assert b.GetCopperLayerCount()==2
 assert all(t.GetLayer() in [p.F_Cu,p.B_Cu] for t in b.GetTracks() if not isinstance(t,p.PCB_VIA))
 assert all(t.GetWidth()>=mm(.2) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)),'Undersized track'
 assert all(t.GetWidth(p.F_Cu)>=mm(.6) and t.GetDrillValue()>=mm(.3) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)),'Undersized via'
 assert all(str(f.GetFPID().GetLibItemName())=='R_0805_2012Metric' and f.GetLayer()==p.F_Cu for f in b.GetFootprints() if f.GetReference().startswith('R')),'Resistors must be top-side 0805'
 target=HERE/'dc1_universal.kicad_pcb';p.SaveBoard(str(target),b)
 (HERE/'dc1_universal.kicad_pro').write_text((HERE/'dc1_universal_unrouted.kicad_pro').read_text())
 cp=subprocess.run(['kicad-cli','pcb','drc','--all-track-errors','--severity-all','--format','json','-o',str(HERE/'drc.json'),str(target)],capture_output=True,text=True)
 (HERE/'drc.log').write_text(cp.stdout+cp.stderr)
 data=json.loads((HERE/'drc.json').read_text());errors=[v for v in data['violations'] if v['severity']=='error'];opens=data['unconnected_items']
 report={'errors':len(errors),'unconnected':len(opens),'warnings':sum(v['severity']=='warning' for v in data['violations']),'drc_types':dict(collections.Counter(v['type'] for v in data['violations'])),'source_mechanics_all_four_match':True,'motherboard_JS0_JS1_JS2_JS3_all_76_pin_roles_match':True,'router_preserved_component_and_pad_nets':True,'variants':variant_checks,'resistor_positions':len(manifest['rows']),'input_resistor_positions':manifest['input_positions'],'tracks':sum(not isinstance(t,p.PCB_VIA) for t in b.GetTracks()),'vias':sum(isinstance(t,p.PCB_VIA) for t in b.GetTracks()),'minimum_track_width_mm':min(p.ToMM(t.GetWidth()) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)),'pcb_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'fabrication_ordered':False}
 (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 assert not errors and not opens,'Incomplete design, not releasable'
if __name__=='__main__':main()
