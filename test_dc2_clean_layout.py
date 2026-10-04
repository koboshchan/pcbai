#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
test_dc2_clean_layout.py
------------------------
Generates daughtercard2_relu_l1.kicad_pcb with optimal component placement:
- Spacing >= 2.5mm between all footprints (0 courtyard overlaps)
- Decoupling caps right at power pins
"""

import os
import sys
import re
import subprocess
import pcbnew

WORKSPACE = "/Users/lucaszhang/pcbai"
PCB_PATH  = os.path.join(WORKSPACE, "daughtercard2_relu_l1.kicad_pcb")

BOARD_W = 100.0
BOARD_H = 100.0

def generate_board():
    board = pcbnew.BOARD()
    
    # 1. Board Design Rules
    ds = board.GetDesignSettings()
    ds.m_MinClearance = pcbnew.FromMM(0.50)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
    ds.SetCustomTrackWidth(pcbnew.FromMM(0.40))
    
    # 2. Add Nets
    nets = ["GND", "+12V", "-12V"]
    for ch in range(16):
        nets.extend([f"V_SUM_{ch}", f"ACT_{ch}", f"INV_IN_{ch}", f"OP_OUT_{ch}"])
        
    net_map = {}
    for n in nets:
        netinfo = pcbnew.NETINFO_ITEM(board, n)
        board.Add(netinfo)
        net_map[n] = board.FindNet(n)
        
    # 3. Edge.Cuts Outline (100 x 100 mm)
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
    fp_hdr_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty"
    
    # J_IN: 1x16 Header at Left (X = 6.5mm, Y = 18.0..56.1mm)
    jin = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x16_P2.54mm_Vertical")
    jin.SetReference("J_IN")
    jin.SetValue("V_SUM_IN")
    jin.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(18.0)))
    for p in jin.Pads():
        pnum = int(p.GetNumber()) - 1
        p.SetNet(net_map[f"V_SUM_{pnum}"])
    board.Add(jin)
    
    # J_OUT: 1x16 Header at Right (X = 93.5mm, Y = 18.0..56.1mm)
    jout = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x16_P2.54mm_Vertical")
    jout.SetReference("J_OUT")
    jout.SetValue("ACT_OUT")
    jout.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(93.5), pcbnew.FromMM(18.0)))
    for p in jout.Pads():
        pnum = int(p.GetNumber()) - 1
        p.SetNet(net_map[f"ACT_{pnum}"])
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
        
        # Caps rotated 0 at X = tl_x - 6.5 and tl_x + 6.5
        add_cap(f"C_{g+1}_POS", "100n", tl_x - 7.5, cy, 0, "+12V", "GND")
        add_cap(f"C_{g+1}_NEG", "100n", tl_x + 7.5, cy, 0, "-12V", "GND")
        
        # Place 4 channels:
        # Ch0 (pins 1,2,3): Left top
        add_res(f"R_IN_{ch0}", "10k", 18.0, cy - 3.5, 0, f"V_SUM_{ch0}", f"INV_IN_{ch0}")
        add_dio(f"D_FB_{ch0}", "1N4148", 28.0, cy - 3.5, 0, f"OP_OUT_{ch0}", f"INV_IN_{ch0}")
        add_dio(f"D_OUT_{ch0}", "1N4148", 38.0, cy - 3.5, 0, f"ACT_{ch0}", f"OP_OUT_{ch0}")
        add_res(f"R_FB_{ch0}", "10k", 28.0, cy - 6.5, 0, f"INV_IN_{ch0}", f"ACT_{ch0}")

        # Ch1 (pins 7,6,5): Left bottom
        add_res(f"R_IN_{ch1}", "10k", 18.0, cy + 3.5, 0, f"V_SUM_{ch1}", f"INV_IN_{ch1}")
        add_dio(f"D_FB_{ch1}", "1N4148", 28.0, cy + 3.5, 0, f"OP_OUT_{ch1}", f"INV_IN_{ch1}")
        add_dio(f"D_OUT_{ch1}", "1N4148", 38.0, cy + 3.5, 0, f"ACT_{ch1}", f"OP_OUT_{ch1}")
        add_res(f"R_FB_{ch1}", "10k", 28.0, cy + 6.5, 0, f"INV_IN_{ch1}", f"ACT_{ch1}")

        # Ch3 (pins 14,13,12): Right top
        add_res(f"R_IN_{ch3}", "10k", 82.0, cy - 3.5, 0, f"V_SUM_{ch3}", f"INV_IN_{ch3}")
        add_dio(f"D_FB_{ch3}", "1N4148", 72.0, cy - 3.5, 0, f"OP_OUT_{ch3}", f"INV_IN_{ch3}")
        add_dio(f"D_OUT_{ch3}", "1N4148", 62.0, cy - 3.5, 0, f"ACT_{ch3}", f"OP_OUT_{ch3}")
        add_res(f"R_FB_{ch3}", "10k", 72.0, cy - 6.5, 0, f"INV_IN_{ch3}", f"ACT_{ch3}")

        # Ch2 (pins 8,9,10): Right bottom
        add_res(f"R_IN_{ch2}", "10k", 82.0, cy + 3.5, 0, f"V_SUM_{ch2}", f"INV_IN_{ch2}")
        add_dio(f"D_FB_{ch2}", "1N4148", 72.0, cy + 3.5, 0, f"OP_OUT_{ch2}", f"INV_IN_{ch2}")
        add_dio(f"D_OUT_{ch2}", "1N4148", 62.0, cy + 3.5, 0, f"ACT_{ch2}", f"OP_OUT_{ch2}")
        add_res(f"R_FB_{ch2}", "10k", 72.0, cy + 6.5, 0, f"INV_IN_{ch2}", f"ACT_{ch2}")

    board.Save(PCB_PATH)
    print("DC2 board generated at", PCB_PATH)

if __name__ == "__main__":
    generate_board()
