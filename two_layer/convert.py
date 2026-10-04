#!/usr/bin/python3
"""Isolated, netlist-preserving two-layer routing preparation and strict DRC."""
from pathlib import Path
import argparse, json, re, subprocess, collections
import pcbnew as p
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent
BOARDS=['motherboard']+[f'daughtercard1{c}_weights_l1' for c in 'abcd']+['daughtercard2_relu_l1','daughtercard3_weights_l2_wta']
def manifest(b):
 return sorted((f.GetReference(),f.GetValue(),sorted((a.GetNumber(),a.GetNetname()) for a in f.Pads())) for f in b.GetFootprints())
def prep(name,mode='fresh'):
 b=p.LoadBoard(str(SOURCE/(name+'.kicad_pcb')))
 original=manifest(b)
 for z in list(b.Zones()): b.Remove(z)
 for t in list(b.GetTracks()):
  if mode=='fresh': b.Remove(t)
  elif isinstance(t,p.PCB_VIA): t.SetLayerPair(p.F_Cu,p.B_Cu)
  elif t.GetLayer() not in [p.F_Cu,p.B_Cu]: t.SetLayer(p.B_Cu)
 b.SetCopperLayerCount(2)
 settings=b.GetDesignSettings()
 settings.m_MinClearance=p.FromMM(.2)
 settings.m_TrackMinWidth=p.FromMM(.2)
 settings.m_ViasMinSize=p.FromMM(.6)
 settings.m_MinThroughDrill=p.FromMM(.3)
 for d in list(b.GetDrawings()):
  if isinstance(d,p.PCB_TEXT) and d.GetLayer() in [p.F_SilkS,p.B_SilkS]: b.Remove(d)
 project=json.loads((SOURCE/(name+'.kicad_pro')).read_text())
 ds=project['board']['design_settings'];ds['drc_exclusions']=[]
 ds['rules'].update(min_clearance=.2,min_track_width=.2,min_via_diameter=.6,min_through_hole_diameter=.3,min_via_annular_width=.15,min_copper_edge_clearance=.3,min_silk_clearance=.15,min_text_height=.8,min_text_thickness=.12)
 project['net_settings']['classes'][0].update(clearance=.2,track_width=.25,via_diameter=.6,via_drill=.3)
 (ROOT/(name+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
 assert manifest(b)==original
 p.SaveBoard(str(ROOT/(name+'_unrouted.kicad_pcb')),b)
 assert p.ExportSpecctraDSN(b,str(ROOT/(name+'.dsn')))
 text=(ROOT/(name+'.dsn')).read_text()
 text=re.sub(r'\(width\s+\d+\)', '(width 250)',text)
 text=re.sub(r'\(clearance\s+\d+', '(clearance 200',text)
 (ROOT/(name+'.dsn')).write_text(text)
 return b

def finish(name):
 b=p.LoadBoard(str(ROOT/(name+'_unrouted.kicad_pcb')))
 assert p.ImportSpecctraSES(b,str(ROOT/(name+'.ses')))
 assert manifest(b)==manifest(p.LoadBoard(str(SOURCE/(name+'.kicad_pcb'))))
 assert b.GetCopperLayerCount()==2
 assert all(isinstance(t,p.PCB_VIA) or t.GetLayer() in [p.F_Cu,p.B_Cu] for t in b.GetTracks())
 bb=b.GetBoardEdgesBoundingBox(); z=p.ZONE(b);z.SetLayer(p.B_Cu);z.SetNetCode(b.GetNetsByName()['GND'].GetNetCode());z.SetLocalClearance(p.FromMM(.2));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetMinThickness(p.FromMM(.2));poly=z.Outline();poly.NewOutline()
 for x,y in [(0.5,0.5),(99.5,0.5),(99.5,99.5),(0.5,99.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
 try:
  from silk_refs import apply_silk
  apply_silk(b)
 except ImportError:pass
 path=ROOT/(name+'.kicad_pcb');p.SaveBoard(str(path),b)
 result=subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','--output',str(ROOT/(name+'_drc.json')),str(path)],capture_output=True,text=True)
 (ROOT/(name+'_drc.log')).write_text(result.stdout+result.stderr)
 report=json.loads((ROOT/(name+'_drc.json')).read_text())
 summary={'board':name,'layers':2,'errors':sum(v.get('severity')=='error' for v in report['violations']),'warnings':sum(v.get('severity')=='warning' for v in report['violations']),'unconnected':len(report['unconnected_items']),'categories':dict(collections.Counter(v['type'] for v in report['violations']))}
 (ROOT/(name+'_status.json')).write_text(json.dumps(summary,indent=2)+'\n'); print(summary)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['prep','finish']);a.add_argument('boards',nargs='*');a.add_argument('--mode',default='fresh');args=a.parse_args()
 for name in args.boards or BOARDS:
  prep(name,args.mode) if args.action=='prep' else finish(name)
