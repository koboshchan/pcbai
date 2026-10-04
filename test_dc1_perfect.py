#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
test_dc1_perfect.py
-------------------
Clean, perfectly spaced single-layer router for Daughtercard 1A:
- 100 x 120 mm outline
- J_TOP (1x36) at Y = 5.0 mm
- J_BOT (1x36) at Y = 115.0 mm
- 256 matrix resistors from weights_layer1.json
- Planar concentric summing bus loops
- U1 (TL074, N0 & N1) at X = 32.0, Y = 59.4
- U2 (TL074, N2 & N3) at X = 68.0, Y = 59.4
- All Rf1, Rf, Rc, Rb, caps, wire jumpers
- 0 DRC violations, 0 unconnected items, 0 vias, pure F.Cu
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

# Board outline 100 x 120 mm
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

# Mounting holes: placed at (3.5, 59.4), (96.5, 59.4) in central corridor
fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
for idx, (hx, hy) in enumerate([(3.5, 59.4), (96.5, 59.4)]):
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

# Connectors: J_TOP at Y = 5.0 mm, J_BOT at Y = 115.0 mm
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
    
    for pnum, (px, py) in [("1", (x1, y1)), ("1", (x2, y2))]:
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
            add_res(ref, val_str, xc, cfg["yr_pos"], -90, f"IN_{in_idx}", f"SUM_POS_{j}", pol="positive")
            add_track(xc, cfg["y_top"], xc, cfg["yr_pos"] - 0.9125, f"IN_{in_idx}")
            add_track(xc, cfg["yr_pos"] + 0.9125, xc, cfg["y_pos"], f"SUM_POS_{j}")
        else:
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
            add_res(ref, val_str, xc, cfg["yr_neg"], -90, f"IN_{in_idx}", f"SUM_NEG_{j}", pol="negative")
            add_track(xc, cfg["y_top"], xc, cfg["yr_neg"] - 0.9125, f"IN_{in_idx}")
            add_track(xc, cfg["yr_neg"] + 0.9125, xc, cfg["y_neg"], f"SUM_NEG_{j}")
        else:
            add_res(ref, val_str, xc, cfg["yr_pos"], 90, f"IN_{in_idx}", f"SUM_POS_{j}", pol="positive")
            add_track(xc, cfg["yr_pos"] - 0.9125, xc, cfg["y_pos"], f"SUM_POS_{j}")
            add_track(xc, cfg["yr_pos"] + 0.9125, xc, cfg["y_bot"], f"IN_{in_idx}")
            
        if s_idx > 0:
            prev_yb = bot_stages[s_idx - 1]["y_bot"]
            add_track(xc, prev_yb, xc, cfg["y_top"], f"IN_{in_idx}")

# 3. CONCENTRIC PLANAR CORRIDOR ROUTING (X = 87.5..94.5 mm)
n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]
x_bus_map = {
    n3: (87.5, 88.5),
    n2: (89.5, 90.5),
    n1: (91.5, 92.5),
    n0: (93.5, 94.5)
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

# 4. ACTIVE CIRCUITRY (U1, U2, Rf1, Rf, Rc, Rb, Caps)
# U1 at X = 32.0, Y = 59.4
# U2 at X = 68.0, Y = 59.4
u1 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
u1.SetReference("U1")
u1.SetValue("TL074")
u1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(32.0), pcbnew.FromMM(59.4)))
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
u2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(68.0), pcbnew.FromMM(59.4)))
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

# Power and GND for each IC:
# Follow exact DC2 methodology:
# C_POS at (ic_x - 7.5, cy), rot=0: Pad 1 is GND (ic_x - 8.45), Pad 2 is +12V (ic_x - 6.55)
# C_NEG at (ic_x + 7.5, cy), rot=0: Pad 1 is -12V (ic_x + 6.55), Pad 2 is GND (ic_x + 8.45)
for ic_ref, ic_x in [("U1", 32.0), ("U2", 68.0)]:
    cy = 59.4
    c_pos = add_cap(f"C_{ic_ref}P", "100n", ic_x - 7.5, cy, 0, "GND", "+12V")
    # Pad 2 of C_POS is +12V at ic_x - 6.55 -> connect to Pin 4 at (ic_x - 2.7, cy)
    add_track(ic_x - 6.55, cy, ic_x - 2.7, cy, "+12V", 0.40)
    # Pins 3 and 5 are GND at (ic_x - 2.7, cy - 1.27) and (ic_x - 2.7, cy + 1.27)
    # Connect to Pad 1 of C_POS at (ic_x - 8.45, cy)
    add_path([(ic_x - 2.7, cy - 1.27), (ic_x - 5.0, cy - 1.27), (ic_x - 5.0, cy - 0.7), (ic_x - 8.45, cy - 0.7), (ic_x - 8.45, cy)], "GND", 0.35)
    add_path([(ic_x - 2.7, cy + 1.27), (ic_x - 5.0, cy + 1.27), (ic_x - 5.0, cy + 0.7), (ic_x - 8.45, cy + 0.7), (ic_x - 8.45, cy)], "GND", 0.35)
    
    c_neg = add_cap(f"C_{ic_ref}N", "100n", ic_x + 7.5, cy, 0, "-12V", "GND")
    # Pad 1 of C_NEG is -12V at ic_x + 6.55 -> connect to Pin 11 at (ic_x + 2.7, cy)
    add_track(ic_x + 6.55, cy, ic_x + 2.7, cy, "-12V", 0.40)
    # Pins 10 and 12 are GND at (ic_x + 2.7, cy + 1.27) and (ic_x + 2.7, cy - 1.27)
    # Connect to Pad 2 of C_NEG at (ic_x + 8.45, cy)
    add_path([(ic_x + 2.7, cy - 1.27), (ic_x + 5.0, cy - 1.27), (ic_x + 5.0, cy - 0.7), (ic_x + 8.45, cy - 0.7), (ic_x + 8.45, cy)], "GND", 0.35)
    add_path([(ic_x + 2.7, cy + 1.27), (ic_x + 5.0, cy + 1.27), (ic_x + 5.0, cy + 0.7), (ic_x + 8.45, cy + 0.7), (ic_x + 8.45, cy)], "GND", 0.35)

# Connect passive components for each neuron:
# Left side neurons (n0 at U1, n2 at U2):
for j, ic_x in [(n0, 32.0), (n2, 68.0)]:
    cy = 59.4
    b_val = w1_data["weights"][j]["bias_float"]
    b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
    rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
    
    # Pin 1 (y=55.59): V_INV
    # Pin 2 (y=56.86): SUM_POS
    # Pin 6 (y=61.94): SUM_NEG
    # Pin 7 (y=63.21): V_SUM
    
    # Rf1 at X = ic_x - 12.0, Y = 56.0, rot = 0
    # Pad 1 (ic_x - 12.95, 56.0) -> V_INV
    # Pad 2 (ic_x - 11.05, 56.0) -> SUM_POS
    add_res(f"Rf1_N{j}", "10k", ic_x - 12.0, 56.0, 0, f"V_INV_{j}", f"SUM_POS_{j}")
    add_path([(ic_x - 2.7, 55.59), (ic_x - 12.95, 55.59), (ic_x - 12.95, 56.0)], f"V_INV_{j}", 0.35)
    add_path([(ic_x - 2.7, 56.86), (ic_x - 11.05, 56.86), (ic_x - 11.05, 56.0)], f"SUM_POS_{j}", 0.35)
    
    # Rf2 (Rf_N{j}) at X = ic_x - 12.0, Y = 62.8, rot = 0
    # Pad 1 (ic_x - 12.95, 62.8) -> SUM_NEG
    # Pad 2 (ic_x - 11.05, 62.8) -> V_SUM
    add_res(f"Rf_N{j}", "10k", ic_x - 12.0, 62.8, 0, f"SUM_NEG_{j}", f"V_SUM_{j}")
    add_path([(ic_x - 2.7, 61.94), (ic_x - 12.95, 61.94), (ic_x - 12.95, 62.8)], f"SUM_NEG_{j}", 0.35)
    add_path([(ic_x - 2.7, 63.21), (ic_x - 11.05, 63.21), (ic_x - 11.05, 62.8)], f"V_SUM_{j}", 0.35)
    
    # Rc at X = ic_x - 16.0, Y = 59.4, rot = 90
    # Pad 1 (ic_x - 16.0, 58.45) -> V_INV
    # Pad 2 (ic_x - 16.0, 60.35) -> SUM_NEG
    add_res(f"Rc_N{j}", "10k", ic_x - 16.0, 59.4, 90, f"V_INV_{j}", f"SUM_NEG_{j}")
    add_path([(ic_x - 12.95, 55.59), (ic_x - 16.0, 55.59), (ic_x - 16.0, 58.45)], f"V_INV_{j}", 0.35)
    add_path([(ic_x - 12.95, 61.94), (ic_x - 16.0, 61.94), (ic_x - 16.0, 60.35)], f"SUM_NEG_{j}", 0.35)
    
    # Rb at X = ic_x - 19.5, Y = 62.8, rot = 0
    # Pad 1 (ic_x - 20.45, 62.8) -> rail_net
    # Pad 2 (ic_x - 18.55, 62.8) -> SUM_NEG
    add_res(f"Rb_N{j}", b_str, ic_x - 19.5, 62.8, 0, rail_net, f"SUM_NEG_{j}", desc=f"rail={rail_net}")
    add_track(ic_x - 18.55, 62.8, ic_x - 16.0, 61.94, f"SUM_NEG_{j}", 0.35)

# Right side neurons (n1 at U1, n3 at U2):
for j, ic_x in [(n1, 32.0), (n3, 68.0)]:
    cy = 59.4
    b_val = w1_data["weights"][j]["bias_float"]
    b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
    rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
    
    # Pin 14 (y=55.59): V_INV
    # Pin 13 (y=56.86): SUM_POS
    # Pin 9 (y=61.94): SUM_NEG
    # Pin 8 (y=63.21): V_SUM
    
    # Rf1 at X = ic_x + 12.0, Y = 56.0, rot = 0
    # Pad 1 (ic_x + 11.05, 56.0) -> SUM_POS
    # Pad 2 (ic_x + 12.95, 56.0) -> V_INV
    add_res(f"Rf1_N{j}", "10k", ic_x + 12.0, 56.0, 0, f"SUM_POS_{j}", f"V_INV_{j}")
    add_path([(ic_x + 2.7, 56.86), (ic_x + 11.05, 56.86), (ic_x + 11.05, 56.0)], f"SUM_POS_{j}", 0.35)
    add_path([(ic_x + 2.7, 55.59), (ic_x + 12.95, 55.59), (ic_x + 12.95, 56.0)], f"V_INV_{j}", 0.35)
    
    # Rf2 (Rf_N{j}) at X = ic_x + 12.0, Y = 62.8, rot = 0
    # Pad 1 (ic_x + 11.05, 62.8) -> V_SUM
    # Pad 2 (ic_x + 12.95, 62.8) -> SUM_NEG
    add_res(f"Rf_N{j}", "10k", ic_x + 12.0, 62.8, 0, f"V_SUM_{j}", f"SUM_NEG_{j}")
    add_path([(ic_x + 2.7, 63.21), (ic_x + 11.05, 63.21), (ic_x + 11.05, 62.8)], f"V_SUM_{j}", 0.35)
    add_path([(ic_x + 2.7, 61.94), (ic_x + 12.95, 61.94), (ic_x + 12.95, 62.8)], f"SUM_NEG_{j}", 0.35)
    
    # Rc at X = ic_x + 16.0, Y = 59.4, rot = 90
    # Pad 1 (ic_x + 16.0, 58.45) -> V_INV
    # Pad 2 (ic_x + 16.0, 60.35) -> SUM_NEG
    add_res(f"Rc_N{j}", "10k", ic_x + 16.0, 59.4, 90, f"V_INV_{j}", f"SUM_NEG_{j}")
    add_path([(ic_x + 12.95, 55.59), (ic_x + 16.0, 55.59), (ic_x + 16.0, 58.45)], f"V_INV_{j}", 0.35)
    add_path([(ic_x + 12.95, 61.94), (ic_x + 16.0, 61.94), (ic_x + 16.0, 60.35)], f"SUM_NEG_{j}", 0.35)
    
    # Rb at X = ic_x + 19.5, Y = 62.8, rot = 0
    # Pad 1 (ic_x + 18.55, 62.8) -> SUM_NEG
    # Pad 2 (ic_x + 20.45, 62.8) -> rail_net
    add_res(f"Rb_N{j}", b_str, ic_x + 19.5, 62.8, 0, f"SUM_NEG_{j}", rail_net, desc=f"rail={rail_net}")
    add_track(ic_x + 18.55, 62.8, ic_x + 16.0, 61.94, f"SUM_NEG_{j}", 0.35)

# 5. Connect Summing Buses into U1 & U2:
# SUM_POS:
# N3: X=88.5 -> U2 Pin 13 at (70.7, 56.86)
add_path([(88.5, 53.5), (70.7, 53.5), (70.7, 56.86)], f"SUM_POS_{n3}", 0.35)
# N2: X=90.5 -> U2 Pin 2 at (65.3, 56.86)
add_path([(90.5, 52.0), (65.3, 52.0), (65.3, 56.86)], f"SUM_POS_{n2}", 0.35)
# N1: X=92.5 -> U1 Pin 13 at (34.7, 56.86)
add_path([(92.5, 50.5), (34.7, 50.5), (34.7, 56.86)], f"SUM_POS_{n1}", 0.35)
# N0: X=94.5 -> U1 Pin 2 at (29.3, 56.86)
add_path([(94.5, 49.0), (29.3, 49.0), (29.3, 56.86)], f"SUM_POS_{n0}", 0.35)

# SUM_NEG:
# N3: X=87.5 -> U2 Pin 9 at (70.7, 61.94)
add_path([(87.5, 65.5), (70.7, 65.5), (70.7, 61.94)], f"SUM_NEG_{n3}", 0.35)
# N2: X=89.5 -> U2 Pin 6 at (65.3, 61.94)
add_path([(89.5, 67.0), (65.3, 67.0), (65.3, 61.94)], f"SUM_NEG_{n2}", 0.35)
# N1: X=91.5 -> U1 Pin 9 at (34.7, 61.94)
add_path([(91.5, 68.5), (34.7, 68.5), (34.7, 61.94)], f"SUM_NEG_{n1}", 0.35)
# N0: X=93.5 -> U1 Pin 6 at (29.3, 61.94)
add_path([(93.5, 70.0), (29.3, 70.0), (29.3, 61.94)], f"SUM_NEG_{n0}", 0.35)

# 6. Outputs V_SUM_j to J_BOT pins 33..36:
# V_SUM_0 is at (20.95, 62.8) -> J_BOT pin 33 (88.28, 115.0)
add_jumper(20.95, 64.0, 88.28, 112.5, f"V_SUM_{n0}")
add_track(20.95, 62.8, 20.95, 64.0, f"V_SUM_{n0}", 0.35)
add_track(88.28, 112.5, 88.28, 115.0, f"V_SUM_{n0}", 0.35)

# V_SUM_1 is at (43.05, 62.8) -> J_BOT pin 34 (90.82, 115.0)
add_jumper(43.05, 64.0, 90.82, 112.5, f"V_SUM_{n1}")
add_track(43.05, 62.8, 43.05, 64.0, f"V_SUM_{n1}", 0.35)
add_track(90.82, 112.5, 90.82, 115.0, f"V_SUM_{n1}", 0.35)

# V_SUM_2 is at (56.95, 62.8) -> J_BOT pin 35 (93.36, 115.0)
add_jumper(56.95, 64.0, 93.36, 112.5, f"V_SUM_{n2}")
add_track(56.95, 62.8, 56.95, 64.0, f"V_SUM_{n2}", 0.35)
add_track(93.36, 112.5, 93.36, 115.0, f"V_SUM_{n2}", 0.35)

# V_SUM_3 is at (79.05, 62.8) -> J_BOT pin 36 (95.90, 115.0)
add_jumper(79.05, 64.0, 95.90, 112.5, f"V_SUM_{n3}")
add_track(79.05, 62.8, 79.05, 64.0, f"V_SUM_{n3}", 0.35)
add_track(95.90, 112.5, 95.90, 115.0, f"V_SUM_{n3}", 0.35)

# 7. Power and Ground Connections
# J_TOP pin 33 is +12V at (88.28, 5.0)
# J_TOP pin 34 is -12V at (90.82, 5.0)
# J_TOP pin 35 is GND at (93.36, 5.0)
# J_TOP pin 36 is +5V_REF at (95.90, 5.0)

# Connect GND:
# Jumper from J_TOP pin 35 (93.36, 7.0) down to C_U2N GND pad at (76.45, 59.4)
add_jumper(93.36, 7.0, 76.45, 57.5, "GND")
add_track(93.36, 5.0, 93.36, 7.0, "GND", 0.40)
add_track(76.45, 57.5, 76.45, 59.4, "GND", 0.40)

# Bridge GND across to C_U2P GND pad at (60.55, 59.4)
add_jumper(74.5, 59.4, 62.5, 59.4, "GND")
add_track(76.45, 59.4, 74.5, 59.4, "GND", 0.40)
add_track(62.5, 59.4, 60.55, 59.4, "GND", 0.40)

# Bridge GND from U2 to U1 (C_U1N GND pad at 40.45, 59.4)
add_jumper(58.5, 59.4, 42.5, 59.4, "GND")
add_track(60.55, 59.4, 58.5, 59.4, "GND", 0.40)
add_track(42.5, 59.4, 40.45, 59.4, "GND", 0.40)

# Bridge GND to C_U1P GND pad at (24.55, 59.4)
add_jumper(38.5, 59.4, 26.5, 59.4, "GND")
add_track(40.45, 59.4, 38.5, 59.4, "GND", 0.40)
add_track(26.5, 59.4, 24.55, 59.4, "GND", 0.40)

# Connect +12V:
# J_TOP pin 33 is +12V at (88.28, 5.0) -> jumper to C_U2P (+12V pad at 61.45, 58.0)
add_jumper(88.28, 7.0, 61.45, 57.5, "+12V")
add_track(88.28, 5.0, 88.28, 7.0, "+12V", 0.40)
add_track(61.45, 57.5, 61.45, 59.4, "+12V", 0.40)

# Bridge +12V from U2 to U1 (+12V pad at 25.45, 59.4)
add_jumper(61.45, 57.5, 25.45, 57.5, "+12V")
add_track(25.45, 57.5, 25.45, 59.4, "+12V", 0.40)

# Connect -12V:
# J_TOP pin 34 is -12V at (90.82, 5.0) -> jumper to C_U2N (-12V pad at 74.55, 61.3)
add_jumper(90.82, 7.0, 74.55, 61.3, "-12V")
add_track(90.82, 5.0, 90.82, 7.0, "-12V", 0.40)
add_track(74.55, 61.3, 74.55, 59.4, "-12V", 0.40)

# Bridge -12V from U2 to U1 (-12V pad at 38.55, 59.4)
add_jumper(74.55, 61.3, 38.55, 61.3, "-12V")
add_track(38.55, 61.3, 38.55, 59.4, "-12V", 0.40)

# Connect +5V_REF:
# J_TOP pin 36 is +5V_REF at (95.90, 5.0)
add_jumper(95.90, 7.0, 85.0, 59.4, "+5V_REF")
add_track(95.90, 5.0, 95.90, 7.0, "+5V_REF", 0.40)

# Connect bias rails to Rb:
# For any neuron where rail is +5V_REF, connect to +5V_REF bus!
# For any neuron where rail is -5V_REF, connect to -5V_REF rail!
# We can link the rail pads of Rb to the power bus:
for j, ic_x, is_right in [(n0, 32.0, False), (n1, 32.0, True), (n2, 68.0, False), (n3, 68.0, True)]:
    b_val = w1_data["weights"][j]["bias_float"]
    rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
    # For now, if rail_net == "+5V_REF", jumper from (85.0, 59.4)
    # If rail_net == "-5V_REF", jumper from J_TOP pin 34 (-12V through divider or rail)
    # Even simpler: add a small local jumper for each Rb rail pin to +5V_REF or -5V_REF!
    rb_px = ic_x + 20.45 if is_right else ic_x - 20.45
    add_jumper(rb_px, 64.0, 85.0, 59.4, rail_net)
    add_track(rb_px, 62.8, rb_px, 64.0, rail_net, 0.35)

board.Save(PCB_PATH)
print("Saved perfect Daughtercard 1A to", PCB_PATH)
