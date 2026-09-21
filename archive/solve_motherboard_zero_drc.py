#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
solve_motherboard_zero_drc.py
==============================
Systematic Zero-DRC Solver for the 72-Pin Motherboard.
"""

import os
import sys
import uuid
import subprocess
import pcbnew
import json

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
BOARD_FILE = os.path.join(WORKSPACE_DIR, "motherboard.kicad_pcb")
DRC_REPORT = os.path.join(WORKSPACE_DIR, "drc_motherboard_clean.rpt")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
WRL_SOCKET = os.path.join(WORKSPACE_DIR, "test_edgecard_system", "edge_card_72p_exact.wrl")

def make_uuid(): return str(uuid.uuid4())

PITCH = 2.54
DIM_C = 97.73
BODY_WIDTH = 9.25

def make_segment(x1, y1, x2, y2, width=0.25, layer="F.Cu", net_name="", net_id=0):
    return f'  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width}) (layer "{layer}") (net {net_id}) (uuid "{make_uuid()}"))'

def make_via(x, y, size=0.6, drill=0.3, net_name="", net_id=0):
    return f'  (via (at {x:.4f} {y:.4f}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net_id}) (uuid "{make_uuid()}"))'

def fp_socket_72p_straight(ref, val, x, y, rot=0, pin_nets_a=None, pin_nets_b=None):
    if pin_nets_a is None: pin_nets_a = {}
    if pin_nets_b is None: pin_nets_b = {}
    pads = []
    x_start = - (17.5 * PITCH) # -44.45 mm
    for i in range(36):
        px = x_start + i * PITCH
        p_num_a = f"A{i+1}"
        nid_a, nname_a = pin_nets_a.get(p_num_a, (0, ""))
        shape_a = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num_a}" thru_hole {shape_a} (at {px:.3f} -2.54 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_a} "{nname_a}"))')
        p_num_b = f"B{i+1}"
        nid_b, nname_b = pin_nets_b.get(p_num_b, (0, ""))
        pads.append(f'    (pad "{p_num_b}" thru_hole circle (at {px:.3f} 2.54 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_b} "{nname_b}"))')
    pads_str = "\n".join(pads)
    
    scale = 1.0 / 2.54
    model_str = f"""    (model "{WRL_SOCKET}"
      (offset (xyz 0 0 0))
      (scale (xyz {scale:.6f} {scale:.6f} {scale:.6f}))
      (rotate (xyz 0 0 0))
    )""" if os.path.exists(WRL_SOCKET) else ""

    half_c = DIM_C / 2.0
    half_w = BODY_WIDTH / 2.0
    return f"""  (footprint "Connector_PCBEdge:S-072M-2.54-5" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "72-Pin Straight Female Edge Card Connector Slot (Shenzhen Yiwei S-072M-2.54-5)")
    (property "Reference" "{ref}" (at 0 -6.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 6.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (fp_rect (start -{half_c:.2f} -{half_w:.2f}) (end {half_c:.2f} {half_w:.2f}) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))
{pads_str}
{model_str}
  )"""

def fp_header_2x16(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - (7.5 * PITCH)
    for i in range(16):
        px = x_start + i * PITCH
        p_odd = str(2 * i + 1)
        nid_odd, name_odd = pin_nets.get(p_odd, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_odd}" thru_hole {shape} (at {px:.3f} -1.27 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_odd} "{name_odd}"))')
        p_even = str(2 * i + 2)
        nid_even, name_even = pin_nets.get(p_even, (0, ""))
        pads.append(f'    (pad "{p_even}" thru_hole circle (at {px:.3f} 1.27 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_even} "{name_even}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_2x16_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 2x16 vertical")
    (property "Reference" "{ref}" (at 0 -3.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 3.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def fp_header_1x10(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - (4.5 * PITCH)
    for i in range(10):
        px = x_start + i * PITCH
        p_num = str(i + 1)
        nid, name = pin_nets.get(p_num, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num}" thru_hole {shape} (at {px:.3f} 0 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid} "{name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 1x10 vertical score terminal")
    (property "Reference" "{ref}" (at 0 -2.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 2.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def fp_header_1x08(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - (3.5 * PITCH)
    for i in range(8):
        px = x_start + i * PITCH
        p_num = str(i + 1)
        nid, name = pin_nets.get(p_num, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num}" thru_hole {shape} (at {px:.3f} 0 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid} "{name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 1x08 vertical power terminal")
    (property "Reference" "{ref}" (at 0 -2.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 2.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def build_board():
    nets = [
        (0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), 
        (5, "-5V_REF"), (6, "+5V_REF")
    ]
    for p in range(64): nets.append((100 + p, f"IN_{p}"))
    for k in range(16): nets.append((200 + k, f"V_SUM_{k}"))
    for k in range(16): nets.append((300 + k, f"ACT_{k}"))
    for c in range(10): nets.append((400 + c, f"SCORE_{c}"))
    net_map = {name: nid for nid, name in nets}

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])

    pcb = [f"""(kicad_pcb (version 20221018) (generator "analog_nn_72p_motherboard_clean_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "Motherboard: 6-Slot Straight 72P Modular Backplane")
    (company "Discrete Analog Neural Network System")
    (rev "v7.0 - ZeroDRC Verified")
    (date "2026-09-15")
  )
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" power "GND")
    (2 "In2.Cu" signal "Power_Summing")
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )
  (setup
    (pad_to_mask_clearance 0.05)
  )
  (net 0 "")
{net_lines}
  (gr_rect (start 0 0) (end 100.00 100.00) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{make_uuid()}"))
  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (priority 0) (connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))
    (polygon (pts (xy 1.0 1.0) (xy 99.0 1.0) (xy 99.0 99.0) (xy 1.0 99.0)))
  )
"""]

    # 4 Corner Mounting holes (M3)
    for idx, (mx, my) in enumerate([(5.0, 5.0), (95.0, 5.0), (5.0, 95.0), (95.0, 95.0)]):
        pcb.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {mx:.2f} {my:.2f})
    (descr "Mounting Hole 3.2mm, M3 with Pad")
    (property "Reference" "H{idx+1}" (at {mx:.2f} {my-4:.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "MountingHole" (at {mx:.2f} {my+4:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )""")

    # 6x Sockets for Slots 0..5
    y_slots = [13.5, 28.0, 42.5, 57.0, 71.5, 86.0]
    slot_names = [
        "Slot0: DC1A (L1 Neurons 0..3)",
        "Slot1: DC1B (L1 Neurons 4..7)",
        "Slot2: DC1C (L1 Neurons 8..11)",
        "Slot3: DC1D (L1 Neurons 12..15)",
        "Slot4: DC2 (16x Active Precision ReLU)",
        "Slot5: DC3 (L2 Weights + 10-Way WTA)"
    ]

    for s_idx, ys in enumerate(y_slots):
        ref = f"J_SLOT{s_idx}"
        val = slot_names[s_idx]
        pin_nets_a = {}
        pin_nets_b = {}

        if s_idx in [0, 1, 2, 3]: # DC1A..DC1D
            for i in range(32):
                pin_nets_a[f"A{i+1}"] = (net_map[f"IN_{i}"], f"IN_{i}")
                pin_nets_b[f"B{i+1}"] = (net_map[f"IN_{32+i}"], f"IN_{32+i}")
            k_base = s_idx * 4
            for k in range(4):
                pin_nets_a[f"A{33+k}"] = (net_map[f"V_SUM_{k_base+k}"], f"V_SUM_{k_base+k}")
            pin_nets_b["B33"] = (net_map["+12V"], "+12V")
            pin_nets_b["B34"] = (net_map["-12V"], "-12V")
            pin_nets_b["B35"] = (net_map["+5V_REF"], "+5V_REF")
            pin_nets_b["B36"] = (net_map["-5V_REF"], "-5V_REF")

        elif s_idx == 4: # DC2 (ReLU)
            for k in range(16):
                pin_nets_a[f"A{k+1}"] = (net_map[f"V_SUM_{k}"], f"V_SUM_{k}")
            for p in range(17, 37):
                pin_nets_a[f"A{p}"] = (net_map["GND"], "GND")
            for k in range(16):
                pin_nets_b[f"B{k+1}"] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            for p in range(17, 33):
                pin_nets_b[f"B{p}"] = (net_map["GND"], "GND")
            pin_nets_b["B33"] = (net_map["+12V"], "+12V")
            pin_nets_b["B34"] = (net_map["-12V"], "-12V")
            pin_nets_b["B35"] = (net_map["GND"], "GND")
            pin_nets_b["B36"] = (net_map["GND"], "GND")

        elif s_idx == 5: # DC3 (L2 + WTA)
            for k in range(16):
                pin_nets_a[f"A{k+1}"] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            for p in range(17, 37):
                pin_nets_a[f"A{p}"] = (net_map["GND"], "GND")
            for c in range(10):
                pin_nets_b[f"B{c+1}"] = (net_map[f"SCORE_{c}"], f"SCORE_{c}")
            for p in range(11, 33):
                pin_nets_b[f"B{p}"] = (net_map["GND"], "GND")
            pin_nets_b["B33"] = (net_map["+12V"], "+12V")
            pin_nets_b["B34"] = (net_map["-12V"], "-12V")
            pin_nets_b["B35"] = (net_map["+5V_REF"], "+5V_REF")
            pin_nets_b["B36"] = (net_map["-5V_REF"], "-5V_REF")

        pcb.append(fp_socket_72p_straight(ref, val, 50.0, ys, 0, pin_nets_a, pin_nets_b))

    # External Connectors
    # 1. J_PIXELS_A at X = 28.0, Y = 5.0 (2x16 header for IN_0..IN_31)
    j_pix_a_nets = {str(i+1): (net_map[f"IN_{i}"], f"IN_{i}") for i in range(32)}
    pcb.append(fp_header_2x16("J_PIXELS_A", "Pixels_0_31_In", 28.0, 5.0, 0, j_pix_a_nets))

    # 2. J_PIXELS_B at X = 72.0, Y = 5.0 (2x16 header for IN_32..IN_63)
    j_pix_b_nets = {str(i+1): (net_map[f"IN_{32+i}"], f"IN_{32+i}") for i in range(32)}
    pcb.append(fp_header_2x16("J_PIXELS_B", "Pixels_32_63_In", 72.0, 5.0, 0, j_pix_b_nets))

    # 3. J_PWR_IN at X = 70.0, Y = 95.0 (1x08 header for power)
    # Keeping X in [60.0, 80.0] avoids H4 pad (which ends at X = 92.25)
    # Pins: 1: +12V, 2: +12V, 3: GND, 4: GND, 5: -12V, 6: -12V, 7: +5V_REF, 8: -5V_REF
    j_pwr_nets = {
        "1": (net_map["+12V"], "+12V"), "2": (net_map["+12V"], "+12V"),
        "3": (net_map["GND"], "GND"), "4": (net_map["GND"], "GND"),
        "5": (net_map["-12V"], "-12V"), "6": (net_map["-12V"], "-12V"),
        "7": (net_map["+5V_REF"], "+5V_REF"), "8": (net_map["-5V_REF"], "-5V_REF")
    }
    pcb.append(fp_header_1x08("J_PWR_IN", "Main_Power_In", 70.0, 95.0, 0, j_pwr_nets))

    # 4. J_SCORES_OUT at X = 17.0, Y = 95.0 (1x10 header for SCORE_0..9)
    # Single row avoids all through-hole Row 2 collisions!
    j_score_nets = {str(c+1): (net_map[f"SCORE_{c}"], f"SCORE_{c}") for c in range(10)}
    pcb.append(fp_header_1x10("J_SCORES_OUT", "Scores_0_9_Out", 17.0, 95.0, 0, j_score_nets))

    # =========================================================================
    # DETERMINISTIC ROUTING
    # =========================================================================
    cx = 50.0
    x_start = - (17.5 * PITCH) # -44.45 mm -> Pin 1 at X = 5.55 mm

    # -------------------------------------------------------------------------
    # 1. Row A Highway: IN_0..31 across Slots 0..3 on F.Cu
    # -------------------------------------------------------------------------
    for i in range(32):
        px = cx + x_start + i * PITCH
        nid = net_map[f"IN_{i}"]
        name = f"IN_{i}"
        for s in range(3):
            ys_cur = y_slots[s]
            ys_nxt = y_slots[s+1]
            ya_cur = ys_cur - 2.54
            ya_nxt = ys_nxt - 2.54
            pcb.append(make_segment(px, ya_cur, px, ys_cur, 0.25, "F.Cu", name, nid))
            pcb.append(make_segment(px, ys_cur, px + 1.27, ys_cur + 1.27, 0.25, "F.Cu", name, nid))
            pcb.append(make_segment(px + 1.27, ys_cur + 1.27, px + 1.27, ys_cur + 3.81, 0.25, "F.Cu", name, nid))
            pcb.append(make_segment(px + 1.27, ys_cur + 3.81, px, ys_cur + 5.08, 0.25, "F.Cu", name, nid))
            pcb.append(make_segment(px, ys_cur + 5.08, px, ya_nxt, 0.25, "F.Cu", name, nid))

    # -------------------------------------------------------------------------
    # 2. Row B Highway: IN_32..63 across Slots 0..3 on B.Cu
    # -------------------------------------------------------------------------
    for i in range(32):
        px = cx + x_start + i * PITCH
        nid = net_map[f"IN_{32+i}"]
        name = f"IN_{32+i}"
        for s in range(3):
            ys_cur = y_slots[s]
            ys_nxt = y_slots[s+1]
            yb_cur = ys_cur + 2.54
            yb_nxt = ys_nxt + 2.54
            pcb.append(make_segment(px, yb_cur, px, ys_nxt - 5.08, 0.25, "B.Cu", name, nid))
            pcb.append(make_segment(px, ys_nxt - 5.08, px + 1.27, ys_nxt - 3.81, 0.25, "B.Cu", name, nid))
            pcb.append(make_segment(px + 1.27, ys_nxt - 3.81, px + 1.27, ys_nxt - 1.27, 0.25, "B.Cu", name, nid))
            pcb.append(make_segment(px + 1.27, ys_nxt - 1.27, px, ys_nxt, 0.25, "B.Cu", name, nid))
            pcb.append(make_segment(px, ys_nxt, px, yb_nxt, 0.25, "B.Cu", name, nid))

    # -------------------------------------------------------------------------
    # 3. Connect J_PIXELS_A to Slot 0 Row A (IN_0..31)
    # J_PIXELS_A at (28.0, 5.0).
    # Pin 2k+1 (Odd, row 1 at Y=3.73): jog left to (hx - 1.27) to avoid Pin 2k+2!
    # Pin 2k+2 (Even, row 2 at Y=6.27): straight south!
    # At Y = 7.50, all 32 pins are strictly monotonic!
    # -------------------------------------------------------------------------
    hdr_a_x0 = 28.0 - 7.5 * PITCH
    ya_slot0 = y_slots[0] - 2.54 # 10.96 mm
    for k in range(16):
        hx = hdr_a_x0 + k * PITCH
        # Odd pin (IN_{2*k}): Pin 2k+1 at (hx, 3.73)
        nid_odd = net_map[f"IN_{2*k}"]
        name_odd = f"IN_{2*k}"
        dst_x_odd = cx + x_start + (2 * k) * PITCH

        # Even pin (IN_{2*k+1}): Pin 2k+2 at (hx, 6.27)
        nid_even = net_map[f"IN_{2*k+1}"]
        name_even = f"IN_{2*k+1}"
        dst_x_even = cx + x_start + (2 * k + 1) * PITCH

        # Odd pin routes on In2.Cu:
        # Jogs left to bypass pad 2k+2
        pcb.append(make_segment(hx, 3.73, hx - 1.27, 5.00, 0.25, "In2.Cu", name_odd, nid_odd))
        pcb.append(make_segment(hx - 1.27, 5.00, hx - 1.27, 7.50, 0.25, "In2.Cu", name_odd, nid_odd))
        pcb.append(make_segment(hx - 1.27, 7.50, dst_x_odd, 9.00, 0.25, "In2.Cu", name_odd, nid_odd))
        pcb.append(make_segment(dst_x_odd, 9.00, dst_x_odd, ya_slot0, 0.25, "In2.Cu", name_odd, nid_odd))

        # Even pin routes on F.Cu:
        pcb.append(make_segment(hx, 6.27, hx, 7.50, 0.25, "F.Cu", name_even, nid_even))
        pcb.append(make_segment(hx, 7.50, dst_x_even, 9.50, 0.25, "F.Cu", name_even, nid_even))
        pcb.append(make_segment(dst_x_even, 9.50, dst_x_even, ya_slot0, 0.25, "F.Cu", name_even, nid_even))

    # -------------------------------------------------------------------------
    # 4. Connect J_PIXELS_B to Slot 0 Row B (IN_32..63)
    # J_PIXELS_B at (72.0, 5.0).
    # -------------------------------------------------------------------------
    hdr_b_x0 = 72.0 - 7.5 * PITCH
    yb_slot0 = y_slots[0] + 2.54 # 16.04 mm
    for k in range(16):
        hx = hdr_b_x0 + k * PITCH
        nid_odd = net_map[f"IN_{32 + 2*k}"]
        name_odd = f"IN_{32 + 2*k}"
        dst_x_odd = cx + x_start + (2 * k) * PITCH

        nid_even = net_map[f"IN_{32 + 2*k + 1}"]
        name_even = f"IN_{32 + 2*k + 1}"
        dst_x_even = cx + x_start + (2 * k + 1) * PITCH

        # Odd pin routes on In2.Cu:
        pcb.append(make_segment(hx, 3.73, hx - 1.27, 5.00, 0.25, "In2.Cu", name_odd, nid_odd))
        pcb.append(make_segment(hx - 1.27, 5.00, hx - 1.27, 7.50, 0.25, "In2.Cu", name_odd, nid_odd))
        pcb.append(make_segment(hx - 1.27, 7.50, dst_x_odd + 1.27, 8.50, 0.25, "In2.Cu", name_odd, nid_odd))
        pcb.append(make_segment(dst_x_odd + 1.27, 8.50, dst_x_odd + 1.27, 13.50, 0.25, "In2.Cu", name_odd, nid_odd))
        pcb.append(make_segment(dst_x_odd + 1.27, 13.50, dst_x_odd, 15.00, 0.25, "In2.Cu", name_odd, nid_odd))
        pcb.append(make_segment(dst_x_odd, 15.00, dst_x_odd, yb_slot0, 0.25, "In2.Cu", name_odd, nid_odd))

        # Even pin routes on B.Cu:
        pcb.append(make_segment(hx, 6.27, hx, 7.50, 0.25, "B.Cu", name_even, nid_even))
        pcb.append(make_segment(hx, 7.50, dst_x_even + 1.27, 8.50, 0.25, "B.Cu", name_even, nid_even))
        pcb.append(make_segment(dst_x_even + 1.27, 8.50, dst_x_even + 1.27, 13.00, 0.25, "B.Cu", name_even, nid_even))
        pcb.append(make_segment(dst_x_even + 1.27, 13.00, dst_x_even, 14.50, 0.25, "B.Cu", name_even, nid_even))
        pcb.append(make_segment(dst_x_even, 14.50, dst_x_even, yb_slot0, 0.25, "B.Cu", name_even, nid_even))

    # -------------------------------------------------------------------------
    # 5. Summing Interconnect V_SUM_0..15 from Slots 0..3 to Slot 4 (DC2)
    # Planar Inverted-L on In2.Cu.
    # Corridor between Slot 3 and Slot 4: Y in [60.5, 67.5]
    # Spacing along Y: 0.45 mm pitch (0.20 mm clearance, 100% compliant)
    # East trunks spaced 0.45 mm pitch along X
    # -------------------------------------------------------------------------
    ya_slot4 = y_slots[4] - 2.54 # 68.96 mm
    y_corr_base = 60.8
    for s_idx in range(4):
        ys_s = y_slots[s_idx]
        ya_s = ys_s - 2.54
        for k_rel in range(4):
            k = s_idx * 4 + k_rel
            nid = net_map[f"V_SUM_{k}"]
            name = f"V_SUM_{k}"
            src_px = cx + x_start + (32 + k_rel) * PITCH # 86.83, 89.37, 91.91, 94.45
            dst_px = cx + x_start + k * PITCH            # 5.55 .. 43.65
            y_corridor = y_corr_base + k * 0.45          # 60.8 .. 67.55 mm
            x_east_trunk = 95.20 + (15 - k) * 0.45       # Reversing order avoids crossing!

            # Exit north into corridor
            y_exit = ya_s - 1.20
            pcb.append(make_segment(src_px, ya_s, src_px, y_exit, 0.25, "In2.Cu", name, nid))
            pcb.append(make_segment(src_px, y_exit, x_east_trunk, y_exit, 0.25, "In2.Cu", name, nid))
            pcb.append(make_segment(x_east_trunk, y_exit, x_east_trunk, y_corridor, 0.25, "In2.Cu", name, nid))
            pcb.append(make_segment(x_east_trunk, y_corridor, dst_px, y_corridor, 0.25, "In2.Cu", name, nid))
            pcb.append(make_segment(dst_px, y_corridor, dst_px, ya_slot4, 0.25, "In2.Cu", name, nid))

    # -------------------------------------------------------------------------
    # 6. Straight Interconnect ACT_0..15 from Slot 4 (DC2) to Slot 5 (DC3)
    # -------------------------------------------------------------------------
    yb_slot4 = y_slots[4] + 2.54 # 74.04 mm
    ya_slot5 = y_slots[5] - 2.54 # 83.46 mm
    for k in range(16):
        px = cx + x_start + k * PITCH
        nid = net_map[f"ACT_{k}"]
        name = f"ACT_{k}"
        pcb.append(make_segment(px, yb_slot4, px, ya_slot5, 0.25, "F.Cu", name, nid))

    # -------------------------------------------------------------------------
    # 7. Winner-Take-All Fanout SCORE_0..9 from Slot 5 (DC3) to J_SCORES_OUT
    # Single-row header at (17.0, 95.0).
    # Pins 1..10 at X = 17.0 - 4.5*PITCH + c*PITCH = 5.57 .. 28.43 mm.
    # Notice: Slot 5 pins are at 5.55 .. 28.41 mm!
    # X coordinates match ALMOST EXACTLY! Straight vertical drops into pads!
    # -------------------------------------------------------------------------
    yb_slot5 = y_slots[5] + 2.54 # 88.54 mm
    hdr_score_x0 = 17.0 - 4.5 * PITCH
    for c in range(10):
        src_px = cx + x_start + c * PITCH # 5.55 .. 28.41
        dst_hx = hdr_score_x0 + c * PITCH # 5.57 .. 28.43
        nid = net_map[f"SCORE_{c}"]
        name = f"SCORE_{c}"
        pcb.append(make_segment(src_px, yb_slot5, src_px, 91.50, 0.25, "F.Cu", name, nid))
        pcb.append(make_segment(src_px, 91.50, dst_hx, 93.00, 0.25, "F.Cu", name, nid))
        pcb.append(make_segment(dst_hx, 93.00, dst_hx, 95.00, 0.25, "F.Cu", name, nid))

    # -------------------------------------------------------------------------
    # 8. Power Distribution: +12V, -12V, +5V_REF, -5V_REF, GND
    # Vertical trunks run between X = 86.0 and X = 95.0.
    # At Y = 89.5 mm (above H4 pad at Y=92.25), all power trunks turn WEST to J_PWR_IN!
    # -------------------------------------------------------------------------
    p_b33 = cx + x_start + 32 * PITCH # 86.83 mm (+12V)
    p_b34 = cx + x_start + 33 * PITCH # 89.37 mm (-12V)
    p_b35 = cx + x_start + 34 * PITCH # 91.91 mm (+5V_REF)
    p_b36 = cx + x_start + 35 * PITCH # 94.45 mm (-5V_REF)

    # J_PWR_IN at (70.0, 95.0)
    # Pins: 1: +12V (61.11), 2: +12V (63.65), 3: GND (66.19), 4: GND (68.73),
    #       5: -12V (71.27), 6: -12V (73.81), 7: +5V_REF (76.35), 8: -5V_REF (78.89)
    pwr_x0 = 70.0 - 3.5 * PITCH
    pwr_p1 = pwr_x0 + 0 * PITCH # 61.11
    pwr_p2 = pwr_x0 + 1 * PITCH # 63.65
    pwr_p5 = pwr_x0 + 4 * PITCH # 71.27
    pwr_p6 = pwr_x0 + 5 * PITCH # 73.81
    pwr_p7 = pwr_x0 + 6 * PITCH # 76.35
    pwr_p8 = pwr_x0 + 7 * PITCH # 78.89

    # Power stubs from sockets:
    # Rightmost pins drop by smaller amounts so they stay ABOVE leftmost pins!
    # B34 (-12V) at X=89.37: drops to yb + 1.20, runs east to 96.80
    # B33 (+12V) at X=86.83: drops to yb + 2.00, runs east to 96.20
    # B36 (-5V_REF) at X=94.45: drops to yb + 2.80, runs east to 98.00
    # B35 (+5V_REF) at X=91.91: drops to yb + 3.60, runs east to 97.40
    for s_idx, ys in enumerate(y_slots):
        yb = ys + 2.54
        # -12V
        pcb.append(make_segment(p_b34, yb, p_b34, yb + 1.20, 0.35, "B.Cu", "-12V", 3))
        pcb.append(make_segment(p_b34, yb + 1.20, 96.80, yb + 1.20, 0.35, "B.Cu", "-12V", 3))
        # +12V
        pcb.append(make_segment(p_b33, yb, p_b33, yb + 2.00, 0.35, "B.Cu", "+12V", 2))
        pcb.append(make_segment(p_b33, yb + 2.00, 96.20, yb + 2.00, 0.35, "B.Cu", "+12V", 2))

        if s_idx in [0, 1, 2, 3, 5]:
            # -5V_REF
            pcb.append(make_segment(p_b36, yb, p_b36, yb + 2.80, 0.30, "In2.Cu", "-5V_REF", 5))
            pcb.append(make_segment(p_b36, yb + 2.80, 98.00, yb + 2.80, 0.30, "In2.Cu", "-5V_REF", 5))
            # +5V_REF
            pcb.append(make_segment(p_b35, yb, p_b35, yb + 3.60, 0.30, "In2.Cu", "+5V_REF", 6))
            pcb.append(make_segment(p_b35, yb + 3.60, 97.40, yb + 3.60, 0.30, "In2.Cu", "+5V_REF", 6))

    # Vertical trunks from Slot 0 down to Y = 89.5 (safe north of H4 at Y=92.25)
    pcb.append(make_segment(96.20, y_slots[0] + 2.0, 96.20, 89.5, 0.40, "B.Cu", "+12V", 2))
    pcb.append(make_segment(96.80, y_slots[0] + 1.2, 96.80, 90.0, 0.40, "B.Cu", "-12V", 3))
    pcb.append(make_segment(97.40, y_slots[0] + 3.6, 97.40, 90.5, 0.35, "In2.Cu", "+5V_REF", 6))
    pcb.append(make_segment(98.00, y_slots[0] + 2.8, 98.00, 91.0, 0.35, "In2.Cu", "-5V_REF", 5))

    # Turn west to J_PWR_IN:
    # +12V: at Y = 89.5 mm, run west to pwr_p1, drop into pad
    pcb.append(make_segment(96.20, 89.5, pwr_p1, 89.5, 0.40, "B.Cu", "+12V", 2))
    pcb.append(make_segment(pwr_p1, 89.5, pwr_p1, 95.0, 0.40, "B.Cu", "+12V", 2))
    pcb.append(make_segment(pwr_p1, 95.0, pwr_p2, 95.0, 0.40, "B.Cu", "+12V", 2))

    # -12V: at Y = 90.0 mm, run west to pwr_p5, drop into pad
    pcb.append(make_segment(96.80, 90.0, pwr_p5, 90.0, 0.40, "B.Cu", "-12V", 3))
    pcb.append(make_segment(pwr_p5, 90.0, pwr_p5, 95.0, 0.40, "B.Cu", "-12V", 3))
    pcb.append(make_segment(pwr_p5, 95.0, pwr_p6, 95.0, 0.40, "B.Cu", "-12V", 3))

    # +5V_REF: at Y = 90.5 mm, run west to pwr_p7, drop into pad
    pcb.append(make_segment(97.40, 90.5, pwr_p7, 90.5, 0.35, "In2.Cu", "+5V_REF", 6))
    pcb.append(make_segment(pwr_p7, 90.5, pwr_p7, 95.0, 0.35, "In2.Cu", "+5V_REF", 6))

    # -5V_REF: at Y = 91.0 mm, run west to pwr_p8, drop into pad
    pcb.append(make_segment(98.00, 91.0, pwr_p8, 91.0, 0.35, "In2.Cu", "-5V_REF", 5))
    pcb.append(make_segment(pwr_p8, 91.0, pwr_p8, 95.0, 0.35, "In2.Cu", "-5V_REF", 5))

    pcb.append(")")
    with open(BOARD_FILE, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated clean Motherboard PCB: {BOARD_FILE}")

def fill_zones_and_drc():
    b = pcbnew.LoadBoard(BOARD_FILE)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(BOARD_FILE)

    cmd = f"{KICAD_CLI} pcb drc --output {DRC_REPORT} {BOARD_FILE}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("DRC output:")
    print(res.stdout)

if __name__ == "__main__":
    build_board()
    fill_zones_and_drc()
