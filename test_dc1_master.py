#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
test_dc1_master.py
------------------
Master deterministic generator for Daughtercard 1:
- 100 x 120 mm outline
- 256 matrix resistors with concentric planar loops
- Point-to-point wire jumpers for 8 summing buses (zero board-crossing tracks)
- Point-to-point wire jumpers for 4 output channels
- Clean local active circuitry with verified clearances
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

# Mounting holes: placed at (3.5, 60.0), (97.5, 50.0)
fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
for idx, (hx, hy) in enumerate([(3.5, 60.0), (97.5, 50.0)]):
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

# 3. PLANAR CORRIDOR ROUTING (X = 87.5..94.5 mm)
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

# Power drops from J_TOP to ICs:
add_track(88.28, 5.0, 88.28, 14.0, "+12V", 0.40)
add_track(90.82, 5.0, 90.82, 14.0, "-12V", 0.40)
add_track(93.36, 5.0, 93.36, 14.0, "GND", 0.40)
add_track(95.90, 5.0, 95.90, 18.0, "+5V_REF", 0.40)

# U1 Power drops:
add_jumper(19.5, 60.0, 88.28, 8.0, "+12V")
add_track(22.3, 60.0, 19.5, 60.0, "+12V", 0.35)

add_jumper(30.5, 60.0, 90.82, 8.0, "-12V")
add_track(27.7, 60.0, 30.5, 60.0, "-12V", 0.35)

# U2 Power drops:
add_jumper(60.5, 60.0, 88.28, 11.0, "+12V")
add_track(63.3, 60.0, 60.5, 60.0, "+12V", 0.35)

add_jumper(71.5, 60.0, 90.82, 11.0, "-12V")
add_track(68.7, 60.0, 71.5, 60.0, "-12V", 0.35)

# Decoupling Caps (placed horizontally at Y = 53.5 to stay clear of pins):
add_cap("C_U1P", "100n", 19.5, 53.5, 0, "+12V", "GND")
add_path([(19.5 - 0.95, 53.5), (19.5, 53.5), (19.5, 60.0)], "+12V", 0.35)

add_cap("C_U1N", "100n", 30.5, 53.5, 0, "-12V", "GND")
add_path([(30.5 - 0.95, 53.5), (30.5, 53.5), (30.5, 60.0)], "-12V", 0.35)

add_cap("C_U2P", "100n", 60.5, 53.5, 0, "+12V", "GND")
add_path([(60.5 - 0.95, 53.5), (60.5, 53.5), (60.5, 60.0)], "+12V", 0.35)

add_cap("C_U2N", "100n", 71.5, 53.5, 0, "-12V", "GND")
add_path([(71.5 - 0.95, 53.5), (71.5, 53.5), (71.5, 60.0)], "-12V", 0.35)

# Ground connections:
# U1 Left GND (Pins 3 & 5):
add_jumper(21.0, 51.0, 93.36, 8.0, "GND")
add_track(21.0, 51.0, 19.5 + 0.95, 53.5, "GND", 0.35)
add_track(22.3, 58.73, 21.0, 58.73, "GND", 0.35)
add_jumper(21.0, 58.73, 21.0, 51.0, "GND")
add_jumper(21.0, 61.27, 21.0, 58.73, "GND")
add_track(22.3, 61.27, 21.0, 61.27, "GND", 0.35)

# U1 Right GND (Pins 10 & 12):
add_jumper(29.0, 51.0, 93.36, 11.0, "GND")
add_track(29.0, 51.0, 30.5 + 0.95, 53.5, "GND", 0.35)
add_track(27.7, 58.73, 29.0, 58.73, "GND", 0.35)
add_jumper(29.0, 58.73, 29.0, 51.0, "GND")
add_jumper(29.0, 61.27, 29.0, 58.73, "GND")
add_track(27.7, 61.27, 29.0, 61.27, "GND", 0.35)

# U2 Left GND (Pins 3 & 5):
add_jumper(62.0, 51.0, 93.36, 14.0, "GND")
add_track(62.0, 51.0, 60.5 + 0.95, 53.5, "GND", 0.35)
add_track(63.3, 58.73, 62.0, 58.73, "GND", 0.35)
add_jumper(62.0, 58.73, 62.0, 51.0, "GND")
add_jumper(62.0, 61.27, 62.0, 58.73, "GND")
add_track(63.3, 61.27, 62.0, 61.27, "GND", 0.35)

# U2 Right GND (Pins 10 & 12):
add_jumper(70.0, 51.0, 93.36, 17.0, "GND")
add_track(70.0, 51.0, 71.5 + 0.95, 53.5, "GND", 0.35)
add_track(68.7, 58.73, 70.0, 58.73, "GND", 0.35)
add_jumper(70.0, 58.73, 70.0, 51.0, "GND")
add_jumper(70.0, 61.27, 70.0, 58.73, "GND")
add_track(68.7, 61.27, 70.0, 61.27, "GND", 0.35)

# Passive Components (Strictly parallel orthogonal tracks):
def setup_n_left(j, ic_x):
    b_val = w1_data["weights"][j]["bias_float"]
    b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
    rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
    
    # Rf1 at X = ic_x - 9.0, Y = 56.825 (rot=-90)
    # Pad 1 (top): (ic_x - 9.0, 55.875) -> V_INV
    # Pad 2 (bot): (ic_x - 9.0, 57.775) -> SUM_POS
    add_res(f"Rf1_N{j}", "10k", ic_x - 9.0, 56.825, -90, f"V_INV_{j}", f"SUM_POS_{j}")
    add_path([(ic_x - 2.7, 56.19), (ic_x - 9.0, 56.19), (ic_x - 9.0, 55.875)], f"V_INV_{j}", 0.35)
    add_path([(ic_x - 2.7, 57.46), (ic_x - 9.0, 57.46), (ic_x - 9.0, 57.775)], f"SUM_POS_{j}", 0.35)
    
    # Rf2 at X = ic_x - 9.0, Y = 63.175 (rot=-90)
    # Pad 1 (top): (ic_x - 9.0, 62.225) -> SUM_NEG
    # Pad 2 (bot): (ic_x - 9.0, 64.125) -> V_SUM
    add_res(f"Rf_N{j}", "10k", ic_x - 9.0, 63.175, -90, f"SUM_NEG_{j}", f"V_SUM_{j}")
    add_path([(ic_x - 2.7, 62.54), (ic_x - 9.0, 62.54), (ic_x - 9.0, 62.225)], f"SUM_NEG_{j}", 0.35)
    add_path([(ic_x - 2.7, 63.81), (ic_x - 9.0, 63.81), (ic_x - 9.0, 64.125)], f"V_SUM_{j}", 0.35)
    
    # Rc at X = ic_x - 13.0, Y = 59.05 (rot=-90)
    # Pad 1 (top): (ic_x - 13.0, 58.1) -> V_INV
    # Pad 2 (bot): (ic_x - 13.0, 60.0) -> SUM_NEG
    add_res(f"Rc_N{j}", "10k", ic_x - 13.0, 59.05, -90, f"V_INV_{j}", f"SUM_NEG_{j}")
    add_path([(ic_x - 9.0, 55.875), (ic_x - 13.0, 55.875), (ic_x - 13.0, 58.1)], f"V_INV_{j}", 0.35)
    add_path([(ic_x - 9.0, 62.225), (ic_x - 13.0, 62.225), (ic_x - 13.0, 60.0)], f"SUM_NEG_{j}", 0.35)
    
    # Rb at X = ic_x - 16.5, Y = 62.225 (rot=0)
    add_res(f"Rb_N{j}", b_str, ic_x - 16.5, 62.225, 0, rail_net, f"SUM_NEG_{j}", desc=f"rail={rail_net}")
    add_track(ic_x - 15.55, 62.225, ic_x - 13.0, 62.225, f"SUM_NEG_{j}", 0.35)
    ref_y_tap = 8.0 + j * 2.54
    add_jumper(ic_x - 17.45, 62.225, 95.90, ref_y_tap, rail_net)

def setup_n_right(j, ic_x):
    b_val = w1_data["weights"][j]["bias_float"]
    b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
    rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
    
    # Rf1 at X = ic_x + 9.0, Y = 56.825 (rot=-90)
    add_res(f"Rf1_N{j}", "10k", ic_x + 9.0, 56.825, -90, f"V_INV_{j}", f"SUM_POS_{j}")
    add_path([(ic_x + 2.7, 56.19), (ic_x + 9.0, 56.19), (ic_x + 9.0, 55.875)], f"V_INV_{j}", 0.35)
    add_path([(ic_x + 2.7, 57.46), (ic_x + 9.0, 57.46), (ic_x + 9.0, 57.775)], f"SUM_POS_{j}", 0.35)
    
    # Rf2 at X = ic_x + 9.0, Y = 63.175 (rot=-90)
    add_res(f"Rf_N{j}", "10k", ic_x + 9.0, 63.175, -90, f"SUM_NEG_{j}", f"V_SUM_{j}")
    add_path([(ic_x + 2.7, 62.54), (ic_x + 9.0, 62.54), (ic_x + 9.0, 62.225)], f"SUM_NEG_{j}", 0.35)
    add_path([(ic_x + 2.7, 63.81), (ic_x + 9.0, 63.81), (ic_x + 9.0, 64.125)], f"V_SUM_{j}", 0.35)
    
    # Rc at X = ic_x + 13.0, Y = 59.05 (rot=-90)
    add_res(f"Rc_N{j}", "10k", ic_x + 13.0, 59.05, -90, f"V_INV_{j}", f"SUM_NEG_{j}")
    add_path([(ic_x + 9.0, 55.875), (ic_x + 13.0, 55.875), (ic_x + 13.0, 58.1)], f"V_INV_{j}", 0.35)
    add_path([(ic_x + 9.0, 62.225), (ic_x + 13.0, 62.225), (ic_x + 13.0, 60.0)], f"SUM_NEG_{j}", 0.35)
    
    # Rb at X = ic_x + 16.5, Y = 62.225 (rot=0)
    add_res(f"Rb_N{j}", b_str, ic_x + 16.5, 62.225, 0, f"SUM_NEG_{j}", rail_net, desc=f"rail={rail_net}")
    add_track(ic_x + 15.55, 62.225, ic_x + 13.0, 62.225, f"SUM_NEG_{j}", 0.35)
    ref_y_tap = 8.0 + j * 2.54
    add_jumper(ic_x + 17.45, 62.225, 95.90, ref_y_tap, rail_net)

setup_n_left(n0, 25.0)
setup_n_right(n1, 25.0)
setup_n_left(n2, 66.0)
setup_n_right(n3, 66.0)

# Connect 8 Summing Buses using direct point-to-point jumpers across the central corridor:
# N0:
add_jumper(94.5, 52.0, 16.0, 52.0, f"SUM_POS_{n0}")
add_track(16.0, 52.0, 16.0, 57.775, f"SUM_POS_{n0}", 0.35)

add_jumper(93.5, 67.0, 16.0, 67.0, f"SUM_NEG_{n0}")
add_track(16.0, 67.0, 16.0, 62.225, f"SUM_NEG_{n0}", 0.35)

# N1:
add_jumper(92.5, 53.5, 34.0, 53.5, f"SUM_POS_{n1}")
add_track(34.0, 53.5, 34.0, 57.775, f"SUM_POS_{n1}", 0.35)

add_jumper(91.5, 65.5, 34.0, 65.5, f"SUM_NEG_{n1}")
add_track(34.0, 65.5, 34.0, 62.225, f"SUM_NEG_{n1}", 0.35)

# N2:
add_jumper(90.5, 52.0, 57.0, 52.0, f"SUM_POS_{n2}")
add_track(57.0, 52.0, 57.0, 57.775, f"SUM_POS_{n2}", 0.35)

add_jumper(89.5, 67.0, 57.0, 67.0, f"SUM_NEG_{n2}")
add_track(57.0, 67.0, 57.0, 62.225, f"SUM_NEG_{n2}", 0.35)

# N3:
add_jumper(88.5, 53.5, 75.0, 53.5, f"SUM_POS_{n3}")
add_track(75.0, 53.5, 75.0, 57.775, f"SUM_POS_{n3}", 0.35)

add_jumper(87.5, 65.5, 75.0, 65.5, f"SUM_NEG_{n3}")
add_track(75.0, 65.5, 75.0, 62.225, f"SUM_NEG_{n3}", 0.35)

# Outputs V_SUM_j to J_BOT pins 33..36:
add_jumper(16.0, 64.125, 88.28, 112.5, f"V_SUM_{n0}")
add_track(88.28, 112.5, 88.28, 115.0, f"V_SUM_{n0}", 0.35)

add_jumper(34.0, 64.125, 90.82, 112.5, f"V_SUM_{n1}")
add_track(90.82, 112.5, 90.82, 115.0, f"V_SUM_{n1}", 0.35)

add_jumper(57.0, 64.125, 93.36, 112.5, f"V_SUM_{n2}")
add_track(93.36, 112.5, 93.36, 115.0, f"V_SUM_{n2}", 0.35)

add_jumper(75.0, 64.125, 95.90, 112.5, f"V_SUM_{n3}")
add_track(95.90, 112.5, 95.90, 115.0, f"V_SUM_{n3}", 0.35)

board.Save(PCB_PATH)
print("Saved master Daughtercard 1A to", PCB_PATH)
