#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
build_shifter_board.py
----------------------
Generates 'shifter_board' (50x70mm, single-layer F.Cu) for 4-channel ±15V to 0-5V level shifting.
- 4x 33k 0805 (R1_TOP, R2_TOP, R3_TOP, R4_TOP)
- 8x 10k 0805 (R1_PU..R4_PU, R1_PD..R4_PD)
- J_IN 1x5 header (IN1-4, GND)
- J_OUT 1x6 header (OUT1-4, +5V, GND)
- 3x Jumper_Wire through-hole jumpers (W1, W2, W3) for +5V distribution
- 4x M3 mounting holes (3.2mm drill)
- Detailed silkscreen labels for every pin, component, value, and board function.
"""

import os
import sys
import re
import subprocess
import pcbnew

WORKSPACE = "/Users/lucaszhang/pcbai"
BOARD_PATH = os.path.join(WORKSPACE, "shifter_board.kicad_pcb")
PRO_PATH   = os.path.join(WORKSPACE, "shifter_board.kicad_pro")
DSN_PATH   = os.path.join(WORKSPACE, "shifter_board.dsn")
SES_PATH   = os.path.join(WORKSPACE, "shifter_board.ses")
JAR_PATH   = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
if not os.path.exists(JAR_PATH):
    JAR_PATH = os.path.join(WORKSPACE, "freerouting.jar")

BOARD_W = 50.0  # mm
BOARD_H = 70.0  # mm

def create_board():
    board = pcbnew.BOARD()
    
    # 1. Design Rules & Board Settings
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = pcbnew.FromMM(0.3)
    ds.m_MinClearance  = pcbnew.FromMM(0.5)
    ds.SetCustomTrackWidth(pcbnew.FromMM(0.5))
    
    # 2. Add Nets
    net_names = [
        "GND", "+5V",
        "IN1", "IN2", "IN3", "IN4",
        "MID1", "MID2", "MID3", "MID4",
        "+5V_CH1", "+5V_CH2", "+5V_CH3",
        "GND_CH1", "GND_CH2", "GND_CH3"
    ]
    net_objs = {}
    for name in net_names:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
        net_objs[name] = board.FindNet(name)
        
    # 3. Board Outline on Edge.Cuts (50 x 70 mm)
    corners = [
        (0.0, 0.0),
        (BOARD_W, 0.0),
        (BOARD_W, BOARD_H),
        (0.0, BOARD_H),
        (0.0, 0.0)
    ]
    for i in range(len(corners) - 1):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
        seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
        seg.SetWidth(pcbnew.FromMM(0.15))
        seg.SetLayer(pcbnew.Edge_Cuts)
        board.Add(seg)

    # 4. Mounting Holes (M3, 3.2mm drill)
    fp_mh_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
    m_holes = [
        (4.0, 4.0),
        (BOARD_W - 4.0, 4.0),
        (4.0, BOARD_H - 4.0),
        (BOARD_W - 4.0, BOARD_H - 4.0)
    ]
    for idx, (hx, hy) in enumerate(m_holes):
        mh = pcbnew.FootprintLoad(fp_mh_path, "MountingHole_3.2mm_M3")
        mh.SetReference(f"MH{idx+1}")
        mh.Reference().SetVisible(False)
        mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
        board.Add(mh)

    # Footprint libraries
    fp_res_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty"
    fp_hdr_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty"

    # Helper: add resistor footprint
    def add_resistor(ref, val, pos_x, pos_y, rot_deg, net1_name, net2_name):
        fp = pcbnew.FootprintLoad(fp_res_path, "R_0805_2012Metric")
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pos_x), pcbnew.FromMM(pos_y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot_deg, pcbnew.DEGREES_T))
        
        # Configure pads
        for pad in fp.Pads():
            if pad.GetNumber() == "1":
                pad.SetNet(net_objs[net1_name])
            elif pad.GetNumber() == "2":
                pad.SetNet(net_objs[net2_name])
        # Hide default ref and val to prevent overlap with pads/traces
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        board.Add(fp)
        return fp

    # Helper: add wire jumper footprint (PTH pads, net tie)
    def add_jumper(ref, val, pos_x, pos_y, length_mm, rot_deg, net1_name, net2_name):
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetFPID(pcbnew.LIB_ID('', 'Jumper_Wire'))
        fp.SetKeywords("net tie")
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pos_x), pcbnew.FromMM(pos_y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot_deg, pcbnew.DEGREES_T))
        
        lset = pcbnew.LSET.AllCuMask()
        lset.AddLayer(pcbnew.F_Mask)
        lset.AddLayer(pcbnew.B_Mask)

        # Pad 1 (top pad if rot=90)
        p1 = pcbnew.PAD(fp)
        p1.SetNumber("1")
        p1.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p1.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p1.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.0), pcbnew.FromMM(2.0)))
        p1.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
        p1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pos_x), pcbnew.FromMM(pos_y - length_mm / 2.0)))
        p1.SetLayerSet(lset)
        p1.SetNet(net_objs[net1_name])
        fp.Add(p1)

        # Pad 2 (bottom pad if rot=90)
        p2 = pcbnew.PAD(fp)
        p2.SetNumber("2")
        p2.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p2.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p2.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.0), pcbnew.FromMM(2.0)))
        p2.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
        p2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pos_x), pcbnew.FromMM(pos_y + length_mm / 2.0)))
        p2.SetLayerSet(lset)
        p2.SetNet(net_objs[net2_name])
        fp.Add(p2)

        # Silkscreen jumper outline (between pads, avoiding pad holes)
        line = pcbnew.PCB_SHAPE(fp)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(pos_x), pcbnew.FromMM(pos_y - length_mm / 2.0 + 1.4)))
        line.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(pos_x), pcbnew.FromMM(pos_y + length_mm / 2.0 - 1.4)))
        line.SetWidth(pcbnew.FromMM(0.20))
        line.SetLayer(pcbnew.F_SilkS)
        fp.Add(line)

        # Reference position
        ref_text = fp.Reference()
        ref_text.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pos_x + 2.2), pcbnew.FromMM(pos_y)))
        ref_text.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        ref_text.SetTextThickness(pcbnew.FromMM(0.15))
        ref_text.SetLayer(pcbnew.F_SilkS)

        board.Add(fp)
        return fp

    # 5. Place Connectors J_IN and J_OUT
    # J_IN: 1x5 header at X = 6.5 mm
    jin_y_start = 16.0
    jin = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x05_P2.54mm_Vertical")
    jin.SetReference("J_IN")
    jin.SetValue("1x05_IN_GND")
    jin.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(jin_y_start)))
    jin_nets = ["IN1", "IN2", "IN3", "IN4", "GND"]
    for pad in jin.Pads():
        p_num = int(pad.GetNumber())
        pad.SetNet(net_objs[jin_nets[p_num - 1]])
    jin.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(jin_y_start - 3.5)))
    board.Add(jin)

    # J_OUT: 1x6 header at X = 43.5 mm
    jout_y_start = 16.0
    jout = pcbnew.FootprintLoad(fp_hdr_path, "PinHeader_1x06_P2.54mm_Vertical")
    jout.SetReference("J_OUT")
    jout.SetValue("1x06_OUT_5V_GND")
    jout.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(43.5), pcbnew.FromMM(jout_y_start)))
    jout_nets = ["MID1", "MID2", "MID3", "MID4", "+5V", "GND"]
    for pad in jout.Pads():
        p_num = int(pad.GetNumber())
        pad.SetNet(net_objs[jout_nets[p_num - 1]])
    jout.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(43.5), pcbnew.FromMM(jout_y_start - 3.5)))
    board.Add(jout)

    # 6. Place Channels 1..4 (Resistors)
    ch_y = [16.0, 28.0, 40.0, 52.0]
    pu_nets = ["+5V_CH1", "+5V_CH2", "+5V_CH3", "+5V"]
    pd_nets = ["GND", "GND_CH1", "GND_CH2", "GND_CH3"]

    for i in range(4):
        ch_idx = i + 1
        cy = ch_y[i]
        in_net = f"IN{ch_idx}"
        mid_net = f"MID{ch_idx}"
        pu_net = pu_nets[i]
        pd_net = pd_nets[i]

        # R_TOP (33k): X = 20.0 mm, Y = cy, rot=0 (Pad 1 IN at left, Pad 2 MID at right)
        r_top = add_resistor(f"R{ch_idx}_TOP", "33k", 20.0, cy, 0, in_net, mid_net)

        # R_PD (10k): X = 20.0 mm, Y = cy - 2.5 mm, rot=0 (Pad 1 GND at left, Pad 2 MID at right)
        r_pd = add_resistor(f"R{ch_idx}_PD", "10k", 20.0, cy - 2.5, 0, pd_net, mid_net)

        # R_PU (10k): X = 25.0 mm, Y = cy + 2.5 mm, rot=0 (Pad 1 MID at left, Pad 2 +5V at right)
        r_pu = add_resistor(f"R{ch_idx}_PU", "10k", 25.0, cy + 2.5, 0, mid_net, pu_net)

    # 7. Place Jumpers: W4..W6 (GND on West at X=13.5) and W1..W3 (+5V on East at X=33.5)
    add_jumper("W4", "Jumper_Wire", 13.5, 28.0, 7.62, 90, "GND_CH1", "GND_CH2")
    add_jumper("W5", "Jumper_Wire", 13.5, 40.0, 7.62, 90, "GND_CH2", "GND_CH3")
    add_jumper("W6", "Jumper_Wire", 13.5, 52.0, 7.62, 90, "GND_CH3", "GND")

    add_jumper("W1", "Jumper_Wire", 33.5, 28.0, 7.62, 90, "+5V_CH1", "+5V_CH2")
    add_jumper("W2", "Jumper_Wire", 33.5, 40.0, 7.62, 90, "+5V_CH2", "+5V_CH3")
    add_jumper("W3", "Jumper_Wire", 33.5, 52.0, 7.62, 90, "+5V_CH3", "+5V")

    # Inter-jumper backbone links (fixed F.Cu tracks connecting jumper pairs vertically)
    backbone_links = [
        # (net, x, y_start, y_end)
        ("GND_CH2", 13.5, 31.81, 36.19),  # W4 Pad 2 to W5 Pad 1
        ("GND_CH3", 13.5, 43.81, 48.19),  # W5 Pad 2 to W6 Pad 1
        ("+5V_CH2", 33.5, 31.81, 36.19),  # W1 Pad 2 to W2 Pad 1
        ("+5V_CH3", 33.5, 43.81, 48.19),  # W2 Pad 2 to W3 Pad 1
    ]
    for n_name, bx, by1, by2 in backbone_links:
        t_bb = pcbnew.PCB_TRACK(board)
        t_bb.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by1)))
        t_bb.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by2)))
        t_bb.SetWidth(pcbnew.FromMM(0.5))
        t_bb.SetLayer(pcbnew.F_Cu)
        t_bb.SetNet(net_objs[n_name])
        board.Add(t_bb)

    # 8. Fixed GND Perimeter Routing (Single-layer F.Cu path connecting J_IN-5, W6-2, J_OUT-6, and R1_PD)
    pts_gnd = [
        (19.09, 13.5),  # R1_PD Pad 1
        (19.09, 11.5),  # North of CH1
        (3.6, 11.5),    # West top perimeter
        (3.6, 26.16),   # West to J_IN pin 5 level
        (6.5, 26.16),   # J_IN pin 5
        (3.6, 26.16),   # Back to west edge
        (3.6, 61.5),    # Down west edge
        (46.4, 61.5),   # Along south perimeter
        (46.4, 28.7),   # Up east edge
        (43.5, 28.7),   # J_OUT pin 6
    ]
    for i in range(len(pts_gnd) - 1):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(pts_gnd[i][0]), pcbnew.FromMM(pts_gnd[i][1])))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(pts_gnd[i+1][0]), pcbnew.FromMM(pts_gnd[i+1][1])))
        t.SetWidth(pcbnew.FromMM(0.5))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(net_objs["GND"])
        board.Add(t)

    # Tap from bottom perimeter up to W6 Pad 2 (13.5, 55.81)
    t_tap = pcbnew.PCB_TRACK(board)
    t_tap.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(13.5), pcbnew.FromMM(61.5)))
    t_tap.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(13.5), pcbnew.FromMM(55.81)))
    t_tap.SetWidth(pcbnew.FromMM(0.5))
    t_tap.SetLayer(pcbnew.F_Cu)
    t_tap.SetNet(net_objs["GND"])
    board.Add(t_tap)

    # Straight horizontal route for IN1
    t_in1 = pcbnew.PCB_TRACK(board)
    t_in1.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(16.0)))
    t_in1.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(19.09), pcbnew.FromMM(16.0)))
    t_in1.SetWidth(pcbnew.FromMM(0.4))
    t_in1.SetLayer(pcbnew.F_Cu)
    t_in1.SetNet(net_objs["IN1"])
    board.Add(t_in1)

    # Clean guided routes for IN2, IN3, IN4 passing through W4, W5, W6
    input_bus = [
        ("IN2", [(6.5, 18.54), (10.9, 22.94), (10.9, 28.0), (19.09, 28.0)]),
        ("IN3", [(6.5, 21.08), (9.7, 24.28), (9.7, 40.0), (19.09, 40.0)]),
        ("IN4", [(6.5, 23.62), (8.5, 25.62), (8.5, 52.0), (19.09, 52.0)]),
    ]
    for net_name, pts_in in input_bus:
        for i in range(len(pts_in) - 1):
            t_in = pcbnew.PCB_TRACK(board)
            t_in.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(pts_in[i][0]), pcbnew.FromMM(pts_in[i][1])))
            t_in.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(pts_in[i+1][0]), pcbnew.FromMM(pts_in[i+1][1])))
            t_in.SetWidth(pcbnew.FromMM(0.4))
            t_in.SetLayer(pcbnew.F_Cu)
            t_in.SetNet(net_objs[net_name])
            board.Add(t_in)

    # Route connecting W4 Pad 1 to R2_PD Pad 1 (GND_CH1) north of IN2
    t_ch1 = pcbnew.PCB_TRACK(board)
    t_ch1.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(13.5), pcbnew.FromMM(24.19)))
    t_ch1.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(17.5), pcbnew.FromMM(24.19)))
    t_ch1.SetWidth(pcbnew.FromMM(0.5))
    t_ch1.SetLayer(pcbnew.F_Cu)
    t_ch1.SetNet(net_objs["GND_CH1"])
    board.Add(t_ch1)

    t_ch1_diag = pcbnew.PCB_TRACK(board)
    t_ch1_diag.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(17.5), pcbnew.FromMM(24.19)))
    t_ch1_diag.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(19.09), pcbnew.FromMM(25.5)))
    t_ch1_diag.SetWidth(pcbnew.FromMM(0.5))
    t_ch1_diag.SetLayer(pcbnew.F_Cu)
    t_ch1_diag.SetNet(net_objs["GND_CH1"])
    board.Add(t_ch1_diag)

    # 8. Silkscreen Labels
    def add_label(text, px, py, size_mm=1.0, bold=True, layer=pcbnew.F_SilkS, angle=0):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size_mm), pcbnew.FromMM(size_mm)))
        t.SetTextThickness(pcbnew.FromMM(0.20 if bold else 0.15))
        t.SetLayer(layer)
        if angle != 0:
            t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        board.Add(t)

    # Board Title Block
    add_label("4-CH LEVEL SHIFTER", 25.0, 6.0, size_mm=1.5, bold=True)
    add_label("+/-15V TO 0-5V (UNO ADC)", 25.0, 8.5, size_mm=1.0, bold=True)
    add_label("SINGLE LAYER F.Cu ONLY", 25.0, 64.0, size_mm=1.0, bold=True)

    # Pin labels for J_IN (placed at X = 2.8 mm to avoid connector outline)
    jin_pins = [
        ("IN1", 1),
        ("IN2", 2),
        ("IN3", 3),
        ("IN4", 4),
        ("GND", 5)
    ]
    for name, p in jin_pins:
        py = jin_y_start + (p - 1) * 2.54
        add_label(name, 2.8, py, size_mm=0.8, bold=True)

    # Pin labels for J_OUT (placed at X = 47.0 mm to avoid connector outline)
    jout_pins = [
        ("OUT1", 1),
        ("OUT2", 2),
        ("OUT3", 3),
        ("OUT4", 4),
        ("+5V",  5),
        ("GND",  6)
    ]
    for name, p in jout_pins:
        py = jout_y_start + (p - 1) * 2.54
        add_label(name, 47.0, py, size_mm=0.8, bold=True)

    # Channel Divider lines on Silkscreen (ended before W jumpers)
    for cy in [22.0, 34.0, 46.0]:
        div = pcbnew.PCB_SHAPE(board)
        div.SetShape(pcbnew.SHAPE_T_SEGMENT)
        div.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(16.0), pcbnew.FromMM(cy)))
        div.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(30.0), pcbnew.FromMM(cy)))
        div.SetWidth(pcbnew.FromMM(0.15))
        div.SetLayer(pcbnew.F_SilkS)
        board.Add(div)

    # Channel ID labels (placed at X = 22.5, Y = cy - 4.5 mm, safely above channel resistors)
    for i in range(4):
        ch_idx = i + 1
        cy = ch_y[i]
        add_label(f"CH{ch_idx}", 22.5, cy - 4.5, size_mm=0.8, bold=True)

    board.Save(BOARD_PATH)
    print(f"Saved initial unrouted board to {BOARD_PATH}")

    # Create shifter_board.kicad_pro
    pro_content = '''{
  "board": {
    "design_settings": {
      "rules": {
        "max_error": 0.005,
        "min_clearance": 0.5,
        "min_hole_clearance": 0.5,
        "min_hole_to_hole": 0.5,
        "min_microvia_diameter": 0.2,
        "min_microvia_drill": 0.1,
        "min_silk_clearance": 0.0,
        "min_through_hole_diameter": 0.3,
        "min_track_width": 0.3,
        "min_via_annular_width": 0.05,
        "min_via_diameter": 0.5
      }
    }
  },
  "boards": [],
  "meta": {
    "filename": "shifter_board.kicad_pro",
    "version": 1
  },
  "net_settings": {
    "classes": [
      {
        "clearance": 0.5,
        "name": "Default",
        "track_width": 0.5,
        "via_diameter": 0.8,
        "via_drill": 0.4
      }
    ]
  }
}
'''
    with open(PRO_PATH, "w") as f:
        f.write(pro_content)
    print(f"Saved project file to {PRO_PATH}")

    # Inject net_tie_pad_groups into the file for DRC
    with open(BOARD_PATH, "r") as f:
        content = f.read()
    content = content.replace('(tags "net tie")', '(tags "net tie")\n    (net_tie_pad_groups "1,2")')
    with open(BOARD_PATH, "w") as f:
        f.write(content)
        
    return board

if __name__ == "__main__":
    create_board()
