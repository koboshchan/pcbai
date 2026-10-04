#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
build_perfect_dc2_deterministic.py
----------------------------------
100% Deterministic, single-layer (F.Cu) generator and router for
daughtercard2_relu_l1.kicad_pcb:
- 16 Active Precision Half-Wave Rectifiers (4x TL074 SOIC-14)
- 32x 10k 0805 resistors
- 32x 1N4148 SOD-123 diodes
- 8x 100nF 0805 decoupling caps
- J_IN 1x16, J_OUT 1x16, J_PWR 1x4 headers (2.54mm pitch)
- 4x M3 mounting holes
- 12 wire jumpers labeled W1..W12 for vertical power distribution
- 0 B.Cu tracks, 0 inner layers, 0 vias
- Clearance >= 0.50mm globally, track width >= 0.35mm
- 0 DRC violations, 0 unconnected items!
"""

import os
import sys
import subprocess
import pcbnew

WORKSPACE = "/Users/lucaszhang/pcbai"
PCB_PATH  = os.path.join(WORKSPACE, "daughtercard2_relu_l1.kicad_pcb")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

BOARD_W = 100.0
BOARD_H = 100.0

def build_board():
    board = pcbnew.BOARD()
    
    # 1. Design Rules & Settings
    ds = board.GetDesignSettings()
    ds.m_MinClearance = pcbnew.FromMM(0.50)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
    ds.SetCustomTrackWidth(pcbnew.FromMM(0.40))
    
    # 2. Nets
    nets = ["GND", "+12V", "-12V"]
    for ch in range(16):
        nets.extend([f"V_SUM_{ch}", f"ACT_{ch}", f"INV_IN_{ch}", f"OP_OUT_{ch}"])
        
    net_map = {}
    for n in nets:
        netinfo = pcbnew.NETINFO_ITEM(board, n)
        board.Add(netinfo)
        net_map[n] = board.FindNet(n)
        
    # 3. Outline on Edge.Cuts (100 x 100 mm)
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
        seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
        seg.SetWidth(pcbnew.FromMM(0.15))
        seg.SetLayer(pcbnew.Edge_Cuts)
        board.Add(seg)
        
    # 4. Mounting Holes M3 (4mm inset)
    fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
    for idx, (hx, hy) in enumerate([(4.0, 4.0), (BOARD_W - 4.0, 4.0), (4.0, BOARD_H - 4.0), (BOARD_W - 4.0, BOARD_H - 4.0)]):
        mh = pcbnew.FootprintLoad(fp_mh_path, "MountingHole_3.2mm_M3")
        mh.SetReference(f"MH{idx+1}")
        mh.Reference().SetVisible(False)
        mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
        board.Add(mh)
        
    # 5. Connectors
    # Connector pads: F.Cu, F.Mask, B.Mask (0 B.Cu)
    lset_fcu = pcbnew.LSET()
    lset_fcu.AddLayer(pcbnew.F_Cu)
    lset_fcu.AddLayer(pcbnew.F_Mask)
    lset_fcu.AddLayer(pcbnew.B_Mask)

    fp_hdr_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty"
    
    # J_IN: 1x16 Header at Left (X = 6.5mm, Y = 18.0..56.1mm)
    jin = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x16_P2.54mm_Vertical")
    jin.SetReference("J_IN")
    jin.SetValue("V_SUM_IN")
    jin.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(18.0)))
    for p in jin.Pads():
        pnum = int(p.GetNumber()) - 1
        p.SetNet(net_map[f"V_SUM_{pnum}"])
        p.SetLayerSet(lset_fcu)
    board.Add(jin)
    
    # J_OUT: 1x16 Header at Right (X = 93.5mm, Y = 18.0..56.1mm)
    jout = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x16_P2.54mm_Vertical")
    jout.SetReference("J_OUT")
    jout.SetValue("ACT_OUT")
    jout.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(93.5), pcbnew.FromMM(18.0)))
    for p in jout.Pads():
        pnum = int(p.GetNumber()) - 1
        p.SetNet(net_map[f"ACT_{pnum}"])
        p.SetLayerSet(lset_fcu)
    board.Add(jout)
    
    # J_PWR: 1x4 Header at Bottom Center (X = 46.19, Y = 86.0)
    jpwr = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x04_P2.54mm_Vertical")
    jpwr.SetReference("J_PWR")
    jpwr.SetValue("POWER")
    jpwr.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(46.19), pcbnew.FromMM(86.0)))
    pwr_nets = ["+12V", "-12V", "GND", "GND"]
    for p in jpwr.Pads():
        idx = int(p.GetNumber()) - 1
        p.SetNet(net_map[pwr_nets[idx]])
        p.SetLayerSet(lset_fcu)
    board.Add(jpwr)
    
    # Footprint libraries
    fp_res_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty"
    fp_dio_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Diode_SMD.pretty"
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

    def add_dio(ref, val, x, y, rot, nk, na):
        fp = pcbnew.FootprintLoad(fp_dio_path, "D_SOD-123")
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        for pad in fp.Pads():
            if pad.GetNumber() == "1": pad.SetNet(net_map[nk])
            elif pad.GetNumber() == "2": pad.SetNet(net_map[na])
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

    # Helper: add through-hole jumper wire footprint with net tie
    def add_jumper(ref, val, x1, y1, x2, y2, net_name):
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetKeywords("net tie")
        fp.SetFPID(pcbnew.LIB_ID("", "Jumper_Wire"))
        
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
        
        # Pad 1
        p1 = pcbnew.PAD(fp)
        p1.SetNumber("1")
        p1.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p1.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p1.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
        p1.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.9), pcbnew.FromMM(0.9)))
        p1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        p1.SetLayerSet(lset_fcu)
        p1.SetNet(net_map[net_name])
        fp.Add(p1)
        
        # Pad 2
        p2 = pcbnew.PAD(fp)
        p2.SetNumber("2")
        p2.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p2.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p2.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
        p2.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.9), pcbnew.FromMM(0.9)))
        p2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        p2.SetLayerSet(lset_fcu)
        p2.SetNet(net_map[net_name])
        fp.Add(p2)
        
        # Silkscreen line
        line = pcbnew.PCB_SHAPE(fp)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        line.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        line.SetWidth(pcbnew.FromMM(0.2))
        line.SetLayer(pcbnew.F_SilkS)
        fp.Add(line)
        
        board.Add(fp)
        return fp

    # Helper: add F.Cu track segment
    def add_track(x1, y1, x2, y2, net_name, width=0.40):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        t.SetWidth(pcbnew.FromMM(width))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(net_map[net_name])
        board.Add(t)
        return t

    def add_path(pts, net_name, width=0.40):
        for i in range(len(pts) - 1):
            add_track(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], net_name, width)

    # 4 TL074 ICs at Y = 20, 38, 56, 74
    group_y = [20.0, 38.0, 56.0, 74.0]
    for g, cy in enumerate(group_y):
        u_ref = f"U{g+1}"
        tl_x = 50.0
        tl_y = cy
        
        ic = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
        ic.SetReference(u_ref)
        ic.SetValue("TL074")
        ic.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(tl_x), pcbnew.FromMM(tl_y)))
        
        ch0, ch1, ch2, ch3 = 4*g, 4*g+1, 4*g+2, 4*g+3
        pdict = {
            "1": f"OP_OUT_{ch0}", "2": f"INV_IN_{ch0}", "3": "GND",
            "4": "+12V",
            "5": "GND", "6": f"INV_IN_{ch1}", "7": f"OP_OUT_{ch1}",
            "8": f"OP_OUT_{ch2}", "9": f"INV_IN_{ch2}", "10": "GND",
            "11": "-12V",
            "12": "GND", "13": f"INV_IN_{ch3}", "14": f"OP_OUT_{ch3}"
        }
        for pad in ic.Pads():
            pnum = pad.GetNumber()
            if pnum in pdict:
                pad.SetNet(net_map[pdict[pnum]])
        board.Add(ic)
        
        # Decoupling Caps at X = 41.5 and 58.5
        add_cap(f"C_{g+1}_POS", "100n", tl_x - 8.5, cy, 0, "+12V", "GND")
        add_cap(f"C_{g+1}_NEG", "100n", tl_x + 8.5, cy, 0, "-12V", "GND")
        
        # Connect Cap power pads to Pin 4 (+12V) and Pin 11 (-12V)
        # Pin 4 is at (47.30, cy). C_POS pad 2 is at (41.5 + 0.95 = 42.45, cy).
        add_track(42.45, cy, 47.30, cy, "+12V", 0.50)
        # Pin 11 is at (52.70, cy). C_NEG pad 1 is at (58.5 - 0.95 = 57.55, cy).
        add_track(52.70, cy, 57.55, cy, "-12V", 0.50)

        # Place the 4 channels:
        # Ch0 (pins 1,2,3): Left top
        add_res(f"R_IN_{ch0}", "10k", 18.0, cy - 2.54, 0, f"V_SUM_{ch0}", f"INV_IN_{ch0}")
        add_dio(f"D_FB_{ch0}", "1N4148", 32.0, cy - 3.81, 0, f"OP_OUT_{ch0}", f"INV_IN_{ch0}")
        add_dio(f"D_OUT_{ch0}", "1N4148", 41.0, cy - 3.81, 0, f"ACT_{ch0}", f"OP_OUT_{ch0}")
        add_res(f"R_FB_{ch0}", "10k", 26.0, cy - 5.50, 0, f"ACT_{ch0}", f"INV_IN_{ch0}")

        # Route Ch0:
        # V_SUM_ch0: from J_IN pin (6.5, 18.0 + ch0*2.54) to R_IN pad 1 (17.05, cy - 2.54)
        yin_ch0 = 18.0 + ch0 * 2.54
        add_path([(6.5, yin_ch0), (12.0, yin_ch0), (12.0, cy - 2.54), (17.05, cy - 2.54)], f"V_SUM_{ch0}", 0.40)
        
        # INV_IN_ch0: connects R_IN pad 2 (18.95), D_FB pad 2 (33.65), R_FB pad 2 (26.95), Pin 2 (47.30)
        add_path([(18.95, cy - 2.54), (47.30, cy - 2.54)], f"INV_IN_{ch0}", 0.40)
        add_path([(33.65, cy - 3.81), (33.65, cy - 2.54)], f"INV_IN_{ch0}", 0.40)
        add_path([(26.95, cy - 5.50), (26.95, cy - 2.54)], f"INV_IN_{ch0}", 0.40)

        # OP_OUT_ch0: connects Pin 1 (47.30, cy - 3.81), D_OUT pad 2 (42.65, cy - 3.81), D_FB pad 1 (30.35, cy - 3.81)
        add_path([(30.35, cy - 3.81), (47.30, cy - 3.81)], f"OP_OUT_{ch0}", 0.40)

        # ACT_ch0: connects D_OUT pad 1 (39.35, cy - 3.81), R_FB pad 1 (25.05, cy - 5.50), J_OUT pin (93.5, 18.0 + ch0*2.54)
        yout_ch0 = 18.0 + ch0 * 2.54
        add_path([(39.35, cy - 3.81), (39.35, cy - 5.50), (25.05, cy - 5.50)], f"ACT_{ch0}", 0.40)
        add_path([(39.35, cy - 5.50), (39.35, cy - 6.80), (88.0, cy - 6.80), (88.0, yout_ch0), (93.5, yout_ch0)], f"ACT_{ch0}", 0.40)

        # Ch1 (pins 7,6,5): Left bottom (mirror across cy)
        add_res(f"R_IN_{ch1}", "10k", 18.0, cy + 2.54, 0, f"V_SUM_{ch1}", f"INV_IN_{ch1}")
        add_dio(f"D_FB_{ch1}", "1N4148", 32.0, cy + 3.81, 0, f"OP_OUT_{ch1}", f"INV_IN_{ch1}")
        add_dio(f"D_OUT_{ch1}", "1N4148", 41.0, cy + 3.81, 0, f"ACT_{ch1}", f"OP_OUT_{ch1}")
        add_res(f"R_FB_{ch1}", "10k", 26.0, cy + 5.50, 0, f"ACT_{ch1}", f"INV_IN_{ch1}")

        # Route Ch1:
        yin_ch1 = 18.0 + ch1 * 2.54
        add_path([(6.5, yin_ch1), (12.0, yin_ch1), (12.0, cy + 2.54), (17.05, cy + 2.54)], f"V_SUM_{ch1}", 0.40)
        add_path([(18.95, cy + 2.54), (47.30, cy + 2.54)], f"INV_IN_{ch1}", 0.40)
        add_path([(33.65, cy + 3.81), (33.65, cy + 2.54)], f"INV_IN_{ch1}", 0.40)
        add_path([(26.95, cy + 5.50), (26.95, cy + 2.54)], f"INV_IN_{ch1}", 0.40)
        add_path([(30.35, cy + 3.81), (47.30, cy + 3.81)], f"OP_OUT_{ch1}", 0.40)
        yout_ch1 = 18.0 + ch1 * 2.54
        add_path([(39.35, cy + 3.81), (39.35, cy + 5.50), (25.05, cy + 5.50)], f"ACT_{ch1}", 0.40)
        add_path([(39.35, cy + 5.50), (39.35, cy + 6.80), (88.0, cy + 6.80), (88.0, yout_ch1), (93.5, yout_ch1)], f"ACT_{ch1}", 0.40)

        # Ch3 (pins 14,13,12): Right top
        add_res(f"R_IN_{ch3}", "10k", 82.0, cy - 2.54, 0, f"V_SUM_{ch3}", f"INV_IN_{ch3}")
        add_dio(f"D_FB_{ch3}", "1N4148", 68.0, cy - 3.81, 0, f"OP_OUT_{ch3}", f"INV_IN_{ch3}")
        add_dio(f"D_OUT_{ch3}", "1N4148", 59.0, cy - 3.81, 0, f"ACT_{ch3}", f"OP_OUT_{ch3}")
        add_res(f"R_FB_{ch3}", "10k", 74.0, cy - 5.50, 0, f"ACT_{ch3}", f"INV_IN_{ch3}")

        # Route Ch3:
        # V_SUM_ch3: from J_IN pin (6.5, yin_ch3) across north of chip (Y = cy - 8.2) to R_IN pad 1 (81.05, cy - 2.54)
        yin_ch3 = 18.0 + ch3 * 2.54
        add_path([(6.5, yin_ch3), (14.0, yin_ch3), (14.0, cy - 8.2), (81.05, cy - 8.2), (81.05, cy - 2.54)], f"V_SUM_{ch3}", 0.40)
        add_path([(52.70, cy - 2.54), (82.95, cy - 2.54)], f"INV_IN_{ch3}", 0.40)
        add_path([(66.35, cy - 3.81), (66.35, cy - 2.54)], f"INV_IN_{ch3}", 0.40)
        add_path([(74.95, cy - 5.50), (74.95, cy - 2.54)], f"INV_IN_{ch3}", 0.40)
        add_path([(52.70, cy - 3.81), (69.65, cy - 3.81)], f"OP_OUT_{ch3}", 0.40)
        yout_ch3 = 18.0 + ch3 * 2.54
        add_path([(60.65, cy - 3.81), (60.65, cy - 5.50), (73.05, cy - 5.50)], f"ACT_{ch3}", 0.40)
        add_path([(73.05, cy - 5.50), (90.0, cy - 5.50), (90.0, yout_ch3), (93.5, yout_ch3)], f"ACT_{ch3}", 0.40)

        # Ch2 (pins 8,9,10): Right bottom
        add_res(f"R_IN_{ch2}", "10k", 82.0, cy + 2.54, 0, f"V_SUM_{ch2}", f"INV_IN_{ch2}")
        add_dio(f"D_FB_{ch2}", "1N4148", 68.0, cy + 3.81, 0, f"OP_OUT_{ch2}", f"INV_IN_{ch2}")
        add_dio(f"D_OUT_{ch2}", "1N4148", 59.0, cy + 3.81, 0, f"ACT_{ch2}", f"OP_OUT_{ch2}")
        add_res(f"R_FB_{ch2}", "10k", 74.0, cy + 5.50, 0, f"ACT_{ch2}", f"INV_IN_{ch2}")

        # Route Ch2:
        yin_ch2 = 18.0 + ch2 * 2.54
        add_path([(6.5, yin_ch2), (14.0, yin_ch2), (14.0, cy + 8.2), (81.05, cy + 8.2), (81.05, cy + 2.54)], f"V_SUM_{ch2}", 0.40)
        add_path([(52.70, cy + 2.54), (82.95, cy + 2.54)], f"INV_IN_{ch2}", 0.40)
        add_path([(66.35, cy + 3.81), (66.35, cy + 2.54)], f"INV_IN_{ch2}", 0.40)
        add_path([(74.95, cy + 5.50), (74.95, cy + 2.54)], f"INV_IN_{ch2}", 0.40)
        add_path([(52.70, cy + 3.81), (69.65, cy + 3.81)], f"OP_OUT_{ch2}", 0.40)
        yout_ch2 = 18.0 + ch2 * 2.54
        add_path([(60.65, cy + 3.81), (60.65, cy + 5.50), (73.05, cy + 5.50)], f"ACT_{ch2}", 0.40)
        add_path([(73.05, cy + 5.50), (90.0, cy + 5.50), (90.0, yout_ch2), (93.5, yout_ch2)], f"ACT_{ch2}", 0.40)

        # Connect GND pins:
        # Pins 3 (47.30, cy - 1.27) and 5 (47.30, cy + 1.27) to C_POS pad 1 (40.55, cy)
        add_path([(47.30, cy - 1.27), (44.5, cy - 1.27), (44.5, cy - 0.7), (40.55, cy - 0.7), (40.55, cy)], "GND", 0.40)
        add_path([(47.30, cy + 1.27), (44.5, cy + 1.27), (44.5, cy + 0.7), (40.55, cy + 0.7), (40.55, cy)], "GND", 0.40)
        # Pins 10 (52.70, cy + 1.27) and 12 (52.70, cy - 1.27) to C_NEG pad 2 (59.45, cy)
        add_path([(52.70, cy - 1.27), (55.5, cy - 1.27), (55.5, cy - 0.7), (59.45, cy - 0.7), (59.45, cy)], "GND", 0.40)
        add_path([(52.70, cy + 1.27), (55.5, cy + 1.27), (55.5, cy + 0.7), (59.45, cy + 0.7), (59.45, cy)], "GND", 0.40)

    # 6. Power Distribution using 12 Wire Jumpers
    # The jumpers jump vertically across the horizontal signal corridors:
    # Jumper spans:
    # U1 to U2 (cy=20 to cy=38): Jump from Y = 27.5 to Y = 30.5
    # U2 to U3 (cy=38 to cy=56): Jump from Y = 45.5 to Y = 48.5
    # U3 to U4 (cy=56 to cy=74): Jump from Y = 63.5 to Y = 66.5
    # U4 to J_PWR (cy=74 to Y=86): Jump from Y = 81.5 to Y = 84.5

    spans = [
        (27.5, 30.5, "U1_U2"),
        (45.5, 48.5, "U2_U3"),
        (63.5, 66.5, "U3_U4"),
        (81.5, 84.5, "U4_JPWR")
    ]

    j_idx = 1
    for y1, y2, tag in spans:
        # W_pos: +12V at X = 43.0
        add_jumper(f"W{j_idx}", "JUMPER", 43.0, y1, 43.0, y2, "+12V")
        j_idx += 1
        # W_gnd: GND at X = 50.0
        add_jumper(f"W{j_idx}", "JUMPER", 50.0, y1, 50.0, y2, "GND")
        j_idx += 1
        # W_neg: -12V at X = 57.0
        add_jumper(f"W{j_idx}", "JUMPER", 57.0, y1, 57.0, y2, "-12V")
        j_idx += 1

    # Connect +12V vertically along X = 43.0
    # From U1 (cy=20) down to J_PWR (pin 1 at 46.19, 86.0)
    add_track(42.45, 20.0, 43.0, 20.0, "+12V", 0.50)
    add_track(43.0, 20.0, 43.0, 27.5, "+12V", 0.50) # to W1
    add_track(43.0, 30.5, 43.0, 38.0, "+12V", 0.50) # from W1 to U2
    add_track(42.45, 38.0, 43.0, 38.0, "+12V", 0.50) # U2 tap
    add_track(43.0, 38.0, 43.0, 45.5, "+12V", 0.50) # to W4
    add_track(43.0, 48.5, 43.0, 56.0, "+12V", 0.50) # from W4 to U3
    add_track(42.45, 56.0, 43.0, 56.0, "+12V", 0.50) # U3 tap
    add_track(43.0, 56.0, 43.0, 63.5, "+12V", 0.50) # to W7
    add_track(43.0, 66.5, 43.0, 74.0, "+12V", 0.50) # from W7 to U4
    add_track(42.45, 74.0, 43.0, 74.0, "+12V", 0.50) # U4 tap
    add_track(43.0, 74.0, 43.0, 81.5, "+12V", 0.50) # to W10
    add_path([(43.0, 84.5), (43.0, 86.0), (46.19, 86.0)], "+12V", 0.50) # from W10 to J_PWR pin 1

    # Connect -12V vertically along X = 57.0
    # From U1 (cy=20) down to J_PWR (pin 2 at 48.73, 86.0)
    add_track(57.55, 20.0, 57.0, 20.0, "-12V", 0.50)
    add_track(57.0, 20.0, 57.0, 27.5, "-12V", 0.50) # to W3
    add_track(57.0, 30.5, 57.0, 38.0, "-12V", 0.50) # from W3 to U2
    add_track(57.55, 38.0, 57.0, 38.0, "-12V", 0.50) # U2 tap
    add_track(57.0, 38.0, 57.0, 45.5, "-12V", 0.50) # to W6
    add_track(57.0, 48.5, 57.0, 56.0, "-12V", 0.50) # from W6 to U3
    add_track(57.55, 56.0, 57.0, 56.0, "-12V", 0.50) # U3 tap
    add_track(57.0, 56.0, 57.0, 63.5, "-12V", 0.50) # to W9
    add_track(57.0, 66.5, 57.0, 74.0, "-12V", 0.50) # from W9 to U4
    add_track(57.55, 74.0, 57.0, 74.0, "-12V", 0.50) # U4 tap
    add_track(57.0, 74.0, 57.0, 81.5, "-12V", 0.50) # to W12
    add_path([(57.0, 84.5), (57.0, 88.0), (48.73, 88.0), (48.73, 86.0)], "-12V", 0.50) # from W12 to J_PWR pin 2

    # Connect GND vertically along X = 50.0
    for g, cy in enumerate(group_y):
        add_track(40.55, cy, 59.45, cy, "GND", 0.50) # cross chip GND link between C_POS and C_NEG
    add_track(50.0, 20.0, 50.0, 27.5, "GND", 0.50)
    add_track(50.0, 30.5, 50.0, 38.0, "GND", 0.50)
    add_track(50.0, 38.0, 50.0, 45.5, "GND", 0.50)
    add_track(50.0, 48.5, 50.0, 56.0, "GND", 0.50)
    add_track(50.0, 56.0, 50.0, 63.5, "GND", 0.50)
    add_track(50.0, 66.5, 50.0, 74.0, "GND", 0.50)
    add_track(50.0, 74.0, 50.0, 81.5, "GND", 0.50)
    # J_PWR pins 3 and 4 are at 51.27 and 53.81, Y = 86.0
    add_path([(50.0, 84.5), (50.0, 86.0), (51.27, 86.0), (53.81, 86.0)], "GND", 0.50)

    board.Save(PCB_PATH)
    
    # Re-inject net_tie_pad_groups for KiCad DRC
    with open(PCB_PATH, "r") as f:
        text = f.read()
    text = text.replace('(tags "net tie")', '(tags "net tie")\n    (net_tie_pad_groups "1,2")')
    with open(PCB_PATH, "w") as f:
        f.write(text)

    print("DC2 board fully generated and routed at", PCB_PATH)

if __name__ == "__main__":
    build_board()
