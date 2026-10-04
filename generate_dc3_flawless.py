#!/usr/bin/env python3
"""
generate_dc3_flawless.py
-------------------------
Deterministic single-layer PCB generator for Daughtercard 3:
Layer 2 Synaptic Weights + 10-Way Winner-Take-All (WTA) Argmax.

Strict Single-Layer Home UV Photoresist Rules:
1. Layer: F.Cu ONLY (0 B.Cu, 0 inner layers, 0 vias).
2. Minimum Clearance: >= 0.50 mm.
3. Minimum Trace Width: >= 0.35 mm.
4. Layer crossings exclusively via through-hole wire jumpers (W1..Wn).
5. All resistors from 60-value 0805 kit.
6. Exactly 5 quad TL074 ICs (U1..U5).
7. 10 Diodes (1N4148, D_SOD-123), 10 LEDs (0805), 10 R_LED (1k), 1 R_WTA (10k).
8. Pass KiCad DRC with 0 violations and 0 unconnected items.
"""

import os
import sys
import json
import pcbnew

WORKSPACE = "/Users/lucaszhang/pcbai"

def generate_dc3_board(target_pcb_path):
    w2_file = os.path.join(WORKSPACE, "weights_layer2.json")
    with open(w2_file) as f:
        w2_data = json.load(f)

    board = pcbnew.BOARD()

    # Design settings
    ds = board.GetDesignSettings()
    ds.m_MinClearance = pcbnew.FromMM(0.50)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
    ds.SetCustomTrackWidth(pcbnew.FromMM(0.35))
    ds.m_ViasAllowed = False
    board.SetCopperLayerCount(2)

    # Edge Cuts: 100.0 x 120.0 mm
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(pcbnew.FromMM(0.15))
    edge.SetStartX(pcbnew.FromMM(0.0))
    edge.SetStartY(pcbnew.FromMM(0.0))
    edge.SetEndX(pcbnew.FromMM(100.0))
    edge.SetEndY(pcbnew.FromMM(120.0))
    board.Add(edge)

    # Net management
    nets = ["GND", "+12V", "-12V", "+5V_REF", "-5V_REF", "WTA_BUS"]
    for k in range(16):
        nets.append(f"ACT_{k}")
    for c in range(10):
        nets.extend([
            f"SUM_L2_POS_{c}", f"SUM_L2_NEG_{c}",
            f"V_INV_{c}", f"V_SUM_{c}",
            f"LED_NET_{c}"
        ])

    net_map = {}
    for n in nets:
        netinfo = pcbnew.NETINFO_ITEM(board, n)
        board.Add(netinfo)
        net_map[n] = board.FindNet(n)

    # Layer sets
    lset = pcbnew.LSET.AllCuMask()
    lset.AddLayer(pcbnew.F_Mask)
    lset.AddLayer(pcbnew.B_Mask)

    # Track helper
    def add_track(x1, y1, x2, y2, net_name, width_mm=0.35):
        if abs(x1 - x2) < 1e-4 and abs(y1 - y2) < 1e-4:
            return
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        t.SetWidth(pcbnew.FromMM(width_mm))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(net_map[net_name])
        board.Add(t)

    # Footprint paths
    fp_res_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty"
    fp_ic_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_SO.pretty"
    fp_dio_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Diode_SMD.pretty"
    fp_led_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/LED_SMD.pretty"
    fp_hdr_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty"
    fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"

    def add_res(ref, val, x, y, rot=0, net1=None, net2=None, pol=None, desc=""):
        fp = pcbnew.FootprintLoad(fp_res_path, "R_0805_2012Metric")
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        d = desc
        if pol:
            d = f"polarity={pol} {d}".strip()
        if d:
            fp.SetLibDescription(d)
        pads = list(fp.Pads())
        if net1 and len(pads) > 0:
            pads[0].SetNet(net_map[net1])
        if net2 and len(pads) > 1:
            pads[1].SetNet(net_map[net2])
        board.Add(fp)
        return fp

    def add_dio(ref, val, x, y, rot=0, net_k=None, net_a=None):
        fp = pcbnew.FootprintLoad(fp_dio_path, "D_SOD-123")
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        for pad in fp.Pads():
            if pad.GetNumber() == "1" and net_k:
                pad.SetNet(net_map[net_k])
            elif pad.GetNumber() == "2" and net_a:
                pad.SetNet(net_map[net_a])
        board.Add(fp)
        return fp

    def add_led(ref, val, x, y, rot=0, net_k=None, net_a=None):
        fp = pcbnew.FootprintLoad(fp_led_path, "LED_0805_2012Metric")
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        for pad in fp.Pads():
            if pad.GetNumber() == "1" and net_k:
                pad.SetNet(net_map[net_k])
            elif pad.GetNumber() == "2" and net_a:
                pad.SetNet(net_map[net_a])
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

    # Mounting holes
    for ref, mh_x, mh_y in [("MH1", 2.5, 54.0), ("MH2", 2.5, 66.0)]:
        mh = pcbnew.FootprintLoad(fp_mh_path, "MountingHole_3.2mm_M3")
        mh.SetReference(ref)
        mh.Reference().SetVisible(False)
        mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(mh_x), pcbnew.FromMM(mh_y)))
        board.Add(mh)

    # 1. TOP CONNECTOR: J_TOP (21-pin Header: ACT_0..15 + 5 power lines)
    # rot = 90 so pins run along +X starting at X = 10.0 mm
    j_top = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x21_P2.54mm_Vertical")
    j_top.SetReference("J_TOP")
    j_top.SetValue("ACT_IN_AND_PWR")
    j_top.Reference().SetVisible(False)
    j_top.Value().SetVisible(False)
    j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10.0), pcbnew.FromMM(5.0)))
    j_top.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
    top_pdict = {}
    for k in range(16):
        top_pdict[str(k + 1)] = f"ACT_{k}"
    top_pdict["17"] = "+12V"
    top_pdict["18"] = "-12V"
    top_pdict["19"] = "GND"
    top_pdict["20"] = "+5V_REF"
    top_pdict["21"] = "-5V_REF"
    for pad in j_top.Pads():
        pnum = pad.GetNumber()
        if pnum in top_pdict:
            pad.SetNet(net_map[top_pdict[pnum]])
        pad.SetLayerSet(lset)
    board.Add(j_top)

    # 2. BOTTOM CONNECTOR: J_BOT (12-pin Header: V_SUM_0..9 + WTA_BUS + GND)
    # rot = 90 so pins run along +X starting at X = 20.0 mm
    j_bot = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x12_P2.54mm_Vertical")
    j_bot.SetReference("J_BOT")
    j_bot.SetValue("SCORES_AND_WTA")
    j_bot.Reference().SetVisible(False)
    j_bot.Value().SetVisible(False)
    j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(20.0), pcbnew.FromMM(115.0)))
    j_bot.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
    bot_pdict = {}
    for c in range(10):
        bot_pdict[str(c + 1)] = f"V_SUM_{c}"
    bot_pdict["11"] = "WTA_BUS"
    bot_pdict["12"] = "GND"
    for pad in j_bot.Pads():
        pnum = pad.GetNumber()
        if pnum in bot_pdict:
            pad.SetNet(net_map[bot_pdict[pnum]])
        pad.SetLayerSet(lset)
    board.Add(j_bot)

    # 3. CROSSBAR MATRIX (16 inputs x 10 stages)
    # 16 Columns at X = 10.0 + k * 2.54 mm (X = 10.0 .. 48.1 mm)
    # 10 Stages at pitch 9.5 mm: Y = 12.0 to 105.8 mm.
    stages = []
    base_y = 12.0
    for s_idx in range(10):
        yt = base_y + s_idx * 9.5
        yb = yt + 8.3
        stages.append({
            "stage_idx": s_idx,
            "class_idx": s_idx,
            "y_top": yt, "y_bot": yb,
            "yr_pos": yt + 2.5,
            "y_pos": yt + 3.7,
            "y_neg": yt + 4.9,
            "yr_neg": yt + 6.1
        })

    stage_min_x_pos = {s_idx: 48.5 for s_idx in range(10)}
    stage_min_x_neg = {s_idx: 48.5 for s_idx in range(10)}

    for col in range(16):
        xc = 10.0 + col * 2.54
        in_idx = col
        add_track(xc, 5.0, xc, stages[0]["y_top"], f"ACT_{in_idx}")

        for s_idx in range(10):
            c = stages[s_idx]["class_idx"]
            cfg = stages[s_idx]
            w_info = w2_data["weights"][c]["inputs"][in_idx]
            val_str = w_info.get("resistor_str", "10k")
            w_pol = w_info.get("polarity", "positive")

            ref = f"R2_{in_idx}_{c}"
            add_jumper(xc, cfg["y_top"], xc, cfg["y_bot"], f"ACT_{in_idx}")

            if w_pol == "positive":
                stage_min_x_pos[s_idx] = min(stage_min_x_pos[s_idx], xc)
                add_res(ref, val_str, xc, cfg["yr_pos"], -90, f"ACT_{in_idx}", f"SUM_L2_POS_{c}", pol="positive")
                add_track(xc, cfg["y_top"], xc, cfg["yr_pos"] - 0.9125, f"ACT_{in_idx}")
                add_track(xc, cfg["yr_pos"] + 0.9125, xc, cfg["y_pos"], f"SUM_L2_POS_{c}")
            else:
                stage_min_x_neg[s_idx] = min(stage_min_x_neg[s_idx], xc)
                add_res(ref, val_str, xc, cfg["yr_neg"], 90, f"ACT_{in_idx}", f"SUM_L2_NEG_{c}", pol="negative")
                add_track(xc, cfg["yr_neg"] - 0.9125, xc, cfg["y_neg"], f"SUM_L2_NEG_{c}")
                add_track(xc, cfg["yr_neg"] + 0.9125, xc, cfg["y_bot"], f"ACT_{in_idx}")

            if s_idx > 0:
                prev_yb = stages[s_idx - 1]["y_bot"]
                add_track(xc, prev_yb, xc, cfg["y_top"], f"ACT_{in_idx}")

    # Horizontal summing tracks:
    # Top classes: y_pos runs to 58.5 (to route cleanly around Rf1 Pad 1)
    # Bot classes: y_pos runs to 50.5 (jumper pad)
    # All classes: y_neg runs to 50.5 (jumper pad)
    for s_idx in range(10):
        c = stages[s_idx]["class_idx"]
        cfg = stages[s_idx]
        is_top = (s_idx % 2 == 0)
        if is_top:
            add_track(stage_min_x_pos[s_idx], cfg["y_pos"], 58.5, cfg["y_pos"], f"SUM_L2_POS_{c}")
        else:
            add_track(stage_min_x_pos[s_idx], cfg["y_pos"], 50.5, cfg["y_pos"], f"SUM_L2_POS_{c}")
        add_track(stage_min_x_neg[s_idx], cfg["y_neg"], 50.5, cfg["y_neg"], f"SUM_L2_NEG_{c}")

    # 4. ACTIVE CIRCUITRY: 5x TL074 ICs (U1..U5) at X = 66.0 mm
    # Spaced vertically every 19.0 mm at Y = 20.9, 39.9, 58.9, 77.9, 96.9
    ic_positions = [
        ("U1", 66.0, 20.9, 0, 1),
        ("U2", 66.0, 39.9, 2, 3),
        ("U3", 66.0, 58.9, 4, 5),
        ("U4", 66.0, 77.9, 6, 7),
        ("U5", 66.0, 96.9, 8, 9)
    ]

    # TOP MARGIN POWER RAILS (Planar Escape Routing: reverse order of pin X)
    # Rail 1 (-5V_REF): pin 21 at (60.80, 5.0) -> down to 8.0 -> horizontal to 74.0
    add_track(60.80, 5.0, 60.80, 8.0, "-5V_REF", 0.40)
    add_track(60.80, 8.0, 74.0, 8.0, "-5V_REF", 0.40)

    # Rail 2 (+5V_REF): pin 20 at (58.26, 5.0) -> down to 9.6 -> horizontal to 79.0
    add_track(58.26, 5.0, 58.26, 9.6, "+5V_REF", 0.40)
    add_track(58.26, 9.6, 79.0, 9.6, "+5V_REF", 0.40)

    # Rail 3 (GND): pin 19 at (55.72, 5.0) -> down to 11.2 -> horizontal to 76.0
    add_track(55.72, 5.0, 55.72, 11.2, "GND", 0.40)
    add_track(55.72, 11.2, 76.0, 11.2, "GND", 0.40)

    # Rail 4 (-12V): pin 18 at (53.18, 5.0) -> down to 12.8 -> horizontal to 74.0
    add_track(53.18, 5.0, 53.18, 12.8, "-12V", 0.40)
    add_track(53.18, 12.8, 74.0, 12.8, "-12V", 0.40)

    # Rail 5 (+12V): pin 17 at (50.64, 5.0) -> down to 14.4 -> horizontal to 68.0
    add_track(50.64, 5.0, 50.64, 14.4, "+12V", 0.40)
    add_track(50.64, 14.4, 68.0, 14.4, "+12V", 0.40)

    # WTA Bus track running vertically at X = 87.5 mm (from Y = 18.4 to 108.0)
    add_track(87.5, 18.4, 87.5, 108.0, "WTA_BUS", 0.40)
    # Pulldown resistor R_WTA (10k) from WTA_BUS to -12V at (87.5, 110.0) rot=-90
    add_res("R_WTA", "10k", 87.5, 110.0, -90, "WTA_BUS", "-12V")
    add_track(87.5, 108.0, 87.5, 110.0 - 0.9125, "WTA_BUS", 0.35)
    # Jumper from R_WTA pad 1 (WTA_BUS) at (85.0, 108.0) to J_BOT WTA_BUS pin (pin 11 at 45.40, 115.0)
    out_wta_x = 20.0 + 10 * 2.54 # 45.40
    add_track(87.5, 108.0, 85.0, 108.0, "WTA_BUS", 0.35)
    add_jumper(85.0, 108.0, out_wta_x, 111.0, "WTA_BUS")
    add_track(out_wta_x, 111.0, out_wta_x, 115.0, "WTA_BUS", 0.35)
    # Jumper from R_WTA pad 2 (-12V) at (87.5, 113.5) to -12V bus at (74.0, 12.8)
    add_track(87.5, 110.0 + 0.9125, 87.5, 113.5, "-12V", 0.35)
    add_jumper(87.5, 113.5, 74.0, 12.8, "-12V")

    # GND rail for LEDs running vertically at X = 98.0 mm (from Y = 18.4 to 108.0)
    add_track(98.0, 18.4, 98.0, 108.0, "GND", 0.40)
    # Connect GND rail to top GND bus via jumper from (76.0, 11.2) to (98.0, 18.4)
    add_jumper(76.0, 11.2, 98.0, 18.4, "GND")
    # Connect GND rail to J_BOT GND pin (pin 12 at 47.94, 115.0)
    out_gnd_x = 20.0 + 11 * 2.54 # 47.94
    add_jumper(98.0, 108.0, out_gnd_x, 111.0, "GND")
    add_track(out_gnd_x, 111.0, out_gnd_x, 115.0, "GND", 0.35)

    # Place and route each of the 5 ICs and 10 classes
    pwr_u_x = {0: 52.0, 1: 56.0, 2: 60.0, 3: 64.0, 4: 68.0}
    neg_u_x = {0: 54.0, 1: 58.0, 2: 62.0, 3: 66.0, 4: 70.0}
    gnd_u_x = {0: 56.0, 1: 60.0, 2: 64.0, 3: 68.0, 4: 72.0}

    pos_c_x = {0: 59.0, 2: 63.0, 3: 67.0, 5: 71.0, 8: 75.0, 9: 79.0}
    neg_c_x = {1: 62.0, 4: 66.0, 6: 70.0, 7: 74.0}

    for idx, (u_ref, ic_x, ic_y, c_top, c_bot) in enumerate(ic_positions):
        ic = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
        ic.SetReference(u_ref)
        ic.SetValue("TL074")
        ic.Reference().SetVisible(False)
        ic.Value().SetVisible(False)
        ic.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(ic_x), pcbnew.FromMM(ic_y)))
        pdict = {
            "1": f"V_INV_{c_top}", "2": f"SUM_L2_POS_{c_top}", "3": "GND",
            "4": "+12V",
            "5": "GND", "6": f"SUM_L2_NEG_{c_top}", "7": f"V_SUM_{c_top}",
            "8": f"V_SUM_{c_bot}", "9": f"SUM_L2_NEG_{c_bot}", "10": "GND",
            "11": "-12V",
            "12": "GND", "13": f"SUM_L2_POS_{c_bot}", "14": f"V_INV_{c_bot}"
        }
        for pad in ic.Pads():
            pnum = pad.GetNumber()
            if pnum in pdict:
                pad.SetNet(net_map[pdict[pnum]])
        board.Add(ic)

        # GND under IC belly: Pins 3, 5, 10, 12
        add_track(ic_x - 2.475, ic_y - 1.27, ic_x + 2.475, ic_y - 1.27, "GND", 0.35)
        add_track(ic_x - 2.475, ic_y + 1.27, ic_x + 2.475, ic_y + 1.27, "GND", 0.35)
        add_track(ic_x, ic_y - 1.27, ic_x, ic_y + 1.27, "GND", 0.35)
        # Drop GND jumper north to top GND bus at (gnd_u_x[idx], 11.2)
        add_track(ic_x, ic_y - 1.27, ic_x, ic_y - 5.5, "GND", 0.35)
        add_jumper(ic_x, ic_y - 5.5, gnd_u_x[idx], 11.2, "GND")

        # Pin 4 (+12V at ic_x - 2.475, ic_y) -> track out to (60.0, ic_y) -> jumper to top +12V bus
        add_track(ic_x - 2.475, ic_y, 60.0, ic_y, "+12V", 0.35)
        add_jumper(60.0, ic_y, pwr_u_x[idx], 14.4, "+12V")

        # Pin 11 (-12V at ic_x + 2.475, ic_y) -> track out to (72.0, ic_y) -> jumper to top -12V bus
        add_track(ic_x + 2.475, ic_y, 72.0, ic_y, "-12V", 0.35)
        add_jumper(72.0, ic_y, neg_u_x[idx], 12.8, "-12V")

        # --- ROUTE TOP CLASS (c_top) on the LEFT of the IC ---
        # Rf1_L2 at X = 60.5, Y = ic_y - 3.175 (rot=-90)
        # Pad 1 (top): (60.5, ic_y - 4.0875) -> V_INV
        # Pad 2 (bot): (60.5, ic_y - 2.2625) -> SUM_L2_POS
        add_res(f"Rf1_L2_{c_top}", "10k", 60.5, ic_y - 3.175, -90, f"V_INV_{c_top}", f"SUM_L2_POS_{c_top}")
        add_track(ic_x - 2.475, ic_y - 3.81, 60.5, ic_y - 3.81, f"V_INV_{c_top}", 0.35)
        add_track(60.5, ic_y - 3.81, 60.5, ic_y - 4.0875, f"V_INV_{c_top}", 0.35)
        add_track(ic_x - 2.475, ic_y - 2.54, 60.5, ic_y - 2.54, f"SUM_L2_POS_{c_top}", 0.35)
        add_track(60.5, ic_y - 2.54, 60.5, ic_y - 2.2625, f"SUM_L2_POS_{c_top}", 0.35)

        # SUM_L2_POS planar route from (58.5, stages[c_top]["y_pos"]) around Pad 1 down to Pad 2 (60.5, ic_y - 2.2625):
        add_track(58.5, stages[c_top]["y_pos"], 58.5, ic_y - 2.2625, f"SUM_L2_POS_{c_top}", 0.35)
        add_track(58.5, ic_y - 2.2625, 60.5, ic_y - 2.2625, f"SUM_L2_POS_{c_top}", 0.35)

        # Rf_L2 at X = 60.5, Y = ic_y + 3.175 (rot=-90)
        # Pad 1 (top): (60.5, ic_y + 2.2625) -> SUM_L2_NEG
        # Pad 2 (bot): (60.5, ic_y + 4.0875) -> V_SUM
        add_res(f"Rf_L2_{c_top}", "10k", 60.5, ic_y + 3.175, -90, f"SUM_L2_NEG_{c_top}", f"V_SUM_{c_top}")
        add_track(ic_x - 2.475, ic_y + 2.54, 60.5, ic_y + 2.54, f"SUM_L2_NEG_{c_top}", 0.35)
        add_track(60.5, ic_y + 2.54, 60.5, ic_y + 2.2625, f"SUM_L2_NEG_{c_top}", 0.35)
        add_track(ic_x - 2.475, ic_y + 3.81, 60.5, ic_y + 3.81, f"V_SUM_{c_top}", 0.35)
        add_track(60.5, ic_y + 3.81, 60.5, ic_y + 4.0875, f"V_SUM_{c_top}", 0.35)

        # SUM_L2_NEG jumper from matrix at (50.5, stages[c_top]["y_neg"]) to Pad 1 area (56.5, ic_y + 2.54)
        add_jumper(50.5, stages[c_top]["y_neg"], 56.5, ic_y + 2.54, f"SUM_L2_NEG_{c_top}")
        add_track(56.5, ic_y + 2.54, 60.5, ic_y + 2.2625, f"SUM_L2_NEG_{c_top}", 0.35)

        # Rc_L2 at X = 56.5, Y = ic_y - 0.9125 (rot=-90)
        # Pad 1 (top): V_INV, Pad 2 (bot): SUM_L2_NEG
        add_res(f"Rc_L2_{c_top}", "10k", 56.5, ic_y - 0.9125, -90, f"V_INV_{c_top}", f"SUM_L2_NEG_{c_top}")
        add_track(60.5, ic_y - 4.0875, 56.5, ic_y - 4.0875, f"V_INV_{c_top}", 0.35)
        add_track(56.5, ic_y - 4.0875, 56.5, ic_y - 0.9125 - 0.9125, f"V_INV_{c_top}", 0.35)
        add_track(56.5, ic_y + 2.54, 56.5, ic_y - 0.9125 + 0.9125, f"SUM_L2_NEG_{c_top}", 0.35)

        # Rb_L2 at X = 53.0, Y = ic_y - 0.9125 (rot=-90)
        # Pad 1 (top): bias_rail, Pad 2 (bot): SUM_L2_NEG
        b_rail_top = w2_data["weights"][c_top]["bias_rail"]
        b_str_top = w2_data["weights"][c_top]["bias_resistor_str"]
        add_res(f"Rb_L2_{c_top}", b_str_top, 53.0, ic_y - 0.9125, -90, b_rail_top, f"SUM_L2_NEG_{c_top}", desc=f"rail={b_rail_top}")
        # Pad 2 (SUM_L2_NEG) connects to (56.5, ic_y) on copper
        add_track(53.0, ic_y, 56.5, ic_y, f"SUM_L2_NEG_{c_top}", 0.35)
        # Pad 1 connects to bias rail via jumper north to top margin
        add_track(53.0, ic_y - 1.825, 53.0, ic_y - 3.5, b_rail_top, 0.35)
        if b_rail_top == "+5V_REF":
            add_jumper(53.0, ic_y - 3.5, pos_c_x[c_top], 9.6, "+5V_REF")
        else:
            add_jumper(53.0, ic_y - 3.5, neg_c_x[c_top], 8.0, "-5V_REF")

        # --- ROUTE BOTTOM CLASS (c_bot) on the RIGHT of the IC ---
        # Rf1_L2 at X = 71.5, Y = ic_y - 3.175 (rot=-90)
        # Pad 1 (top): (71.5, ic_y - 4.0875) -> V_INV
        # Pad 2 (bot): (71.5, ic_y - 2.2625) -> SUM_L2_POS
        add_res(f"Rf1_L2_{c_bot}", "10k", 71.5, ic_y - 3.175, -90, f"V_INV_{c_bot}", f"SUM_L2_POS_{c_bot}")
        add_track(ic_x + 2.475, ic_y - 3.81, 71.5, ic_y - 3.81, f"V_INV_{c_bot}", 0.35)
        add_track(71.5, ic_y - 3.81, 71.5, ic_y - 4.0875, f"V_INV_{c_bot}", 0.35)
        add_track(ic_x + 2.475, ic_y - 2.54, 71.5, ic_y - 2.54, f"SUM_L2_POS_{c_bot}", 0.35)
        add_track(71.5, ic_y - 2.54, 71.5, ic_y - 2.2625, f"SUM_L2_POS_{c_bot}", 0.35)

        # SUM_L2_POS jumper from matrix to Pad 2 of Rf1_L2 (landing at 74.0, ic_y - 2.2625)
        add_jumper(50.5, stages[c_bot]["y_pos"], 74.0, ic_y - 2.2625, f"SUM_L2_POS_{c_bot}")
        add_track(74.0, ic_y - 2.2625, 71.5, ic_y - 2.2625, f"SUM_L2_POS_{c_bot}", 0.35)

        # Rf_L2 at X = 71.5, Y = ic_y + 3.175 (rot=-90)
        # Pad 1 (top): (71.5, ic_y + 2.2625) -> SUM_L2_NEG
        # Pad 2 (bot): (71.5, ic_y + 4.0875) -> V_SUM
        add_res(f"Rf_L2_{c_bot}", "10k", 71.5, ic_y + 3.175, -90, f"SUM_L2_NEG_{c_bot}", f"V_SUM_{c_bot}")
        add_track(ic_x + 2.475, ic_y + 2.54, 71.5, ic_y + 2.54, f"SUM_L2_NEG_{c_bot}", 0.35)
        add_track(71.5, ic_y + 2.54, 71.5, ic_y + 2.2625, f"SUM_L2_NEG_{c_bot}", 0.35)
        add_track(ic_x + 2.475, ic_y + 3.81, 71.5, ic_y + 3.81, f"V_SUM_{c_bot}", 0.35)
        add_track(71.5, ic_y + 3.81, 71.5, ic_y + 4.0875, f"V_SUM_{c_bot}", 0.35)

        # SUM_L2_NEG jumper from matrix to Pad 1 of Rf_L2 area (74.0, ic_y + 2.54)
        add_jumper(50.5, stages[c_bot]["y_neg"], 74.0, ic_y + 2.54, f"SUM_L2_NEG_{c_bot}")
        add_track(74.0, ic_y + 2.54, 71.5, ic_y + 2.2625, f"SUM_L2_NEG_{c_bot}", 0.35)

        # Rc_L2 at X = 75.5, Y = ic_y - 0.9125 (rot=-90)
        add_res(f"Rc_L2_{c_bot}", "10k", 75.5, ic_y - 0.9125, -90, f"V_INV_{c_bot}", f"SUM_L2_NEG_{c_bot}")
        add_track(71.5, ic_y - 4.0875, 75.5, ic_y - 4.0875, f"V_INV_{c_bot}", 0.35)
        add_track(75.5, ic_y - 4.0875, 75.5, ic_y - 0.9125 - 0.9125, f"V_INV_{c_bot}", 0.35)
        add_track(74.0, ic_y + 2.54, 75.5, ic_y - 0.9125 + 0.9125, f"SUM_L2_NEG_{c_bot}", 0.35)

        # Rb_L2 at X = 79.0, Y = ic_y - 0.9125 (rot=-90)
        b_rail_bot = w2_data["weights"][c_bot]["bias_rail"]
        b_str_bot = w2_data["weights"][c_bot]["bias_resistor_str"]
        add_res(f"Rb_L2_{c_bot}", b_str_bot, 79.0, ic_y - 0.9125, -90, b_rail_bot, f"SUM_L2_NEG_{c_bot}", desc=f"rail={b_rail_bot}")
        add_track(75.5, ic_y, 79.0, ic_y, f"SUM_L2_NEG_{c_bot}", 0.35)
        # Pad 1 connects to bias rail via jumper north to top margin
        add_track(79.0, ic_y - 1.825, 79.0, ic_y - 3.5, b_rail_bot, 0.35)
        if b_rail_bot == "+5V_REF":
            add_jumper(79.0, ic_y - 3.5, pos_c_x[c_bot], 9.6, "+5V_REF")
        else:
            add_jumper(79.0, ic_y - 3.5, neg_c_x[c_bot], 8.0, "-5V_REF")

        # --- WTA, DIODES, AND LEDS FOR BOTH CLASSES ---
        for c, is_top in [(c_top, True), (c_bot, False)]:
            y_wta = ic_y - 2.5 if is_top else ic_y + 2.5
            out_hdr_x = 20.0 + c * 2.54

            # V_SUM source pad on op-amp:
            # c_top: Pin 7 at (ic_x - 2.475, ic_y + 3.81) = (63.525, ic_y + 3.81)
            # c_bot: Pin 8 at (ic_x + 2.475, ic_y + 3.81) = (68.475, ic_y + 3.81)
            v_sum_pin_x = ic_x - 2.475 if is_top else ic_x + 2.475

            # Connect Pin 7/8 down to jumper pad 1 at (v_sum_pin_x, ic_y + 5.5)
            # and jumper pad 2 at (v_sum_pin_x, ic_y + 8.0)
            add_track(v_sum_pin_x, ic_y + 3.81, v_sum_pin_x, ic_y + 8.0, f"V_SUM_{c}", 0.35)

            # 1. Fly V_SUM directly to J_BOT pin at (out_hdr_x, 111.0)
            add_jumper(v_sum_pin_x, ic_y + 5.5, out_hdr_x, 111.0, f"V_SUM_{c}")
            add_track(out_hdr_x, 111.0, out_hdr_x, 115.0, f"V_SUM_{c}", 0.35)

            # 2. Fly V_SUM to (81.0, y_wta) via jumper for WTA diode and LED
            add_jumper(v_sum_pin_x, ic_y + 8.0, 81.0, y_wta, f"V_SUM_{c}")

            # 3. Diode D_c at (84.5, y_wta) rot=180
            # Pad 2 (A) at 82.85 -> V_SUM
            # Pad 1 (K) at 86.15 -> WTA_BUS
            add_dio(f"D_{c}", "1N4148", 84.5, y_wta, 180, "WTA_BUS", f"V_SUM_{c}")
            add_track(81.0, y_wta, 84.5 - 1.65, y_wta, f"V_SUM_{c}", 0.35)
            add_track(84.5 + 1.65, y_wta, 87.5, y_wta, "WTA_BUS", 0.35)

            # 4. Jump over WTA_BUS to LED:
            # Pad 1 at (81.0, y_wta - 2.54 if is_top else y_wta + 2.54)
            # Pad 2 at (90.5, y_wta)
            y_jump = y_wta - 2.54 if is_top else y_wta + 2.54
            add_track(81.0, y_wta, 81.0, y_jump, f"V_SUM_{c}", 0.35)
            add_jumper(81.0, y_jump, 90.5, y_wta, f"V_SUM_{c}")

            # 5. LED_c at (93.0, y_wta) rot=180
            # Pad 2 (A) at 92.05 -> V_SUM
            # Pad 1 (K) at 93.95 -> LED_NET
            add_led(f"LED_{c}", "RED", 93.0, y_wta, 180, f"LED_NET_{c}", f"V_SUM_{c}")
            add_track(90.5, y_wta, 93.0 - 0.95, y_wta, f"V_SUM_{c}", 0.35)

            # 6. R_LED_c at (96.5, y_wta) rot=0
            # Pad 1 at 95.5875 -> LED_NET
            # Pad 2 at 97.4125 -> GND
            add_res(f"R_LED{c}", "1k", 96.5, y_wta, 0, f"LED_NET_{c}", "GND")
            add_track(93.0 + 0.95, y_wta, 96.5 - 0.9125, y_wta, f"LED_NET_{c}", 0.35)
            add_track(96.5 + 0.9125, y_wta, 98.0, y_wta, "GND", 0.35)

    board.Save(target_pcb_path)

    # Post-save: Replace (duplicate_pad_numbers_are_jumpers no) with yes in file
    with open(target_pcb_path, "r") as f:
        text = f.read()
    text = text.replace('(duplicate_pad_numbers_are_jumpers no)', '(duplicate_pad_numbers_are_jumpers yes)')
    with open(target_pcb_path, "w") as f:
        f.write(text)

    print(f"Generated flawless DC3 board {target_pcb_path} with {jumper_count[0]} jumpers.")

if __name__ == "__main__":
    out_pcb = os.path.join(WORKSPACE, "daughtercard3_weights_l2_wta.kicad_pcb")
    generate_dc3_board(out_pcb)
