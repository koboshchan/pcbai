#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
test_dc2_perfect_flow.py
------------------------
Implements the clean autoroute + jumper conversion pipeline on daughtercard2_relu_l1.kicad_pcb.
"""

import os
import sys
import re
import subprocess
import pcbnew
from collections import defaultdict

WORKSPACE = "/Users/lucaszhang/pcbai"
PCB_PATH  = os.path.join(WORKSPACE, "daughtercard2_relu_l1.kicad_pcb")
DSN_PATH  = os.path.join(WORKSPACE, "daughtercard2_relu_l1.dsn")
SES_PATH  = os.path.join(WORKSPACE, "daughtercard2_relu_l1.ses")
DRC_JSON  = os.path.join(WORKSPACE, "daughtercard2_relu_l1_drc.json")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

BOARD_W = 100.0
BOARD_H = 100.0

def build_board():
    board = pcbnew.BOARD()
    
    # Design rules
    ds = board.GetDesignSettings()
    ds.m_MinClearance = pcbnew.FromMM(0.50)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
    ds.SetCustomTrackWidth(pcbnew.FromMM(0.40))
    
    # Nets
    nets = ["GND", "+12V", "-12V"]
    for ch in range(16):
        nets.extend([f"V_SUM_{ch}", f"ACT_{ch}", f"INV_IN_{ch}", f"OP_OUT_{ch}"])
        
    net_map = {}
    for n in nets:
        netinfo = pcbnew.NETINFO_ITEM(board, n)
        board.Add(netinfo)
        net_map[n] = board.FindNet(n)
        
    # Outline on Edge.Cuts
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
        seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
        seg.SetWidth(pcbnew.FromMM(0.15))
        seg.SetLayer(pcbnew.Edge_Cuts)
        board.Add(seg)
        
    # Mounting holes
    fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
    for idx, (hx, hy) in enumerate([(4.0, 4.0), (BOARD_W - 4.0, 4.0), (4.0, BOARD_H - 4.0), (BOARD_W - 4.0, BOARD_H - 4.0)]):
        mh = pcbnew.FootprintLoad(fp_mh_path, "MountingHole_3.2mm_M3")
        mh.SetReference(f"MH{idx+1}")
        mh.Reference().SetVisible(False)
        mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
        board.Add(mh)
        
    # Connector LayerSet: F.Cu only! (No B.Cu)
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
        
        # Decoupling Caps at X = 42.5 and 57.5
        add_cap(f"C_{g+1}_POS", "100n", tl_x - 7.5, cy, 0, "+12V", "GND")
        add_cap(f"C_{g+1}_NEG", "100n", tl_x + 7.5, cy, 0, "-12V", "GND")
        
        # Place 4 channels:
        # Ch0: Left top
        add_res(f"R_IN_{ch0}", "10k", 18.0, cy - 3.5, 0, f"V_SUM_{ch0}", f"INV_IN_{ch0}")
        add_dio(f"D_FB_{ch0}", "1N4148", 28.0, cy - 3.5, 0, f"OP_OUT_{ch0}", f"INV_IN_{ch0}")
        add_dio(f"D_OUT_{ch0}", "1N4148", 38.0, cy - 3.5, 0, f"ACT_{ch0}", f"OP_OUT_{ch0}")
        add_res(f"R_FB_{ch0}", "10k", 28.0, cy - 6.5, 0, f"INV_IN_{ch0}", f"ACT_{ch0}")

        # Ch1: Left bottom
        add_res(f"R_IN_{ch1}", "10k", 18.0, cy + 3.5, 0, f"V_SUM_{ch1}", f"INV_IN_{ch1}")
        add_dio(f"D_FB_{ch1}", "1N4148", 28.0, cy + 3.5, 0, f"OP_OUT_{ch1}", f"INV_IN_{ch1}")
        add_dio(f"D_OUT_{ch1}", "1N4148", 38.0, cy + 3.5, 0, f"ACT_{ch1}", f"OP_OUT_{ch1}")
        add_res(f"R_FB_{ch1}", "10k", 28.0, cy + 6.5, 0, f"INV_IN_{ch1}", f"ACT_{ch1}")

        # Ch3: Right top
        add_res(f"R_IN_{ch3}", "10k", 82.0, cy - 3.5, 0, f"V_SUM_{ch3}", f"INV_IN_{ch3}")
        add_dio(f"D_FB_{ch3}", "1N4148", 72.0, cy - 3.5, 0, f"OP_OUT_{ch3}", f"INV_IN_{ch3}")
        add_dio(f"D_OUT_{ch3}", "1N4148", 62.0, cy - 3.5, 0, f"ACT_{ch3}", f"OP_OUT_{ch3}")
        add_res(f"R_FB_{ch3}", "10k", 72.0, cy - 6.5, 0, f"INV_IN_{ch3}", f"ACT_{ch3}")

        # Ch2: Right bottom
        add_res(f"R_IN_{ch2}", "10k", 82.0, cy + 3.5, 0, f"V_SUM_{ch2}", f"INV_IN_{ch2}")
        add_dio(f"D_FB_{ch2}", "1N4148", 72.0, cy + 3.5, 0, f"OP_OUT_{ch2}", f"INV_IN_{ch2}")
        add_dio(f"D_OUT_{ch2}", "1N4148", 62.0, cy + 3.5, 0, f"ACT_{ch2}", f"OP_OUT_{ch2}")
        add_res(f"R_FB_{ch2}", "10k", 72.0, cy + 6.5, 0, f"INV_IN_{ch2}", f"ACT_{ch2}")

    board.Save(PCB_PATH)
    print("DC2 board built successfully.")

def run_autoroute():
    board = pcbnew.LoadBoard(PCB_PATH)
    pcbnew.ExportSpecctraDSN(board, DSN_PATH)
    
    with open(DSN_PATH) as f:
        dsn = f.read()

    # In DSN:
    # 1. Set clearance to 550 um (0.55 mm)
    dsn = re.sub(r"\(clearance\s+\d+\)", "(clearance 550)", dsn)
    dsn = re.sub(r"\(clearance\s+\d+\s+\(type smd_smd\)\)", "(clearance 550 (type smd_smd))", dsn)
    dsn = re.sub(r"\(width\s+\d+\)", "(width 350)", dsn)

    # 2. Set via diameter to 1800 um (1.8 mm pad for jumper wire)
    dsn = re.sub(r"\(shape\s+\(circle\s+F\.Cu\s+600\)\)", "(shape (circle F.Cu 1800))", dsn)
    dsn = re.sub(r"\(shape\s+\(circle\s+B\.Cu\s+600\)\)", "(shape (circle B.Cu 1800))", dsn)

    with open(DSN_PATH, "w") as f:
        f.write(dsn)

    cmd = [
        "/opt/homebrew/opt/openjdk@25/bin/java", "-jar", "freerouting.jar",
        "-de", DSN_PATH,
        "-do", SES_PATH,
        "--gui.enabled=false",
        "-mp", "60",
        "-mt", "1"
    ]
    res = subprocess.run(cmd, check=True)
    print("FreeRouting completed successfully.")

def convert_to_jumpers():
    board = pcbnew.LoadBoard(PCB_PATH)
    pcbnew.ImportSpecctraSES(board, SES_PATH)
    
    # Enforce min track width 0.35 mm
    for t in board.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA):
            if pcbnew.ToMM(t.GetWidth()) < 0.35:
                t.SetWidth(pcbnew.FromMM(0.35))
                
    vias = [t for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    bcu_tracks = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu]
    
    via_positions = {(v.GetPosition().x, v.GetPosition().y): v for v in vias}
    
    adj = defaultdict(set)
    edge_net = {}
    for t in bcu_tracks:
        p1 = (t.GetStart().x, t.GetStart().y)
        p2 = (t.GetEnd().x, t.GetEnd().y)
        adj[p1].add(p2)
        adj[p2].add(p1)
        edge_net[(min(p1, p2), max(p1, p2))] = t.GetNet()
        
    visited = set()
    components = []
    for p in adj:
        if p not in visited:
            comp = []
            q = [p]
            visited.add(p)
            while q:
                curr = q.pop()
                comp.append(curr)
                for nbr in adj[curr]:
                    if nbr not in visited:
                        visited.add(nbr)
                        q.append(nbr)
            components.append(comp)

    print(f"B.Cu connected components: {len(components)}")
    
    lset = pcbnew.LSET.AllCuMask()
    lset.AddLayer(pcbnew.F_Mask)
    lset.AddLayer(pcbnew.B_Mask)
    
    jumper_count = 0
    for idx, comp in enumerate(components):
        comp_vias = [p for p in comp if p in via_positions]
        if len(comp_vias) < 2:
            comp_vias = [p for p in comp if len(adj[p]) == 1]
            
        net = edge_net.get((min(comp[0], list(adj[comp[0]])[0]), max(comp[0], list(adj[comp[0]])[0])))
        if not net:
            for nbr in adj[comp[0]]:
                net = edge_net.get((min(comp[0], nbr), max(comp[0], nbr)))
                if net: break
                
        # Connect vias with jumpers
        comp_vias.sort()
        for i in range(len(comp_vias) - 1):
            p1 = comp_vias[i]
            p2 = comp_vias[i+1]
            
            jumper_count += 1
            ref = f"W{jumper_count}"
            
            fp = pcbnew.FOOTPRINT(board)
            fp.SetReference(ref)
            fp.SetValue("JUMPER")
            fp.SetKeywords("net tie")
            fp.SetFPID(pcbnew.LIB_ID("", "Jumper_Wire"))
            
            cx = (p1[0] + p2[0]) // 2
            cy = (p1[1] + p2[1]) // 2
            fp.SetPosition(pcbnew.VECTOR2I(cx, cy))
            
            # Pad 1
            pad1 = pcbnew.PAD(fp)
            pad1.SetNumber("1")
            pad1.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad1.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad1.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
            pad1.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.9), pcbnew.FromMM(0.9)))
            pad1.SetPosition(pcbnew.VECTOR2I(p1[0], p1[1]))
            pad1.SetLayerSet(lset)
            pad1.SetNet(net)
            fp.Add(pad1)
            
            # Pad 2
            pad2 = pcbnew.PAD(fp)
            pad2.SetNumber("2")
            pad2.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad2.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad2.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
            pad2.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.9), pcbnew.FromMM(0.9)))
            pad2.SetPosition(pcbnew.VECTOR2I(p2[0], p2[1]))
            pad2.SetLayerSet(lset)
            pad2.SetNet(net)
            fp.Add(pad2)
            
            # Silkscreen line
            line = pcbnew.PCB_SHAPE(fp)
            line.SetShape(pcbnew.SHAPE_T_SEGMENT)
            line.SetStart(pcbnew.VECTOR2I(p1[0], p1[1]))
            line.SetEnd(pcbnew.VECTOR2I(p2[0], p2[1]))
            line.SetWidth(pcbnew.FromMM(0.2))
            line.SetLayer(pcbnew.F_SilkS)
            fp.Add(line)
            
            board.Add(fp)

    print(f"Converted to {jumper_count} wire jumpers.")
    
    # Remove all B.Cu tracks and vias
    for t in bcu_tracks:
        board.Remove(t)
    for v in vias:
        board.Remove(v)
        
    board.Save(PCB_PATH)
    
    # Re-inject net_tie_pad_groups for KiCad DRC
    with open(PCB_PATH, "r") as f:
        text = f.read()
    text = text.replace('(tags "net tie")', '(tags "net tie")\n    (net_tie_pad_groups "1,2")')
    with open(PCB_PATH, "w") as f:
        f.write(text)
        
    print(f"Board saved to {PCB_PATH} with 0 B.Cu, 0 vias, {jumper_count} jumpers.")

def run_drc():
    cmd = [
        KICAD_CLI, "pcb", "drc",
        "--output", DRC_JSON,
        "--format", "json",
        "--severity-all",
        PCB_PATH
    ]
    subprocess.run(cmd, check=True)
    with open(DRC_JSON) as f:
        drc = json.load(f)
    violations = drc.get("violations", [])
    unconnected = drc.get("unconnected_items", [])
    print(f"DRC Violations: {len(violations)}, Unconnected: {len(unconnected)}")
    return len(violations), len(unconnected)

if __name__ == "__main__":
    build_board()
    run_autoroute()
    convert_to_jumpers()
    run_drc()
