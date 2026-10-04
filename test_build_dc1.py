#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
test_build_dc1.py
-----------------
Tests building daughtercard1a_weights_l1.kicad_pcb with non-overlapping footprints.
"""

import os
import sys
import json
import subprocess
import pcbnew

WORKSPACE = "/Users/lucaszhang/pcbai"
W1_PATH   = os.path.join(WORKSPACE, "weights_layer1.json")
PCB_PATH  = os.path.join(WORKSPACE, "daughtercard1a_weights_l1.kicad_pcb")

BOARD_W = 100.0
BOARD_H = 100.0

def build_dc1(filename=PCB_PATH, neuron_range=range(0, 4), title="Daughtercard 1A: L1 Weights (Neurons 0..3)"):
    with open(W1_PATH) as f:
        w1_data = json.load(f)
        
    board = pcbnew.BOARD()
    
    # 1. Rules
    ds = board.GetDesignSettings()
    ds.m_MinClearance = pcbnew.FromMM(0.50)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
    ds.SetCustomTrackWidth(pcbnew.FromMM(0.40))
    
    # 2. Add Nets
    nets = ["GND", "+12V", "-12V", "+5V_REF"]
    for i in range(64):
        nets.append(f"IN_{i}")
    for j in neuron_range:
        nets.extend([f"SUM_POS_{j}", f"SUM_NEG_{j}", f"V_INV_{j}", f"V_SUM_{j}"])
        
    net_map = {}
    for n in nets:
        netinfo = pcbnew.NETINFO_ITEM(board, n)
        board.Add(netinfo)
        net_map[n] = board.FindNet(n)
        
    # 3. Outline (100 x 100 mm)
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
        seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
        seg.SetWidth(pcbnew.FromMM(0.15))
        seg.SetLayer(pcbnew.Edge_Cuts)
        board.Add(seg)
        
    # 4. Mounting Holes M3
    fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
    for idx, (hx, hy) in enumerate([(4.0, 4.0), (BOARD_W - 4.0, 4.0), (4.0, BOARD_H - 4.0), (BOARD_W - 4.0, BOARD_H - 4.0)]):
        mh = pcbnew.FootprintLoad(fp_mh_path, "MountingHole_3.2mm_M3")
        mh.SetReference(f"MH{idx+1}")
        mh.Reference().SetVisible(False)
        mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
        board.Add(mh)
        
    # 5. Connectors
    fp_hdr_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty"
    
    # J_IN_A: 1x36 at bottom (Y = 94.0mm, X = 5.5..94.4mm)
    j_in_a = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x36_P2.54mm_Vertical")
    j_in_a.SetReference("J_IN_A")
    j_in_a.SetValue("INPUTS_0_31_PWR")
    j_in_a.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.5), pcbnew.FromMM(94.0)))
    j_in_a.SetOrientation(pcbnew.EDA_ANGLE(-90, pcbnew.DEGREES_T)) # Horizontal along bottom
    for p in j_in_a.Pads():
        pnum = int(p.GetNumber())
        if pnum <= 32:
            p.SetNet(net_map[f"IN_{pnum-1}"])
        elif pnum == 33: p.SetNet(net_map["+12V"])
        elif pnum == 34: p.SetNet(net_map["-12V"])
        elif pnum == 35: p.SetNet(net_map["GND"])
        elif pnum == 36: p.SetNet(net_map["+5V_REF"])
    board.Add(j_in_a)

    # J_IN_B: 1x36 at top (Y = 6.0mm, X = 5.5..94.4mm)
    j_in_b = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x36_P2.54mm_Vertical")
    j_in_b.SetReference("J_IN_B")
    j_in_b.SetValue("INPUTS_32_63_SUM")
    j_in_b.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.5), pcbnew.FromMM(6.0)))
    j_in_b.SetOrientation(pcbnew.EDA_ANGLE(-90, pcbnew.DEGREES_T)) # Horizontal along top
    for p in j_in_b.Pads():
        pnum = int(p.GetNumber())
        if pnum <= 32:
            p.SetNet(net_map[f"IN_{32 + pnum - 1}"])
        else:
            j_local = pnum - 33
            j_global = neuron_range[j_local]
            p.SetNet(net_map[f"V_SUM_{j_global}"])
    board.Add(j_in_b)
    
    # 6. Footprints
    fp_res_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty"
    fp_ic_path  = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_SO.pretty"
    fp_cap_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Capacitor_SMD.pretty"

    def add_res(ref, val, x, y, rot, n1, n2):
        fp = pcbnew.FootprintLoad(fp_res_path, "R_0805_2012Metric")
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

    # 7. Op-Amps: 2x TL074 (U1 for U_INV, U2 for U_SUM)
    # U1 (Inverters for SUM_NEG_0..3) placed at X = 88.0, Y = 28.0
    u1 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
    u1.SetReference("U1")
    u1.SetValue("TL074_INV")
    u1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(88.0), pcbnew.FromMM(28.0)))
    n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]
    u1_pdict = {
        "1": f"V_INV_{n0}", "2": f"SUM_NEG_{n0}", "3": "GND",
        "4": "+12V",
        "5": "GND", "6": f"SUM_NEG_{n1}", "7": f"V_INV_{n1}",
        "8": f"V_INV_{n2}", "9": f"SUM_NEG_{n2}", "10": "GND",
        "11": "-12V",
        "12": "GND", "13": f"SUM_NEG_{n3}", "14": f"V_INV_{n3}"
    }
    for pad in u1.Pads():
        pnum = pad.GetNumber()
        if pnum in u1_pdict:
            pad.SetNet(net_map[u1_pdict[pnum]])
    board.Add(u1)
    
    # U2 (Summers for SUM_POS_0..3 + Coupling) placed at X = 88.0, Y = 70.0
    u2 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
    u2.SetReference("U2")
    u2.SetValue("TL074_SUM")
    u2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(88.0), pcbnew.FromMM(70.0)))
    u2_pdict = {
        "1": f"V_SUM_{n0}", "2": f"SUM_POS_{n0}", "3": "GND",
        "4": "+12V",
        "5": "GND", "6": f"SUM_POS_{n1}", "7": f"V_SUM_{n1}",
        "8": f"V_SUM_{n2}", "9": f"SUM_POS_{n2}", "10": "GND",
        "11": "-12V",
        "12": "GND", "13": f"SUM_POS_{n3}", "14": f"V_SUM_{n3}"
    }
    for pad in u2.Pads():
        pnum = pad.GetNumber()
        if pnum in u2_pdict:
            pad.SetNet(net_map[u2_pdict[pnum]])
    board.Add(u2)

    # Decoupling Caps for U1 and U2
    add_cap("C_U1_POS", "100n", 80.0, 28.0, 0, "+12V", "GND")
    add_cap("C_U1_NEG", "100n", 96.0, 28.0, 0, "-12V", "GND")
    add_cap("C_U2_POS", "100n", 80.0, 70.0, 0, "+12V", "GND")
    add_cap("C_U2_NEG", "100n", 96.0, 70.0, 0, "-12V", "GND")

    # Feedback & Coupling Resistors for each neuron:
    # Placed in the corridor X = 80..96, Y = 40..58
    for local_idx, j in enumerate(neuron_range):
        y_rf1 = 40.0 + local_idx * 4.5
        y_rc  = 40.0 + local_idx * 4.5
        y_rf2 = 40.0 + local_idx * 4.5
        
        add_res(f"Rf1_N{j}", "10k", 80.0, y_rf1, 0, f"V_INV_{j}", f"SUM_NEG_{j}")
        add_res(f"Rc_N{j}",  "10k", 88.0, y_rc,  0, f"V_INV_{j}", f"SUM_POS_{j}")
        add_res(f"Rf2_N{j}", "10k", 96.0, y_rf2, 0, f"V_SUM_{j}", f"SUM_POS_{j}")

        # Bias from weights_layer1.json
        b_val = w1_data["weights"][j]["bias_float"]
        b_str = w1_data["weights"][j].get("bias_resistor_str", "10k")
        bus_net = f"SUM_POS_{j}" if b_val >= 0 else f"SUM_NEG_{j}"
        add_res(f"Rb_N{j}", b_str, 88.0, 16.0 + local_idx * 3.0, 0, "+5V_REF", bus_net)

    # 8. Synaptic Resistor Matrix (256 components)
    # 32 columns at X = 5.5 + col * 2.25 mm (X = 5.5 to 75.25 mm)
    # 8 rows at Y = 16.0, 24.0, 32.0, 40.0, 52.0, 60.0, 68.0, 76.0
    row_y = [16.0, 24.0, 32.0, 40.0, 52.0, 60.0, 68.0, 76.0]
    col_x_start = 5.5
    col_dx = 2.25

    active_synapses = 0
    for col in range(32):
        cx = col_x_start + col * col_dx
        for r in range(8):
            ry = row_y[r]
            in_idx = col if r < 4 else (32 + col)
            local_n = r % 4
            j = neuron_range[local_n]
            
            w_info = w1_data["weights"][j]["inputs"][in_idx]
            val_str = w_info.get("resistor_str", "OPEN")
            w_pol = w_info.get("polarity", "positive")
            
            bus_net = f"SUM_POS_{j}" if w_pol == "positive" else f"SUM_NEG_{j}"
            
            ref = f"R1_{in_idx}_{local_n}"
            add_res(ref, val_str, cx, ry, 90, f"IN_{in_idx}", bus_net)
            if val_str not in ["OPEN", "DNP", "NC", None]:
                active_synapses += 1

    board.Save(filename)
    print(f"DC1 board saved to {filename} ({active_synapses} active synapses).")

if __name__ == "__main__":
    build_dc1()
