#!/usr/bin/env python3
import os
import re
import sys
import subprocess
import pcbnew
from collections import defaultdict

WORKSPACE = "/Users/lucaszhang/pcbai"
JAVA_BIN = "/opt/homebrew/opt/openjdk@25/bin/java"
JAR_PATH = os.path.join(WORKSPACE, "freerouting.jar")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

import build_dc2_relu_single_layer
pcb_file = os.path.join(WORKSPACE, "daughtercard2_relu_l1.kicad_pcb")
dsn_file = os.path.join(WORKSPACE, "daughtercard2_relu_l1.dsn")
ses_file = os.path.join(WORKSPACE, "daughtercard2_relu_l1.ses")
drc_json = os.path.join(WORKSPACE, "daughtercard2_relu_l1_drc.json")

print("1. Generating clean DC2 board...")
build_dc2_relu_single_layer.generate_dc2_board(pcb_file)

print("2. Exporting and patching DSN...")
board = pcbnew.LoadBoard(pcb_file)
pcbnew.ExportSpecctraDSN(board, dsn_file)

with open(dsn_file, "r") as f:
    dsn = f.read()

# Replace via diameter with 1800 um (1.8 mm)
dsn = re.sub(r'\(shape\s+\(circle\s+F\.Cu\s+\d+\)\)', '(shape (circle F.Cu 1800))', dsn)
dsn = re.sub(r'\(shape\s+\(circle\s+B\.Cu\s+\d+\)\)', '(shape (circle B.Cu 1800))', dsn)

# Set width to 350 um and clearance to 500 um
dsn = re.sub(r'\(width\s+\d+\)', '(width 350)', dsn)
dsn = re.sub(r'\(clearance\s+\d+\)', '(clearance 500)', dsn)
dsn = re.sub(r'\(clearance\s+\d+\s+\(type smd_smd\)\)', '(clearance 500 (type smd_smd))', dsn)

with open(dsn_file, "w") as f:
    f.write(dsn)

print("3. Running FreeRouting...")
if os.path.exists(ses_file): os.remove(ses_file)
cmd = [
    JAVA_BIN, "-jar", JAR_PATH,
    "-de", dsn_file,
    "-do", ses_file,
    "--gui.enabled=false",
    "-mp", "60",
    "-mt", "1"
]
subprocess.run(cmd, check=True)

print("4. Importing SES and converting to Single-Layer Jumper Wire Footprints...")
board = pcbnew.LoadBoard(pcb_file)
ok = pcbnew.ImportSpecctraSES(board, ses_file)
print(f"   ImportSpecctraSES: {ok}")

bcu_tracks = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu]
vias = [t for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]

adj = defaultdict(set)
edge_net = {}
for t in bcu_tracks:
    p1 = (t.GetStart().x, t.GetStart().y)
    p2 = (t.GetEnd().x, t.GetEnd().y)
    adj[p1].add(p2)
    adj[p2].add(p1)
    edge_net[(min(p1, p2), max(p1, p2))] = t.GetNet()

visited = set()
chains = []
for p in adj:
    if p not in visited:
        comp = []
        q = [p]
        visited.add(p)
        while q:
            curr = q.pop()
            comp.append(curr)
            for nbr in adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    q.append(nbr)
        chains.append(comp)

print(f"   Found {len(chains)} jumper chains.")

lset = pcbnew.LSET()
lset.AddLayer(pcbnew.F_Cu)
lset.AddLayer(pcbnew.B_Cu)
lset.AddLayer(pcbnew.F_Mask)
lset.AddLayer(pcbnew.B_Mask)

jumper_count = 0
for idx, c in enumerate(chains):
    deg1 = [pt for pt in c if len(adj[pt]) == 1]
    if len(deg1) != 2:
        continue
    p1, p2 = deg1
    net = None
    for nbr in adj[p1]:
        net = edge_net.get((min(p1, nbr), max(p1, nbr)))
        if net: break
    if not net: continue
    
    jumper_count += 1
    ref = f"W{jumper_count}"
    
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue("JUMPER")
    fp.SetFPID(pcbnew.LIB_ID("", "Jumper_Wire"))
    fp.SetKeywords("net tie")
    
    cx = (p1[0] + p2[0]) // 2
    cy = (p1[1] + p2[1]) // 2
    fp.SetPosition(pcbnew.VECTOR2I(cx, cy))
    
    pad1 = pcbnew.PAD(fp)
    pad1.SetNumber("1")
    pad1.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad1.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad1.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
    pad1.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.9), pcbnew.FromMM(0.9)))
    pad1.SetPosition(pcbnew.VECTOR2I(p1[0], p1[1]))
    pad1.SetLayerSet(lset)
    pad1.SetNet(net)
    fp.Add(pad1)
    
    pad2 = pcbnew.PAD(fp)
    pad2.SetNumber("2")
    pad2.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad2.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad2.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
    pad2.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.9), pcbnew.FromMM(0.9)))
    pad2.SetPosition(pcbnew.VECTOR2I(p2[0], p2[1]))
    pad2.SetLayerSet(lset)
    pad2.SetNet(net)
    fp.Add(pad2)
    
    line = pcbnew.PCB_SHAPE(fp)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(pcbnew.VECTOR2I(p1[0], p1[1]))
    line.SetEnd(pcbnew.VECTOR2I(p2[0], p2[1]))
    line.SetWidth(pcbnew.FromMM(0.2))
    line.SetLayer(pcbnew.F_SilkS)
    fp.Add(line)
    
    board.Add(fp)

# Remove all B.Cu tracks and vias
for t in bcu_tracks:
    board.Remove(t)
for v in vias:
    board.Remove(v)

board.Save(pcb_file)

# Inject net tie groups
with open(pcb_file) as f:
    text = f.read()
text = text.replace('(tags "net tie")', '(tags "net tie")\n    (net_tie_pad_groups "1,2")')
with open(pcb_file, "w") as f:
    f.write(text)

print(f"   Created {jumper_count} jumpers. Removed all B.Cu and vias.")

print("5. Running KiCad DRC...")
cmd_drc = [
    KICAD_CLI, "pcb", "drc",
    "--severity-all",
    "--format", "json",
    "-o", drc_json,
    pcb_file
]
subprocess.run(cmd_drc, check=False)
import json
with open(drc_json) as f:
    drc = json.load(f)

viols = drc.get("violations", [])
unconn = drc.get("unconnected_items", [])
print(f"   DRC Result: {len(viols)} violations, {len(unconn)} unconnected items")
for v in viols[:5]:
    print("    Violation:", v.get("description"), v.get("type"))
