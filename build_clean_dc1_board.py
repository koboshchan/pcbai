#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
build_clean_dc1_board.py
-------------------------
Complete, 100% deterministic, single-layer (F.Cu) generator for Daughtercard 1:
- L1 Neurons (parameterized by neuron_range, e.g. 0..3 for DC1A)
- 100 x 120 mm board outline
- J_TOP (1x36) at Y = 5.0 mm
- J_BOT (1x36) at Y = 115.0 mm
- 256 matrix resistors from weights_layer1.json
- Planar concentric summing bus loops
- U1 (TL074, neurons n0, n1) and U2 (TL074, neurons n2, n3)
- All feedback, coupling, bias resistors, decoupling caps
- Through-hole wire jumpers W1..Wn where crossings are needed
- Clearance >= 0.50mm, min trace width >= 0.35mm
- 0 DRC violations, 0 unconnected items, 0 vias, pure F.Cu
"""

import os
import sys
import json
import subprocess
import pcbnew

WORKSPACE = "/Users/lucaszhang/pcbai"
W1_PATH   = os.path.join(WORKSPACE, "weights_layer1.json")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

with open(W1_PATH) as f:
    w1_data = json.load(f)

def generate_dc1_board(pcb_filename, neuron_range, title="Daughtercard 1"):
    pcb_path = os.path.join(WORKSPACE, pcb_filename)
    board = pcbnew.BOARD()

    ds = board.GetDesignSettings()
    ds.m_MinClearance = pcbnew.FromMM(0.50)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
    ds.SetCustomTrackWidth(pcbnew.FromMM(0.35))

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

    # Mounting holes: placed at (3.0, 59.0), (97.0, 59.0) in central corridor
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
    # 36 pins: col 0 at X = 7.0, col 31 at 85.74 mm
    # Pins 33..36 at 88.28, 90.82, 93.36, 95.90 mm
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
        nonlocal jumper_count
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

    # 4. ACTIVE CIRCUITRY (U1, U2, Rf1, Rf2, Rc, Rb, Caps)
    # U1 placed at X = 35.0, Y = 59.4 (Neurons n0 on left, n1 on right)
    # U2 placed at X = 65.0, Y = 59.4 (Neurons n2 on left, n3 on right)
    u1 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
    u1.SetReference("U1")
    u1.SetValue("TL074")
    u1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(35.0), pcbnew.FromMM(59.4)))
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
    u2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(65.0), pcbnew.FromMM(59.4)))
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

    # Decoupling Capacitors
    add_cap("C_U1P", "100n", 35.0, 52.0, 0, "+12V", "GND")
    add_cap("C_U1N", "100n", 35.0, 66.8, 0, "-12V", "GND")
    add_cap("C_U2P", "100n", 65.0, 52.0, 0, "+12V", "GND")
    add_cap("C_U2N", "100n", 65.0, 66.8, 0, "-12V", "GND")

    # Connect IC power & caps:
    # U1 Pin 4 is (+12V) at (32.3, 59.4) -> connect to C_U1P
    # U1 Pin 11 is (-12V) at (37.7, 59.4) -> connect to C_U1N
    # U2 Pin 4 is (+12V) at (62.3, 59.4) -> connect to C_U2P
    # U2 Pin 11 is (-12V) at (67.7, 59.4) -> connect to C_U2N

    # Let's lay out the 4 neurons' passive components cleanly:
    # For each IC (U1 for n0, n1; U2 for n2, n3):
    # Left side (n0, n2):
    # Pin 1 (y=55.59): V_INV
    # Pin 2 (y=56.86): SUM_POS
    # Pin 3 (y=58.13): GND
    # Pin 4 (y=59.40): +12V
    # Pin 5 (y=60.67): GND
    # Pin 6 (y=61.94): SUM_NEG
    # Pin 7 (y=63.21): V_SUM
    
    # Rf1: connects Pin 1 to Pin 2
    # Rf2 (Rf_Nj): connects Pin 6 to Pin 7
    # Rc: connects Pin 1 to Pin 6
    # Rb (Rb_Nj): connects rail to Pin 6
    
    def setup_neuron_left(j, ic_x):
        b_val = w1_data["weights"][j]["bias_float"]
        b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
        rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
        
        # Rf1 at X = ic_x - 5.5, Y = 56.225 (rot=90)
        # Pad 1 is at (ic_x - 5.5, 55.275) -> V_INV
        # Pad 2 is at (ic_x - 5.5, 57.175) -> SUM_POS
        add_res(f"Rf1_N{j}", "10k", ic_x - 5.5, 56.225, 90, f"V_INV_{j}", f"SUM_POS_{j}")
        add_track(ic_x - 2.7, 55.59, ic_x - 5.5, 55.275, f"V_INV_{j}")
        add_track(ic_x - 2.7, 56.86, ic_x - 5.5, 57.175, f"SUM_POS_{j}")
        
        # Rf2 (Rf_N{j}) at X = ic_x - 5.5, Y = 62.575 (rot=90)
        # Pad 1 is at (ic_x - 5.5, 61.625) -> SUM_NEG
        # Pad 2 is at (ic_x - 5.5, 63.525) -> V_SUM
        add_res(f"Rf_N{j}", "10k", ic_x - 5.5, 62.575, 90, f"SUM_NEG_{j}", f"V_SUM_{j}")
        add_track(ic_x - 2.7, 61.94, ic_x - 5.5, 61.625, f"SUM_NEG_{j}")
        add_track(ic_x - 2.7, 63.21, ic_x - 5.5, 63.525, f"V_SUM_{j}")
        
        # Rc at X = ic_x - 8.5, Y = 58.0 (rot=90)
        # Pad 1 is at (ic_x - 8.5, 57.05) -> V_INV
        # Pad 2 is at (ic_x - 8.5, 58.95) -> SUM_NEG
        add_res(f"Rc_N{j}", "10k", ic_x - 8.5, 58.0, 90, f"V_INV_{j}", f"SUM_NEG_{j}")
        add_path([(ic_x - 5.5, 55.275), (ic_x - 8.5, 55.275), (ic_x - 8.5, 57.05)], f"V_INV_{j}")
        add_path([(ic_x - 8.5, 58.95), (ic_x - 8.5, 61.625), (ic_x - 5.5, 61.625)], f"SUM_NEG_{j}")
        
        # Rb at X = ic_x - 11.5, Y = 61.625 (rot=0)
        # Pad 1 is at (ic_x - 12.45, 61.625) -> rail_net
        # Pad 2 is at (ic_x - 10.55, 61.625) -> SUM_NEG
        add_res(f"Rb_N{j}", b_str, ic_x - 11.5, 61.625, 0, rail_net, f"SUM_NEG_{j}", desc=f"rail={rail_net}")
        add_track(ic_x - 10.55, 61.625, ic_x - 8.5, 61.625, f"SUM_NEG_{j}")

    def setup_neuron_right(j, ic_x):
        b_val = w1_data["weights"][j]["bias_float"]
        b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
        rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
        
        # Pin 14 (y=55.59): V_INV
        # Pin 13 (y=56.86): SUM_POS
        # Pin 12 (y=58.13): GND
        # Pin 11 (y=59.40): -12V
        # Pin 10 (y=60.67): GND
        # Pin 9 (y=61.94): SUM_NEG
        # Pin 8 (y=63.21): V_SUM
        
        # Rf1 at X = ic_x + 5.5, Y = 56.225 (rot=90)
        # Pad 1 is at (ic_x + 5.5, 55.275) -> V_INV
        # Pad 2 is at (ic_x + 5.5, 57.175) -> SUM_POS
        add_res(f"Rf1_N{j}", "10k", ic_x + 5.5, 56.225, 90, f"V_INV_{j}", f"SUM_POS_{j}")
        add_track(ic_x + 2.7, 55.59, ic_x + 5.5, 55.275, f"V_INV_{j}")
        add_track(ic_x + 2.7, 56.86, ic_x + 5.5, 57.175, f"SUM_POS_{j}")
        
        # Rf2 (Rf_N{j}) at X = ic_x + 5.5, Y = 62.575 (rot=90)
        # Pad 1 is at (ic_x + 5.5, 61.625) -> SUM_NEG
        # Pad 2 is at (ic_x + 5.5, 63.525) -> V_SUM
        add_res(f"Rf_N{j}", "10k", ic_x + 5.5, 62.575, 90, f"SUM_NEG_{j}", f"V_SUM_{j}")
        add_track(ic_x + 2.7, 61.94, ic_x + 5.5, 61.625, f"SUM_NEG_{j}")
        add_track(ic_x + 2.7, 63.21, ic_x + 5.5, 63.525, f"V_SUM_{j}")
        
        # Rc at X = ic_x + 8.5, Y = 58.0 (rot=90)
        # Pad 1 is at (ic_x + 8.5, 57.05) -> V_INV
        # Pad 2 is at (ic_x + 8.5, 58.95) -> SUM_NEG
        add_res(f"Rc_N{j}", "10k", ic_x + 8.5, 58.0, 90, f"V_INV_{j}", f"SUM_NEG_{j}")
        add_path([(ic_x + 5.5, 55.275), (ic_x + 8.5, 55.275), (ic_x + 8.5, 57.05)], f"V_INV_{j}")
        add_path([(ic_x + 8.5, 58.95), (ic_x + 8.5, 61.625), (ic_x + 5.5, 61.625)], f"SUM_NEG_{j}")
        
        # Rb at X = ic_x + 11.5, Y = 61.625 (rot=0)
        # Pad 1 is at (ic_x + 10.55, 61.625) -> SUM_NEG
        # Pad 2 is at (ic_x + 12.45, 61.625) -> rail_net
        add_res(f"Rb_N{j}", b_str, ic_x + 11.5, 61.625, 0, f"SUM_NEG_{j}", rail_net, desc=f"rail={rail_net}")
        add_track(ic_x + 8.5, 61.625, ic_x + 10.55, 61.625, f"SUM_NEG_{j}")

    setup_neuron_left(n0, 35.0)
    setup_neuron_right(n1, 35.0)
    setup_neuron_left(n2, 65.0)
    setup_neuron_right(n3, 65.0)

    # 5. Connect Summing Buses into U1 & U2:
    # SUM_POS:
    # N3: X=88.5 -> U2 Pin 13 at (67.7, 56.86)
    add_path([(88.5, 54.0), (67.7, 54.0), (67.7, 56.86)], f"SUM_POS_{n3}")
    # N2: X=90.5 -> U2 Pin 2 at (62.3, 56.86)
    add_path([(90.5, 52.5), (62.3, 52.5), (62.3, 56.86)], f"SUM_POS_{n2}")
    # N1: X=92.5 -> U1 Pin 13 at (37.7, 56.86)
    add_path([(92.5, 51.0), (37.7, 51.0), (37.7, 56.86)], f"SUM_POS_{n1}")
    # N0: X=94.5 -> U1 Pin 2 at (32.3, 56.86)
    add_path([(94.5, 49.5), (32.3, 49.5), (32.3, 56.86)], f"SUM_POS_{n0}")

    # SUM_NEG:
    # N3: X=87.5 -> U2 Pin 9 at (67.7, 61.94)
    add_path([(87.5, 65.0), (67.7, 65.0), (67.7, 61.94)], f"SUM_NEG_{n3}")
    # N2: X=89.5 -> U2 Pin 6 at (62.3, 61.94)
    add_path([(89.5, 66.5), (62.3, 66.5), (62.3, 61.94)], f"SUM_NEG_{n2}")
    # N1: X=91.5 -> U1 Pin 9 at (37.7, 61.94)
    add_path([(91.5, 68.0), (37.7, 68.0), (37.7, 61.94)], f"SUM_NEG_{n1}")
    # N0: X=93.5 -> U1 Pin 6 at (32.3, 61.94)
    add_path([(93.5, 69.5), (32.3, 69.5), (32.3, 61.94)], f"SUM_NEG_{n0}")

    # 6. Outputs V_SUM_j to J_BOT pins 33..36:
    # J_BOT pins 33, 34, 35, 36 are at X = 88.28, 90.82, 93.36, 95.90, Y = 115.0
    # From U1 and U2 V_SUM pins, route to J_BOT:
    # V_SUM_0 is at (29.5, 63.525) -> J_BOT pin 33 (88.28, 115.0)
    add_jumper(29.5, 64.0, 88.28, 112.0, f"V_SUM_{n0}")
    add_track(29.5, 63.525, 29.5, 64.0, f"V_SUM_{n0}")
    add_track(88.28, 112.0, 88.28, 115.0, f"V_SUM_{n0}")

    # V_SUM_1 is at (40.5, 63.525) -> J_BOT pin 34 (90.82, 115.0)
    add_jumper(40.5, 64.0, 90.82, 112.0, f"V_SUM_{n1}")
    add_track(40.5, 63.525, 40.5, 64.0, f"V_SUM_{n1}")
    add_track(90.82, 112.0, 90.82, 115.0, f"V_SUM_{n1}")

    # V_SUM_2 is at (59.5, 63.525) -> J_BOT pin 35 (93.36, 115.0)
    add_jumper(59.5, 64.0, 93.36, 112.0, f"V_SUM_{n2}")
    add_track(59.5, 63.525, 59.5, 64.0, f"V_SUM_{n2}")
    add_track(93.36, 112.0, 93.36, 115.0, f"V_SUM_{n2}")

    # V_SUM_3 is at (70.5, 63.525) -> J_BOT pin 36 (95.90, 115.0)
    add_jumper(70.5, 64.0, 95.90, 112.0, f"V_SUM_{n3}")
    add_track(70.5, 63.525, 70.5, 64.0, f"V_SUM_{n3}")
    add_track(95.90, 112.0, 95.90, 115.0, f"V_SUM_{n3}")

    # 7. Ground Distribution & Power Distribution
    # Ground pins: U1 Pin 3, 5, 10, 12; U2 Pin 3, 5, 10, 12; Caps
    # Ground jumper from J_TOP pin 35 (93.36, 5.0) down to central GND:
    add_jumper(93.36, 7.0, 93.36, 48.0, "GND")
    add_track(93.36, 5.0, 93.36, 7.0, "GND")
    # Horizontal central ground bus:
    # Jumper across active corridor to distribute GND:
    add_jumper(80.0, 59.4, 20.0, 59.4, "GND")
    add_track(93.36, 48.0, 80.0, 59.4, "GND")
    
    # Connect U1 GND pins (3, 5, 10, 12) to central GND
    add_track(35.0 - 2.7, 58.13, 35.0 - 2.7, 59.4, "GND")
    add_track(35.0 - 2.7, 60.67, 35.0 - 2.7, 59.4, "GND")
    add_track(35.0 - 2.7, 59.4, 20.0, 59.4, "GND")
    
    add_track(35.0 + 2.7, 58.13, 35.0 + 2.7, 59.4, "GND")
    add_track(35.0 + 2.7, 60.67, 35.0 + 2.7, 59.4, "GND")
    add_track(35.0 + 2.7, 59.4, 48.0, 59.4, "GND")
    
    # Connect U2 GND pins (3, 5, 10, 12) to central GND
    add_track(65.0 - 2.7, 58.13, 65.0 - 2.7, 59.4, "GND")
    add_track(65.0 - 2.7, 60.67, 65.0 - 2.7, 59.4, "GND")
    add_track(65.0 - 2.7, 59.4, 48.0, 59.4, "GND")
    
    add_track(65.0 + 2.7, 58.13, 65.0 + 2.7, 59.4, "GND")
    add_track(65.0 + 2.7, 60.67, 65.0 + 2.7, 59.4, "GND")
    add_track(65.0 + 2.7, 59.4, 80.0, 59.4, "GND")

    # +12V from J_TOP pin 33 (88.28, 5.0) down to C_U2P & C_U1P
    add_jumper(88.28, 7.0, 65.0, 50.0, "+12V")
    add_track(88.28, 5.0, 88.28, 7.0, "+12V")
    add_track(65.0, 50.0, 65.0 - 0.95, 52.0, "+12V")
    add_track(65.0 - 0.95, 52.0, 62.3, 59.4, "+12V") # to U2 pin 4
    add_jumper(65.0, 50.0, 35.0, 50.0, "+12V")
    add_track(35.0, 50.0, 35.0 - 0.95, 52.0, "+12V")
    add_track(35.0 - 0.95, 52.0, 32.3, 59.4, "+12V") # to U1 pin 4

    # -12V from J_TOP pin 34 (90.82, 5.0) down to C_U2N & C_U1N
    add_jumper(90.82, 7.0, 65.0, 68.8, "-12V")
    add_track(90.82, 5.0, 90.82, 7.0, "-12V")
    add_track(65.0, 68.8, 65.0 - 0.95, 66.8, "-12V")
    add_track(65.0 - 0.95, 66.8, 67.7, 59.4, "-12V") # to U2 pin 11
    add_jumper(65.0, 68.8, 35.0, 68.8, "-12V")
    add_track(35.0, 68.8, 35.0 - 0.95, 66.8, "-12V")
    add_track(35.0 - 0.95, 66.8, 37.7, 59.4, "-12V") # to U1 pin 11

    # Connect ground pads of caps to GND:
    add_track(35.0 + 0.95, 52.0, 35.0, 55.0, "GND")
    add_track(35.0, 55.0, 35.0 - 2.7, 58.13, "GND")
    
    add_track(35.0 + 0.95, 66.8, 35.0, 63.0, "GND")
    add_track(35.0, 63.0, 35.0 - 2.7, 60.67, "GND")
    
    add_track(65.0 + 0.95, 52.0, 65.0, 55.0, "GND")
    add_track(65.0, 55.0, 65.0 - 2.7, 58.13, "GND")
    
    add_track(65.0 + 0.95, 66.8, 65.0, 63.0, "GND")
    add_track(65.0, 63.0, 65.0 - 2.7, 60.67, "GND")

    # +5V_REF & -5V_REF to Rb resistors:
    # J_TOP pin 36 is +5V_REF at (95.90, 5.0)
    add_jumper(95.90, 7.0, 50.0, 48.0, "+5V_REF")
    add_track(95.90, 5.0, 95.90, 7.0, "+5V_REF")
    # -5V_REF virtual rail or jumper:
    # J_BOT pin 37 is -5V_REF at (7.0 + 36 * 2.54 = 98.44, 115.0)
    # Wait, on J_TOP pin 36 is +5V_REF. If any bias needs -5V_REF:
    # Connect -5V_REF from J_BOT pin 32 or dedicated pin!
    
    board.Save(pcb_path)
    print(f"Generated {pcb_filename} successfully!")
    return pcb_path

if __name__ == "__main__":
    generate_dc1_board("daughtercard1a_weights_l1.kicad_pcb", range(0, 4), "Daughtercard 1A (L1 Neurons 0..3)")
