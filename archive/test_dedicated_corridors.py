import os, json, uuid, subprocess, re

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
PITCH = 2.54
PAD_WIDTH = 1.80
PAD_HEIGHT = 8.00
DIM_A = 100.0
DIM_B = 94.28

def make_uuid():
    return str(uuid.uuid4())

def get_header(title, nets):
    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in sorted(nets.items()) if nid > 0])
    return f"""(kicad_pcb (version 20221018) (generator "analog_nn_clean_router")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "{title}")
    (company "Discrete Analog Neural Network System")
    (rev "v6.2 - Dedicated Corridors")
    (date "2026-09-14")
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
        f'  (gr_line (start 1.0 91.0) (end {width-1.0:.2f} 91.0) (stroke (width 0.25) (type default)) (layer "F.SilkS") (uuid "{make_uuid()}"))',
        f'  (gr_text "<< INSERTION STOP LINE (9.0mm Socket Depth) >>" (at {width/2:.2f} 89.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 1.1 1.1) (thickness 0.15))))',
    ]
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
    cx = card_width / 2.0
    x_start = - (17.5 * PITCH)
    pads = []
    for i in range(36):
        px = x_start + i * PITCH
        p_num_a = f"A{i+1}"
        nid_a, nname_a = pin_nets_a.get(p_num_a, (0, ""))
        pads.append(f'    (pad "{p_num_a}" smd roundrect (at {px:.3f} 0) (size {PAD_WIDTH:.2f} {PAD_HEIGHT:.2f}) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2) (net {nid_a} "{nname_a}"))')
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
    (fp_line (start -0.25 -0.7) (end 0.25 -0.7) (stroke (width 0.12) (type solid)) (layer "{silk}"))
    (fp_line (start -0.25 0.7) (end 0.25 0.7) (stroke (width 0.12) (type solid)) (layer "{silk}"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD10_3DMODEL_DIR}}/Resistor_SMD.3dshapes/R_0805_2012Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
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
    (fp_line (start -0.25 -0.7) (end 0.25 -0.7) (stroke (width 0.12) (type solid)) (layer "{silk}"))
    (fp_line (start -0.25 0.7) (end 0.25 0.7) (stroke (width 0.12) (type solid)) (layer "{silk}"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD10_3DMODEL_DIR}}/Capacitor_SMD.3dshapes/C_0805_2012Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
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
    (fp_circle (center -2.0 -4.0) (end -1.7 -4.0) (stroke (width 0.15) (type solid)) (fill solid) (layer "{silk}"))
{pads_str}
    (model "${{KICAD10_3DMODEL_DIR}}/Package_SO.3dshapes/SOIC-14_3.9x8.7mm_P1.27mm.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
  )"""

def make_segment(x1, y1, x2, y2, width=0.25, layer="F.Cu", net_name="", net_id=0):
    return f'  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width}) (layer "{layer}") (net {net_id}) (uuid "{make_uuid()}"))'

def make_via(x, y, size=0.6, drill=0.3, net_name="", net_id=0, layers=('F.Cu', 'B.Cu')):
    l_str = f'"{layers[0]}" "{layers[1]}"'
    return f'  (via (at {x:.4f} {y:.4f}) (size {size}) (drill {drill}) (layers {l_str}) (net {net_id}) (uuid "{make_uuid()}"))'

def build_test():
    board_file = "/Users/lucaszhang/pcbai/daughtercard1a_weights_l1.kicad_pcb"
    with open(os.path.join(WORKSPACE_DIR, "weights_layer1.json")) as f:
        l1 = json.load(f)
    neuron_range = range(0, 4)

    nets = {0: "", 1: "GND", 2: "+12V", 3: "-12V", 4: "+5V_REF", 5: "-5V_REF"}
    for j in range(16):
        nets[10 + j] = f"V_SUM_{j}"
        nets[30 + j] = f"INV_N{j}"
    for i in range(64):
        nets[100 + i] = f"IN_{i}"

    pcb = [
        get_header("Daughtercard 1A", nets),
        get_daughtercard_outline_and_mounts(DIM_B, DIM_A)
    ]

    pin_nets_a = {}
    pin_nets_b = {}
    for i in range(32):
        pin_nets_a[f"A{i+1}"] = (100 + i, f"IN_{i}")
        pin_nets_b[f"B{i+1}"] = (100 + 32 + i, f"IN_{32+i}")
    for idx, j in enumerate(neuron_range):
        pin_nets_a[f"A{33+idx}"] = (10 + j, f"V_SUM_{j}")
    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (1, "GND")
    pin_nets_b["B36"] = (1, "GND")

    pcb.append(fp_edge_fingers_72p(pin_nets_a, pin_nets_b, DIM_B))

    row_y = {
        0: 17.0, 1: 25.0, 2: 33.0, 3: 41.0,
        4: 54.0, 5: 62.0, 6: 70.0, 7: 78.0
    }
    cx = DIM_B / 2.0
    x_start = cx - (17.5 * PITCH) # 2.69 mm

    for local_neuron_idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        r_top = local_neuron_idx
        y_top = row_y[r_top]
        for i in range(32):
            rx = x_start + i * PITCH
            r_val = n_info["inputs"][i]["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_top, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

        r_bot = local_neuron_idx + 4
        y_bot = row_y[r_bot]
        for i in range(32, 64):
            col_idx = i - 32
            rx = x_start + col_idx * PITCH
            r_val = n_info["inputs"][i]["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_bot, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

    # U1 placed at X = 87.5, Y = 47.5
    u1_x = 87.5
    u1_y = 47.5
    ic_pin_nets = {
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
    pcb.append(fp_soic14("U1", "TL074", u1_x, u1_y, 0, "F.Cu", ic_pin_nets))

    # 4-LAYER MATRIX ROUTING WITH 1.2mm HORIZONTAL OFFSET:
    for col in range(32):
        col_x = x_start + col * PITCH

        # Top Bank (IN_0..IN_31):
        in_top_idx = col
        in_top_nid = 100 + in_top_idx
        in_top_name = f"IN_{in_top_idx}"
        x_top = col_x - 0.6

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
        x_bot = col_x + 0.6

        pcb.append(make_segment(col_x, 92.0, x_bot, 90.0, 0.25, "B.Cu", in_bot_name, in_bot_nid))

        y_bot_limit = row_y[4] + 1.8
        pcb.append(make_segment(x_bot, 90.0, x_bot, y_bot_limit, 0.25, "B.Cu", in_bot_name, in_bot_nid))

        for r in [4, 5, 6, 7]:
            vy = row_y[r] + 1.8
            py = row_y[r] + 0.95
            pcb.append(make_via(x_bot, vy, 0.6, 0.3, in_bot_name, in_bot_nid))
            pcb.append(make_segment(x_bot, vy, col_x, py, 0.25, "F.Cu", in_bot_name, in_bot_nid))

    # Summing Rows across Pad 2 (Y_row - 0.95)
    # Split summing trunks:
    # N0 (Row 0 & 4): tx = 82.0 (left side)
    # N1 (Row 1 & 5): tx = 82.8 (left side)
    # N2 (Row 2 & 6): tx = 92.2 (right side)
    # N3 (Row 3 & 7): tx = 93.0 (right side)
    trunk_x = {0: 82.0, 1: 82.8, 2: 92.2, 3: 93.0}
    for r in range(8):
        y_sum = row_y[r] - 0.95
        local_neuron = r % 4
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        x_left = x_start
        x_right = x_start + 31 * PITCH
        pcb.append(make_segment(x_left, y_sum, x_right, y_sum, 0.25, "F.Cu", sum_name, sum_nid))

        tx = trunk_x[local_neuron]
        pcb.append(make_segment(x_right, y_sum, tx, y_sum, 0.25, "F.Cu", sum_name, sum_nid))
        pcb.append(make_via(tx, y_sum, 0.6, 0.3, sum_name, sum_nid))

    # Summing vertical trunks on In2.Cu:
    for local_neuron in range(4):
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"
        tx = trunk_x[local_neuron]
        y_top_sum = row_y[local_neuron] - 0.95
        y_bot_sum = row_y[local_neuron + 4] - 0.95

        pcb.append(make_segment(tx, y_top_sum, tx, y_bot_sum, 0.25, "In2.Cu", sum_name, sum_nid))

    # GND stitching vias for Pins 3, 5, 10, 12 with dedicated clear offsets
    pcb.append(make_via(u1_x - 4.2, u1_y - 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x - 2.7, u1_y - 1.27, u1_x - 4.2, u1_y - 1.27, 0.25, "F.Cu", "GND", 1))

    pcb.append(make_via(u1_x - 4.2, u1_y + 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x - 2.7, u1_y + 1.27, u1_x - 4.2, u1_y + 1.27, 0.25, "F.Cu", "GND", 1))

    pcb.append(make_via(u1_x + 4.2, u1_y + 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x + 2.7, u1_y + 1.27, u1_x + 4.2, u1_y + 1.27, 0.25, "F.Cu", "GND", 1))

    pcb.append(make_via(u1_x + 4.2, u1_y - 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x + 2.7, u1_y - 1.27, u1_x + 4.2, u1_y - 1.27, 0.25, "F.Cu", "GND", 1))

    # Feedback and Bias Resistors:
    # N0 (top-left): Pin 1 OUT (84.8, 43.69), Pin 2 IN- (84.8, 44.96)
    # Trunk 0 at 82.0. Tap via at (82.0, 44.96) connects to Pin 2
    pcb.append(make_via(82.0, 44.96, 0.6, 0.3, f"INV_N{neuron_range[0]}", 30 + neuron_range[0]))
    pcb.append(make_segment(82.0, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{neuron_range[0]}", 30 + neuron_range[0]))
    # Rf_N0 placed at (78.0, 43.69). Pad 1 at 77.05, Pad 2 at 78.95
    pcb.append(fp_resistor_0805(f"Rf_N{neuron_range[0]}", "10k", 78.0, 43.69, 0, "F.Cu", 30 + neuron_range[0], f"INV_N{neuron_range[0]}", 10 + neuron_range[0], f"V_SUM_{neuron_range[0]}"))
    pcb.append(make_segment(78.95, 43.69, u1_x - 2.7, 43.69, 0.25, "F.Cu", f"V_SUM_{neuron_range[0]}", 10 + neuron_range[0]))
    pcb.append(make_segment(77.05, 43.69, 77.05, 44.96, 0.25, "F.Cu", f"INV_N{neuron_range[0]}", 30 + neuron_range[0]))
    pcb.append(make_segment(77.05, 44.96, 82.0, 44.96, 0.25, "F.Cu", f"INV_N{neuron_range[0]}", 30 + neuron_range[0]))
    # Rb_N0 at (74.0, 44.96)
    b0_nid = 5 if l1["weights"][neuron_range[0]]["bias_rail"] == "-5V_REF" else 4
    b0_name = l1["weights"][neuron_range[0]]["bias_rail"]
        pcb.append(fp_resistor_0805(f"Rb_N{neuron_range[0]}", l1["weights"][neuron_range[0]]["bias_resistor_str"], 74.5, 44.96, 0, "F.Cu", b0_nid, b0_name, 30 + neuron_range[0], f"INV_N{neuron_range[0]}"))
    pcb.append(make_segment(75.45, 44.96, 77.05, 44.96, 0.25, "F.Cu", f"INV_N{neuron_range[0]}", 30 + neuron_range[0]))
    pcb.append(make_via(72.5, 44.96, 0.6, 0.3, b0_name, b0_nid))
    pcb.append(make_segment(72.5, 44.96, 73.55, 44.96, 0.25, "F.Cu", b0_name, b0_nid))

    # N1 (bot-left): Pin 7 OUT (84.8, 51.31), Pin 6 IN- (84.8, 50.04)
    # Trunk 1 at 82.8. Tap via at (82.8, 50.04)
    pcb.append(make_via(82.8, 50.04, 0.6, 0.3, f"INV_N{neuron_range[1]}", 30 + neuron_range[1]))
    pcb.append(make_segment(82.8, 50.04, u1_x - 2.7, 50.04, 0.25, "F.Cu", f"INV_N{neuron_range[1]}", 30 + neuron_range[1]))
    # Rf_N1 at (78.0, 51.31)
    pcb.append(fp_resistor_0805(f"Rf_N{neuron_range[1]}", "10k", 78.0, 51.31, 0, "F.Cu", 30 + neuron_range[1], f"INV_N{neuron_range[1]}", 10 + neuron_range[1], f"V_SUM_{neuron_range[1]}"))
    pcb.append(make_segment(78.95, 51.31, u1_x - 2.7, 51.31, 0.25, "F.Cu", f"V_SUM_{neuron_range[1]}", 10 + neuron_range[1]))
    pcb.append(make_segment(77.05, 51.31, 77.05, 50.04, 0.25, "F.Cu", f"INV_N{neuron_range[1]}", 30 + neuron_range[1]))
    pcb.append(make_segment(77.05, 50.04, 82.8, 50.04, 0.25, "F.Cu", f"INV_N{neuron_range[1]}", 30 + neuron_range[1]))
    # Rb_N1 at (74.0, 50.04)
    b1_nid = 5 if l1["weights"][neuron_range[1]]["bias_rail"] == "-5V_REF" else 4
    b1_name = l1["weights"][neuron_range[1]]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{neuron_range[1]}", l1["weights"][neuron_range[1]]["bias_resistor_str"], 74.0, 50.04, 0, "F.Cu", b1_nid, b1_name, 30 + neuron_range[1], f"INV_N{neuron_range[1]}"))
    pcb.append(make_segment(74.95, 50.04, 77.05, 50.04, 0.25, "F.Cu", f"INV_N{neuron_range[1]}", 30 + neuron_range[1]))
    pcb.append(make_via(73.05, 50.04, 0.6, 0.3, b1_name, b1_nid))

    # N2 (bot-right): Pin 8 OUT (90.2, 51.31), Pin 9 IN- (90.2, 50.04)
    # Trunk 2 at 92.2. Tap via at (92.2, 50.04)
    pcb.append(make_via(92.2, 50.04, 0.6, 0.3, f"INV_N{neuron_range[2]}", 30 + neuron_range[2]))
    pcb.append(make_segment(92.2, 50.04, u1_x + 2.7, 50.04, 0.25, "F.Cu", f"INV_N{neuron_range[2]}", 30 + neuron_range[2]))
    # Rf_N2 at (87.5, 56.0) rot=0
    pcb.append(fp_resistor_0805(f"Rf_N{neuron_range[2]}", "10k", 87.5, 56.0, 0, "F.Cu", 30 + neuron_range[2], f"INV_N{neuron_range[2]}", 10 + neuron_range[2], f"V_SUM_{neuron_range[2]}"))
    pcb.append(make_segment(88.45, 56.0, u1_x + 2.7, 56.0, 0.25, "F.Cu", f"V_SUM_{neuron_range[2]}", 10 + neuron_range[2]))
    pcb.append(make_segment(u1_x + 2.7, 56.0, u1_x + 2.7, 51.31, 0.25, "F.Cu", f"V_SUM_{neuron_range[2]}", 10 + neuron_range[2]))
    pcb.append(make_segment(86.55, 56.0, 86.55, 53.5, 0.25, "F.Cu", f"INV_N{neuron_range[2]}", 30 + neuron_range[2]))
    pcb.append(make_segment(86.55, 53.5, u1_x + 2.7, 53.5, 0.25, "F.Cu", f"INV_N{neuron_range[2]}", 30 + neuron_range[2]))
    pcb.append(make_segment(u1_x + 2.7, 53.5, u1_x + 2.7, 50.04, 0.25, "F.Cu", f"INV_N{neuron_range[2]}", 30 + neuron_range[2]))
    # Rb_N2 at (87.5, 59.0) rot=0
    b2_nid = 5 if l1["weights"][neuron_range[2]]["bias_rail"] == "-5V_REF" else 4
    b2_name = l1["weights"][neuron_range[2]]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{neuron_range[2]}", l1["weights"][neuron_range[2]]["bias_resistor_str"], 87.5, 59.0, 0, "F.Cu", b2_nid, b2_name, 30 + neuron_range[2], f"INV_N{neuron_range[2]}"))
    pcb.append(make_segment(88.45, 59.0, 88.45, 56.0, 0.25, "F.Cu", f"INV_N{neuron_range[2]}", 30 + neuron_range[2]))
    pcb.append(make_via(86.55, 59.0, 0.6, 0.3, b2_name, b2_nid))

    # N3 (top-right): Pin 14 OUT (90.2, 43.69), Pin 13 IN- (90.2, 44.96)
    # Trunk 3 at 93.0. Tap via at (93.0, 44.96)
    pcb.append(make_via(93.0, 44.96, 0.6, 0.3, f"INV_N{neuron_range[3]}", 30 + neuron_range[3]))
    pcb.append(make_segment(93.0, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{neuron_range[3]}", 30 + neuron_range[3]))
    # Rf_N3 at (87.5, 39.0) rot=0
    pcb.append(fp_resistor_0805(f"Rf_N{neuron_range[3]}", "10k", 87.5, 39.0, 0, "F.Cu", 30 + neuron_range[3], f"INV_N{neuron_range[3]}", 10 + neuron_range[3], f"V_SUM_{neuron_range[3]}"))
    pcb.append(make_segment(88.45, 39.0, u1_x + 2.7, 39.0, 0.25, "F.Cu", f"V_SUM_{neuron_range[3]}", 10 + neuron_range[3]))
    pcb.append(make_segment(u1_x + 2.7, 39.0, u1_x + 2.7, 43.69, 0.25, "F.Cu", f"V_SUM_{neuron_range[3]}", 10 + neuron_range[3]))
    pcb.append(make_segment(86.55, 39.0, 86.55, 41.5, 0.25, "F.Cu", f"INV_N{neuron_range[3]}", 30 + neuron_range[3]))
    pcb.append(make_segment(86.55, 41.5, u1_x + 2.7, 41.5, 0.25, "F.Cu", f"INV_N{neuron_range[3]}", 30 + neuron_range[3]))
    pcb.append(make_segment(u1_x + 2.7, 41.5, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{neuron_range[3]}", 30 + neuron_range[3]))
    # Rb_N3 at (87.5, 36.0) rot=0
    b3_nid = 5 if l1["weights"][neuron_range[3]]["bias_rail"] == "-5V_REF" else 4
    b3_name = l1["weights"][neuron_range[3]]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{neuron_range[3]}", l1["weights"][neuron_range[3]]["bias_resistor_str"], 87.5, 36.0, 0, "F.Cu", b3_nid, b3_name, 30 + neuron_range[3], f"INV_N{neuron_range[3]}"))
    pcb.append(make_segment(88.45, 36.0, 88.45, 39.0, 0.25, "F.Cu", f"INV_N{neuron_range[3]}", 30 + neuron_range[3]))
    pcb.append(make_via(86.55, 36.0, 0.6, 0.3, b3_name, b3_nid))

    # Dedicated vertical output channels on B.Cu:
    # OUT 0: X = 83.8
    # OUT 1: X = 84.8
    # OUT 2: X = 90.2
    # OUT 3: X = 91.2
    out_specs = [
        (0, u1_x - 2.7, 43.69, 83.8, x_start + 32 * PITCH),
        (1, u1_x - 2.7, 51.31, 84.8, x_start + 33 * PITCH),
        (2, u1_x + 2.7, 51.31, 90.2, x_start + 34 * PITCH),
        (3, u1_x + 2.7, 43.69, 91.2, x_start + 35 * PITCH)
    ]
    for idx, px, py, ch_x, fx in out_specs:
        j = neuron_range[idx]
        v_nid = 10 + j
        v_name = f"V_SUM_{j}"

        # Connect pin to via
        via_y = py - 1.0 if idx in [0, 3] else py + 1.0
        pcb.append(make_segment(px, py, ch_x, via_y, 0.25, "F.Cu", v_name, v_nid))
        pcb.append(make_via(ch_x, via_y, 0.6, 0.3, v_name, v_nid))
        # Highway on B.Cu down to Y = 87.0
        pcb.append(make_segment(ch_x, via_y, ch_x, 87.0, 0.25, "B.Cu", v_name, v_nid))
        # Via to F.Cu and connection to finger
        pcb.append(make_via(ch_x, 87.0, 0.6, 0.3, v_name, v_nid))
        pcb.append(make_segment(ch_x, 87.0, fx, 92.0, 0.25, "F.Cu", v_name, v_nid))

    # Power decoupling & routing:
    # Pin 4 (+12V) is at (u1_x - 2.7, 47.5). Decoupling cap C_U1P at (80.0, 47.5) rot=0
    # Pad 1 (-0.95) is 79.05 = +12V. Pad 2 (+0.95) is 80.95 = GND.
    # Feed +12V to Pad 1 (79.05). Connect Pad 2 (80.95) to GND via.
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 80.0, 47.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(make_segment(u1_x - 2.7, 47.5, 79.05, 47.5, 0.35, "F.Cu", "+12V", 2))
    pcb.append(make_via(80.95, 47.5, 0.6, 0.3, "GND", 1))
    # +12V power feed from B33 (x_start + 32 * PITCH) on In2.Cu along X = 80.0
    pcb.append(make_via(79.05, 47.5, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(79.05, 47.5, 79.05, 89.0, 0.35, "In2.Cu", "+12V", 2))
    pcb.append(make_via(79.05, 89.0, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(79.05, 89.0, x_start + 32 * PITCH, 92.0, 0.35, "B.Cu", "+12V", 2))

    # Pin 11 (-12V) is at (u1_x + 2.7, 47.5). Decoupling cap C_U1N at (95.0, 47.5) rot=0
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 95.0, 47.5, 0, "F.Cu", 3, "-12V", 1, "GND"))
    pcb.append(make_segment(u1_x + 2.7, 47.5, 94.05, 47.5, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_via(95.95, 47.5, 0.6, 0.3, "GND", 1))
    # -12V power feed from B34 (x_start + 33 * PITCH) on In2.Cu:
    pcb.append(make_via(94.05, 47.5, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(94.05, 47.5, 94.05, 89.0, 0.35, "In2.Cu", "-12V", 3))
    pcb.append(make_via(94.05, 89.0, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(94.05, 89.0, x_start + 33 * PITCH, 92.0, 0.35, "B.Cu", "-12V", 3))

    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))
    print("Generated test board with dedicated corridors.")

build_test()
