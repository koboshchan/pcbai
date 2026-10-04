#!/usr/bin/python3
"""Isolated CRB change helpers. No autorouter or source-board mutation."""
from pathlib import Path
import sys,json,shutil
import pcbnew as p
D=Path(__file__).resolve().parent
R=D.parents[1]
sys.path.insert(0,str(R))
import successor100 as s
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
dc=R/'successor100/DC0_routed.kicad_pcb'
def write(name,value):
 s.write(D/name,value)
def copper(board):
 return {t.m_Uuid.AsString():[t.GetNetname(),t.GetLayer(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth(),isinstance(t,p.PCB_VIA),t.GetDrillValue() if isinstance(t,p.PCB_VIA) else None] for t in board.GetTracks()}
