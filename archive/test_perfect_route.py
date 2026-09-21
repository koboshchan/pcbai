#!/usr/bin/env python3
import os
import json
import uuid
import subprocess

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
    pads_str = "\n".join(pads)
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
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PCBEdge:GoldFingers_72P_2.54mm" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {cx:.3f} 96.00)
    (descr "72-Pin PCB Edge Gold Fingers (36 Front + 36 Back) at 2.54mm pitch")
    (property "Reference" "J_EDGE_FINGERS" (at 0 -6.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "72P_GoldFingers_ENIG" (at 0 6.0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def generate_board():
    with open(os.path.join(WORKSPACE_DIR, "weights_layer1.json"), "r") as f:
        l1 = json.load(f)

    card_w = 94.28
    card_h = 100.0
    pitch = 2.54
    cx = card_w / 2.0
    x_start = cx - (17.5 * pitch) # 2.69 mm

    neuron_range = (0, 1, 2, 3)

    nets = [
        (0, ""), (1, "GND"), (2, "+12V"), (3, "-12V")
    ]
    for j in neuron_range:
        nets.append((10 + j, f"V_SUM_{j}"))
        nets.append((30 + j, f"INV_N{j}"))
    for i in range(64):
        nets.append((100 + i, f"IN_{i}"))

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])

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
    pcb.append(f'  (gr_text "DC1A: Neurons 0-3 [32x8 Spaced Matrix]" (at {card_w/2:.2f} 47.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 1.4 1.4) (thickness 0.2))))')

    # Solid Ground plane zone on In1.Cu
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

    # Mounting holes at top corners
    for idx, (mx, my) in enumerate([(5.0, 5.0), (card_w - 5.0, 5.0)]):
        pcb.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {mx:.2f} {my:.2f})
    (descr "Mounting Hole 3.2mm, M3 with Pad")
    (property "Reference" "H{idx+1}" (at {mx:.2f} {my-4:.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "MountingHole" (at {mx:.2f} {my+4:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )""")

    pin_nets_a = {f"A{i+1}": (100 + i, f"IN_{i}") for i in range(32)}
    for idx, j in enumerate(neuron_range):
        pin_nets_a[f"A{33+idx}"] = (10 + j, f"V_SUM_{j}")

    pin_nets_b = {f"B{i+1}": (132 + i, f"IN_{32+i}") for i in range(32)}
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
    # Rotated 90 deg: Pad 1 at (X, Y+0.95), Pad 2 at (X, Y-0.95)
    for local_neuron, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        r_top = local_neuron
        r_bot = local_neuron + 4

        y_top = row_y[r_top]
        y_bot = row_y[r_bot]

        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        # Top bank (inputs 0..31)
        for i in range(32):
            rx = x_start + i * pitch
            inp = n_info["inputs"][i]
            r_val = inp["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_top, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

        # Bottom bank (inputs 32..63)
        for i in range(32, 64):
            col = i - 32
            rx = x_start + col * pitch
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

    # 4 Feedback Resistors Rf (10k 0805)
    # Rf0: between Pin 2 (INV_N0) and Pin 1 (V_SUM_0)
    # Rf1: between Pin 6 (INV_N1) and Pin 7 (V_SUM_1)
    # Rf2: between Pin 9 (INV_N2) and Pin 8 (V_SUM_2)
    # Rf3: between Pin 13 (INV_N3) and Pin 14 (V_SUM_3)
    pcb.append(fp_resistor_0805("Rf_N0", "10k", u1_x - 5.5, u1_y - 3.81, 0, "F.Cu", 30, "INV_N0", 10, "V_SUM_0"))
    pcb.append(fp_resistor_0805("Rf_N1", "10k", u1_x - 5.5, u1_y + 3.81, 0, "F.Cu", 31, "INV_N1", 11, "V_SUM_1"))
    pcb.append(fp_resistor_0805("Rf_N2", "10k", u1_x + 5.5, u1_y + 3.81, 0, "F.Cu", 32, "INV_N2", 12, "V_SUM_2"))
    pcb.append(fp_resistor_0805("Rf_N3", "10k", u1_x + 5.5, u1_y - 3.81, 0, "F.Cu", 33, "INV_N3", 13, "V_SUM_3"))

    # Bypass Caps
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", u1_x - 5.5, u1_y - 7.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", u1_x + 5.5, u1_y - 7.5, 0, "F.Cu", 3, "-12V", 1, "GND"))

    # =========================================================================
    # ROUTING
    # =========================================================================

    # 1. SUMMING HIGHWAYS
    # Spines on In2.Cu:
    # N0 (Row 0/4) -> spine at X = 83.2
    # N1 (Row 1/5) -> spine at X = 82.6
    # N2 (Row 2/6) -> spine at X = 82.0
    # N3 (Row 3/7) -> spine at X = 81.4
    # Wait, column 31 is at 81.43, so let's place spines at 82.2, 82.8, 83.4, 84.0
    spine_x_map = {0: 84.0, 1: 83.4, 2: 82.8, 3: 82.2}

    for r in range(8):
        y_sum = row_y[r] - 0.95
        local_neuron = r % 4
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        # Horizontal track on F.Cu across row
        x_left = x_start
        x_right = x_start + 31 * pitch
        pcb.append(make_segment(x_left, y_sum, x_right, y_sum, 0.25, "F.Cu", sum_name, sum_nid))

        # Via to In2.Cu at spine_x
        sx = spine_x_map[local_neuron]
        pcb.append(make_segment(x_right, y_sum, sx, y_sum, 0.25, "F.Cu", sum_name, sum_nid))
        pcb.append(make_via(sx, y_sum, 0.6, 0.3, sum_name, sum_nid))

    for local_neuron in range(4):
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"
        sx = spine_x_map[local_neuron]
        y_top_sum = row_y[local_neuron] - 0.95
        y_bot_sum = row_y[local_neuron + 4] - 0.95

        # Vertical spine on In2.Cu
        pcb.append(make_segment(sx, y_top_sum, sx, y_bot_sum, 0.30, "In2.Cu", sum_name, sum_nid))

        # Feed to TL074 pins on F.Cu
        if local_neuron == 0:
            # Pin 2: (84.8, 44.46)
            pcb.append(make_segment(sx, 44.46, u1_x - 3.5, 44.46, 0.25, "In2.Cu", sum_name, sum_nid))
            pcb.append(make_via(u1_x - 3.5, 44.46, 0.6, 0.3, sum_name, sum_nid))
            pcb.append(make_segment(u1_x - 3.5, 44.46, u1_x - 2.7, 44.46, 0.25, "F.Cu", sum_name, sum_nid))
            # Connect Rf0
            pcb.append(make_segment(u1_x - 5.5 + 0.95, u1_y - 3.81, u1_x - 3.5, 44.46, 0.25, "F.Cu", sum_name, sum_nid))
            pcb.append(make_segment(u1_x - 5.5 - 0.95, u1_y - 3.81, u1_x - 2.7, 43.19, 0.25, "F.Cu", "V_SUM_0", 10))
        elif local_neuron == 1:
            # Pin 6: (84.8, 49.54)
            pcb.append(make_segment(sx, 49.54, u1_x - 3.5, 49.54, 0.25, "In2.Cu", sum_name, sum_nid))
            pcb.append(make_via(u1_x - 3.5, 49.54, 0.6, 0.3, sum_name, sum_nid))
            pcb.append(make_segment(u1_x - 3.5, 49.54, u1_x - 2.7, 49.54, 0.25, "F.Cu", sum_name, sum_nid))
            # Connect Rf1
            pcb.append(make_segment(u1_x - 5.5 + 0.95, u1_y + 3.81, u1_x - 3.5, 49.54, 0.25, "F.Cu", sum_name, sum_nid))
            pcb.append(make_segment(u1_x - 5.5 - 0.95, u1_y + 3.81, u1_x - 2.7, 50.81, 0.25, "F.Cu", "V_SUM_1", 11))
        elif local_neuron == 2:
            # Pin 9: (90.2, 49.54)
            pcb.append(make_segment(sx, 49.54, u1_x + 3.5, 49.54, 0.25, "In2.Cu", sum_name, sum_nid))
            pcb.append(make_via(u1_x + 3.5, 49.54, 0.6, 0.3, sum_name, sum_nid))
            pcb.append(make_segment(u1_x + 3.5, 49.54, u1_x + 2.7, 49.54, 0.25, "F.Cu", sum_name, sum_nid))
            # Connect Rf2
            pcb.append(make_segment(u1_x + 5.5 - 0.95, u1_y + 3.81, u1_x + 3.5, 49.54, 0.25, "F.Cu", sum_name, sum_nid))
            pcb.append(make_segment(u1_x + 5.5 + 0.95, u1_y + 3.81, u1_x + 2.7, 50.81, 0.25, "F.Cu", "V_SUM_2", 12))
        elif local_neuron == 3:
            # Pin 13: (90.2, 44.46)
            pcb.append(make_segment(sx, 44.46, u1_x + 3.5, 44.46, 0.25, "In2.Cu", sum_name, sum_nid))
            pcb.append(make_via(u1_x + 3.5, 44.46, 0.6, 0.3, sum_name, sum_nid))
            pcb.append(make_segment(u1_x + 3.5, 44.46, u1_x + 2.7, 44.46, 0.25, "F.Cu", sum_name, sum_nid))
            # Connect Rf3
            pcb.append(make_segment(u1_x + 5.5 - 0.95, u1_y - 3.81, u1_x + 3.5, 44.46, 0.25, "F.Cu", sum_name, sum_nid))
            pcb.append(make_segment(u1_x + 5.5 + 0.95, u1_y - 3.81, u1_x + 2.7, 43.19, 0.25, "F.Cu", "V_SUM_3", 13))

    # 2. INPUT DISTRIBUTION (B.Cu)
    # Bottom Bank (IN_32..IN_63):
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

    # Top Bank (IN_0..IN_31):
    for col in range(32):
        col_x = x_start + col * pitch
        in_idx = col
        in_nid = 100 + in_idx
        in_name = f"IN_{in_idx}"
        corridor_x = col_x + 1.00

        pcb.append(make_segment(col_x, 92.0, corridor_x, 88.0, 0.25, "F.Cu", in_name, in_nid))
        pcb.append(make_via(corridor_x, 88.0, 0.6, 0.3, in_name, in_nid))

        pcb.append(make_segment(corridor_x, 88.0, corridor_x, 46.0, 0.25, "B.Cu", in_name, in_nid))
        pcb.append(make_segment(corridor_x, 46.0, col_x, 43.0, 0.25, "B.Cu", in_name, in_nid))

        y_via_top = row_y[0] + 1.8
        pcb.append(make_segment(col_x, 43.0, col_x, y_via_top, 0.25, "B.Cu", in_name, in_nid))

        for r in [0, 1, 2, 3]:
            vy = row_y[r] + 1.8
            py = row_y[r] + 0.95
            pcb.append(make_via(col_x, vy, 0.6, 0.3, in_name, in_nid))
            pcb.append(make_segment(col_x, vy, col_x, py, 0.25, "F.Cu", in_name, in_nid))

    # 3. OP-AMP OUTPUTS (V_SUM_0..3) to Edge Fingers A33..A36 on F.Cu
    out_pins = [
        (u1_x - 2.7, 43.19), # Pin 1
        (u1_x - 2.7, 50.81), # Pin 7
        (u1_x + 2.7, 50.81), # Pin 8
        (u1_x + 2.7, 43.19)  # Pin 14
    ]
    for idx, j in enumerate(neuron_range):
        v_nid = 10 + j
        v_name = f"V_SUM_{j}"
        ox, oy = out_pins[idx]
        finger_x = x_start + (32 + idx) * pitch

        # Short dogleg escape to finger_x, then straight south
        pcb.append(make_segment(ox, oy, finger_x, oy, 0.25, "F.Cu", v_name, v_nid))
        pcb.append(make_segment(finger_x, oy, finger_x, 92.0, 0.25, "F.Cu", v_name, v_nid))

    # 4. POWER & GROUND
    # +12V (Pin 4 at 84.8, 47.0): feed from B33 on B.Cu, via directly at Pin 4!
    p_12v_x = x_start + 32 * pitch
    m_12v_x = x_start + 33 * pitch

    # +12V track entirely on B.Cu up to U1 Pin 4
    pcb.append(make_segment(p_12v_x, 92.0, p_12v_x, 88.0, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_segment(p_12v_x, 88.0, u1_x - 4.5, 47.0, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_via(u1_x - 4.5, 47.0, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(u1_x - 4.5, 47.0, u1_x - 2.7, 47.0, 0.35, "F.Cu", "+12V", 2))

    # -12V track entirely on B.Cu up to U1 Pin 11
    pcb.append(make_segment(m_12v_x, 92.0, m_12v_x, 88.0, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_segment(m_12v_x, 88.0, u1_x + 4.5, 47.0, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_via(u1_x + 4.5, 47.0, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(u1_x + 4.5, 47.0, u1_x + 2.7, 47.0, 0.35, "F.Cu", "-12V", 3))

    # Non-inverting pins (Pins 3, 5, 10, 12) drop thermal vias inside the chip body into In1.Cu GND plane!
    # Inside the chip body (between X = 86.0 and 89.0), it is completely open!
    pcb.append(make_segment(u1_x - 2.7, 45.73, u1_x - 1.2, 45.73, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_via(u1_x - 1.2, 45.73, 0.6, 0.3, "GND", 1))

    pcb.append(make_segment(u1_x - 2.7, 48.27, u1_x - 1.2, 48.27, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_via(u1_x - 1.2, 48.27, 0.6, 0.3, "GND", 1))

    pcb.append(make_segment(u1_x + 2.7, 48.27, u1_x + 1.2, 48.27, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_via(u1_x + 1.2, 48.27, 0.6, 0.3, "GND", 1))

    pcb.append(make_segment(u1_x + 2.7, 45.73, u1_x + 1.2, 45.73, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_via(u1_x + 1.2, 45.73, 0.6, 0.3, "GND", 1))

    # Connect Bypass Caps
    pcb.append(make_segment(u1_x - 5.5 - 0.95, u1_y - 7.5, u1_x - 4.5, 47.0, 0.25, "F.Cu", "+12V", 2))
    pcb.append(make_via(u1_x - 5.5 + 0.95, u1_y - 7.5, 0.6, 0.3, "GND", 1))

    pcb.append(make_segment(u1_x + 5.5 - 0.95, u1_y - 7.5, u1_x + 4.5, 47.0, 0.25, "F.Cu", "-12V", 3))
    pcb.append(make_via(u1_x + 5.5 + 0.95, u1_y - 7.5, 0.6, 0.3, "GND", 1))

    # GND vias for fingers B35, B36
    pcb.append(make_segment(x_start + 34 * pitch, 92.0, 93.0, 88.0, 0.35, "B.Cu", "GND", 1))
    pcb.append(make_segment(x_start + 35 * pitch, 92.0, 93.0, 88.0, 0.35, "B.Cu", "GND", 1))
    pcb.append(make_via(93.0, 88.0, 0.6, 0.3, "GND", 1))

    pcb.append(")")

    board_path = os.path.join(WORKSPACE_DIR, "daughtercard1a_weights_l1.kicad_pcb")
    with open(board_path, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated {board_path}")

if __name__ == "__main__":
    generate_board()
