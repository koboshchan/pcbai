#!/usr/bin/python3
"""Reserve an outboard coin volume without altering nets or copper rules."""
import json, subprocess
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
path=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
b=p.LoadBoard(str(path)); assert not list(b.GetTracks())
parts={f.GetReference():f for f in b.GetFootprints()}
before={r:{q.GetNumber():q.GetNetname() for q in f.Pads()} for r,f in parts.items()}
f=parts['U_REG5']; f.SetPosition(p.VECTOR2I(p.FromMM(66),p.FromMM(97))); f.SetOrientationDegrees(180)
f.SetLibDescription('ST L7805CV C111887; vertical TO220; IN1 GND2 OUT3; tab GND. Optional glued 25mm coin <2mm thick, no thermal credit without measurement. Outboard component exclusion x50.96..75.96 y99.8..124.8 mm, z0..35mm. See COIN_CLEARANCE.md.')
# Top-side projected exclusion. Back-side passives do not obstruct the above-board volume.
box=(50.96,99.8,75.96,124.8); collisions=[]
for r,g in parts.items():
 if r=='U_REG5' or g.GetLayer()!=p.F_Cu: continue
 bb=g.GetBoundingBox(False,False)
 x,y,w,h=[v/1e6 for v in (bb.GetX(),bb.GetY(),bb.GetWidth(),bb.GetHeight())]
 if x<box[2] and x+w>box[0] and y<box[3] and y+h>box[1]:collisions.append(r)
assert not collisions,collisions
assert before=={r:{q.GetNumber():q.GetNetname() for q in g.Pads()} for r,g in parts.items()}
p.SaveBoard(str(path),b)
drc=ROOT/'motherboard_coin_placement_drc.json'
subprocess.run(['kicad-cli','pcb','drc','--format','json','--all-track-errors','-o',str(drc),str(path)],check=True)
d=json.loads(drc.read_text()); errors=[v for v in d['violations'] if v.get('severity')=='error']; assert not errors,errors
report={'regulator_anchor_mm':[66,97],'rotation_deg':180,'component_free_volume_mm':{'x':[50.96,75.96],'y':[99.8,124.8],'z':[0,35]},'top_component_collisions':collisions,'pad_nets_preserved':True,'copper_keepout_added':False,'coin_thermal_credit':False,'placement_errors':len(errors),'placement_opens':len(d.get('unconnected_items',[])),'daughter_slot_contact_y_max_mm':89.615,'coin_y_min_mm':99.8,'mechanical_assembly_measurement_required':True}
(ROOT/'coin_clearance_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
