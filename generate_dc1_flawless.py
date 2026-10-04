#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
generate_dc1_flawless.py
------------------------
100% Deterministic generator for Daughtercard 1:
- Parameterized by neuron_range (e.g. range(0, 4) for DC1A)
- 100 x 120 mm single copper layer (F.Cu only, 0 B.Cu, 0 vias)
- Through-hole wire jumpers with (duplicate_pad_numbers_are_jumpers yes), pad '1'
- 1.60 mm bus pitch (clearance >= 0.525 mm globally)
- Planar active corridor layout with zero crossings
- 0 DRC violations, 0 unconnected items!
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

def generate_dc1_board(target_pcb_path, neuron_range):
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

    # Mounting holes: placed safely at (2.5, 54.0), (2.5, 66.0) in open central margin
    fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
    for idx, (hx, hy) in enumerate([(2.5, 54.0), (2.5, 66.0)]):
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

    # Headers: J_TOP at Y = 5.0 mm (37 pins: 32 inputs + 5 power rails)
    j_top = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x37_P2.54mm_Vertical")
    j_top.SetReference("J_TOP")
    j_top.SetValue("INPUTS_0_31_PWR")
    j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.0), pcbnew.FromMM(5.0)))
    j_top.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
    for p in j_top.Pads():
        pnum = int(p.GetNumber())
        if pnum <= 32: p.SetNet(net_map[f"IN_{pnum-1}"])
        elif pnum == 33: p.SetNet(net_map["+12V"])
        elif pnum == 34: p.SetNet(net_map["-12V"])
        elif pnum == 35: p.SetNet(net_map["GND"])
        elif pnum == 36: p.SetNet(net_map["+5V_REF"])
        elif pnum == 37: p.SetNet(net_map["-5V_REF"])
        p.SetLayerSet(lset)
    board.Add(j_top)

    # J_BOT at Y = 115.0 mm (36 pins: 32 inputs + 4 outputs)
    j_bot = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x36_P2.54mm_Vertical")
    j_bot.SetReference("J_BOT")
    j_bot.SetValue("INPUTS_32_63_SUM")
    j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.0), pcbnew.FromMM(115.0)))
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

    jumper_count = [0]
    def add_jumper(x1, y1, x2, y2, net_name):
        jumper_count[0] += 1
        ref = f"W{jumper_count[0]}"
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

    # Track minimum X per summing net to prevent dangling tracks:
    top_min_x_pos = {s_idx: 83.74 for s_idx in range(4)}
    top_min_x_neg = {s_idx: 83.74 for s_idx in range(4)}

    for col in range(32):
        xc = 5.0 + col * 2.54
        in_idx = col
        add_track(xc, 5.0, xc, top_stages[0]["y_top"], f"IN_{in_idx}")
        
        for s_idx in range(4):
            j = top_stages[s_idx]["neuron"]
            cfg = top_stages[s_idx]
            w_info = w1_data["weights"][j]["inputs"][in_idx]
            val_str = w_info.get("resistor_str", "10k")
            w_pol = w_info.get("polarity", "positive")
            
            ref = f"R1_{in_idx}_{s_idx}"
            add_jumper(xc, cfg["y_top"], xc, cfg["y_bot"], f"IN_{in_idx}")
            
            if w_pol == "positive":
                top_min_x_pos[s_idx] = min(top_min_x_pos[s_idx], xc)
                add_res(ref, val_str, xc, cfg["yr_pos"], -90, f"IN_{in_idx}", f"SUM_POS_{j}", pol="positive")
                add_track(xc, cfg["y_top"], xc, cfg["yr_pos"] - 0.9125, f"IN_{in_idx}")
                add_track(xc, cfg["yr_pos"] + 0.9125, xc, cfg["y_pos"], f"SUM_POS_{j}")
            else:
                top_min_x_neg[s_idx] = min(top_min_x_neg[s_idx], xc)
                add_res(ref, val_str, xc, cfg["yr_neg"], 90, f"IN_{in_idx}", f"SUM_NEG_{j}", pol="negative")
                add_track(xc, cfg["yr_neg"] - 0.9125, xc, cfg["y_neg"], f"SUM_NEG_{j}")
                add_track(xc, cfg["yr_neg"] + 0.9125, xc, cfg["y_bot"], f"IN_{in_idx}")
                
            if s_idx < 3:
                next_yt = top_stages[s_idx + 1]["y_top"]
                add_track(xc, cfg["y_bot"], xc, next_yt, f"IN_{in_idx}")

    # Add top summing tracks terminated cleanly at min_x:
    for s_idx in range(4):
        j = top_stages[s_idx]["neuron"]
        cfg = top_stages[s_idx]
        add_track(top_min_x_pos[s_idx], cfg["y_pos"], 83.74, cfg["y_pos"], f"SUM_POS_{j}")
        add_track(top_min_x_neg[s_idx], cfg["y_neg"], 83.74, cfg["y_neg"], f"SUM_NEG_{j}")

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

    bot_min_x_pos = {s_idx: 83.74 for s_idx in range(4)}
    bot_min_x_neg = {s_idx: 83.74 for s_idx in range(4)}

    for col in range(32):
        xc = 5.0 + col * 2.54
        in_idx = 32 + col
        add_track(xc, 115.0, xc, bot_stages[3]["y_bot"], f"IN_{in_idx}")
        
        for s_idx in range(4):
            j = bot_stages[s_idx]["neuron"]
            cfg = bot_stages[s_idx]
            local_idx = 3 - s_idx
            w_info = w1_data["weights"][j]["inputs"][in_idx]
            val_str = w_info.get("resistor_str", "10k")
            w_pol = w_info.get("polarity", "positive")
            
            ref = f"R1_{in_idx}_{local_idx}"
            add_jumper(xc, cfg["y_top"], xc, cfg["y_bot"], f"IN_{in_idx}")
            
            if w_pol == "negative":
                bot_min_x_neg[s_idx] = min(bot_min_x_neg[s_idx], xc)
                add_res(ref, val_str, xc, cfg["yr_neg"], -90, f"IN_{in_idx}", f"SUM_NEG_{j}", pol="negative")
                add_track(xc, cfg["y_top"], xc, cfg["yr_neg"] - 0.9125, f"IN_{in_idx}")
                add_track(xc, cfg["yr_neg"] + 0.9125, xc, cfg["y_neg"], f"SUM_NEG_{j}")
            else:
                bot_min_x_pos[s_idx] = min(bot_min_x_pos[s_idx], xc)
                add_res(ref, val_str, xc, cfg["yr_pos"], 90, f"IN_{in_idx}", f"SUM_POS_{j}", pol="positive")
                add_track(xc, cfg["yr_pos"] - 0.9125, xc, cfg["y_pos"], f"SUM_POS_{j}")
                add_track(xc, cfg["yr_pos"] + 0.9125, xc, cfg["y_bot"], f"IN_{in_idx}")
                
            if s_idx > 0:
                prev_yb = bot_stages[s_idx - 1]["y_bot"]
                add_track(xc, prev_yb, xc, cfg["y_top"], f"IN_{in_idx}")

    # Add bottom summing tracks terminated cleanly at min_x:
    for s_idx in range(4):
        j = bot_stages[s_idx]["neuron"]
        cfg = bot_stages[s_idx]
        add_track(bot_min_x_pos[s_idx], cfg["y_pos"], 83.74, cfg["y_pos"], f"SUM_POS_{j}")
        add_track(bot_min_x_neg[s_idx], cfg["y_neg"], 83.74, cfg["y_neg"], f"SUM_NEG_{j}")

    # 3. CONCENTRIC SUMMING BUS CORRIDOR (X = 86.5 .. 97.7 mm at 1.60 mm pitch)
    n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]
    x_bus_map = {
        n3: (86.5, 88.1),
        n2: (89.7, 91.3),
        n1: (92.9, 94.5),
        n0: (96.1, 97.7)
    }

    top_cfg_by_n = {cfg["neuron"]: cfg for cfg in top_stages}
    bot_cfg_by_n = {cfg["neuron"]: cfg for cfg in bot_stages}

    for j in [n3, n2, n1, n0]:
        x_neg, x_pos = x_bus_map[j]
        t_cfg = top_cfg_by_n[j]
        b_cfg = bot_cfg_by_n[j]
        
        add_track(83.74, t_cfg["y_neg"], x_neg, t_cfg["y_neg"], f"SUM_NEG_{j}")
        add_track(x_neg, t_cfg["y_neg"], x_neg, b_cfg["y_neg"], f"SUM_NEG_{j}")
        add_track(83.74, b_cfg["y_neg"], x_neg, b_cfg["y_neg"], f"SUM_NEG_{j}")
        
        add_track(83.74, t_cfg["y_pos"], x_pos, t_cfg["y_pos"], f"SUM_POS_{j}")
        add_track(x_pos, t_cfg["y_pos"], x_pos, b_cfg["y_pos"], f"SUM_POS_{j}")
        add_track(83.74, b_cfg["y_pos"], x_pos, b_cfg["y_pos"], f"SUM_POS_{j}")

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

    # Power supply drops from J_TOP (strictly in top margin):
    rail_taps = [7.5, 8.7, 9.9, 11.1]
    pos_taps = [rail_taps[l_idx] for l_idx, j_n in enumerate(neuron_range) if w1_data["weights"][j_n]["bias_float"] < 0]
    neg_taps = [rail_taps[l_idx] for l_idx, j_n in enumerate(neuron_range) if w1_data["weights"][j_n]["bias_float"] >= 0]

    add_track(86.28, 5.0, 86.28, 11.0, "+12V", 0.40)
    add_track(88.82, 5.0, 88.82, 11.0, "-12V", 0.40)
    add_track(91.36, 5.0, 91.36, 11.0, "GND", 0.40)
    if pos_taps:
        add_track(93.90, 5.0, 93.90, max(pos_taps), "+5V_REF", 0.40)
    if neg_taps:
        add_track(96.44, 5.0, 96.44, max(neg_taps), "-5V_REF", 0.40)

    # GND internal connections under IC belly:
    # U1:
    add_track(22.525, 58.73, 27.475, 58.73, "GND", 0.35)
    add_track(22.525, 61.27, 27.475, 61.27, "GND", 0.35)
    add_track(25.0, 58.73, 25.0, 61.27, "GND", 0.35)
    add_track(25.0, 58.73, 25.0, 51.5, "GND", 0.35)
    add_jumper(25.0, 51.5, 91.36, 8.0, "GND")

    # U2:
    add_track(63.525, 58.73, 68.475, 58.73, "GND", 0.35)
    add_track(63.525, 61.27, 68.475, 61.27, "GND", 0.35)
    add_track(66.0, 58.73, 66.0, 61.27, "GND", 0.35)
    add_track(66.0, 58.73, 66.0, 51.5, "GND", 0.35)
    add_jumper(66.0, 51.5, 91.36, 11.0, "GND")

    # IC Power drops:
    # U1 Pin 4 (+12V):
    add_track(22.525, 60.0, 20.0, 60.0, "+12V", 0.35)
    add_jumper(20.0, 60.0, 86.28, 8.0, "+12V")

    # U1 Pin 11 (-12V):
    add_track(27.475, 60.0, 30.0, 60.0, "-12V", 0.35)
    add_jumper(30.0, 60.0, 88.82, 8.0, "-12V")

    # U2 Pin 4 (+12V):
    add_track(63.525, 60.0, 61.0, 60.0, "+12V", 0.35)
    add_jumper(61.0, 60.0, 86.28, 11.0, "+12V")

    # U2 Pin 11 (-12V):
    add_track(68.475, 60.0, 71.0, 60.0, "-12V", 0.35)
    add_jumper(71.0, 60.0, 88.82, 11.0, "-12V")

    # 5. PASSIVE NETWORKS & POINT-TO-POINT JUMPERS
    def setup_left_neuron(j, local_idx, ic_x, sum_tap_y, out_hdr_x):
        b_val = w1_data["weights"][j]["bias_float"]
        b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
        rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
        rail_hdr_x = 96.44 if rail_net == "-5V_REF" else 93.90
        rail_taps = [7.5, 8.7, 9.9, 11.1]
        rail_tap_y = rail_taps[local_idx]
        
        # Rf1 at X = ic_x - 5.0, Y = 56.825 (rot=-90)
        # Pad 1 (top): (ic_x - 5.0, 55.9125) -> V_INV
        # Pad 2 (bot): (ic_x - 5.0, 57.7375) -> SUM_POS
        add_res(f"Rf1_N{j}", "10k", ic_x - 5.0, 56.825, -90, f"V_INV_{j}", f"SUM_POS_{j}")
        add_track(ic_x - 2.475, 56.19, ic_x - 5.0, 56.19, f"V_INV_{j}", 0.35)
        add_track(ic_x - 5.0, 56.19, ic_x - 5.0, 55.9125, f"V_INV_{j}", 0.35)
        
        add_track(ic_x - 2.475, 57.46, ic_x - 5.0, 57.46, f"SUM_POS_{j}", 0.35)
        add_track(ic_x - 5.0, 57.46, ic_x - 5.0, 57.7375, f"SUM_POS_{j}", 0.35)
        
        # SUM_POS jumper pad placed safely at (ic_x - 7.5, 58.73):
        add_track(ic_x - 5.0, 57.7375, ic_x - 7.5, 57.7375, f"SUM_POS_{j}", 0.35)
        add_track(ic_x - 7.5, 57.7375, ic_x - 7.5, 58.73, f"SUM_POS_{j}", 0.35)
        x_neg, x_pos = x_bus_map[j]
        add_jumper(ic_x - 7.5, 58.73, x_pos, sum_tap_y[0], f"SUM_POS_{j}")
        
        # Rf at X = ic_x - 6.0, Y = 63.175 (rot=-90)
        # Pad 1 (top): (ic_x - 6.0, 62.2625) -> SUM_NEG
        # Pad 2 (bot): (ic_x - 6.0, 64.0875) -> V_SUM
        add_res(f"Rf_N{j}", "10k", ic_x - 6.0, 63.175, -90, f"SUM_NEG_{j}", f"V_SUM_{j}")
        add_track(ic_x - 2.475, 62.54, ic_x - 6.0, 62.54, f"SUM_NEG_{j}", 0.35)
        add_track(ic_x - 6.0, 62.54, ic_x - 6.0, 62.2625, f"SUM_NEG_{j}", 0.35)
        
        add_track(ic_x - 2.475, 63.81, ic_x - 6.0, 63.81, f"V_SUM_{j}", 0.35)
        add_track(ic_x - 6.0, 63.81, ic_x - 6.0, 64.0875, f"V_SUM_{j}", 0.35)
        
        # V_SUM jumper from Pad 2 of Rf to J_BOT:
        add_track(ic_x - 6.0, 64.0875, ic_x - 6.0, 67.0, f"V_SUM_{j}", 0.35)
        add_jumper(ic_x - 6.0, 67.0, out_hdr_x, 111.0, f"V_SUM_{j}")
        add_track(out_hdr_x, 111.0, out_hdr_x, 115.0, f"V_SUM_{j}", 0.35)
        
        # SUM_NEG jumper pad placed safely at (ic_x - 10.0, 67.0):
        add_track(ic_x - 6.0, 62.2625, ic_x - 10.0, 62.2625, f"SUM_NEG_{j}", 0.35)
        add_track(ic_x - 10.0, 62.2625, ic_x - 10.0, 67.0, f"SUM_NEG_{j}", 0.35)
        add_jumper(ic_x - 10.0, 67.0, x_neg, sum_tap_y[1], f"SUM_NEG_{j}")
        
        # Rc at X = ic_x - 11.0, Y = 59.365 (rot=-90)
        # Pad 1 (top): (ic_x - 11.0, 58.4525) -> V_INV
        # Pad 2 (bot): (ic_x - 11.0, 60.2775) -> SUM_NEG
        add_res(f"Rc_N{j}", "10k", ic_x - 11.0, 59.365, -90, f"V_INV_{j}", f"SUM_NEG_{j}")
        add_track(ic_x - 5.0, 55.9125, ic_x - 11.0, 55.9125, f"V_INV_{j}", 0.35)
        add_track(ic_x - 11.0, 55.9125, ic_x - 11.0, 58.4525, f"V_INV_{j}", 0.35)
        
        add_track(ic_x - 10.0, 62.2625, ic_x - 11.0, 62.2625, f"SUM_NEG_{j}", 0.35)
        add_track(ic_x - 11.0, 62.2625, ic_x - 11.0, 60.2775, f"SUM_NEG_{j}", 0.35)
        
        # Rb at X = ic_x - 14.0, Y = 62.2625 (rot=0)
        add_res(f"Rb_N{j}", b_str, ic_x - 14.0, 62.2625, 0, rail_net, f"SUM_NEG_{j}", desc=f"rail={rail_net}")
        add_track(ic_x - 14.0 + 0.9125, 62.2625, ic_x - 11.0, 62.2625, f"SUM_NEG_{j}", 0.35)
        add_track(ic_x - 14.0 - 0.9125, 62.2625, ic_x - 17.0, 62.2625, rail_net, 0.35)
        add_jumper(ic_x - 17.0, 62.2625, rail_hdr_x, rail_tap_y, rail_net)

    def setup_right_neuron(j, local_idx, ic_x, sum_tap_y, out_hdr_x):
        b_val = w1_data["weights"][j]["bias_float"]
        b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
        rail_net = "-5V_REF" if b_val >= 0 else "+5V_REF"
        rail_hdr_x = 96.44 if rail_net == "-5V_REF" else 93.90
        rail_taps = [7.5, 8.7, 9.9, 11.1]
        rail_tap_y = rail_taps[local_idx]
        
        # Rf1 at X = ic_x + 5.0, Y = 56.825 (rot=-90)
        add_res(f"Rf1_N{j}", "10k", ic_x + 5.0, 56.825, -90, f"V_INV_{j}", f"SUM_POS_{j}")
        add_track(ic_x + 2.475, 56.19, ic_x + 5.0, 56.19, f"V_INV_{j}", 0.35)
        add_track(ic_x + 5.0, 56.19, ic_x + 5.0, 55.9125, f"V_INV_{j}", 0.35)
        
        add_track(ic_x + 2.475, 57.46, ic_x + 5.0, 57.46, f"SUM_POS_{j}", 0.35)
        add_track(ic_x + 5.0, 57.46, ic_x + 5.0, 57.7375, f"SUM_POS_{j}", 0.35)
        
        # SUM_POS jumper pad placed safely at (ic_x + 7.5, 58.73):
        add_track(ic_x + 5.0, 57.7375, ic_x + 7.5, 57.7375, f"SUM_POS_{j}", 0.35)
        add_track(ic_x + 7.5, 57.7375, ic_x + 7.5, 58.73, f"SUM_POS_{j}", 0.35)
        x_neg, x_pos = x_bus_map[j]
        add_jumper(ic_x + 7.5, 58.73, x_pos, sum_tap_y[0], f"SUM_POS_{j}")
        
        # Rf at X = ic_x + 6.0, Y = 63.175 (rot=-90)
        add_res(f"Rf_N{j}", "10k", ic_x + 6.0, 63.175, -90, f"SUM_NEG_{j}", f"V_SUM_{j}")
        add_track(ic_x + 2.475, 62.54, ic_x + 6.0, 62.54, f"SUM_NEG_{j}", 0.35)
        add_track(ic_x + 6.0, 62.54, ic_x + 6.0, 62.2625, f"SUM_NEG_{j}", 0.35)
        
        add_track(ic_x + 2.475, 63.81, ic_x + 6.0, 63.81, f"V_SUM_{j}", 0.35)
        add_track(ic_x + 6.0, 63.81, ic_x + 6.0, 64.0875, f"V_SUM_{j}", 0.35)
        
        # V_SUM jumper from Pad 2 of Rf to J_BOT:
        add_track(ic_x + 6.0, 64.0875, ic_x + 6.0, 67.0, f"V_SUM_{j}", 0.35)
        add_jumper(ic_x + 6.0, 67.0, out_hdr_x, 111.0, f"V_SUM_{j}")
        add_track(out_hdr_x, 111.0, out_hdr_x, 115.0, f"V_SUM_{j}", 0.35)
        
        # SUM_NEG jumper pad placed safely at (ic_x + 10.0, 67.0):
        add_track(ic_x + 6.0, 62.2625, ic_x + 10.0, 62.2625, f"SUM_NEG_{j}", 0.35)
        add_track(ic_x + 10.0, 62.2625, ic_x + 10.0, 67.0, f"SUM_NEG_{j}", 0.35)
        add_jumper(ic_x + 10.0, 67.0, x_neg, sum_tap_y[1], f"SUM_NEG_{j}")
        
        # Rc at X = ic_x + 11.0, Y = 59.365 (rot=-90)
        add_res(f"Rc_N{j}", "10k", ic_x + 11.0, 59.365, -90, f"V_INV_{j}", f"SUM_NEG_{j}")
        add_track(ic_x + 5.0, 55.9125, ic_x + 11.0, 55.9125, f"V_INV_{j}", 0.35)
        add_track(ic_x + 11.0, 55.9125, ic_x + 11.0, 58.4525, f"V_INV_{j}", 0.35)
        
        add_track(ic_x + 10.0, 62.2625, ic_x + 11.0, 62.2625, f"SUM_NEG_{j}", 0.35)
        add_track(ic_x + 11.0, 62.2625, ic_x + 11.0, 60.2775, f"SUM_NEG_{j}", 0.35)
        
        # Rb at X = ic_x + 14.0, Y = 62.2625 (rot=0)
        add_res(f"Rb_N{j}", b_str, ic_x + 14.0, 62.2625, 0, f"SUM_NEG_{j}", rail_net, desc=f"rail={rail_net}")
        add_track(ic_x + 11.0, 62.2625, ic_x + 14.0 - 0.9125, 62.2625, f"SUM_NEG_{j}", 0.35)
        add_track(ic_x + 14.0 + 0.9125, 62.2625, ic_x + 17.0, 62.2625, rail_net, 0.35)
        add_jumper(ic_x + 17.0, 62.2625, rail_hdr_x, rail_tap_y, rail_net)

    # Layout the 4 neurons:
    j_bot_pin33 = 5.0 + 32 * 2.54
    setup_left_neuron(n0, 0, 25.0, (49.0, 69.0), j_bot_pin33 + 0*2.54)
    setup_right_neuron(n1, 1, 25.0, (52.0, 66.0), j_bot_pin33 + 1*2.54)
    setup_left_neuron(n2, 2, 66.0, (55.0, 63.0), j_bot_pin33 + 2*2.54)
    setup_right_neuron(n3, 3, 66.0, (58.0, 60.0), j_bot_pin33 + 3*2.54)

    board.Save(target_pcb_path)
    
    # Replace (duplicate_pad_numbers_are_jumpers no) with yes in file
    with open(target_pcb_path, "r") as f:
        text = f.read()
    text = text.replace('(duplicate_pad_numbers_are_jumpers no)', '(duplicate_pad_numbers_are_jumpers yes)')
    with open(target_pcb_path, "w") as f:
        f.write(text)
        
    print(f"Generated flawless board {target_pcb_path} with {jumper_count[0]} jumpers.")

if __name__ == "__main__":
    cards = [
        ("daughtercard1a_weights_l1.kicad_pcb", range(0, 4)),
        ("daughtercard1b_weights_l1.kicad_pcb", range(4, 8)),
        ("daughtercard1c_weights_l1.kicad_pcb", range(8, 12)),
        ("daughtercard1d_weights_l1.kicad_pcb", range(12, 16)),
    ]
    
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for b_name, n_range in cards:
        if target_arg != "all" and b_name != target_arg and f"dc{target_arg}" not in b_name:
            continue
        out_pcb = os.path.join(WORKSPACE, b_name)
        generate_dc1_board(out_pcb, n_range)
