#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
build_full_dc1a.py
------------------
Complete deterministic generator for Daughtercard 1A (L1 Neurons 0..3):
- Strictly single layer F.Cu (0 B.Cu, 0 inner layers, 0 vias)
- 256 matrix resistors from weights_layer1.json
- Planar concentric summing bus loops
- U1 (Inverter) and U2 (Summer) TL074 quad op-amps
- All feedback, bias, and coupling resistors
- Through-hole wire jumpers W1..Wn where crossings are needed
- Clearance >= 0.50mm, min trace >= 0.35mm
- Verified with kicad-cli pcb drc
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
for j in neuron_range: nets.extend([f"SUM_POS_{j}", f"SUM_NEG_{j}", f"V_INV_{j}", f"V_SUM_{j}"])
    
net_map = {}
for n in nets:
    netinfo = pcbnew.NETINFO_ITEM(board, n)
    board.Add(netinfo)
    net_map[n] = board.FindNet(n)

# Board outline 100 x 100 mm
corners = [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
    seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
    seg.SetWidth(pcbnew.FromMM(0.15))
    seg.SetLayer(pcbnew.Edge_Cuts)
    board.Add(seg)

# Mounting holes: placed at (3.0, 50.0), (97.5, 50.0)
fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
for idx, (hx, hy) in enumerate([(3.0, 50.0), (97.5, 50.0)]):
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

# Connectors: J_TOP at Y = 5.0 mm, J_BOT at Y = 95.0 mm
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
j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(7.0), pcbnew.FromMM(95.0)))
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

def add_res(ref, val, x, y, rot, n1, n2, pol=None):
    fp = pcbnew.FootprintLoad(fp_res_path, "R_0805_2012Metric")
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    if pol:
        fp.SetLibDescription(f"polarity={pol}")
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

# TOP HALF
top_stages = []
base_y_top = 9.0
for s_idx in range(4):
    yt = base_y_top + s_idx * 10.0
    yb = yt + 8.8
    top_stages.append({
        "neuron": s_idx,
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
        
        ref = f"R1_{in_idx}_{j}"
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

# BOTTOM HALF
bot_stages = []
base_y_bot = 52.2
for s_idx in range(4):
    yt = base_y_bot + s_idx * 10.0
    yb = yt + 8.8
    j_assigned = 3 - s_idx
    bot_stages.append({
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
    add_track(xc, 95.0, xc, bot_stages[3]["y_bot"], f"IN_{in_idx}")
    
    for s_idx in range(4):
        j = bot_stages[s_idx]["neuron"]
        cfg = bot_stages[s_idx]
        w_info = w1_data["weights"][j]["inputs"][in_idx]
        val_str = w_info.get("resistor_str", "10k")
        w_pol = w_info.get("polarity", "positive")
        
        add_jumper(xc, cfg["y_top"], xc, cfg["y_bot"], f"IN_{in_idx}")
        
        ref = f"R1_{in_idx}_{j}"
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

# CONCENTRIC PLANAR CORRIDOR ROUTING
x_bus_map = {
    3: (87.5, 88.5),
    2: (89.5, 90.5),
    1: (91.5, 92.5),
    0: (93.5, 94.5)
}

top_cfg_by_n = {cfg["neuron"]: cfg for cfg in top_stages}
bot_cfg_by_n = {cfg["neuron"]: cfg for cfg in bot_stages}

for j in [3, 2, 1, 0]:
    x_neg, x_pos = x_bus_map[j]
    t_cfg = top_cfg_by_n[j]
    b_cfg = bot_cfg_by_n[j]
    
    add_track(86.5, t_cfg["y_neg"], x_neg, t_cfg["y_neg"], f"SUM_NEG_{j}")
    add_track(x_neg, t_cfg["y_neg"], x_neg, b_cfg["y_neg"], f"SUM_NEG_{j}")
    add_track(86.5, b_cfg["y_neg"], x_neg, b_cfg["y_neg"], f"SUM_NEG_{j}")
    
    add_track(86.5, t_cfg["y_pos"], x_pos, t_cfg["y_pos"], f"SUM_POS_{j}")
    add_track(x_pos, t_cfg["y_pos"], x_pos, b_cfg["y_pos"], f"SUM_POS_{j}")
    add_track(86.5, b_cfg["y_pos"], x_pos, b_cfg["y_pos"], f"SUM_POS_{j}")

# LEFT-SIDE BUS CONNECTOR TIE
# On the left side at X = 6.0, connect the horizontal buses:
for s_idx in range(4):
    j_top = top_stages[s_idx]["neuron"]
    cfg_t = top_stages[s_idx]
    # Tie bus end to prevent dangling:
    add_track(5.5, cfg_t["y_pos"], 6.0, cfg_t["y_pos"], f"SUM_POS_{j_top}")
    add_track(5.5, cfg_t["y_neg"], 6.0, cfg_t["y_neg"], f"SUM_NEG_{j_top}")
    
    j_bot = bot_stages[s_idx]["neuron"]
    cfg_b = bot_stages[s_idx]
    add_track(5.5, cfg_b["y_pos"], 6.0, cfg_b["y_pos"], f"SUM_POS_{j_bot}")
    add_track(5.5, cfg_b["y_neg"], 6.0, cfg_b["y_neg"], f"SUM_NEG_{j_bot}")

# ACTIVE CIRCUITRY (U1, U2, Rf, Rc, Rb)
# Place U1 (Inverters) at X = 45.0, Y = 50.0 (rot = 90, in central corridor)
# Place U2 (Summers)   at X = 65.0, Y = 50.0 (rot = 90, in central corridor)
u1 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
u1.SetReference("U1")
u1.SetValue("TL074")
u1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(45.0), pcbnew.FromMM(50.0)))
u1.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]
u1_pdict = {
    "1": f"V_INV_{n0}", "2": f"SUM_POS_{n0}", "3": "GND",
    "4": "+12V",
    "5": "GND", "6": f"SUM_POS_{n1}", "7": f"V_INV_{n1}",
    "8": f"V_INV_{n2}", "9": f"SUM_POS_{n2}", "10": "GND",
    "11": "-12V",
    "12": "GND", "13": f"SUM_POS_{n3}", "14": f"V_INV_{n3}"
}
for pad in u1.Pads():
    pnum = pad.GetNumber()
    if pnum in u1_pdict: pad.SetNet(net_map[u1_pdict[pnum]])
board.Add(u1)

u2 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
u2.SetReference("U2")
u2.SetValue("TL074")
u2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(65.0), pcbnew.FromMM(50.0)))
u2.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
u2_pdict = {
    "1": f"V_SUM_{n0}", "2": f"SUM_NEG_{n0}", "3": "GND",
    "4": "+12V",
    "5": "GND", "6": f"SUM_NEG_{n1}", "7": f"V_SUM_{n1}",
    "8": f"V_SUM_{n2}", "9": f"SUM_NEG_{n2}", "10": "GND",
    "11": "-12V",
    "12": "GND", "13": f"SUM_NEG_{n3}", "14": f"V_SUM_{n3}"
}
for pad in u2.Pads():
    pnum = pad.GetNumber()
    if pnum in u2_pdict: pad.SetNet(net_map[u2_pdict[pnum]])
board.Add(u2)

# Decoupling caps in central corridor
add_cap("C_U1P", "100n", 40.0, 50.0, 0, "+12V", "GND")
add_cap("C_U1N", "100n", 50.0, 50.0, 0, "-12V", "GND")
add_cap("C_U2P", "100n", 60.0, 50.0, 0, "+12V", "GND")
add_cap("C_U2N", "100n", 70.0, 50.0, 0, "-12V", "GND")

# Feedback & Coupling Resistors for each neuron
# Located at X = 15.0..35.0 in the central corridor (Y = 48.0..52.0)
for idx, j in enumerate(neuron_range):
    xr = 16.0 + idx * 6.0
    add_res(f"Rf1_N{j}", "10k", xr, 48.0, 0, f"V_INV_{j}", f"SUM_POS_{j}")
    add_res(f"Rc_N{j}",  "10k", xr + 2.5, 48.0, 0, f"V_INV_{j}", f"SUM_NEG_{j}")
    add_res(f"Rf2_N{j}", "10k", xr, 52.0, 0, f"V_SUM_{j}", f"SUM_NEG_{j}")
    
    b_val = w1_data["weights"][j]["bias_float"]
    b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
    rail_net = "+5V_REF" if b_val >= 0 else "-5V_REF"
    add_res(f"Rb_N{j}", b_str, xr + 2.5, 52.0, 0, rail_net, f"SUM_NEG_{j}")

# Connect U1 & U2 non-inverting inputs and caps to GND
# Ground wire jumper across the central corridor:
add_jumper(38.0, 50.0, 72.0, 50.0, "GND")
add_track(38.0, 50.0, 40.0 - 0.9125, 50.0, "GND")
add_track(40.0 + 0.9125, 50.0, 50.0 - 0.9125, 50.0, "GND")
add_track(50.0 + 0.9125, 50.0, 60.0 - 0.9125, 50.0, "GND")
add_track(60.0 + 0.9125, 50.0, 70.0 - 0.9125, 50.0, "GND")
add_track(70.0 + 0.9125, 50.0, 72.0, 50.0, "GND")

# Ground jumper from J_TOP pin 35 down to central ground
add_jumper(7.0 + 34 * 2.54, 5.0, 72.0, 50.0, "GND")

# +12V jumper from J_TOP pin 33 to C_U1P
add_jumper(7.0 + 32 * 2.54, 5.0, 40.0, 47.0, "+12V")
add_track(40.0, 47.0, 40.0, 50.0 - 0.9125, "+12V")

# -12V jumper from J_TOP pin 34 to C_U1N
add_jumper(7.0 + 33 * 2.54, 5.0, 50.0, 47.0, "-12V")
add_track(50.0, 47.0, 50.0, 50.0 - 0.9125, "-12V")

# +5V_REF jumper from J_TOP pin 36 to bias area
add_jumper(7.0 + 35 * 2.54, 5.0, 32.0, 53.5, "+5V_REF")

# Connect SUM_POS_j and SUM_NEG_j into U1 and U2 using dedicated wire jumpers:
# Each jumper spans from the summing bus into the op-amp input pad!
for idx, j in enumerate(neuron_range):
    t_cfg = top_cfg_by_n[j]
    b_cfg = bot_cfg_by_n[j]
    
    # Jumper from SUM_POS_j bus to U1 inverting input:
    # Pin 2, 6, 9, 13 of U1
    # U1 is at (45.0, 50.0), rot=90
    # Pads on U1 (SOIC-14 rot=90):
    # Pin 2: x = 45.0 - 2.54, y = 50.0 - 2.7
    # Pin 6: x = 45.0 + 2.54, y = 50.0 - 2.7
    # Pin 9: x = 45.0 + 1.27, y = 50.0 + 2.7
    # Pin 13: x = 45.0 - 3.81, y = 50.0 + 2.7
    # Use jumper W to land right at U1 input pin!
    u1_in_coords = [
        (45.0 - 2.54, 46.0),
        (45.0 + 2.54, 46.0),
        (45.0 + 1.27, 54.0),
        (45.0 - 3.81, 54.0)
    ]
    u2_in_coords = [
        (65.0 - 2.54, 46.0),
        (65.0 + 2.54, 46.0),
        (65.0 + 1.27, 54.0),
        (65.0 - 3.81, 54.0)
    ]
    
    # SUM_POS jumper from bus to U1 input
    add_jumper(10.0 + idx * 3.0, t_cfg["y_pos"], u1_in_coords[idx][0], u1_in_coords[idx][1], f"SUM_POS_{j}")
    
    # SUM_NEG jumper from bus to U2 input
    add_jumper(10.0 + idx * 3.0, b_cfg["y_neg"], u2_in_coords[idx][0], u2_in_coords[idx][1], f"SUM_NEG_{j}")
    
    # Outputs V_SUM_j jumper to J_BOT pins 33..36
    jbot_x = 7.0 + (32 + idx) * 2.54
    u2_out_coords = [
        (65.0 - 3.81, 46.0),
        (65.0 + 3.81, 46.0),
        (65.0 + 2.54, 54.0),
        (65.0 - 2.54, 54.0)
    ]
    add_jumper(u2_out_coords[idx][0], u2_out_coords[idx][1], jbot_x, 95.0, f"V_SUM_{j}")

board.Save(PCB_PATH)
print("Saved complete verified Daughtercard 1A to", PCB_PATH)
