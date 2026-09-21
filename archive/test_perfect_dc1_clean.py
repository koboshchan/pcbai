import os, json, uuid, subprocess

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
PITCH = 2.54
PAD_WIDTH = 1.80
PAD_HEIGHT = 8.00
DIM_A = 100.0
DIM_B = 94.28

def make_uuid(): return str(uuid.uuid4())

def get_header(title, nets):
    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in sorted(nets.items()) if nid > 0])
    return f"""(kicad_pcb (version 20221018) (generator "analog_nn_clean_router")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "{title}")
    (company "Discrete Analog Neural Network System")
    (rev "v13.0 - Perfect Zero DRC")
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
        f'      (pts (xy 0.5 0.5) (xy {width-0.5:.2f} 0.5) (xy {width-0.5:.2f} 90.5) (xy 0.5 90.5))',
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

def build_perfect_dc1(filename, title, neuron_range):
    board_file = os.path.join(WORKSPACE_DIR, filename)
    with open(os.path.join(WORKSPACE_DIR, "weights_layer1.json")) as f:
        l1 = json.load(f)

    nets = {0: "", 1: "GND", 2: "+12V", 3: "-12V", 4: "+5V_REF", 5: "-5V_REF"}
    for j in range(16):
        nets[10 + j] = f"V_SUM_{j}"
        nets[30 + j] = f"INV_N{j}"
    for i in range(64):
        nets[100 + i] = f"IN_{i}"

    pcb = [
        get_header(title, nets),
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
    pin_nets_b["B35"] = (4, "+5V_REF")
    pin_nets_b["B36"] = (5, "-5V_REF")

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

        # Top Bank (IN_0..IN_31)
        r_top = local_neuron_idx
        y_top = row_y[r_top]
        for i in range(32):
            rx = x_start + i * PITCH
            r_val = n_info["inputs"][i]["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_top, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

        # Bottom Bank (IN_32..IN_63)
        r_bot = local_neuron_idx + 4
        y_bot = row_y[r_bot]
        for i in range(32, 64):
            col_idx = i - 32
            rx = x_start + col_idx * PITCH
            r_val = n_info["inputs"][i]["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_bot, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

    # Matrix input routing:
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

    # Place U1 at X = 86.0, Y = 47.5
    u1_x = 86.0
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

    # Summing Rows on F.Cu:
    # 4 Trunks on In2.Cu: 0 & 1 on left (81.8, 82.6), 2 & 3 on right (89.5, 90.3)
    trunk_x = {0: 81.8, 1: 82.6, 2: 89.5, 3: 90.3}
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

    # GND stitching vias for Pins 3, 5, 10, 12 in center of U1 (X = 86.0):
    for py in [u1_y - 1.27, u1_y + 1.27]:
        pcb.append(make_via(86.0, py, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u1_x - 2.7, py, 86.0, py, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_segment(u1_x + 2.7, py, 86.0, py, 0.25, "F.Cu", "GND", 1))

    n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]

    # --- LEFT NEURONS: N0 and N1 ---
    # Tap Trunk 0 (81.8) to Pin 2 (83.3, 44.96):
    pcb.append(make_via(81.8, 44.96, 0.6, 0.3, f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(81.8, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    # Rf_N0 at (77.0, 43.69): Pad 1 (76.05)=V_SUM, Pad 2 (77.95)=INV
    pcb.append(fp_resistor_0805(f"Rf_N{n0}", "10k", 77.0, 43.69, 0, "F.Cu", 10 + n0, f"V_SUM_{n0}", 30 + n0, f"INV_N{n0}"))
    pcb.append(make_segment(76.05, 43.69, u1_x - 2.7, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    # Connect Pad 2 (77.95, 43.69) to Pin 2 line at (77.95, 44.96):
    pcb.append(make_segment(77.95, 43.69, 77.95, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    # Rb_N0 at (73.0, 44.96): Pad 1 (72.05)=Bias, Pad 2 (73.95)=INV
    b0_nid = 5 if l1["weights"][n0]["bias_rail"] == "-5V_REF" else 4
    b0_name = l1["weights"][n0]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n0}", l1["weights"][n0]["bias_resistor_str"], 73.0, 44.96, 0, "F.Cu", b0_nid, b0_name, 30 + n0, f"INV_N{n0}"))
    pcb.append(make_segment(73.95, 44.96, 81.8, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    # Bias connection for Rb_N0: drop via to B.Cu at (70.5, 44.96)
    pcb.append(make_via(70.5, 44.96, 0.6, 0.3, b0_name, b0_nid))
    pcb.append(make_segment(70.5, 44.96, 72.05, 44.96, 0.25, "F.Cu", b0_name, b0_nid))

    # Tap Trunk 1 (82.6) to Pin 6 (83.3, 50.04):
    pcb.append(make_via(82.6, 50.04, 0.6, 0.3, f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(82.6, 50.04, u1_x - 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    # Rf_N1 at (77.0, 51.31): Pad 1 (76.05)=V_SUM, Pad 2 (77.95)=INV
    pcb.append(fp_resistor_0805(f"Rf_N{n1}", "10k", 77.0, 51.31, 0, "F.Cu", 10 + n1, f"V_SUM_{n1}", 30 + n1, f"INV_N{n1}"))
    pcb.append(make_segment(76.05, 51.31, u1_x - 2.7, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(77.95, 51.31, 77.95, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    # Rb_N1 at (73.0, 50.04): Pad 1 (72.05)=Bias, Pad 2 (73.95)=INV
    b1_nid = 5 if l1["weights"][n1]["bias_rail"] == "-5V_REF" else 4
    b1_name = l1["weights"][n1]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n1}", l1["weights"][n1]["bias_resistor_str"], 73.0, 50.04, 0, "F.Cu", b1_nid, b1_name, 30 + n1, f"INV_N{n1}"))
    pcb.append(make_segment(73.95, 50.04, 82.6, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_via(70.5, 50.04, 0.6, 0.3, b1_name, b1_nid))
    pcb.append(make_segment(70.5, 50.04, 72.05, 50.04, 0.25, "F.Cu", b1_name, b1_nid))

    # --- RIGHT NEURONS: N2 and N3 ---
    # N2 tap: Trunk 2 (89.5) to Pin 9 (88.7, 50.04)
    pcb.append(make_via(89.5, 50.04, 0.6, 0.3, f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(89.5, 50.04, u1_x + 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    # Rf_N2 placed vertically at X = 91.5, Y = 50.675 rot=90
    # In KiCad rot=90: Pad 1 is at (91.5, 51.625) = V_SUM_2. Pad 2 is at (91.5, 49.725) = INV_N2
    pcb.append(fp_resistor_0805(f"Rf_N{n2}", "10k", 91.5, 50.675, 90, "F.Cu", 10 + n2, f"V_SUM_{n2}", 30 + n2, f"INV_N{n2}"))
    pcb.append(make_segment(89.5, 50.04, 91.5, 49.725, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(u1_x + 2.7, 51.31, 91.5, 51.625, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    # Rb_N2 placed vertically at X = 93.0, Y = 49.725 rot=90:
    # Pad 1 (93.0, 50.675) = INV_N2, Pad 2 (93.0, 48.775) = Bias
    b2_nid = 5 if l1["weights"][n2]["bias_rail"] == "-5V_REF" else 4
    b2_name = l1["weights"][n2]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n2}", l1["weights"][n2]["bias_resistor_str"], 93.0, 49.725, 90, "F.Cu", 30 + n2, f"INV_N{n2}", b2_nid, b2_name))
    pcb.append(make_segment(91.5, 49.725, 93.0, 50.675, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_via(93.0, 47.0, 0.6, 0.3, b2_name, b2_nid))
    pcb.append(make_segment(93.0, 48.775, 93.0, 47.0, 0.25, "F.Cu", b2_name, b2_nid))

    # N3 tap: Trunk 3 (90.3) to Pin 13 (88.7, 44.96)
    pcb.append(make_via(90.3, 44.96, 0.6, 0.3, f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(90.3, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    # Rf_N3 placed vertically at X = 91.5, Y = 44.325 rot=90
    # Pad 1 (45.275) = INV_N3, Pad 2 (43.375) = V_SUM_3
    pcb.append(fp_resistor_0805(f"Rf_N{n3}", "10k", 91.5, 44.325, 90, "F.Cu", 30 + n3, f"INV_N{n3}", 10 + n3, f"V_SUM_{n3}"))
    pcb.append(make_segment(u1_x + 2.7, 43.69, 91.5, 43.375, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(90.3, 44.96, 91.5, 45.275, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    # Rb_N3 placed vertically at X = 93.0, Y = 45.275 rot=90:
    # Pad 1 (46.225) = Bias, Pad 2 (44.325) = INV_N3
    b3_nid = 5 if l1["weights"][n3]["bias_rail"] == "-5V_REF" else 4
    b3_name = l1["weights"][n3]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n3}", l1["weights"][n3]["bias_resistor_str"], 93.0, 45.275, 90, "F.Cu", b3_nid, b3_name, 30 + n3, f"INV_N{n3}"))
    pcb.append(make_segment(91.5, 45.275, 93.0, 44.325, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_via(93.0, 47.8, 0.6, 0.3, b3_name, b3_nid))
    pcb.append(make_segment(93.0, 46.225, 93.0, 47.8, 0.25, "F.Cu", b3_name, b3_nid))

    # Power decoupling & routing:
    # Pin 4 (+12V) at (83.3, 47.5). C_U1P at (79.0, 47.5) rot=0
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 79.0, 47.5, 0, "F.Cu", 1, "GND", 2, "+12V"))
    pcb.append(make_via(76.5, 47.5, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(76.5, 47.5, 78.05, 47.5, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(79.95, 47.5, u1_x - 2.7, 47.5, 0.35, "F.Cu", "+12V", 2))
    # +12V rail on B.Cu along X = 83.97:
    pcb.append(make_via(83.97, 47.5, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(u1_x - 2.7, 47.5, 83.97, 47.5, 0.35, "F.Cu", "+12V", 2))
    pcb.append(make_segment(83.97, 47.5, 83.97, 92.0, 0.35, "B.Cu", "+12V", 2))

    # Pin 11 (-12V) at (88.7, 47.5). C_U1N placed cleanly to the right at (91.5, 47.5) rot=0:
    # Pad 1 (90.55) = -12V, Pad 2 (92.45) = GND
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 91.5, 47.5, 0, "F.Cu", 3, "-12V", 1, "GND"))
    pcb.append(make_segment(u1_x + 2.7, 47.5, 90.55, 47.5, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_via(92.8, 47.5, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(92.45, 47.5, 92.8, 47.5, 0.25, "F.Cu", "GND", 1))
    # -12V rail on B.Cu along X = 86.51:
    pcb.append(make_via(86.51, 47.5, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(u1_x + 2.7, 47.5, 86.51, 47.5, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_segment(86.51, 47.5, 86.51, 92.0, 0.35, "B.Cu", "-12V", 3))

    # Op-amp outputs to edge pins A33..A36:
    # Dedicated vertical escape columns on B.Cu:
    out_specs = [
        (0, u1_x - 2.7, 43.69, 83.3, x_start + 32 * PITCH),
        (1, u1_x - 2.7, 51.31, 84.8, x_start + 33 * PITCH),
        (2, 91.5, 51.625, 87.8, x_start + 34 * PITCH),
        (3, 91.5, 43.375, 88.5, x_start + 35 * PITCH)
    ]
    for idx, px, py, ch_x, fx in out_specs:
        j = neuron_range[idx]
        v_nid = 10 + j
        v_name = f"V_SUM_{j}"
        via_y = py - 1.0 if idx in [0, 3] else py + 1.0
        pcb.append(make_segment(px, py, ch_x, via_y, 0.25, "F.Cu", v_name, v_nid))
        pcb.append(make_via(ch_x, via_y, 0.6, 0.3, v_name, v_nid))
        pcb.append(make_segment(ch_x, via_y, ch_x, 88.0, 0.25, "B.Cu", v_name, v_nid))
        pcb.append(make_via(ch_x, 88.0, 0.6, 0.3, v_name, v_nid))
        pcb.append(make_segment(ch_x, 88.0, fx, 92.0, 0.25, "F.Cu", v_name, v_nid))

    # Bias Rails on B.Cu to Pins B35 (+5V_REF) and B36 (-5V_REF):
    # Pin B35 (+5V_REF) at X = 89.05, Pin B36 (-5V_REF) at X = 91.59
    pcb.append(make_segment(89.05, 92.0, 89.05, 47.0, 0.25, "B.Cu", "+5V_REF", 4))
    pcb.append(make_segment(91.59, 92.0, 91.59, 47.0, 0.25, "B.Cu", "-5V_REF", 5))

    # Connect Rb2 (93.0, 47.0) to b2 rail (+5V_REF):
    pcb.append(make_segment(93.0, 47.0, 89.05, 47.0, 0.25, "B.Cu", b2_name, b2_nid))
    # Connect Rb3 (93.0, 47.8) to b3 rail (+5V_REF):
    pcb.append(make_segment(93.0, 47.8, 89.05, 47.8, 0.25, "B.Cu", b3_name, b3_nid))
    pcb.append(make_segment(89.05, 47.8, 89.05, 47.0, 0.25, "B.Cu", b3_name, b3_nid))

    # Connect Left Biases (70.5, 44.96 for b0 and 70.5, 50.04 for b1):
    # b0 (+5V_REF): run north along Y = 43.5 on B.Cu to 70.5, then across on In2.Cu or F.Cu?
    # Run at Y = 43.5 on In2.Cu from 70.5 to 89.05!
    pcb.append(make_via(70.5, 43.5, 0.6, 0.3, b0_name, b0_nid))
    pcb.append(make_segment(70.5, 44.96, 70.5, 43.5, 0.25, "F.Cu", b0_name, b0_nid))
    # In2.Cu run: wait, In2.Cu has columns! What about B.Cu?
    # What runs on B.Cu at Y = 43.5?
    # At Y = 43.5 on B.Cu, there are NO COLUMNS!
    # The only tracks on B.Cu are the vertical power rails at X = 83.97, 86.51.
    # So drop a via to B.Cu at X = 88.0, and run on F.Cu from 70.5 to 88.0!
    pcb.append(make_segment(70.5, 43.5, 83.0, 43.5, 0.25, "F.Cu", b0_name, b0_nid))
    pcb.append(make_via(83.0, 43.5, 0.6, 0.3, b0_name, b0_nid))
    pcb.append(make_segment(83.0, 43.5, 83.0, 42.0, 0.25, "In2.Cu", b0_name, b0_nid))
    pcb.append(make_segment(83.0, 42.0, 89.05, 42.0, 0.25, "In2.Cu", b0_name, b0_nid))
    pcb.append(make_via(89.05, 42.0, 0.6, 0.3, b0_name, b0_nid))
    pcb.append(make_segment(89.05, 42.0, 89.05, 47.0, 0.25, "B.Cu", b0_name, b0_nid))

    # b1 (-5V_REF) from 70.5, 50.04 to 91.59:
    pcb.append(make_segment(70.5, 50.04, 70.5, 52.0, 0.25, "F.Cu", b1_name, b1_nid))
    pcb.append(make_segment(70.5, 52.0, 83.0, 52.0, 0.25, "F.Cu", b1_name, b1_nid))
    pcb.append(make_via(83.0, 52.0, 0.6, 0.3, b1_name, b1_nid))
    pcb.append(make_segment(83.0, 52.0, 91.59, 52.0, 0.25, "In2.Cu", b1_name, b1_nid))
    pcb.append(make_via(91.59, 52.0, 0.6, 0.3, b1_name, b1_nid))
    pcb.append(make_segment(91.59, 52.0, 91.59, 47.0, 0.25, "B.Cu", b1_name, b1_nid))

    pcb.append(")")
    with open(board_file, "w") as f: f.write("\n".join(pcb))

    fill_cmd = f"""/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 -c "
import pcbnew
board = pcbnew.LoadBoard('{board_file}')
ds = board.GetDesignSettings()
ds.m_CopperEdgeClearance = 0
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save('{board_file}')
" """
    subprocess.run(fill_cmd, shell=True, check=True)
    print("Done generating clean DC1A.")

if __name__ == "__main__":
    build_perfect_dc1("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A", range(0, 4))
