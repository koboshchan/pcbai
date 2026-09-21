#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
build_full_72p_system.py
------------------------
Master generator for the 72-Pin Straight Edge Card Modular Analog Neural Network System:
1. Daughtercard 1A: L1 Weights (Neurons 0..3)   [94.28 x 100.0 mm, 4 layers]
2. Daughtercard 1B: L1 Weights (Neurons 4..7)   [94.28 x 100.0 mm, 4 layers]
3. Daughtercard 1C: L1 Weights (Neurons 8..11)  [94.28 x 100.0 mm, 4 layers]
4. Daughtercard 1D: L1 Weights (Neurons 12..15) [94.28 x 100.0 mm, 4 layers]
5. Daughtercard 2:  L1 Active Precision ReLU    [94.28 x 100.0 mm, 4 layers]
6. Daughtercard 3:  L2 Weights + WTA Argmax     [94.28 x 100.0 mm, 4 layers]
7. Motherboard:     6-Slot Straight 72P Backplane [100.0 x 100.0 mm, 4 layers]

All daughtercards have ZERO soldered connectors and 72 exposed gold fingers along the bottom edge.
Motherboard has 6x S-072M-2.54-5 straight female edge card sockets soldered through-hole.
"""

import os
import sys
import json
import uuid
import pcbnew
import subprocess

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
ARTIFACTS_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"

def make_uuid(): return str(uuid.uuid4())
def mm(v): return int(v * 1000000)

# Datasheet exact values
DIM_A = 88.90   # Pin span: 35 * 2.54mm
DIM_B = 94.28   # Daughtercard blade width (Recommended Card Layout)
DIM_C = 97.73   # Outer body length of connector socket
BODY_WIDTH = 9.25
BODY_HEIGHT = 15.60
SLOT_DEPTH = 9.00
ROW_SPACING = 5.08
PAD_WIDTH = 1.60
PAD_HEIGHT = 8.00
PITCH = 2.54

WRL_SOCKET = os.path.join(WORKSPACE_DIR, "test_edgecard_system", "edge_card_72p_exact.wrl")
WRL_BLADE = os.path.join(WORKSPACE_DIR, "test_edgecard_system", "dc_blade_72p_exact.wrl")

# =========================================================================
# Common S-Expression Generators
# =========================================================================
def get_header(board_name, nets):
    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])
    return f"""(kicad_pcb (version 20221018) (generator "analog_nn_72p_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "{board_name}")
    (company "Discrete Analog Neural Network System")
    (rev "v6.0 - 72-Pin Edge Card Modular Stack")
    (date "2026-09-13")
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
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
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
"""

def get_daughtercard_outline_and_mounts(width=94.28, height=100.0):
    items = [
        f'  (gr_rect (start 0 0) (end {width:.2f} {height:.2f}) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{make_uuid()}"))',
        # Ground plane on In1.Cu
        f'  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)',
        '    (priority 0)',
        '    (connect_pads (clearance 0.25))',
        '    (min_thickness 0.25)',
        '    (filled_areas_thickness no)',
        '    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))',
        '    (polygon',
        f'      (pts (xy 1.0 1.0) (xy {width-1.0:.2f} 1.0) (xy {width-1.0:.2f} 90.0) (xy 1.0 90.0))',
        '    )',
        '  )',
        # Insertion stop silkscreen guideline
        f'  (gr_line (start 1.0 91.0) (end {width-1.0:.2f} 91.0) (stroke (width 0.25) (type default)) (layer "F.SilkS") (uuid "{make_uuid()}"))',
        f'  (gr_text "<< INSERTION STOP LINE (9.0mm Socket Depth) >>" (at {width/2:.2f} 89.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 1.1 1.1) (thickness 0.15))))',
    ]
    # M3 mounting / pull holes at top corners
    for idx, (mx, my) in enumerate([(5.0, 5.0), (width - 5.0, 5.0)]):
        items.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {mx:.2f} {my:.2f})
    (descr "Mounting Hole 3.2mm, M3 with Pad")
    (property "Reference" "H{idx+1}" (at {mx:.2f} {my-4:.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "MountingHole" (at {mx:.2f} {my+4:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )""")
    return "\n".join(items)

def fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=94.28):
    """
    Generates 72 gold fingers footprint along the bottom edge (Y=100mm).
    Row A on F.Cu (Pins A1..A36), Row B on B.Cu (Pins B1..B36).
    """
    cx = card_width / 2.0 # 47.14 mm
    x_start = - (17.5 * PITCH) # 36 pins: 35 * 2.54 = 88.90mm span
    pads = []
    
    for i in range(36):
        px = x_start + i * PITCH
        # Front Finger (Row A on F.Cu + F.Mask)
        p_num_a = f"A{i+1}"
        nid_a, nname_a = pin_nets_a.get(p_num_a, (0, ""))
        pads.append(f'    (pad "{p_num_a}" smd roundrect (at {px:.3f} 0) (size {PAD_WIDTH:.2f} {PAD_HEIGHT:.2f}) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2) (net {nid_a} "{nname_a}"))')
        
        # Back Finger (Row B on B.Cu + B.Mask)
        p_num_b = f"B{i+1}"
        nid_b, nname_b = pin_nets_b.get(p_num_b, (0, ""))
        pads.append(f'    (pad "{p_num_b}" smd roundrect (at {px:.3f} 0) (size {PAD_WIDTH:.2f} {PAD_HEIGHT:.2f}) (layers "B.Cu" "B.Mask") (roundrect_rratio 0.2) (net {nid_b} "{nname_b}"))')
        
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PCBEdge:GoldFingers_72P_2.54mm" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {cx:.2f} 96.00)
    (descr "72-Pin PCB Edge Gold Fingers (36 Front + 36 Back) at 2.54mm pitch")
    (property "Reference" "J_EDGE_FINGERS" (at 0 -6.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "72P_GoldFingers_ENIG" (at 0 6.0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def fp_resistor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.2f} {y:.2f} {rot})
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
    (at {x:.2f} {y:.2f} {rot})
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
    (at {x:.2f} {y:.2f} {rot})
    (descr "SOIC, 14 Pin, 3.9x8.7mm body, 1.27mm pitch")
    (property "Reference" "{ref}" (at 0 -5.5 {rot}) (layer "{silk}") (effects (font (size 0.8 0.8) (thickness 0.1))))
    (property "Value" "{val}" (at 0 5.5 {rot}) (layer "{fab}") (effects (font (size 0.8 0.8) (thickness 0.1))))
{pads_str}
  )"""

def fp_diodesod123(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "Diode_SMD:D_SOD-123" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "SOD-123 diode")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -1.65 0 {rot}) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.65 0 {rot}) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
  )"""

def fp_led0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "LED_SMD:LED_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "LED SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -1.05 0 {rot}) (size 1.05 1.25) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.05 0 {rot}) (size 1.05 1.25) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
  )"""

def make_segment(x1, y1, x2, y2, width=0.25, layer="F.Cu", net_name="", net_id=0):
    return f'  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width}) (layer "{layer}") (net {net_id}) (uuid "{make_uuid()}"))'

def make_via(x, y, size=0.6, drill=0.3, net_name="", net_id=0):
    return f'  (via (at {x:.4f} {y:.4f}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net_id}) (uuid "{make_uuid()}"))'

print("Common modules initialized.")

# =========================================================================
# 1. Generator for Layer 1 Synaptic Weight Daughtercards (DC1A, DC1B, DC1C, DC1D)
# =========================================================================
def build_dc1_board(filename, title, neuron_range):
    board_file = os.path.join(WORKSPACE_DIR, filename)
    w1_file = os.path.join(WORKSPACE_DIR, "weights_layer1.json")
    with open(w1_file) as f:
        l1 = json.load(f)

    PITCH = 2.54
    x_start = 2.69

    nets = {0: "", 1: "GND", 2: "+12V", 3: "-12V", 4: "+5V_REF", 5: "-5V_REF"}
    for i in range(64):
        nets[100 + i] = f"IN_{i}"
    for j in range(16):
        nets[10 + j] = f"V_SUM_{j}"
        nets[30 + j] = f"INV_N{j}"

    pin_nets_a = {}
    pin_nets_b = {}

    for i in range(32):
        pin_nets_a[f"A{i+1}"] = (100 + i, f"IN_{i}")
        pin_nets_b[f"B{i+1}"] = (100 + 32 + i, f"IN_{32+i}")

    for idx, j in enumerate(neuron_range):
        pin_nets_a[f"A{33+idx}"] = (10 + j, f"V_SUM_{j}")

    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (4, "+5V_REF")
    pin_nets_b["B36"] = (5, "-5V_REF")

    net_list_tuples = [(nid, name) for nid, name in sorted(nets.items()) if nid > 0]
    pcb = [
        get_header(title, [(0, "")] + net_list_tuples),
        get_daughtercard_outline_and_mounts(width=94.28, height=100.0),
        fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=94.28),
        f'  (gr_text "{title}" (at 47.14 8.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 2.5 2.5) (thickness 0.3))))'
    ]

    row_y = [17.0, 25.0, 33.0, 41.0, 54.0, 62.0, 70.0, 78.0]

    # 1. Matrix Resistors (256 components on F.Cu):
    for col in range(32):
        col_x = x_start + col * PITCH
        for r in range(8):
            ry = row_y[r]
            in_idx = col if r < 4 else (32 + col)
            in_nid = 100 + in_idx
            in_name = f"IN_{in_idx}"
            local_neuron = r % 4
            j = neuron_range[local_neuron]
            sum_nid = 30 + j
            sum_name = f"INV_N{j}"
            res_str = l1["weights"][j]["inputs"][in_idx]["resistor_str"]
            ref = f"R1_{in_idx}_{local_neuron}"
            pcb.append(fp_resistor_0805(ref, res_str, col_x, ry, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

    # 2. Matrix Columns (Top Bank on In2.Cu, Bottom Bank on B.Cu):
    for col in range(32):
        col_x = x_start + col * PITCH
        # Top Bank (IN_0..IN_31):
        in_top_idx = col
        in_top_nid = 100 + in_top_idx
        in_top_name = f"IN_{in_top_idx}"
        x_top = col_x - 0.5

        pcb.append(make_segment(col_x, 92.0, x_top, 88.0, 0.25, "F.Cu", in_top_name, in_top_nid))
        pcb.append(make_via(x_top, 88.0, 0.6, 0.3, in_top_name, in_top_nid))
        y_top_limit = row_y[0] + 1.8
        pcb.append(make_segment(x_top, 88.0, x_top, y_top_limit, 0.25, "In2.Cu", in_top_name, in_top_nid))

        for r in [0, 1, 2, 3]:
            vy = row_y[r] + 1.8
            py = row_y[r] + 0.95
            pcb.append(make_via(x_top, vy, 0.6, 0.3, in_top_name, in_top_nid))
            pcb.append(make_segment(x_top, vy, col_x, py, 0.25, "F.Cu", in_top_name, in_top_nid))

        # Bottom Bank (IN_32..IN_63):
        in_bot_idx = 32 + col
        in_bot_nid = 100 + in_bot_idx
        in_bot_name = f"IN_{in_bot_idx}"
        x_bot = col_x + 0.5

        pcb.append(make_segment(col_x, 92.0, x_bot, 90.0, 0.25, "B.Cu", in_bot_name, in_bot_nid))
        y_bot_limit = row_y[4] + 1.8
        pcb.append(make_segment(x_bot, 90.0, x_bot, y_bot_limit, 0.25, "B.Cu", in_bot_name, in_bot_nid))

        for r in [4, 5, 6, 7]:
            vy = row_y[r] + 1.8
            py = row_y[r] + 0.95
            pcb.append(make_via(x_bot, vy, 0.6, 0.3, in_bot_name, in_bot_nid))
            pcb.append(make_segment(x_bot, vy, col_x, py, 0.25, "F.Cu", in_bot_name, in_bot_nid))

    # 3. Summing Rows on F.Cu -> 4 Vertical Trunks on In2.Cu:
    n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]
    tx_map = {0: 82.65, 1: 83.35, 2: 84.75, 3: 84.05}

    for r in range(8):
        y_sum = row_y[r] - 0.95
        local_neuron = r % 4
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        x_left = x_start
        tx = tx_map[local_neuron]
        pcb.append(make_segment(x_left, y_sum, tx, y_sum, 0.25, "F.Cu", sum_name, sum_nid))
        pcb.append(make_via(tx, y_sum, 0.6, 0.3, sum_name, sum_nid))

    # Summing vertical trunks:
    pcb.append(make_segment(82.65, row_y[0] - 0.95, 82.65, row_y[4] - 0.95, 0.25, "In2.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(83.35, row_y[1] - 0.95, 83.35, row_y[5] - 0.95, 0.25, "In2.Cu", f"INV_N{n1}", 30 + n1))
    
    # Trunk 3 (INV_N3):
    pcb.append(make_segment(84.05, row_y[7] - 0.95, 84.05, 12.0, 0.25, "In2.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(84.05, 12.0, 92.60, 12.0, 0.25, "In2.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(92.60, 12.0, 92.60, 44.96, 0.25, "In2.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_via(92.60, 44.96, 0.6, 0.3, f"INV_N{n3}", 30 + n3))
    
    # Trunk 2 (INV_N2):
    pcb.append(make_segment(84.75, row_y[2] - 0.95, 84.75, 82.0, 0.25, "In2.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_via(84.75, 82.0, 0.6, 0.3, f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(84.75, 82.0, 92.60, 82.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(92.60, 82.0, 92.60, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))

    # 4. Place U1 (TL074) at X = 88.0, Y = 47.5
    u1_x = 88.0
    u1_y = 47.5
    ic_pin_nets = {
        "1": (10 + n0, f"V_SUM_{n0}"),
        "2": (30 + n0, f"INV_N{n0}"),
        "3": (1, "GND"),
        "4": (2, "+12V"),
        "5": (1, "GND"),
        "6": (30 + n1, f"INV_N{n1}"),
        "7": (10 + n1, f"V_SUM_{n1}"),
        "8": (10 + n2, f"V_SUM_{n2}"),
        "9": (30 + n2, f"INV_N{n2}"),
        "10": (1, "GND"),
        "11": (3, "-12V"),
        "12": (1, "GND"),
        "13": (30 + n3, f"INV_N{n3}"),
        "14": (10 + n3, f"V_SUM_{n3}")
    }
    pcb.append(fp_soic14("U1", "TL074", u1_x, u1_y, 0, "F.Cu", ic_pin_nets))

    # Ground vias for Pins 3, 5, 10, 12:
    pcb.append(make_via(86.5, u1_y - 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x - 2.7, u1_y - 1.27, 86.5, u1_y - 1.27, 0.25, "F.Cu", "GND", 1))

    pcb.append(make_via(86.5, u1_y + 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x - 2.7, u1_y + 1.27, 86.5, u1_y + 1.27, 0.25, "F.Cu", "GND", 1))

    pcb.append(make_via(89.5, u1_y - 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x + 2.7, u1_y - 1.27, 89.5, u1_y - 1.27, 0.25, "F.Cu", "GND", 1))

    pcb.append(make_via(89.5, u1_y + 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x + 2.7, u1_y + 1.27, 89.5, u1_y + 1.27, 0.25, "F.Cu", "GND", 1))

    # Decoupling Capacitors:
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 80.5, 47.50, 0, "F.Cu", 1, "GND", 2, "+12V"))
    pcb.append(make_via(79.55, 45.8, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(79.55, 45.8, 79.55, 47.50, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(81.45, 47.50, u1_x - 2.7, 47.50, 0.35, "F.Cu", "+12V", 2))

    # C_U1N at (93.0, 47.50) rot=90:
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 93.0, 47.50, 90, "F.Cu", 3, "-12V", 1, "GND"))
    pcb.append(make_segment(u1_x + 2.7, 47.50, 91.80, 47.50, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_segment(91.80, 47.50, 91.80, 48.45, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_segment(91.80, 48.45, 93.00, 48.45, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_segment(93.0, 46.55, 91.80, 46.55, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(91.80, 46.55, 91.80, 46.23, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(91.80, 46.23, u1_x + 2.7, 46.23, 0.25, "F.Cu", "GND", 1))

    # 5. Connect Trunks to Op-Amp Inverting Inputs:
    pcb.append(make_via(82.65, 44.96, 0.6, 0.3, f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(82.65, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))

    pcb.append(make_via(83.35, 50.04, 0.6, 0.3, f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(83.35, 50.04, u1_x - 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))

    pcb.append(make_segment(92.60, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(92.60, 50.04, u1_x + 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))

    # 6. NEURON 0 (Above U1):
    # Rf0 at (86.5, 36.0) rot=0: Pad 1 (85.55) = V_SUM_0, Pad 2 (87.45) = INV_N0
    pcb.append(fp_resistor_0805(f"Rf_N{n0}", "10k", 86.5, 36.0, 0, "F.Cu", 10 + n0, f"V_SUM_{n0}", 30 + n0, f"INV_N{n0}"))
    b0_nid = 5 if l1["weights"][n0]["bias_rail"] == "-5V_REF" else 4
    b0_name = l1["weights"][n0]["bias_rail"]
    # Rb0 at (86.5, 29.0) rot=90:
    # Pad 1 (86.5, 29.95) = INV_N0, Pad 2 (86.5, 28.05) = Bias rail
    pcb.append(fp_resistor_0805(f"Rb_N{n0}", l1["weights"][n0]["bias_resistor_str"], 86.5, 29.0, 90, "F.Cu", 30 + n0, f"INV_N{n0}", b0_nid, b0_name))
    # INV_N0: Pad 1 of Rb0 (86.5, 29.95) -> (87.45, 29.95) -> Pad 2 of Rf0 (87.45, 36.0) -> Pin 2 (85.3, 44.96)
    pcb.append(make_segment(86.50, 29.95, 87.45, 29.95, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(87.45, 29.95, 87.45, 36.00, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(87.45, 36.00, 87.45, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(87.45, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    # V_SUM_0: Pin 1 (85.3, 43.69) to Pad 1 of Rf0 (85.55, 36.0)
    pcb.append(make_segment(u1_x - 2.7, 43.69, 85.55, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.55, 43.69, 85.55, 36.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))

    # 7. NEURON 1 (Below U1):
    # Rf1 at (85.5, 56.0) rot=0: Pad 1 (84.55) = INV_N1, Pad 2 (86.45) = V_SUM_1
    pcb.append(fp_resistor_0805(f"Rf_N{n1}", "10k", 85.5, 56.0, 0, "F.Cu", 30 + n1, f"INV_N{n1}", 10 + n1, f"V_SUM_{n1}"))
    b1_nid = 5 if l1["weights"][n1]["bias_rail"] == "-5V_REF" else 4
    b1_name = l1["weights"][n1]["bias_rail"]
    # Rb1 at (85.5, 63.0) rot=90:
    # Pad 1 (85.5, 63.95) = Bias rail, Pad 2 (85.5, 62.05) = INV_N1
    pcb.append(fp_resistor_0805(f"Rb_N{n1}", l1["weights"][n1]["bias_resistor_str"], 85.5, 63.0, 90, "F.Cu", b1_nid, b1_name, 30 + n1, f"INV_N{n1}"))
    # INV_N1: Pin 6 (85.3, 50.04) -> (83.60, 50.04) -> (83.60, 56.0) -> Pad 1 of Rf1 (84.55, 56.0) -> Pad 2 of Rb1 (85.5, 62.05)
    pcb.append(make_segment(u1_x - 2.7, 50.04, 83.60, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(83.60, 50.04, 83.60, 56.0, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(83.60, 56.0, 84.55, 56.0, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(84.55, 56.0, 85.50, 62.05, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    # V_SUM_1: Pin 7 (85.3, 51.31) to Pad 2 of Rf1 (86.45, 56.0)
    pcb.append(make_segment(u1_x - 2.7, 51.31, 86.45, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.45, 51.31, 86.45, 56.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))

    # 8. NEURON 3 (Above U1):
    # Rf3 at (90.5, 36.0) rot=0: Pad 1 (89.55) = INV_N3, Pad 2 (91.45) = V_SUM_3
    pcb.append(fp_resistor_0805(f"Rf_N{n3}", "10k", 90.5, 36.0, 0, "F.Cu", 30 + n3, f"INV_N{n3}", 10 + n3, f"V_SUM_{n3}"))
    b3_nid = 5 if l1["weights"][n3]["bias_rail"] == "-5V_REF" else 4
    b3_name = l1["weights"][n3]["bias_rail"]
    # Rb3 at (89.55, 25.0) rot=90:
    # Pad 1 (89.55, 25.95) = INV_N3, Pad 2 (89.55, 24.05) = Bias rail
    pcb.append(fp_resistor_0805(f"Rb_N{n3}", l1["weights"][n3]["bias_resistor_str"], 89.55, 25.0, 90, "F.Cu", 30 + n3, f"INV_N{n3}", b3_nid, b3_name))
    # INV_N3: Pad 1 of Rb3 (89.55, 25.95) -> Pad 1 of Rf3 (89.55, 36.0) -> Pin 13 (90.7, 44.96)
    pcb.append(make_segment(89.55, 25.95, 89.55, 36.0, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(89.55, 36.0, 89.55, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(89.55, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    # V_SUM_3: Pin 14 (90.7, 43.69) to Pad 2 of Rf3 (91.45, 36.0)
    pcb.append(make_segment(u1_x + 2.7, 43.69, 91.45, 43.69, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(91.45, 43.69, 91.45, 36.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))

    # 9. NEURON 2 (Below U1):
    # Rf2 at (90.5, 56.0) rot=0: Pad 1 (89.55) = V_SUM_2, Pad 2 (91.45) = INV_N2
    pcb.append(fp_resistor_0805(f"Rf_N{n2}", "10k", 90.5, 56.0, 0, "F.Cu", 10 + n2, f"V_SUM_{n2}", 30 + n2, f"INV_N{n2}"))
    b2_nid = 5 if l1["weights"][n2]["bias_rail"] == "-5V_REF" else 4
    b2_name = l1["weights"][n2]["bias_rail"]
    # Rb2 at (91.45, 68.0) rot=90:
    # Pad 1 (91.45, 68.95) = Bias rail, Pad 2 (91.45, 67.05) = INV_N2
    pcb.append(fp_resistor_0805(f"Rb_N{n2}", l1["weights"][n2]["bias_resistor_str"], 91.45, 68.0, 90, "F.Cu", b2_nid, b2_name, 30 + n2, f"INV_N{n2}"))
    # INV_N2: Pin 9 (90.7, 50.04) -> (92.40, 50.04) -> (92.40, 56.0) -> Pad 2 of Rf2 (91.45, 56.0) -> Pad 2 of Rb2 (91.45, 67.05)
    pcb.append(make_segment(u1_x + 2.7, 50.04, 92.40, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(92.40, 50.04, 92.40, 56.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(92.40, 56.0, 91.45, 56.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(91.45, 56.0, 91.45, 67.05, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    # V_SUM_2: Pin 8 (90.7, 51.31) to Pad 1 of Rf2 (89.55, 56.0)
    pcb.append(make_segment(u1_x + 2.7, 51.31, 89.55, 51.31, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(89.55, 51.31, 89.55, 56.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))

    # 10. Dedicated Parallel Signals on In2.Cu and B.Cu:
    # Output 0 (V_SUM_0)
    pcb.append(make_segment(85.55, 36.0, 85.55, 38.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_via(85.55, 38.0, 0.6, 0.3, f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.55, 38.0, 85.55, 85.0, 0.25, "B.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_via(85.55, 85.0, 0.6, 0.3, f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.55, 85.0, 83.97, 92.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))

    # Output 1 (V_SUM_1)
    pcb.append(make_segment(86.45, 56.0, 86.45, 58.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_via(86.45, 58.0, 0.6, 0.3, f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.45, 58.0, 86.45, 87.0, 0.25, "B.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_via(86.45, 87.0, 0.6, 0.3, f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.45, 87.0, 86.51, 92.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))

    # Output 2 (V_SUM_2)
    pcb.append(make_segment(89.55, 56.0, 89.55, 58.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_via(89.55, 58.0, 0.6, 0.3, f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(89.55, 58.0, 89.55, 88.0, 0.25, "B.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_via(89.55, 88.0, 0.6, 0.3, f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(89.55, 88.0, 89.05, 92.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))

    # Output 3 (V_SUM_3)
    pcb.append(make_segment(91.45, 36.0, 91.45, 38.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_via(91.45, 38.0, 0.6, 0.3, f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(91.45, 38.0, 91.45, 87.0, 0.25, "B.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_via(91.45, 87.0, 0.6, 0.3, f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(91.45, 87.0, 91.59, 92.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))

    # Power Rails on In2.Cu:
    # +12V
    pcb.append(make_segment(83.97, 92.0, 87.20, 87.50, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_via(87.20, 87.50, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(87.20, 87.50, 87.20, 47.50, 0.35, "In2.Cu", "+12V", 2))
    pcb.append(make_via(87.20, 47.50, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(87.20, 47.50, 85.30, 47.50, 0.35, "F.Cu", "+12V", 2))

    # -12V
    pcb.append(make_segment(86.51, 92.0, 88.00, 89.50, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_via(88.00, 89.50, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(88.00, 89.50, 88.00, 48.50, 0.35, "In2.Cu", "-12V", 3))
    pcb.append(make_via(88.00, 48.50, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(88.00, 48.50, 90.70, 47.50, 0.35, "F.Cu", "-12V", 3))

    bias_taps = [
        (b0_name, 28.05),
        (b3_name, 24.05),
        (b1_name, 63.95),
        (b2_name, 68.95),
    ]
    p5_taps = [y for name, y in bias_taps if name == "+5V_REF"]
    m5_taps = [y for name, y in bias_taps if name == "-5V_REF"]

    if p5_taps:
        p5_top = min(p5_taps)
        pcb.append(make_segment(89.05, 92.0, 88.80, 86.50, 0.35, "B.Cu", "+5V_REF", 4))
        pcb.append(make_via(88.80, 86.50, 0.6, 0.3, "+5V_REF", 4))
        pcb.append(make_segment(88.80, 86.50, 88.80, p5_top, 0.35, "In2.Cu", "+5V_REF", 4))

    if m5_taps:
        m5_top = min(m5_taps)
        pcb.append(make_segment(91.59, 92.0, 90.50, 88.50, 0.35, "B.Cu", "-5V_REF", 5))
        pcb.append(make_via(90.50, 88.50, 0.6, 0.3, "-5V_REF", 5))
        pcb.append(make_segment(90.50, 88.50, 90.50, m5_top, 0.35, "In2.Cu", "-5V_REF", 5))

    # Bias Taps on In2.Cu:
    # Rb_N0 at (86.5, 29.0): Pad 2 is at (86.50, 28.05)
    r0_rx = 88.80 if b0_name == "+5V_REF" else 90.50
    pcb.append(make_segment(86.50, 28.05, r0_rx, 28.05, 0.25, "F.Cu", b0_name, b0_nid))
    pcb.append(make_via(r0_rx, 28.05, 0.6, 0.3, b0_name, b0_nid))

    # Rb_N3 at (89.55, 25.0): Pad 2 is at (89.55, 24.05)
    r3_rx = 88.80 if b3_name == "+5V_REF" else 90.50
    pcb.append(make_segment(89.55, 24.05, r3_rx, 24.05, 0.25, "F.Cu", b3_name, b3_nid))
    pcb.append(make_via(r3_rx, 24.05, 0.6, 0.3, b3_name, b3_nid))

    # Rb_N1 at (85.5, 63.0): Pad 1 is at (85.50, 63.95)
    r1_rx = 88.80 if b1_name == "+5V_REF" else 90.50
    pcb.append(make_segment(85.50, 63.95, r1_rx, 63.95, 0.25, "F.Cu", b1_name, b1_nid))
    pcb.append(make_via(r1_rx, 63.95, 0.6, 0.3, b1_name, b1_nid))

    # Rb_N2 at (91.45, 68.0): Pad 1 is at (91.45, 68.95)
    r2_rx = 88.80 if b2_name == "+5V_REF" else 90.50
    pcb.append(make_segment(91.45, 68.95, r2_rx, 68.95, 0.25, "F.Cu", b2_name, b2_nid))
    pcb.append(make_via(r2_rx, 68.95, 0.6, 0.3, b2_name, b2_nid))

    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))

    fill_cmd = f"""/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 -c "
import pcbnew
board = pcbnew.LoadBoard('{board_file}')
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save('{board_file}')
" """
    subprocess.run(fill_cmd, shell=True, check=True)
    print(f"Generated 72P DC1 Board (Zero-Error Architecture): {board_file}")


# =========================================================================
# 2. Generator for Layer 1 Activation Daughtercard (DC2: 16x Active Precision ReLU)
# =========================================================================
def build_dc2_board(filename="daughtercard2_relu_l1.kicad_pcb", title="Daughtercard 2: 16-Channel Precision Active ReLU"):
    board_file = os.path.join(WORKSPACE_DIR, filename)

    nets = [(0, ""), (1, "GND"), (2, "+12V"), (3, "-12V")]
    for k in range(16):
        nets.append((100 + k, f"V_SUM_{k}"))
        nets.append((200 + k, f"ACT_{k}"))
        nets.append((300 + k, f"INV_RELU_{k}"))
        nets.append((400 + k, f"OP_OUT_{k}"))

    # Pin mapping for 72 Gold Fingers:
    # Row A: Pins A1..A16 = V_SUM_0..15, A17..A32 = GND (shields), A33..A36 = ACT_0..3
    pin_nets_a = {f"A{k+1}": (100 + k, f"V_SUM_{k}") for k in range(16)}
    for p in range(17, 33): pin_nets_a[f"A{p}"] = (1, "GND")
    for k in range(4): pin_nets_a[f"A{33+k}"] = (200 + k, f"ACT_{k}")

    # Row B: Pins B1..B16 = ACT_0..15, B17..B32 = GND, B33 = +12V, B34 = -12V, B35 = GND, B36 = GND
    pin_nets_b = {f"B{k+1}": (200 + k, f"ACT_{k}") for k in range(16)}
    for p in range(17, 33): pin_nets_b[f"B{p}"] = (1, "GND")
    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (1, "GND")
    pin_nets_b["B36"] = (1, "GND")

    pcb = [
        get_header(title, nets),
        get_daughtercard_outline_and_mounts(width=DIM_B, height=100.0),
        fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=DIM_B),
    ]

    # 4x TL074 quad op-amps placed in 2 columns:
    # Col 1 (U1, U2 for ch 0..7) at X = 28.0, Y = 32.0 and Y = 62.0
    # Col 2 (U3, U4 for ch 8..15) at X = 66.0, Y = 32.0 and Y = 62.0
    ic_positions = [(28.0, 32.0), (28.0, 62.0), (66.0, 32.0), (66.0, 62.0)]
    for u_idx, (ux, uy) in enumerate(ic_positions):
        u_ref = f"U{u_idx+1}"
        k_base = u_idx * 4
        ic_pin_nets = {
            "4": (2, "+12V"), "11": (3, "-12V"),
            "1": (400 + k_base, f"OP_OUT_{k_base}"), "2": (300 + k_base, f"INV_RELU_{k_base}"), "3": (1, "GND"),
            "7": (400 + k_base + 1, f"OP_OUT_{k_base+1}"), "6": (300 + k_base + 1, f"INV_RELU_{k_base+1}"), "5": (1, "GND"),
            "8": (400 + k_base + 2, f"OP_OUT_{k_base+2}"), "9": (300 + k_base + 2, f"INV_RELU_{k_base+2}"), "10": (1, "GND"),
            "14": (400 + k_base + 3, f"OP_OUT_{k_base+3}"), "13": (300 + k_base + 3, f"INV_RELU_{k_base+3}"), "12": (1, "GND")
        }
        pcb.append(fp_soic14(u_ref, "TL074", ux, uy, 0, "F.Cu", ic_pin_nets))
        pcb.append(fp_capacitor_0805(f"C_{u_ref}P", "0.1uF", ux, uy - 7.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
        pcb.append(fp_capacitor_0805(f"C_{u_ref}N", "0.1uF", ux, uy + 7.5, 0, "F.Cu", 3, "-12V", 1, "GND"))

        # 4 Rectifier Channels around this IC:
        # Each channel has: Rin (10k), Rfb (10k), D_rect (1N4148), D_clamp (1N4148)
        for ch_rel in range(4):
            k = k_base + ch_rel
            ry = uy - 6.0 + ch_rel * 4.0
            rx_passives = ux - 12.0 if u_idx < 2 else ux + 12.0
            # Input Resistor Rin (V_SUM_k to INV_RELU_k)
            pcb.append(fp_resistor_0805(f"R_IN_{k}", "10k", rx_passives - 2.5, ry, 0, "F.Cu", 100 + k, f"V_SUM_{k}", 300 + k, f"INV_RELU_{k}"))
            # Feedback Resistor Rfb (INV_RELU_k to ACT_k)
            pcb.append(fp_resistor_0805(f"R_FB_{k}", "10k", rx_passives + 2.5, ry, 0, "F.Cu", 300 + k, f"INV_RELU_{k}", 200 + k, f"ACT_{k}"))
            # Rectifier Diode D_rect (OP_OUT_k anode to ACT_k cathode)
            pcb.append(fp_diodesod123(f"D_RECT_{k}", "1N4148", rx_passives, ry - 1.2, 0, "F.Cu", 400 + k, f"OP_OUT_{k}", 200 + k, f"ACT_{k}"))
            # Clamp Diode D_clamp (INV_RELU_k to OP_OUT_k)
            pcb.append(fp_diodesod123(f"D_CLAMP_{k}", "1N4148", rx_passives, ry + 1.2, 0, "F.Cu", 300 + k, f"INV_RELU_{k}", 400 + k, f"OP_OUT_{k}"))

    # Escape routing from fingers to channels:
    cx = DIM_B / 2.0
    x_start = - (17.5 * PITCH)
    for k in range(16):
        px_a = cx + x_start + k * PITCH # Finger pad X for V_SUM_k
        px_b = cx + x_start + k * PITCH # Finger pad X for ACT_k
        v_nid = 100 + k
        act_nid = 200 + k
        # V_SUM_k track on F.Cu
        pcb.append(make_segment(px_a, 92.0, px_a, 85.0, 0.25, "F.Cu", f"V_SUM_{k}", v_nid))
        # ACT_k track on B.Cu
        pcb.append(make_segment(px_b, 92.0, px_b, 85.0, 0.25, "B.Cu", f"ACT_{k}", act_nid))

    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated 72P DC2 Board: {board_file}")


# =========================================================================
# 3. Generator for Layer 2 Synaptic Weights & Winner-Take-All (DC3)
# =========================================================================
def build_dc3_board(filename="daughtercard3_weights_l2_wta.kicad_pcb", title="Daughtercard 3: L2 Synaptic Weights + 10-Way Winner-Take-All"):
    board_file = os.path.join(WORKSPACE_DIR, filename)
    w2_file = os.path.join(WORKSPACE_DIR, "weights_layer2.json")
    with open(w2_file) as f:
        l2 = json.load(f)

    nets = [(0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), (4, "+5V"), (5, "-5V_REF"), (6, "+5V_REF"), (7, "WTA_BUS")]
    for k in range(16):
        nets.append((20 + k, f"ACT_{k}"))
    for c in range(10):
        nets.append((50 + c, f"SCORE_{c}"))
        nets.append((60 + c, f"INV_L2_{c}"))
        nets.append((70 + c, f"LED_N_{c}"))

    net_map = {name: nid for nid, name in nets}

    # Pin mapping for 72 Gold Fingers:
    pin_nets_a = {f"A{k+1}": (20 + k, f"ACT_{k}") for k in range(16)}
    for p in range(17, 33): pin_nets_a[f"A{p}"] = (1, "GND")
    for c in range(4): pin_nets_a[f"A{33+c}"] = (50 + c, f"SCORE_{c}")

    pin_nets_b = {f"B{c+1}": (50 + c, f"SCORE_{c}") for c in range(10)}
    for p in range(11, 33): pin_nets_b[f"B{p}"] = (1, "GND")
    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (1, "GND")
    pin_nets_b["B36"] = (1, "GND")

    pcb = [
        get_header(title, nets),
        get_daughtercard_outline_and_mounts(width=DIM_B, height=100.0),
        fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=DIM_B),
    ]

    # 10 Indicator LEDs (Digits 0..9) + 1k ballast resistors along top edge:
    # X range: 18.0 to 76.0 mm (pitch = 6.4 mm) at Y = 12.0 mm
    for c in range(10):
        lx = 18.0 + c * 6.40
        pcb.append(fp_led0805(f"D_LED_{c}", f"Digit_{c}", lx, 12.0, 0, "F.Cu", 50 + c, f"SCORE_{c}", 70 + c, f"LED_N_{c}"))
        pcb.append(fp_resistor_0805(f"R_LED_{c}", "1k", lx, 16.0, 0, "F.Cu", 70 + c, f"LED_N_{c}", 1, "GND"))

    # 160 Resistors: 16 inputs x 10 classes
    # X range: 18.0 to 66.0 mm (pitch = 3.20 mm)
    # Y range: 24.0 to 78.0 mm (pitch = 6.00 mm for 10 classes)
    for c in range(10):
        cy = 24.0 + c * 5.80
        c_info = l2["weights"][c]
        rb_str = c_info["bias_resistor_str"]
        b_rail = c_info["bias_rail"]
        b_nid = 5 if b_rail == "-5V_REF" else 6
        # Feedback & Bias Resistors at X = 74.0 mm
        pcb.append(fp_resistor_0805(f"Rf_L2_{c}", "10k", 74.0, cy - 1.2, 0, "F.Cu", 50 + c, f"SCORE_{c}", 60 + c, f"INV_L2_{c}"))
        pcb.append(fp_resistor_0805(f"Rb_L2_{c}", rb_str, 74.0, cy + 1.2, 0, "F.Cu", b_nid, b_rail, 60 + c, f"INV_L2_{c}"))
        # WTA Diode (SCORE_c to WTA_BUS)
        pcb.append(fp_diodesod123(f"D_WTA_{c}", "1N4148", 78.0, cy, 0, "F.Cu", 50 + c, f"SCORE_{c}", 7, "WTA_BUS"))

        for k in range(16):
            inp = c_info["inputs"][k]
            rx = 18.0 + k * 3.20
            pcb.append(fp_resistor_0805(f"R2_{k}_{c}", inp["resistor_str"], rx, cy, 90, "F.Cu", 20 + k, f"ACT_{k}", 60 + c, f"INV_L2_{c}"))

    # 3x TL074 Op-Amps at X = 84.0 mm:
    # U1 at Y = 32.0, U2 at Y = 52.0, U3 at Y = 72.0
    for u_idx, uy in enumerate([32.0, 52.0, 72.0]):
        u_ref = f"U{u_idx+1}"
        c_base = u_idx * 4
        ic_pin_nets = {
            "4": (2, "+12V"), "11": (3, "-12V"),
            "1": (50 + c_base, f"SCORE_{c_base}"), "2": (60 + c_base, f"INV_L2_{c_base}"), "3": (1, "GND"),
            "7": (50 + c_base + 1, f"SCORE_{c_base+1}"), "6": (60 + c_base + 1, f"INV_L2_{c_base+1}"), "5": (1, "GND"),
            "8": (50 + c_base + 2, f"SCORE_{c_base+2}"), "9": (60 + c_base + 2, f"INV_L2_{c_base+2}"), "10": (1, "GND"),
            "14": (50 + c_base + 3 if c_base + 3 < 10 else 1, f"SCORE_{c_base+3}" if c_base + 3 < 10 else "GND"),
            "13": (60 + c_base + 3 if c_base + 3 < 10 else 1, f"INV_L2_{c_base+3}" if c_base + 3 < 10 else "GND"),
            "12": (1, "GND")
        }
        pcb.append(fp_soic14(u_ref, "TL074", 84.0, uy, 0, "F.Cu", ic_pin_nets))
        pcb.append(fp_capacitor_0805(f"C_{u_ref}P", "0.1uF", 84.0, uy - 7.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
        pcb.append(fp_capacitor_0805(f"C_{u_ref}N", "0.1uF", 84.0, uy + 7.5, 0, "F.Cu", 3, "-12V", 1, "GND"))

    # Escape routing from fingers to ACT lines:
    cx = DIM_B / 2.0
    x_start = - (17.5 * PITCH)
    for k in range(16):
        px = cx + x_start + k * PITCH
        col_x = 18.0 + k * 3.20
        act_nid = 20 + k
        pcb.append(make_segment(px, 92.0, px, 86.0, 0.25, "F.Cu", f"ACT_{k}", act_nid))
        pcb.append(make_segment(px, 86.0, col_x, 80.0, 0.25, "F.Cu", f"ACT_{k}", act_nid))
        pcb.append(make_segment(col_x, 80.0, col_x, 24.0, 0.25, "F.Cu", f"ACT_{k}", act_nid))

    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated 72P DC3 Board: {board_file}")


# =========================================================================
# 4. Generator for 6-Slot Straight 72P Motherboard Backplane
# =========================================================================
def fp_socket_72p_straight(ref, val, x, y, rot=0, pin_nets_a=None, pin_nets_b=None, blade_wrl=None):
    if pin_nets_a is None: pin_nets_a = {}
    if pin_nets_b is None: pin_nets_b = {}
    pads = []
    x_start = - (17.5 * PITCH) # -44.45 mm
    for i in range(36):
        px = x_start + i * PITCH
        # Row A at Y = -2.54
        p_num_a = f"A{i+1}"
        nid_a, nname_a = pin_nets_a.get(p_num_a, (0, ""))
        shape_a = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num_a}" thru_hole {shape_a} (at {px:.3f} -2.54 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_a} "{nname_a}"))')
        # Row B at Y = +2.54
        p_num_b = f"B{i+1}"
        nid_b, nname_b = pin_nets_b.get(p_num_b, (0, ""))
        pads.append(f'    (pad "{p_num_b}" thru_hole circle (at {px:.3f} 2.54 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_b} "{nname_b}"))')
    pads_str = "\n".join(pads)

    scale = 1.0 / 2.54
    models = []
    if os.path.exists(WRL_SOCKET):
        models.append(f"""    (model "{WRL_SOCKET}"
      (offset (xyz 0 0 0))
      (scale (xyz {scale:.6f} {scale:.6f} {scale:.6f}))
      (rotate (xyz 0 0 0))
    )""")
    if blade_wrl and os.path.exists(blade_wrl):
        models.append(f"""    (model "{blade_wrl}"
      (offset (xyz 0 0 0))
      (scale (xyz {scale:.6f} {scale:.6f} {scale:.6f}))
      (rotate (xyz 0 0 0))
    )""")
    models_str = "\n".join(models)

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
{models_str}
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

def fp_header_2x05(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - (2.0 * PITCH)
    for i in range(5):
        px = x_start + i * PITCH
        p_odd = str(2 * i + 1)
        nid_odd, name_odd = pin_nets.get(p_odd, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_odd}" thru_hole {shape} (at {px:.3f} -1.27 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_odd} "{name_odd}"))')
        p_even = str(2 * i + 2)
        nid_even, name_even = pin_nets.get(p_even, (0, ""))
        pads.append(f'    (pad "{p_even}" thru_hole circle (at {px:.3f} 1.27 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_even} "{name_even}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 2x05 vertical")
    (property "Reference" "{ref}" (at 0 -3.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 3.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def fp_header_1x06(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - (2.5 * PITCH)
    for i in range(6):
        px = x_start + i * PITCH
        p_num = str(i + 1)
        nid, name = pin_nets.get(p_num, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num}" thru_hole {shape} (at {px:.3f} 0 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid} "{name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 1x06 vertical power terminal")
    (property "Reference" "{ref}" (at 0 -2.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 2.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def build_motherboard(filename="motherboard.kicad_pcb", title="Motherboard: 6-Slot Straight 72P Modular Backplane", blade_wrls=None):
    board_file = os.path.join(WORKSPACE_DIR, filename)

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

    pcb = [f"""(kicad_pcb (version 20221018) (generator "analog_nn_72p_motherboard_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "{title}")
    (company "Discrete Analog Neural Network System")
    (rev "v6.0 - 100x100mm 4-Layer 72P Backplane")
    (date "2026-09-13")
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

    # 4 Corner Mounting Holes (M3)
    for idx, (mx, my) in enumerate([(5.0, 5.0), (95.0, 5.0), (5.0, 95.0), (95.0, 95.0)]):
        pcb.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {mx:.2f} {my:.2f})
    (descr "Mounting Hole 3.2mm, M3 with Pad")
    (property "Reference" "H{idx+1}" (at {mx:.2f} {my-4:.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "MountingHole" (at {mx:.2f} {my+4:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )""")

    # 6x Sockets for Slots 0..5 (Pitch = 14.0 mm)
    y_slots = [15.0, 29.0, 43.0, 57.0, 71.0, 85.0]
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
            pin_nets_b["B35"] = (net_map["GND"], "GND")
            pin_nets_b["B36"] = (net_map["GND"], "GND")

        elif s_idx == 4: # DC2 (ReLU)
            for k in range(16):
                pin_nets_a[f"A{k+1}"] = (net_map[f"V_SUM_{k}"], f"V_SUM_{k}")
                pin_nets_b[f"B{k+1}"] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            for p in range(17, 33):
                pin_nets_a[f"A{p}"] = (net_map["GND"], "GND")
                pin_nets_b[f"B{p}"] = (net_map["GND"], "GND")
            for k in range(4):
                pin_nets_a[f"A{33+k}"] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            pin_nets_b["B33"] = (net_map["+12V"], "+12V")
            pin_nets_b["B34"] = (net_map["-12V"], "-12V")
            pin_nets_b["B35"] = (net_map["GND"], "GND")
            pin_nets_b["B36"] = (net_map["GND"], "GND")

        elif s_idx == 5: # DC3 (L2 + WTA)
            for k in range(16):
                pin_nets_a[f"A{k+1}"] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            for p in range(17, 33):
                pin_nets_a[f"A{p}"] = (net_map["GND"], "GND")
            for c in range(4):
                pin_nets_a[f"A{33+c}"] = (net_map[f"SCORE_{c}"], f"SCORE_{c}")
            for c in range(10):
                pin_nets_b[f"B{c+1}"] = (net_map[f"SCORE_{c}"], f"SCORE_{c}")
            for p in range(11, 33):
                pin_nets_b[f"B{p}"] = (net_map["GND"], "GND")
            pin_nets_b["B33"] = (net_map["+12V"], "+12V")
            pin_nets_b["B34"] = (net_map["-12V"], "-12V")
            pin_nets_b["B35"] = (net_map["GND"], "GND")
            pin_nets_b["B36"] = (net_map["GND"], "GND")

        b_wrl = blade_wrls[s_idx] if blade_wrls else None
        pcb.append(fp_socket_72p_straight(ref, val, 50.0, ys, 0, pin_nets_a, pin_nets_b, blade_wrl=b_wrl))

    # External Headers
    # 1. J_PIXELS_A at X = 28.0, Y = 5.08 (2x16 header for IN_0..IN_31)
    j_pix_a_nets = {str(i+1): (net_map[f"IN_{i}"], f"IN_{i}") for i in range(32)}
    pcb.append(fp_header_2x16("J_PIXELS_A", "Pixels_0_31_In", 28.0, 5.08, 0, j_pix_a_nets))

    # 2. J_PIXELS_B at X = 72.0, Y = 5.08 (2x16 header for IN_32..IN_63)
    j_pix_b_nets = {str(i+1): (net_map[f"IN_{32+i}"], f"IN_{32+i}") for i in range(32)}
    pcb.append(fp_header_2x16("J_PIXELS_B", "Pixels_32_63_In", 72.0, 5.08, 0, j_pix_b_nets))

    # 3. J_PWR_IN at X = 30.0, Y = 94.92 (1x06 header for power)
    j_pwr_nets = {
        "1": (net_map["+12V"], "+12V"), "2": (net_map["+12V"], "+12V"),
        "3": (net_map["GND"], "GND"), "4": (net_map["GND"], "GND"),
        "5": (net_map["-12V"], "-12V"), "6": (net_map["-12V"], "-12V")
    }
    pcb.append(fp_header_1x06("J_PWR_IN", "Main_Power_In", 30.0, 94.92, 0, j_pwr_nets))

    # 4. J_SCORES_OUT at X = 70.0, Y = 94.92 (2x05 header for SCORE_0..9)
    j_score_nets = {str(c+1): (net_map[f"SCORE_{c}"], f"SCORE_{c}") for c in range(10)}
    pcb.append(fp_header_2x05("J_SCORES_OUT", "Scores_0_9_Out", 70.0, 94.92, 0, j_score_nets))

    # Deterministic Routing
    cx = 50.0
    x_start = - (17.5 * PITCH) # -44.45 mm

    # 1. Vertical IN_0..IN_31 Bus on F.Cu across Slots 0..3
    ya_slot0 = y_slots[0] - 2.54 # 12.46 mm
    ya_slot3 = y_slots[3] - 2.54 # 54.46 mm
    for i in range(32):
        px = cx + x_start + i * PITCH
        nid = net_map[f"IN_{i}"]
        name = f"IN_{i}"
        pcb.append(make_segment(px, ya_slot0, px, ya_slot3, 0.25, "F.Cu", name, nid))
        # Connection up to J_PIXELS_A header
        hdr_x = 28.0 - (7.5 * PITCH) + (i // 2) * PITCH
        hdr_y = 5.08 + (-1.27 if (i % 2 == 0) else 1.27)
        pcb.append(make_segment(px, ya_slot0, hdr_x, 8.0, 0.25, "F.Cu", name, nid))
        pcb.append(make_segment(hdr_x, 8.0, hdr_x, hdr_y, 0.25, "F.Cu", name, nid))

    # 2. Vertical IN_32..IN_63 Bus on B.Cu across Slots 0..3
    yb_slot0 = y_slots[0] + 2.54 # 17.54 mm
    yb_slot3 = y_slots[3] + 2.54 # 59.54 mm
    for i in range(32):
        px = cx + x_start + i * PITCH
        nid = net_map[f"IN_{32+i}"]
        name = f"IN_{32+i}"
        pcb.append(make_segment(px, yb_slot0, px, yb_slot3, 0.25, "B.Cu", name, nid))
        # Connection up to J_PIXELS_B header
        hdr_x = 72.0 - (7.5 * PITCH) + (i // 2) * PITCH
        hdr_y = 5.08 + (-1.27 if (i % 2 == 0) else 1.27)
        pcb.append(make_segment(px, yb_slot0, hdr_x, 8.0, 0.25, "B.Cu", name, nid))
        pcb.append(make_segment(hdr_x, 8.0, hdr_x, hdr_y, 0.25, "B.Cu", name, nid))

    # 3. Interconnect V_SUM_0..15 from Slots 0..3 to Slot 4 (DC2)
    ya_slot4 = y_slots[4] - 2.54 # 68.46 mm
    corridor_y_base = 61.5
    for s_idx in range(4):
        k_base = s_idx * 4
        src_ya = y_slots[s_idx] - 2.54
        for k_rel in range(4):
            k = k_base + k_rel
            src_px = cx + x_start + (32 + k_rel) * PITCH
            dst_px = cx + x_start + k * PITCH
            nid = net_map[f"V_SUM_{k}"]
            name = f"V_SUM_{k}"
            y_corridor = corridor_y_base + k * 0.40
            pcb.append(make_segment(src_px, src_ya, src_px, y_corridor, 0.25, "In2.Cu", name, nid))
            pcb.append(make_via(src_px, src_ya, 0.6, 0.3, name, nid))
            pcb.append(make_segment(src_px, y_corridor, dst_px, y_corridor, 0.25, "In2.Cu", name, nid))
            pcb.append(make_segment(dst_px, y_corridor, dst_px, ya_slot4, 0.25, "In2.Cu", name, nid))
            pcb.append(make_via(dst_px, ya_slot4, 0.6, 0.3, name, nid))

    # 4. Interconnect ACT_0..15 from Slot 4 (DC2) to Slot 5 (DC3)
    yb_slot4 = y_slots[4] + 2.54 # 73.54 mm
    ya_slot5 = y_slots[5] - 2.54 # 82.46 mm
    for k in range(16):
        px = cx + x_start + k * PITCH
        nid = net_map[f"ACT_{k}"]
        name = f"ACT_{k}"
        pcb.append(make_segment(px, yb_slot4, px, ya_slot5, 0.25, "F.Cu", name, nid))

    # 5. Interconnect SCORE_0..9 from Slot 5 (DC3) to J_SCORES_OUT
    yb_slot5 = y_slots[5] + 2.54 # 87.54 mm
    for c in range(10):
        src_px = cx + x_start + c * PITCH
        nid = net_map[f"SCORE_{c}"]
        name = f"SCORE_{c}"
        hdr_x = 70.0 - (2.0 * PITCH) + (c // 2) * PITCH
        hdr_y = 94.92 + (-1.27 if (c % 2 == 0) else 1.27)
        pcb.append(make_segment(src_px, yb_slot5, src_px, 90.5, 0.25, "F.Cu", name, nid))
        pcb.append(make_segment(src_px, 90.5, hdr_x, 92.5, 0.25, "F.Cu", name, nid))
        pcb.append(make_segment(hdr_x, 92.5, hdr_x, hdr_y, 0.25, "F.Cu", name, nid))

    # 6. Power Distribution (+12V on B33, -12V on B34, GND on B35..B36)
    p_b33 = cx + x_start + 32 * PITCH # 86.83 mm
    p_b34 = cx + x_start + 33 * PITCH # 89.37 mm
    p_b35 = cx + x_start + 34 * PITCH # 91.91 mm
    p_b36 = cx + x_start + 35 * PITCH # 94.45 mm

    # +12V Bus on B.Cu
    pcb.append(make_segment(p_b33, y_slots[0] + 2.54, p_b33, y_slots[5] + 2.54, 0.40, "B.Cu", "+12V", 2))
    pcb.append(make_segment(p_b33, y_slots[5] + 2.54, 30.0 - 2.5 * PITCH, 94.92, 0.40, "B.Cu", "+12V", 2))

    # -12V Bus on B.Cu
    pcb.append(make_segment(p_b34, y_slots[0] + 2.54, p_b34, y_slots[5] + 2.54, 0.40, "B.Cu", "-12V", 3))
    pcb.append(make_segment(p_b34, y_slots[5] + 2.54, 30.0 + 2.5 * PITCH, 94.92, 0.40, "B.Cu", "-12V", 3))

    # GND thermal vias
    for ys in y_slots:
        yb = ys + 2.54
        pcb.append(make_via(p_b35, yb, 0.7, 0.4, "GND", 1))
        pcb.append(make_via(p_b36, yb, 0.7, 0.4, "GND", 1))
    pcb.append(make_via(30.0 - 0.5 * PITCH, 94.92, 0.7, 0.4, "GND", 1))
    pcb.append(make_via(30.0 + 0.5 * PITCH, 94.92, 0.7, 0.4, "GND", 1))

    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated 72P Motherboard: {board_file}")


# =========================================================================
# 5. Generator for 6-Blade Vertical Rack 3D VRML Models & Master Assembly
# =========================================================================
def generate_blade_wrl(filename, label_text, r=0.08, g=0.32, b=0.18, has_leds=False):
    blade_path = os.path.join(WORKSPACE_DIR, filename)
    led_wrl = ""
    if has_leds:
        led_shapes = []
        for c in range(10):
            lx = -28.8 + c * 6.40
            led_shapes.append(f"""    Transform {{
      translation {lx:.2f} 0.90 94.0
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.95 0.85 0.10
              emissiveColor 0.80 0.70 0.10
              shininess 0.9
            }}
          }}
          geometry Box {{ size 2.0 1.2 2.0 }}
        }}
      ]
    }}""")
        led_wrl = "\n".join(led_shapes)

    wrl = f"""#VRML V2.0 utf8
# Exact 94.28mm x 100.0mm Daughtercard Blade standing vertically in 72P Slot
Transform {{
  children [
    # PCB Blade
    Transform {{
      translation 0 0 56.60
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor {r:.2f} {g:.2f} {b:.2f}
              specularColor 0.3 0.4 0.3
              shininess 0.5
            }}
          }}
          geometry Box {{ size {DIM_B:.2f} 1.57 100.0 }}
        }}
      ]
    }},
    # Silkscreen Text Banner on Daughtercard
    Transform {{
      translation 0 0.81 72.0
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.95 0.95 0.95
              specularColor 0.5 0.5 0.5
              shininess 0.2
            }}
          }}
          geometry Box {{ size 84.0 0.04 14.0 }}
        }}
      ]
    }},
    # Gold Contact Fingers (Front Row wiping inside socket)
    Transform {{
      translation 0 0.80 10.60
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }}
          }}
          geometry Box {{ size {DIM_A:.2f} 0.04 {PAD_HEIGHT:.2f} }}
        }}
      ]
    }},
    # Gold Contact Fingers (Back Row wiping inside socket)
    Transform {{
      translation 0 -0.80 10.60
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }}
          }}
          geometry Box {{ size {DIM_A:.2f} 0.04 {PAD_HEIGHT:.2f} }}
        }}
      ]
    }}
{led_wrl}
  ]
}}
"""
    with open(blade_path, "w") as f:
        f.write(wrl)
    return blade_path

def build_complete_assembly():
    # Generate 6 custom 3D blades
    wrl_dc1a = generate_blade_wrl("blade_dc1a.wrl", "DC1A: L1 NEURONS 0..3", 0.08, 0.32, 0.22)
    wrl_dc1b = generate_blade_wrl("blade_dc1b.wrl", "DC1B: L1 NEURONS 4..7", 0.08, 0.32, 0.22)
    wrl_dc1c = generate_blade_wrl("blade_dc1c.wrl", "DC1C: L1 NEURONS 8..11", 0.08, 0.32, 0.22)
    wrl_dc1d = generate_blade_wrl("blade_dc1d.wrl", "DC1D: L1 NEURONS 12..15", 0.08, 0.32, 0.22)
    wrl_dc2  = generate_blade_wrl("blade_dc2.wrl",  "DC2: 16-CH ACTIVE RELU", 0.12, 0.30, 0.35)
    wrl_dc3  = generate_blade_wrl("blade_dc3.wrl",  "DC3: L2 WEIGHTS + 10-WAY WTA", 0.35, 0.22, 0.10, has_leds=True)
    
    blade_wrls = [wrl_dc1a, wrl_dc1b, wrl_dc1c, wrl_dc1d, wrl_dc2, wrl_dc3]
    build_motherboard(filename="full_system_assembly.kicad_pcb", title="Full System 6-Blade Vertical Rack Assembly", blade_wrls=blade_wrls)
    print("Generated Complete 6-Blade Assembly Board: full_system_assembly.kicad_pcb")


# =========================================================================
# MAIN EXECUTION ENTRY POINT
# =========================================================================
if __name__ == "__main__":
    print("=================================================================")
    print("BUILDING COMPLETE 72-PIN STRAIGHT EDGE CARD MODULAR ANALOG SYSTEM")
    print("=================================================================")
    
    # 1. Generate 4 Layer 1 Synaptic Weight Daughtercards (DC1A..DC1D)
    build_dc1_board("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A: Layer 1 Synaptic Weights (Neurons 0..3)", range(0, 4))
    build_dc1_board("daughtercard1b_weights_l1.kicad_pcb", "Daughtercard 1B: Layer 1 Synaptic Weights (Neurons 4..7)", range(4, 8))
    build_dc1_board("daughtercard1c_weights_l1.kicad_pcb", "Daughtercard 1C: Layer 1 Synaptic Weights (Neurons 8..11)", range(8, 12))
    build_dc1_board("daughtercard1d_weights_l1.kicad_pcb", "Daughtercard 1D: Layer 1 Synaptic Weights (Neurons 12..15)", range(12, 16))
    
    # 2. Generate Layer 1 Active Precision ReLU Daughtercard (DC2)
    build_dc2_board("daughtercard2_relu_l1.kicad_pcb", "Daughtercard 2: 16-Channel Active Precision ReLU")
    
    # 3. Generate Layer 2 Synaptic Weights + Winner-Take-All Daughtercard (DC3)
    build_dc3_board("daughtercard3_weights_l2_wta.kicad_pcb", "Daughtercard 3: L2 Synaptic Weights + 10-Way Winner-Take-All")
    
    # 4. Generate 6-Slot Straight 72P Motherboard Backplane
    build_motherboard("motherboard.kicad_pcb", "Motherboard: 6-Slot Straight 72P Modular Backplane")
    
    # 5. Generate Master 6-Blade Assembled Rack Board
    build_complete_assembly()
    
    print("=================================================================")
    print("ALL 7 BOARDS + 6-BLADE ASSEMBLY GENERATED SUCCESSFULLY!")
    print("=================================================================")


