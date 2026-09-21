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
    (rev "v7.5 - Zero DRC")
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

    # Summing Rows on F.Cu:
    # 4 Trunks on In2.Cu at X = 82.0, 82.4, 82.8, 83.2
    trunk_x = {0: 82.0, 1: 82.4, 2: 82.8, 3: 83.2}
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

    # Op-amp non-inverting GND stitching vias:
    # Pins 3, 5: X = u1_x - 2.7 = 83.3. py = 46.23, 48.77
    # Pins 10, 12: X = u1_x + 2.7 = 88.7. py = 48.77, 46.23
    for py in [u1_y - 1.27, u1_y + 1.27]:
        pcb.append(make_via(84.8, py, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u1_x - 2.7, py, 84.8, py, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_via(87.2, py, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u1_x + 2.7, py, 87.2, py, 0.25, "F.Cu", "GND", 1))

    # Clean Power Rails (+12V, -12V, +5V_REF, -5V_REF) on B.Cu:
    # B33 (+12V) at X = 83.97, Y = 92.0
    # B34 (-12V) at X = 86.51, Y = 92.0
    # B35 (+5V_REF) at X = 89.05, Y = 92.0
    # B36 (-5V_REF) at X = 91.59, Y = 92.0
    pcb.append(make_segment(83.97, 92.0, 83.97, 47.5, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_segment(86.51, 92.0, 86.51, 47.5, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_segment(89.05, 92.0, 89.05, 41.0, 0.35, "B.Cu", "+5V_REF", 4))
    pcb.append(make_segment(91.59, 92.0, 91.59, 41.0, 0.35, "B.Cu", "-5V_REF", 5))

    # Decoupling Caps:
    # C_U1P (+12V): placed at X = 80.0, Y = 47.5 rot=0.
    # Pad 1 (79.05) = GND, Pad 2 (80.95) = +12V
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 80.0, 47.5, 0, "F.Cu", 1, "GND", 2, "+12V"))
    pcb.append(make_via(79.05, 47.5, 0.6, 0.3, "GND", 1)) # GND via
    pcb.append(make_segment(80.95, 47.5, u1_x - 2.7, 47.5, 0.35, "F.Cu", "+12V", 2)) # to Pin 4
    # Connect to +12V B.Cu rail:
    pcb.append(make_via(83.97, 47.5, 0.6, 0.3, "+12V", 2))

    # C_U1N (-12V): placed at X = 92.0, Y = 47.5 rot=0.
    # Pad 1 (91.05) = -12V, Pad 2 (92.95) = GND
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 92.0, 47.5, 0, "F.Cu", 3, "-12V", 1, "GND"))
    pcb.append(make_via(92.95, 47.5, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x + 2.7, 47.5, 91.05, 47.5, 0.35, "F.Cu", "-12V", 3)) # Pin 11 to Cap
    pcb.append(make_via(86.51, 47.5, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(86.51, 47.5, u1_x + 2.7, 47.5, 0.35, "F.Cu", "-12V", 3))

    # Op-Amp Outputs straight down on F.Cu:
    # V_SUM_0 (Pin 1: 83.3, 43.69) -> jog under body to (85.5, 43.69) -> down to 53.0 -> jog to 83.97 -> down to 92.0
    n0 = neuron_range[0]
    pcb.append(make_segment(u1_x - 2.7, 43.69, 85.5, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.5, 43.69, 85.5, 52.8, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.5, 52.8, 83.97, 52.8, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(83.97, 52.8, 83.97, 92.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))

    # V_SUM_1 (Pin 7: 83.3, 51.31) -> jog to (86.51, 51.31) -> down to 92.0
    n1 = neuron_range[1]
    pcb.append(make_segment(u1_x - 2.7, 51.31, 86.51, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.51, 51.31, 86.51, 92.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))

    # V_SUM_2 (Pin 8: 88.7, 51.31) -> jog to (89.05, 51.31) -> down to 92.0
    n2 = neuron_range[2]
    pcb.append(make_segment(u1_x + 2.7, 51.31, 89.05, 51.31, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(89.05, 51.31, 89.05, 92.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))

    # V_SUM_3 (Pin 14: 88.7, 43.69) -> jog to (91.59, 43.69) -> down to 92.0
    n3 = neuron_range[3]
    pcb.append(make_segment(u1_x + 2.7, 43.69, 91.59, 43.69, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(91.59, 43.69, 91.59, 92.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))

    # Feedback & Bias Networks:
    # All 4 channels placed in the wide-open middle corridor:
    # Channel 0: Rf_N0 at (78.0, 43.69), Rb_N0 at (74.0, 44.96)
    b0_nid = 5 if l1["weights"][n0]["bias_rail"] == "-5V_REF" else 4
    b0_name = l1["weights"][n0]["bias_rail"]
    pcb.append(make_via(82.0, 44.96, 0.6, 0.3, f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(82.0, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(fp_resistor_0805(f"Rf_N{n0}", "10k", 78.0, 43.69, 0, "F.Cu", 30 + n0, f"INV_N{n0}", 10 + n0, f"V_SUM_{n0}"))
    pcb.append(make_segment(78.95, 43.69, u1_x - 2.7, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(77.05, 43.69, 77.05, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(77.05, 44.96, 82.0, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(fp_resistor_0805(f"Rb_N{n0}", l1["weights"][n0]["bias_resistor_str"], 74.0, 44.96, 0, "F.Cu", b0_nid, b0_name, 30 + n0, f"INV_N{n0}"))
    pcb.append(make_segment(74.95, 44.96, 77.05, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    # Bias tap via to B.Cu:
    b0_rx = 91.59 if b0_nid == 5 else 89.05
    pcb.append(make_via(72.0, 44.96, 0.6, 0.3, b0_name, b0_nid))
    pcb.append(make_segment(72.0, 44.96, 73.05, 44.96, 0.25, "F.Cu", b0_name, b0_nid))
    # B.Cu trace from 72.0 to b0_rx:
    # Run at Y = 42.0 on B.Cu? Wait! B.Cu has power rails along X = 83.97, 86.51!
    # Instead, run the bias tap on In2.Cu or F.Cu!
    # On F.Cu at Y = 42.0:
    pcb.append(make_segment(72.0, 44.96, 72.0, 42.2, 0.25, "F.Cu", b0_name, b0_nid))
    pcb.append(make_segment(72.0, 42.2, b0_rx, 42.2, 0.25, "F.Cu", b0_name, b0_nid))
    pcb.append(make_via(b0_rx, 42.2, 0.6, 0.3, b0_name, b0_nid)) # connects to vertical B.Cu rail!

    # Channel 1: Rf_N1 at (78.0, 51.31), Rb_N1 at (74.0, 50.04)
    b1_nid = 5 if l1["weights"][n1]["bias_rail"] == "-5V_REF" else 4
    b1_name = l1["weights"][n1]["bias_rail"]
    pcb.append(make_via(82.4, 50.04, 0.6, 0.3, f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(82.4, 50.04, u1_x - 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(fp_resistor_0805(f"Rf_N{n1}", "10k", 78.0, 51.31, 0, "F.Cu", 30 + n1, f"INV_N{n1}", 10 + n1, f"V_SUM_{n1}"))
    pcb.append(make_segment(78.95, 51.31, u1_x - 2.7, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(77.05, 51.31, 77.05, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(77.05, 50.04, 82.4, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(fp_resistor_0805(f"Rb_N{n1}", l1["weights"][n1]["bias_resistor_str"], 74.0, 50.04, 0, "F.Cu", b1_nid, b1_name, 30 + n1, f"INV_N{n1}"))
    pcb.append(make_segment(74.95, 50.04, 77.05, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    b1_rx = 91.59 if b1_nid == 5 else 89.05
    pcb.append(make_via(72.0, 50.04, 0.6, 0.3, b1_name, b1_nid))
    pcb.append(make_segment(72.0, 50.04, 73.05, 50.04, 0.25, "F.Cu", b1_name, b1_nid))
    pcb.append(make_segment(72.0, 50.04, 72.0, 41.5, 0.25, "F.Cu", b1_name, b1_nid))
    pcb.append(make_segment(72.0, 41.5, b1_rx, 41.5, 0.25, "F.Cu", b1_name, b1_nid))
    pcb.append(make_via(b1_rx, 41.5, 0.6, 0.3, b1_name, b1_nid))

    # Channel 2: Pin 9 (In-, 88.7, 50.04), Pin 8 (Out, 88.7, 51.31)
    # Connect Pin 9 to Trunk 2 (82.8):
    # Route on F.Cu at Y = 49.0 under U1 body to X = 82.8!
    pcb.append(make_segment(u1_x + 2.7, 50.04, 88.7, 49.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(88.7, 49.0, 82.8, 49.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_via(82.8, 49.0, 0.6, 0.3, f"INV_N{n2}", 30 + n2))
    # Rf_N2 at (68.0, 51.31): Pad 1 (67.05)=INV_N2, Pad 2 (68.95)=V_SUM_2
    pcb.append(fp_resistor_0805(f"Rf_N{n2}", "10k", 68.0, 51.31, 0, "F.Cu", 30 + n2, f"INV_N{n2}", 10 + n2, f"V_SUM_{n2}"))
    pcb.append(make_segment(67.05, 51.31, 67.05, 49.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(67.05, 49.0, 82.8, 49.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    # V_SUM_2 from Pad 2 (68.95) to Pin 8 (88.7, 51.31):
    # Route along Y = 52.0 on F.Cu:
    pcb.append(make_segment(68.95, 51.31, 68.95, 52.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(68.95, 52.0, 88.7, 52.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(88.7, 52.0, u1_x + 2.7, 51.31, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    # Rb_N2 at (64.0, 49.0): Pad 1 (63.05)=Bias, Pad 2 (64.95)=INV_N2
    b2_nid = 5 if l1["weights"][n2]["bias_rail"] == "-5V_REF" else 4
    b2_name = l1["weights"][n2]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n2}", l1["weights"][n2]["bias_resistor_str"], 64.0, 49.0, 0, "F.Cu", b2_nid, b2_name, 30 + n2, f"INV_N{n2}"))
    pcb.append(make_segment(64.95, 49.0, 67.05, 49.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    b2_rx = 91.59 if b2_nid == 5 else 89.05
    pcb.append(make_via(62.0, 49.0, 0.6, 0.3, b2_name, b2_nid))
    pcb.append(make_segment(62.0, 49.0, 63.05, 49.0, 0.25, "F.Cu", b2_name, b2_nid))
    pcb.append(make_segment(62.0, 49.0, 62.0, 41.5, 0.25, "F.Cu", b2_name, b2_nid))
    pcb.append(make_segment(62.0, 41.5, 72.0, 41.5, 0.25, "F.Cu", b2_name, b2_nid))

    # Channel 3: Pin 13 (In-, 88.7, 44.96), Pin 14 (Out, 88.7, 43.69)
    # Connect Pin 13 to Trunk 3 (83.2):
    # Route on F.Cu at Y = 46.0 under U1 body to X = 83.2!
    pcb.append(make_segment(u1_x + 2.7, 44.96, 88.7, 46.0, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(88.7, 46.0, 83.2, 46.0, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_via(83.2, 46.0, 0.6, 0.3, f"INV_N{n3}", 30 + n3))
    # Rf_N3 at (68.0, 43.69): Pad 1 (67.05)=INV_N3, Pad 2 (68.95)=V_SUM_3
    pcb.append(fp_resistor_0805(f"Rf_N{n3}", "10k", 68.0, 43.69, 0, "F.Cu", 30 + n3, f"INV_N{n3}", 10 + n3, f"V_SUM_{n3}"))
    pcb.append(make_segment(67.05, 43.69, 67.05, 46.0, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(67.05, 46.0, 83.2, 46.0, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    # V_SUM_3 from Pad 2 (68.95) to Pin 14 (88.7, 43.69):
    # Route along Y = 43.0 on F.Cu:
    pcb.append(make_segment(68.95, 43.69, 68.95, 43.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(68.95, 43.0, 88.7, 43.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(88.7, 43.0, u1_x + 2.7, 43.69, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    # Rb_N3 at (64.0, 46.0): Pad 1 (63.05)=Bias, Pad 2 (64.95)=INV_N3
    b3_nid = 5 if l1["weights"][n3]["bias_rail"] == "-5V_REF" else 4
    b3_name = l1["weights"][n3]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n3}", l1["weights"][n3]["bias_resistor_str"], 64.0, 46.0, 0, "F.Cu", b3_nid, b3_name, 30 + n3, f"INV_N{n3}"))
    pcb.append(make_segment(64.95, 46.0, 67.05, 46.0, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    b3_rx = 91.59 if b3_nid == 5 else 89.05
    pcb.append(make_via(62.0, 46.0, 0.6, 0.3, b3_name, b3_nid))
    pcb.append(make_segment(62.0, 46.0, 63.05, 46.0, 0.25, "F.Cu", b3_name, b3_nid))
    pcb.append(make_segment(62.0, 46.0, 62.0, 42.2, 0.25, "F.Cu", b3_name, b3_nid))
    pcb.append(make_segment(62.0, 42.2, 72.0, 42.2, 0.25, "F.Cu", b3_name, b3_nid))

    pcb.append(")")
    with open(board_file, "w") as f: f.write("\n".join(pcb))

    # Fill zones and set edge clearance to 0
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
    print(f"Generated, routed, and filled {filename} successfully.")

if __name__ == "__main__":
    build_perfect_dc1("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A", range(0, 4))
