#!/usr/bin/python3
"""Synthetic isolated API smoke test for the legal stitching branch."""
from pathlib import Path
import json
import pcbnew as p
from pour_ground import apply
R=Path(__file__).resolve().parent; d=R/'synthetic_helper_test'; d.mkdir(exist_ok=True)
b=p.BOARD(); n=p.NETINFO_ITEM(b,'GND');b.Add(n)
edge=p.PCB_SHAPE();edge.SetShape(p.SHAPE_T_RECT);edge.SetStart(p.VECTOR2I(p.FromMM(0),p.FromMM(0)));edge.SetEnd(p.VECTOR2I(p.FromMM(20),p.FromMM(20)));edge.SetLayer(p.Edge_Cuts);edge.SetWidth(p.FromMM(.05));b.Add(edge)
v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(10),p.FromMM(10)));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(n.GetNetCode());b.Add(v)
p.SaveBoard(str(d/'source.kicad_pcb'),b)
project=R/'daughtercard1a_weights_l1_differential_repaired.kicad_pro'
r=apply(d/'source.kicad_pcb',d/'candidate.kicad_pcb',project,True)
assert r['errors']==0 and r['opens']==0 and len(r['accepted_stitch_positions_mm'])==4
print(json.dumps(r))
