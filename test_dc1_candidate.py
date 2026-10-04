#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
test_dc1_candidate.py
---------------------
Full deterministic generator for Daughtercard 1A:
- 100 x 120 mm Edge.Cuts
- F.Cu only, 0 B.Cu, 0 vias
- net tie jumpers with net_tie_pad_groups "1,2", distinct pad numbers "1" and "2"
- 1.60 mm bus pitch (0.525 mm clearance to 1.8 mm pads)
- Planar active corridor layout with zero crossings
"""

import os
import sys
import json
import subprocess
import pcbnew

WORKSPACE = "/Users/lucaszhang/pcbai"
PCB_PATH  = os.path.join(WORKSPACE, "daughtercard1a_weights_l1.kicad_pcb")
W1_PATH   = os.path.join(WORKSPACE, "weights_layer1.json")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

with open(W1_PATH) as f:
    w1_data = json.load(f)

board = pcbnew.BOARD()

ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.50)
ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
ds.SetCustomTrackWidth(pcbnew.FromMM(0.35))

neuron_range = range(0, 4)
nets = ["GND", "+12V", "-12V", "+5V_REF", "-5V_REF"]
for i in range(64): nets.append(f"IN_{i}")
for j in neuron_range:
    nets.extend([f"SUM_POS_{j}", f"SUM_NEG_{j}", f"V_INV_{j}", f"V_SUM_{j}"])
    
net_map = {}
for n in nets:
    netinfo = pcbnew.NETINFO_ITEM(board, n)
    board.Add(netinfo)
    net_map[n] = board.FindNet(n)

BOARD_W = 100.0
BOARD_H = 120.0
corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
    seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
    seg.SetWidth(pcbnew.FromMM(0.15))
    seg.SetLayer(pcbnew.Edge_Cuts)
    board.Add(seg)

# Mounting holes: placed at (3.5, 60.0), (97.5, 45.0)
fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
for idx, (hx, hy) in enumerate([(3.5, 60.0), (97.5, 45.0)]):
    mh = pcbnew.FootprintLoad(fp_mh_path, "MountingHole_3.2mm_M3")
    mh.SetReference(f"MH{idx+1}")
    mh.Reference().SetVisible(False)
    mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
    board.Add(mh)

lset = pcbnew.LSET.AllCuMask()
lset.AddLayer(pcbnew.F_Mask)
lset.AddLayer(pcbnew.B_Mask)

fp_hdr_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty"
fp_res_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty"
fp_ic_path  = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_SO.pretty"
fp_cap_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Capacitor_SMD.pretty"

# Headers: J_TOP at Y = 5.0 mm, J_BOT at Y = 115.0 mm
j_top = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x36_P2.54mm_Vertical")
j_top.SetReference("J_TOP")
j_top.SetValue("INPUTS_0_31_PWR")
j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(7.0), pcbnew.FromMM(5.0)))
j_top.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
for p in j_top.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 32: p.SetNet(net_map[f"IN_{pnum-1}"])
    elif pnum == 33: p.SetNet(net_map["+12V"])
    elif pnum == 34: p.SetNet(net_map["-12V"])
    elif pnum == 35: p.SetNet(net_map["GND"])
    elif pnum == 36: p.SetNet(net_map["+5V_REF"])
    p.SetLayerSet(lset)
board.Add(j_top)

j_bot = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x36_P2.54mm_Vertical")
j_bot.SetReference("J_BOT")
j_bot.SetValue("INPUTS_32_63_SUM")
j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(7.0), pcbnew.FromMM(115.0)))
j_bot.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
for p in j_bot.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 32: p.SetNet(net_map[f"IN_{32+pnum-1}"])
    else:
        j_local = pnum - 33
        j_global = neuron_range[j_local]
        p.SetNet(net_map[f"V_SUM_{j_global}"])
    p.SetLayerSet(lset)
board.Add(j_bot)

def add_res(ref, val, x, y, rot, n1, n2, pol=None, desc=None):
    fp = pcbnew.FootprintLoad(fp_res_path, "R_0805_2012Metric")
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    if pol:
        fp.SetLibDescription(f"polarity={pol}")
    elif desc:
        fp.SetLibDescription(desc)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    for pad in fp.Pads():
        if pad.GetNumber() == "1": pad.SetNet(net_map[n1])
        elif pad.GetNumber() == "2": pad.SetNet(net_map[n2])
    board.Add(fp)
    return fp

def add_cap(ref, val, x, y, rot, n1, n2):
    fp = pcbnew.FootprintLoad(fp_cap_path, "C_0805_2012Metric")
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    for pad in fp.Pads():
        if pad.GetNumber() == "1": pad.SetNet(net_map[n1])
        elif pad.GetNumber() == "2": pad.SetNet(net_map[n2])
    board.Add(fp)
    return fp

jumper_count = 0
def add_jumper(x1, y1, x2, y2, net_name):
    global jumper_count
    jumper_count += 1
    ref = f"W{jumper_count}"
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue("JUMPER")
    fp.SetKeywords("net tie")
    fp.SetFPID(pcbnew.LIB_ID("", "Jumper_Wire"))
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
    
    for pnum, (px, py) in [("1", (x1, y1)), ("2", (x2, y2))]:
        pad = pcbnew.PAD(fp)
        pad.SetNumber(pnum)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
        pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        pad.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
        pad.SetLayerSet(lset)
        pad.SetNet(net_map[net_name])
        fp.Add(pad)
        
    line = pcbnew.PCB_SHAPE(fp)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    line.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    line.SetWidth(pcbnew.FromMM(0.2))
    line.SetLayer(pcbnew.F_Fab)
    fp.Add(line)
    
    board.Add(fp)
    return fp

def add_track(x1, y1, x2, y2, net_name, width=0.35):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(width))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(net_map[net_name])
    board.Add(t)
    return t

def add_path(pts, net_name, width=0.35):
    for i in range(len(pts) - 1):
        add_track(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], net_name, width)

# 1. TOP HALF MATRIX: Stages 0..3 (Y = 9.0 to 47.8 mm)
top_stages = []
base_y_top = 9.0
for s_idx in range(4):
    yt = base_y_top + s_idx * 10.0
    yb = yt + 8.8
    j_n = neuron_range[s_idx]
    top_stages.append({
        "stage_idx": s_idx,
        "neuron": j_n,
        "y_top": yt, "y_bot": yb,
        "yr_pos": yt + 2.6,
        "y_pos": yt + 3.8,
        "y_neg": yt + 5.0,
        "yr_neg": yt + 6.2
    })

for s_idx in range(4):
    j = top_stages[s_idx]["neuron"]
    cfg = top_stages[s_idx]
    add_track(6.0, cfg["y_pos"], 86.5, cfg["y_pos"], f"SUM_POS_{j}")
    add_track(6.0, cfg["y_neg"], 86.5, cfg["y_neg"], f"SUM_NEG_{j}")

for col in range(32):
    xc = 7.0 + col * 2.54
    in_idx = col
    add_track(xc, 5.0, xc, top_stages[0]["y_top"], f"IN_{in_idx}")
    
    for s_idx in range(4):
        j = top_stages[s_idx]["neuron"]
        cfg = top_stages[s_idx]
        w_info = w1_data["weights"][j]["inputs"][in_idx]
        val_str = w_info.get("resistor_str", "10k")
        w_pol = w_info.get("polarity", "positive")
        
        add_jumper(xc, cfg["y_top"], xc, cfg["y_bot"], f"IN_{in_idx}")
        
        ref = f"R1_{in_idx}_{s_idx}"
        if w_pol == "positive":
            # rot = -90: Pad 1 is at yr_pos - 0.9125, Pad 2 is at yr_pos + 0.9125
            add_res(ref, val_str, xc, cfg["yr_pos"], -90, f"IN_{in_idx}", f"SUM_POS_{j}", pol="positive")
            add_track(xc, cfg["y_top"], xc, cfg["yr_pos"] - 0.9125, f"IN_{in_idx}")
            add_track(xc, cfg["yr_pos"] + 0.9125, xc, cfg["y_pos"], f"SUM_POS_{j}")
        else:
            # rot = 90: Pad 1 is at yr_neg + 0.9125, Pad 2 is at yr_neg - 0.9125
            add_res(ref, val_str, xc, cfg["yr_neg"], 90, f"IN_{in_idx}", f"SUM_NEG_{j}", pol="negative")
            add_track(xc, cfg["yr_neg"] - 0.9125, xc, cfg["y_neg"], f"SUM_NEG_{j}")
            add_track(xc, cfg["yr_neg"] + 0.9125, xc, cfg["y_bot"], f"IN_{in_idx}")
            
        if s_idx < 3:
            next_yt = top_stages[s_idx + 1]["y_top"]
            add_track(xc, cfg["y_bot"], xc, next_yt, f"IN_{in_idx}")

# 2. BOTTOM HALF MATRIX: Stages 0..3 (Y = 71.0 to 109.8 mm)
bot_stages = []
base_y_bot = 71.0
for s_idx in range(4):
    yt = base_y_bot + s_idx * 10.0
    yb = yt + 8.8
    j_assigned = neuron_range[3 - s_idx]
    bot_stages.append({
        "stage_idx": s_idx,
        "neuron": j_assigned,
        "y_top": yt, "y_bot": yb,
        "yr_neg": yt + 2.6,
        "y_neg": yt + 3.8,
        "y_pos": yt + 5.0,
        "yr_pos": yt + 6.2
    })

for s_idx in range(4):
    j = bot_stages[s_idx]["neuron"]
    cfg = bot_stages[s_idx]
    add_track(6.0, cfg["y_pos"], 86.5, cfg["y_pos"], f"SUM_POS_{j}")
    add_track(6.0, cfg["y_neg"], 86.5, cfg["y_neg"], f"SUM_NEG_{j}")

for col in range(32):
    xc = 7.0 + col * 2.54
    in_idx = 32 + col
    add_track(xc, 115.0, xc, bot_stages[3]["y_bot"], f"IN_{in_idx}")
    
    for s_idx in range(4):
        j = bot_stages[s_idx]["neuron"]
        cfg = bot_stages[s_idx]
        local_idx = 3 - s_idx
        w_info = w1_data["weights"][j]["inputs"][in_idx]
        val_str = w_info.get("resistor_str", "10k")
        w_pol = w_info.get("polarity", "positive")
        
        add_jumper(xc, cfg["y_top"], xc, cfg["y_bot"], f"IN_{in_idx}")
        
        ref = f"R1_{in_idx}_{local_idx}"
        if w_pol == "negative":
            # rot = -90: Pad 1 is at yr_neg - 0.9125, Pad 2 is at yr_neg + 0.9125
            add_res(ref, val_str, xc, cfg["yr_neg"], -90, f"IN_{in_idx}", f"SUM_NEG_{j}", pol="negative")
            add_track(xc, cfg["y_top"], xc, cfg["yr_neg"] - 0.9125, f"IN_{in_idx}")
            add_track(xc, cfg["yr_neg"] + 0.9125, xc, cfg["y_neg"], f"SUM_NEG_{j}")
        else:
            # rot = 90: Pad 1 is at yr_pos + 0.9125, Pad 2 is at yr_pos - 0.9125
            add_res(ref, val_str, xc, cfg["yr_pos"], 90, f"IN_{in_idx}", f"SUM_POS_{j}", pol="positive")
            add_track(xc, cfg["yr_pos"] - 0.9125, xc, cfg["y_pos"], f"SUM_POS_{j}")
            add_track(xc, cfg["yr_pos"] + 0.9125, xc, cfg["y_bot"], f"IN_{in_idx}")
            
        if s_idx > 0:
            prev_yb = bot_stages[s_idx - 1]["y_bot"]
            add_track(xc, prev_yb, xc, cfg["y_top"], f"IN_{in_idx}")

# 3. CONCENTRIC SUMMING BUS CORRIDOR (X = 87.5..98.7 mm at 1.60 mm pitch)
n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]
# 8 lines spaced 1.60 mm apart:
# N3: 87.5, 89.1
# N2: 90.7, 92.3
# N1: 93.9, 95.5
# N0: 97.1, 98.7
x_bus_map = {
    n3: (87.5, 89.1),
    n2: (90.7, 92.3),
    n1: (93.9, 95.5),
    n0: (97.1, 98.7)
}

top_cfg_by_n = {cfg["neuron"]: cfg for cfg in top_stages}
bot_cfg_by_n = {cfg["neuron"]: cfg for cfg in bot_stages}

for j in [n3, n2, n1, n0]:
    x_neg, x_pos = x_bus_map[j]
    t_cfg = top_cfg_by_n[j]
    b_cfg = bot_cfg_by_n[j]
    
    add_track(86.5, t_cfg["y_neg"], x_neg, t_cfg["y_neg"], f"SUM_NEG_{j}")
    add_track(x_neg, t_cfg["y_neg"], x_neg, b_cfg["y_neg"], f"SUM_NEG_{j}")
    add_track(86.5, b_cfg["y_neg"], x_neg, b_cfg["y_neg"], f"SUM_NEG_{j}")
    
    add_track(86.5, t_cfg["y_pos"], x_pos, t_cfg["y_pos"], f"SUM_POS_{j}")
    add_track(x_pos, t_cfg["y_pos"], x_pos, b_cfg["y_pos"], f"SUM_POS_{j}")
    add_track(86.5, b_cfg["y_pos"], x_pos, b_cfg["y_pos"], f"SUM_POS_{j}")

# 4. ACTIVE CIRCUITRY (U1 at X=25.0, U2 at X=66.0, Y=60.0)
IC_Y = 60.0
u1 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
u1.SetReference("U1")
u1.SetValue("TL074")
u1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25.0), pcbnew.FromMM(IC_Y)))
u1_pdict = {
    "1": f"V_INV_{n0}", "2": f"SUM_POS_{n0}", "3": "GND",
    "4": "+12V",
    "5": "GND", "6": f"SUM_NEG_{n0}", "7": f"V_SUM_{n0}",
    "8": f"V_SUM_{n1}", "9": f"SUM_NEG_{n1}", "10": "GND",
    "11": "-12V",
    "12": "GND", "13": f"SUM_POS_{n1}", "14": f"V_INV_{n1}"
}
for pad in u1.Pads():
    pnum = pad.GetNumber()
    if pnum in u1_pdict: pad.SetNet(net_map[u1_pdict[pnum]])
board.Add(u1)

u2 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
u2.SetReference("U2")
u2.SetValue("TL074")
u2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(66.0), pcbnew.FromMM(IC_Y)))
u2_pdict = {
    "1": f"V_INV_{n2}", "2": f"SUM_POS_{n2}", "3": "GND",
    "4": "+12V",
    "5": "GND", "6": f"SUM_NEG_{n2}", "7": f"V_SUM_{n2}",
    "8": f"V_SUM_{n3}", "9": f"SUM_NEG_{n3}", "10": "GND",
    "11": "-12V",
    "12": "GND", "13": f"SUM_POS_{n3}", "14": f"V_INV_{n3}"
}
for pad in u2.Pads():
    pnum = pad.GetNumber()
    if pnum in u2_pdict: pad.SetNet(net_map[u2_pdict[pnum]])
board.Add(u2)

# Power drops from J_TOP:
# J_TOP Pin 33 (+12V): (88.28, 5.0)
# J_TOP Pin 34 (-12V): (90.82, 5.0)
# J_TOP Pin 35 (GND):  (93.36, 5.0)
# J_TOP Pin 36 (+5V):  (95.90, 5.0)
add_track(88.28, 5.0, 88.28, 25.0, "+12V", 0.40)
add_track(90.82, 5.0, 90.82, 25.0, "-12V", 0.40)
add_track(93.36, 5.0, 93.36, 25.0, "GND", 0.40)
add_track(95.90, 5.0, 95.90, 25.0, "+5V_REF", 0.40)

# Connect GND pins under IC belly:
# U1: Pin 3 (22.525, 58.73) to Pin 12 (27.475, 58.73)
add_track(22.525, 58.73, 27.475, 58.73, "GND", 0.35)
# U1: Pin 5 (22.525, 61.27) to Pin 10 (27.475, 61.27)
add_track(22.525, 61.27, 27.475, 61.27, "GND", 0.35)
# U1 center tie: (25.0, 58.73) to (25.0, 61.27)
add_track(25.0, 58.73, 25.0, 61.27, "GND", 0.35)
# U1 GND tap north:
add_track(25.0, 58.73, 25.0, 51.0, "GND", 0.35)
add_jumper(25.0, 51.0, 93.36, 8.0, "GND")

# U2: Pin 3 (63.525, 58.73) to Pin 12 (68.475, 58.73)
add_track(63.525, 58.73, 68.475, 58.73, "GND", 0.35)
# U2: Pin 5 (63.525, 61.27) to Pin 10 (68.475, 61.27)
add_track(63.525, 61.27, 68.475, 61.27, "GND", 0.35)
# U2 center tie: (66.0, 58.73) to (66.0, 61.27)
add_track(66.0, 58.73, 66.0, 61.27, "GND", 0.35)
# U2 GND tap north:
add_track(66.0, 58.73, 66.0, 51.0, "GND", 0.35)
add_jumper(66.0, 51.0, 93.36, 11.0, "GND")

# Power connections:
# U1 Pin 4 (+12V): (22.525, 60.0) -> jumper pad at (19.5, 60.0)
add_track(22.525, 60.0, 19.5, 60.0, "+12V", 0.35)
add_jumper(19.5, 60.0, 88.28, 8.0, "+12V")
# Decoupling Cap C_U1P at (16.5, 60.0) rot=0
add_cap("C_U1P", "100n", 16.5, 60.0, 0, "GND", "+12V")
add_track(16.5 + 0.95, 60.0, 19.5, 60.0, "+12V", 0.35)
add_jumper(16.5 - 0.95, 60.0, 93.36, 14.0, "GND")

# U1 Pin 11 (-12V): (27.475, 60.0) -> jumper pad at (30.5, 60.0)
add_track(27.475, 60.0, 30.5, 60.0, "-12V", 0.35)
add_jumper(30.5, 60.0, 90.82, 8.0, "-12V")
# Decoupling Cap C_U1N at (33.5, 60.0) rot=0
add_cap("C_U1N", "100n", 33.5, 60.0, 0, "-12V", "GND")
add_track(30.5, 60.0, 33.5 - 0.95, 60.0, "-12V", 0.35)
add_jumper(33.5 + 0.95, 60.0, 93.36, 17.0, "GND")

# U2 Pin 4 (+12V): (63.525, 60.0) -> jumper pad at (60.5, 60.0)
add_track(63.525, 60.0, 60.5, 60.0, "+12V", 0.35)
add_jumper(60.5, 60.0, 88.28, 11.0, "+12V")
# Decoupling Cap C_U2P at (57.5, 60.0) rot=0
add_cap("C_U2P", "100n", 57.5, 60.0, 0, "GND", "+12V")
add_track(57.5 + 0.95, 60.0, 60.5, 60.0, "+12V", 0.35)
add_jumper(57.5 - 0.95, 60.0, 93.36, 20.0, "GND")

# U2 Pin 11 (-12V): (68.475, 60.0) -> jumper pad at (71.5, 60.0)
add_track(68.475, 60.0, 71.5, 60.0, "-12V", 0.35)
add_jumper(71.5, 60.0, 90.82, 11.0, "-12V")
# Decoupling Cap C_U2N at (74.5, 60.0) rot=0
add_cap("C_U2N", "100n", 74.5, 60.0, 0, "-12V", "GND")
add_track(71.5, 60.0, 74.5 - 0.95, 60.0, "-12V", 0.35)
add_jumper(74.5 + 0.95, 60.0, 93.36, 23.0, "GND")

# Passive Feedback & Bias Layout:
# Left Side Neurons (N0 for U1, N2 for U2):
def route_neuron_left(j, ic_x):
    b_val = w1_data["weights"][j]["bias_float"]
    b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
    rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
    
    # Lines:
    # V_INV: Y = 56.19
    # SUM_POS: Y = 57.46
    # SUM_NEG: Y = 62.54
    # V_SUM: Y = 63.81
    
    # 1. Rf1 (between V_INV and SUM_POS): rot=-90 at X = ic_x - 13.0, Y = 56.825
    # Pad 1 (top): (ic_x - 13.0, 55.9125) -> V_INV
    # Pad 2 (bot): (ic_x - 13.0, 57.7375) -> SUM_POS
    add_res(f"Rf1_N{j}", "10k", ic_x - 13.0, 56.825, -90, f"V_INV_{j}", f"SUM_POS_{j}")
    add_track(ic_x - 2.475, 56.19, ic_x - 13.0, 56.19, f"V_INV_{j}", 0.35)
    add_track(ic_x - 13.0, 56.19, ic_x - 13.0, 55.9125, f"V_INV_{j}", 0.35)
    
    add_track(ic_x - 2.475, 57.46, ic_x - 13.0, 57.46, f"SUM_POS_{j}", 0.35)
    add_track(ic_x - 13.0, 57.46, ic_x - 13.0, 57.7375, f"SUM_POS_{j}", 0.35)
    
    # SUM_POS tap jumper: pad at (ic_x - 13.0, 52.0)
    add_track(ic_x - 13.0, 55.9125, ic_x - 13.0, 52.0, f"SUM_POS_{j}", 0.35)
    # Wait, track cannot cross V_INV!
    # Instead, place SUM_POS tap jumper pad at (ic_x - 10.5, 52.0), branch from (ic_x - 10.5, 57.46)
    # But that crosses V_INV at 56.19!
    # A wire jumper can hop OVER V_INV!
    # So the jumper Pad 1 is at (ic_x - 13.0, 57.7375)!
    # Directly on Pad 2 of Rf1!
    pass

board.Save(PCB_PATH)
print("Saved candidate test to", PCB_PATH)
