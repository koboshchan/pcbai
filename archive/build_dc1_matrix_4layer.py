#!/usr/bin/env python3
"""
build_dc1_matrix_4layer.py
--------------------------
Generates 4-layer, 32-column x 8-row Crossbar Matrix Layout for Layer 1 Daughtercards
(DC1A, DC1B, DC1C, DC1D).
"""

import os
import json
import uuid

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"

def make_uuid():
    return str(uuid.uuid4())

def make_segment(x1, y1, x2, y2, width=0.25, layer="F.Cu", net_name="", net_id=0):
    return f'  (segment (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (width {width:.2f}) (layer "{layer}") (net {net_id}) (uuid "{make_uuid()}"))'

def make_via(x, y, size=0.6, drill=0.3, net_name="", net_id=0):
    return f'  (via (at {x:.3f} {y:.3f}) (size {size:.2f}) (drill {drill:.2f}) (layers "F.Cu" "B.Cu") (net {net_id}) (uuid "{make_uuid()}"))'

def fp_resistor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Resistor SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
  )"""

def fp_capacitor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=2, net1_name="+12V", net2=1, net2_name="GND"):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "Capacitor_SMD:C_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Capacitor SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
  )"""

def fp_soic14(ref, val, x, y, rot=0, layer="F.Cu", pin_nets=None):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    pads = []
    pitch = 1.27
    y_start = - (3 * pitch)
    for i in range(7):
        py = y_start + i * pitch
        pin_num = str(i + 1)
        nid, nname = pin_nets.get(pin_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_num}" smd roundrect (at -2.7 {py:.3f} {rot}) (size 1.95 0.6) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    for i in range(7):
        py = y_start + (6 - i) * pitch
        pin_num = str(i + 8)
        nid, nname = pin_nets.get(pin_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_num}" smd roundrect (at 2.7 {py:.3f} {rot}) (size 1.95 0.6) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    pads_str = "
".join(pads)
    return f"""  (footprint "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "SOIC, 14 Pin, 3.9x8.7mm body, 1.27mm pitch")
    (property "Reference" "{ref}" (at 0 -5.5 {rot}) (layer "{silk}") (effects (font (size 0.8 0.8) (thickness 0.1))))
    (property "Value" "{val}" (at 0 5.5 {rot}) (layer "{fab}") (effects (font (size 0.8 0.8) (thickness 0.1))))
{pads_str}
  )"""

def fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=94.28):
    cx = card_width / 2.0
    pitch = 2.54
    pad_w = 1.60
    pad_h = 8.00
    x_start = - (17.5 * pitch)
    pads = []
    for i in range(36):
        px = x_start + i * pitch
        p_num_a = f"A{i+1}"
        nid_a, nname_a = pin_nets_a.get(p_num_a, (0, ""))
        pads.append(f'    (pad "{p_num_a}" smd roundrect (at {px:.3f} 0) (size {pad_w:.2f} {pad_h:.2f}) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2) (net {nid_a} "{nname_a}"))')
        p_num_b = f"B{i+1}"
        nid_b, nname_b = pin_nets_b.get(p_num_b, (0, ""))
        pads.append(f'    (pad "{p_num_b}" smd roundrect (at {px:.3f} 0) (size {pad_w:.2f} {pad_h:.2f}) (layers "B.Cu" "B.Mask") (roundrect_rratio 0.2) (net {nid_b} "{nname_b}"))')
    pads_str = "
".join(pads)
    return f"""  (footprint "Connector_PCBEdge:GoldFingers_72P_2.54mm" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {cx:.3f} 96.00)
    (descr "72-Pin PCB Edge Gold Fingers (36 Front + 36 Back) at 2.54mm pitch")
    (property "Reference" "J_EDGE_FINGERS" (at 0 -6.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "72P_GoldFingers_ENIG" (at 0 6.0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def build_dc1_board(neuron_range=(0, 1, 2, 3), filename="daughtercard1a_weights_l1.kicad_pcb", title="DC1A: Neurons 0-3"):
    with open(os.path.join(WORKSPACE_DIR, "synaptic_weights.json"), "r") as f:
        weights_data = json.load(f)
    l1 = weights_data["layer1"]

    card_w = 94.28
    card_h = 100.0
    pitch = 2.54
    cx = card_w / 2.0
    x_start = cx - (17.5 * pitch) # 2.69 mm

    nets = [
        (0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), (5, "-5V_REF"), (6, "+5V_REF")
    ]
    for j in neuron_range:
        nets.append((10 + j, f"V_SUM_{j}"))
        nets.append((30 + j, f"INV_N{j}"))
    for i in range(64):
        nets.append((100 + i, f"IN_{i}"))

    net_lines = "
".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])

    pcb = [f"""(kicad_pcb (version 20221018) (generator pcbnew)
  (general (thickness 1.6))
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (4 "In1.Cu" power "GND")
    (6 "In2.Cu" signal)
    (2 "B.Cu" signal)
    (31 "B.Mask" user)
    (32 "F.Mask" user)
    (33 "B.Paste" user)
    (34 "F.Paste" user)
    (35 "B.SilkS" user)
    (36 "F.SilkS" user)
    (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user)
    (47 "F.CrtYd" user)
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )
  (setup
    (pad_to_mask_clearance 0.05)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (disableapertmacros false)
      (usegerberextensions true)
      (usegerberattributes true)
      (usegerberadvancedattributes true)
      (creategerberjobfile true)
      (svgprecision 4)
      (plotsilentmode false)
      (outputdirectory "")
    )
  )
  (net 0 "")
{net_lines}
"""]

    pcb.append(f'  (gr_rect (start 0 0) (end {card_w:.2f} {card_h:.2f}) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{make_uuid()}"))')
    pcb.append(f'  (gr_line (start 1.0 91.0) (end {card_w-1.0:.2f} 91.0) (stroke (width 0.25) (type default)) (layer "F.SilkS") (uuid "{make_uuid()}"))')
    pcb.append(f'  (gr_text "<< INSERTION STOP LINE (9.0mm Socket Depth) >>" (at {card_w/2:.2f} 89.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 1.1 1.1) (thickness 0.15))))')
    pcb.append(f'  (gr_text "{title} [32x8 Spaced Matrix]" (at {card_w/2:.2f} 47.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 1.4 1.4) (thickness 0.2))))')

    # Ground plane zone on In1.Cu
    pcb.append(f"""  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (priority 0)
    (connect_pads (clearance 0.25))
    (min_thickness 0.25)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))
    (polygon
      (pts (xy 1.0 1.0) (xy {card_w-1.0:.2f} 1.0) (xy {card_w-1.0:.2f} 90.0) (xy 1.0 90.0))
    )
  )""")

    # Mounting holes
    for idx, (mx, my) in enumerate([(5.0, 5.0), (card_w - 5.0, 5.0)]):
        pcb.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {mx:.2f} {my:.2f})
    (descr "Mounting Hole 3.2mm, M3 with Pad")
    (property "Reference" "H{idx+1}" (at {mx:.2f} {my-4:.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "MountingHole" (at {mx:.2f} {my+4:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )""")

    # Fingers
    pin_nets_a = {}
    pin_nets_b = {}
    for i in range(32):
        pin_nets_a[f"A{i+1}"] = (100 + i, f"IN_{i}")
        pin_nets_b[f"B{i+1}"] = (132 + i, f"IN_{32+i}")
    for idx, j in enumerate(neuron_range):
        pin_nets_a[f"A{33+idx}"] = (10 + j, f"V_SUM_{j}")
    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (1, "GND")
    pin_nets_b["B36"] = (1, "GND")

    pcb.append(fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_w))

    row_y = {
        0: 16.0,
        1: 24.0,
        2: 32.0,
        3: 40.0,
        4: 54.0,
        5: 62.0,
        6: 70.0,
        7: 78.0
    }

    # 256 Resistors
    for local_neuron_idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        r_top_row = local_neuron_idx
        r_bot_row = local_neuron_idx + 4

        y_top = row_y[r_top_row]
        y_bot = row_y[r_bot_row]

        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        for i in range(32):
            rx = x_start + i * pitch
            inp = n_info["inputs"][i]
            r_val = inp["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_top, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

        for i in range(32, 64):
            col_idx = i - 32
            rx = x_start + col_idx * pitch
            inp = n_info["inputs"][i]
            r_val = inp["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_bot, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

    # TL074 Quad Op-Amp at X = 87.5, Y = 47.0
    u1_x = 87.5
    u1_y = 47.0
    u1_pin_nets = {
        "1": (10 + neuron_range[0], f"V_SUM_{neuron_range[0]}"),
        "2": (30 + neuron_range[0], f"INV_N{neuron_range[0]}"),
        "3": (1, "GND"),
        "4": (2, "+12V"),
        "5": (1, "GND"),
        "6": (30 + neuron_range[1], f"INV_N{neuron_range[1]}"),
        "7": (10 + neuron_range[1], f"V_SUM_{neuron_range[1]}"),
        "8": (10 + neuron_range[2], f"V_SUM_{neuron_range[2]}"),
        "9": (30 + neuron_range[2], f"INV_N{neuron_range[2]}"),
        "10": (1, "GND"),
        "11": (3, "-12V"),
        "12": (1, "GND"),
        "13": (30 + neuron_range[3], f"INV_N{neuron_range[3]}"),
        "14": (10 + neuron_range[3], f"V_SUM_{neuron_range[3]}")
    }
    pcb.append(fp_soic14("U1", "TL074", u1_x, u1_y, 0, "F.Cu", u1_pin_nets))

    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", u1_x - 3.5, u1_y - 8.0, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", u1_x - 3.5, u1_y + 8.0, 0, "F.Cu", 3, "-12V", 1, "GND"))

    for idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        rb_str = n_info["bias_resistor_str"]
        bias_nid = 5 if n_info["bias_rail"] == "-5V_REF" else 6
        bias_name = n_info["bias_rail"]
        v_nid = 10 + j
        v_name = f"V_SUM_{j}"
        inv_nid = 30 + j
        inv_name = f"INV_N{j}"

        if idx == 0:
            fx, fy = u1_x - 5.5, u1_y - 3.5
            bx, by = u1_x - 5.5, u1_y - 1.5
        elif idx == 1:
            fx, fy = u1_x - 5.5, u1_y + 3.5
            bx, by = u1_x - 5.5, u1_y + 1.5
        elif idx == 2:
            fx, fy = u1_x + 5.5, u1_y + 3.5
            bx, by = u1_x + 5.5, u1_y + 1.5
        else:
            fx, fy = u1_x + 5.5, u1_y - 3.5
            bx, by = u1_x + 5.5, u1_y - 1.5

        pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", fx, fy, 0, "F.Cu", inv_nid, inv_name, v_nid, v_name))
        pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, bx, by, 0, "F.Cu", bias_nid, bias_name, inv_nid, inv_name))

    # Summing buses across Pad 2 (Y_row - 0.95)
    for r in range(8):
        y_sum = row_y[r] - 0.95
        local_neuron = r % 4
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"
        
        x_left = x_start
        x_right = x_start + 31 * pitch
        pcb.append(make_segment(x_left, y_sum, x_right, y_sum, 0.25, "F.Cu", sum_name, sum_nid))

        spine_x = 82.5 + local_neuron * 0.8
        pcb.append(make_segment(x_right, y_sum, spine_x, y_sum, 0.25, "F.Cu", sum_name, sum_nid))

    pin_coords = {
        0: (u1_x - 2.7, u1_y - 2.54),
        1: (u1_x - 2.7, u1_y + 2.54),
        2: (u1_x + 2.7, u1_y + 2.54),
        3: (u1_x + 2.7, u1_y - 2.54)
    }

    for local_neuron in range(4):
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"
        spine_x = 82.5 + local_neuron * 0.8
        y_top_sum = row_y[local_neuron] - 0.95
        y_bot_sum = row_y[local_neuron + 4] - 0.95

        pcb.append(make_segment(spine_x, y_top_sum, spine_x, y_bot_sum, 0.30, "F.Cu", sum_name, sum_nid))
        px, py = pin_coords[local_neuron]
        pcb.append(make_segment(spine_x, py, px, py, 0.25, "F.Cu", sum_name, sum_nid))

    # Bottom Bank Inputs (IN_32..IN_63) on B.Cu
    for col in range(32):
        col_x = x_start + col * pitch
        in_idx = 32 + col
        in_nid = 100 + in_idx
        in_name = f"IN_{in_idx}"
        
        y_via_top = row_y[4] + 1.8
        pcb.append(make_segment(col_x, 92.0, col_x, y_via_top, 0.25, "B.Cu", in_name, in_nid))

        for r in [4, 5, 6, 7]:
            vy = row_y[r] + 1.8
            py = row_y[r] + 0.95
            pcb.append(make_via(col_x, vy, 0.6, 0.3, in_name, in_nid))
            pcb.append(make_segment(col_x, vy, col_x, py, 0.25, "F.Cu", in_name, in_nid))

    # Top Bank Inputs (IN_0..IN_31) on In2.Cu
    for col in range(32):
        col_x = x_start + col * pitch
        in_idx = col
        in_nid = 100 + in_idx
        in_name = f"IN_{in_idx}"

        pcb.append(make_segment(col_x, 92.0, col_x, 87.0, 0.25, "F.Cu", in_name, in_nid))
        pcb.append(make_via(col_x, 87.0, 0.6, 0.3, in_name, in_nid))

        y_via_top = row_y[0] + 1.8
        pcb.append(make_segment(col_x, 87.0, col_x, y_via_top, 0.25, "In2.Cu", in_name, in_nid))

        for r in [0, 1, 2, 3]:
            vy = row_y[r] + 1.8
            py = row_y[r] + 0.95
            pcb.append(make_via(col_x, vy, 0.6, 0.3, in_name, in_nid))
            pcb.append(make_segment(col_x, vy, col_x, py, 0.25, "F.Cu", in_name, in_nid))

    # Op-amp outputs
    out_pins = [
        (u1_x - 2.7, u1_y - 3.81),
        (u1_x - 2.7, u1_y + 3.81),
        (u1_x + 2.7, u1_y + 3.81),
        (u1_x + 2.7, u1_y - 3.81)
    ]
    for idx, j in enumerate(neuron_range):
        v_nid = 10 + j
        v_name = f"V_SUM_{j}"
        ox, oy = out_pins[idx]
        finger_x = x_start + (32 + idx) * pitch

        pcb.append(make_segment(ox, oy, finger_x, oy, 0.25, "F.Cu", v_name, v_nid))
        pcb.append(make_segment(finger_x, oy, finger_x, 92.0, 0.25, "F.Cu", v_name, v_nid))

    # Power & Ground
    p_12v_x = x_start + 32 * pitch
    m_12v_x = x_start + 33 * pitch

    pcb.append(make_segment(p_12v_x, 92.0, u1_x - 2.7, 92.0 - (p_12v_x - (u1_x - 2.7)), 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_segment(u1_x - 2.7, 92.0 - (p_12v_x - (u1_x - 2.7)), u1_x - 2.7, u1_y + 1.0, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_via(u1_x - 2.7, u1_y + 1.0, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(u1_x - 2.7, u1_y + 1.0, u1_x - 2.7, u1_y, 0.35, "F.Cu", "+12V", 2))

    pcb.append(make_segment(m_12v_x, 92.0, u1_x + 2.7, 92.0 - (m_12v_x - (u1_x + 2.7)), 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_segment(u1_x + 2.7, 92.0 - (m_12v_x - (u1_x + 2.7)), u1_x + 2.7, u1_y + 1.0, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_via(u1_x + 2.7, u1_y + 1.0, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(u1_x + 2.7, u1_y + 1.0, u1_x + 2.7, u1_y, 0.35, "F.Cu", "-12V", 3))

    for gnd_py in [u1_y - 1.27, u1_y + 1.27]:
        pcb.append(make_via(u1_x - 2.7, gnd_py, 0.6, 0.3, "GND", 1))
        pcb.append(make_via(u1_x + 2.7, gnd_py, 0.6, 0.3, "GND", 1))

    pcb.append(make_via(x_start + 34 * pitch, 92.0, 0.6, 0.3, "GND", 1))
    pcb.append(make_via(x_start + 35 * pitch, 92.0, 0.6, 0.3, "GND", 1))

    pcb.append(")")

    output_path = os.path.join(WORKSPACE_DIR, filename)
    with open(output_path, "w") as f:
        f.write("
".join(pcb))
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    build_dc1_board(neuron_range=(0, 1, 2, 3), filename="daughtercard1a_weights_l1.kicad_pcb", title="DC1A: Neurons 0-3")
