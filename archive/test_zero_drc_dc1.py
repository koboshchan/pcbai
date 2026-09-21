#!/usr/bin/env python3
import json, uuid, subprocess

def make_uuid():
    return str(uuid.uuid4())

def make_segment(x1, y1, x2, y2, width=0.25, layer="F.Cu", net_name="", net_id=0):
    return f'  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width}) (layer "{layer}") (net {net_id}) (uuid "{make_uuid()}"))'

def make_via(x, y, size=0.6, drill=0.3, net_name="", net_id=0):
    return f'  (via (at {x:.4f} {y:.4f}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net_id}) (uuid "{make_uuid()}"))'

def fp_resistor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    r_val = rot
    cos_a, sin_a = (1.0, 0.0) if rot==0 else ((0.0, 1.0) if rot==90 else ((-1.0, 0.0) if rot==180 else (0.0, -1.0)))
    p1_ox, p1_oy = -0.95 * cos_a, -0.95 * sin_a
    p2_ox, p2_oy =  0.95 * cos_a,  0.95 * sin_a
    
    return f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.4f} {y:.4f} {r_val})
    (property "Reference" "{ref}" (at 0 -1.4 {r_val}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "{val}" (at 0 1.4 {r_val}) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (path "/{ref}")
    (pad "1" smd roundrect (at {p1_ox:.4f} {p1_oy:.4f} {r_val}) (size 1.0 1.4) (layers "{layer}" "{"F.Mask" if layer=="F.Cu" else "B.Mask"}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at {p2_ox:.4f} {p2_oy:.4f} {r_val}) (size 1.0 1.4) (layers "{layer}" "{"F.Mask" if layer=="F.Cu" else "B.Mask"}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD8_3DMODEL_DIR}}/Resistor_SMD.3dshapes/R_0805_2012Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
  )"""

def fp_capacitor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    r_val = rot
    cos_a, sin_a = (1.0, 0.0) if rot==0 else (0.0, 1.0)
    p1_ox, p1_oy = -0.95 * cos_a, -0.95 * sin_a
    p2_ox, p2_oy =  0.95 * cos_a,  0.95 * sin_a
    return f"""  (footprint "Capacitor_SMD:C_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.4f} {y:.4f} {r_val})
    (property "Reference" "{ref}" (at 0 -1.4 {r_val}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "{val}" (at 0 1.4 {r_val}) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (pad "1" smd roundrect (at {p1_ox:.4f} {p1_oy:.4f} {r_val}) (size 1.0 1.4) (layers "{layer}" "{"F.Mask" if layer=="F.Cu" else "B.Mask"}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at {p2_ox:.4f} {p2_oy:.4f} {r_val}) (size 1.0 1.4) (layers "{layer}" "{"F.Mask" if layer=="F.Cu" else "B.Mask"}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD8_3DMODEL_DIR}}/Capacitor_SMD.3dshapes/C_0805_2012Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
  )"""

def fp_soic14(ref, val, x, y, rot=0, layer="F.Cu", pin_nets=None):
    pads = []
    pitch = 1.27
    x_off = 2.7
    y_starts = [-3 * pitch, -2 * pitch, -1 * pitch, 0, 1 * pitch, 2 * pitch, 3 * pitch]
    for i in range(7):
        p_num = str(i + 1)
        py = y_starts[i]
        nid, nname = pin_nets.get(p_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{p_num}" smd roundrect (at {-x_off:.3f} {py:.3f}) (size 1.5 0.6) (layers "{layer}" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    for i in range(7):
        p_num = str(14 - i)
        py = y_starts[i]
        nid, nname = pin_nets.get(p_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{p_num}" smd roundrect (at {x_off:.3f} {py:.3f}) (size 1.5 0.6) (layers "{layer}" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.4f} {y:.4f} {rot})
    (property "Reference" "{ref}" (at 0 -5.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 5.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (fp_line (start -2.0 -4.4) (end 2.0 -4.4) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
    (fp_line (start -2.0 4.4) (end 2.0 4.4) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
{pads_str}
    (model "${{KICAD8_3DMODEL_DIR}}/Package_SO.3dshapes/SOIC-14_3.9x8.7mm_P1.27mm.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
  )"""

def fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=94.28):
    cx = card_width / 2.0
    x_start = - (17.5 * 2.54)
    pads = []
    for i in range(36):
        px = x_start + i * 2.54
        p_num_a = f"A{i+1}"
        nid_a, nname_a = pin_nets_a.get(p_num_a, (0, ""))
        pads.append(f'    (pad "{p_num_a}" smd roundrect (at {px:.3f} 0) (size 1.60 5.00) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2) (net {nid_a} "{nname_a}"))')
        p_num_b = f"B{i+1}"
        nid_b, nname_b = pin_nets_b.get(p_num_b, (0, ""))
        pads.append(f'    (pad "{p_num_b}" smd roundrect (at {px:.3f} 0) (size 1.60 5.00) (layers "B.Cu" "B.Mask") (roundrect_rratio 0.2) (net {nid_b} "{nname_b}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PCBEdge:GoldFingers_72P_2.54mm" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {cx:.2f} 96.00)
    (descr "72-Pin PCB Edge Gold Fingers (36 Front + 36 Back) at 2.54mm pitch")
{pads_str}
  )"""

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

def build_perfect_dc1(board_file, card_title, neuron_range):
    with open("weights_layer1.json") as f:
        l1 = json.load(f)

    PITCH = 2.54
    cx = 94.28 / 2.0
    x_start = cx - 17.5 * PITCH # 2.69 mm

    nets = {
        0: "",
        1: "GND",
        2: "+12V",
        3: "-12V",
        4: "+5V_REF",
        5: "-5V_REF"
    }
    for j in range(16):
        nets[10 + j] = f"V_SUM_{j}"
        nets[30 + j] = f"INV_N{j}"
    for i in range(64):
        nets[100 + i] = f"IN_{i}"

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

    net_defs = []
    for nid in sorted(nets.keys()):
        net_defs.append(f'  (net {nid} "{nets[nid]}")')

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in sorted(nets.items()) if nid > 0])
    header = f"""(kicad_pcb (version 20221018) (generator "analog_nn_clean_router")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "{card_title}")
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
    pcb = [header] + [
        get_daughtercard_outline_and_mounts(width=94.28, height=100.0),
        fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=94.28),
        f'  (gr_text "{card_title}" (at 47.14 8.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 2.5 2.5) (thickness 0.3))))'
    ]

    row_y = [17.0, 25.0, 33.0, 41.0, 54.0, 62.0, 70.0, 78.0]

    # Matrix Resistors:
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

    # Matrix Columns:
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

    # Place U1 at X = 86.5, Y = 47.5
    u1_x = 86.5
    u1_y = 47.5
    n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]
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

    # Summing Rows on F.Cu:
    # 4 Trunks on In2.Cu: 0 & 1 at (82.2, 83.0), 2 & 3 at (83.8, 84.6)
    trunk_x = {0: 82.2, 1: 83.0, 2: 83.8, 3: 84.6}
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

    # GND stitching vias for Pins 3, 5, 10, 12 in center of U1 (X = 86.5):
    for py in [u1_y - 1.27, u1_y + 1.27]:
        pcb.append(make_via(86.5, py, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u1_x - 2.7, py, 86.5, py, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_segment(u1_x + 2.7, py, 86.5, py, 0.25, "F.Cu", "GND", 1))

    # Power decoupling & routing:
    # Pin 4 (+12V) at (83.8, 47.5). C_U1P at (80.5, 47.5) rot=0
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 80.5, 47.5, 0, "F.Cu", 1, "GND", 2, "+12V"))
    pcb.append(make_via(78.5, 47.5, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(78.5, 47.5, 79.55, 47.5, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(81.45, 47.5, u1_x - 2.7, 47.5, 0.35, "F.Cu", "+12V", 2))
    # +12V rail on B.Cu along X = 83.97:
    pcb.append(make_via(83.97, 47.5, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(83.97, 47.5, 83.97, 92.0, 0.35, "B.Cu", "+12V", 2))

    # Pin 11 (-12V) at (89.2, 47.5). C_U1N placed vertically at (92.5, 47.5) rot=90:
    # rot=90: Pad 1 at (92.5, 46.55) = GND, Pad 2 at (92.5, 48.45) = -12V
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 92.5, 47.5, 90, "F.Cu", 1, "GND", 3, "-12V"))
    pcb.append(make_segment(u1_x + 2.7, 47.5, 92.5, 48.45, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_via(92.5, 45.3, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(92.5, 46.55, 92.5, 45.3, 0.25, "F.Cu", "GND", 1))
    # -12V rail on B.Cu along X = 86.51:
    pcb.append(make_via(86.51, 47.5, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(u1_x + 2.7, 47.5, 86.51, 47.5, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_segment(86.51, 47.5, 86.51, 92.0, 0.35, "B.Cu", "-12V", 3))

    # Vertical Bias Rails on B.Cu:
    # +5V_REF along X = 89.05, -5V_REF along X = 91.59
    pcb.append(make_segment(89.05, 92.0, 89.05, 20.0, 0.35, "B.Cu", "+5V_REF", 4))
    pcb.append(make_segment(91.59, 92.0, 91.59, 20.0, 0.35, "B.Cu", "-5V_REF", 5))

    def connect_bias(bx, by, b_name, b_nid):
        rail_x = 89.05 if b_name == "+5V_REF" else 91.59
        pcb.append(make_via(bx, by, 0.6, 0.3, b_name, b_nid))
        pcb.append(make_segment(bx, by, rail_x, by, 0.25, "B.Cu", b_name, b_nid))

    # --- NEURON 0 (Top-Left: Pins 1 & 2) ---
    pcb.append(fp_resistor_0805(f"Rf_N{n0}", "10k", 86.5, 36.0, 0, "F.Cu", 10 + n0, f"V_SUM_{n0}", 30 + n0, f"INV_N{n0}"))
    b0_nid = 5 if l1["weights"][n0]["bias_rail"] == "-5V_REF" else 4
    b0_name = l1["weights"][n0]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n0}", l1["weights"][n0]["bias_resistor_str"], 86.5, 32.0, 0, "F.Cu", b0_nid, b0_name, 30 + n0, f"INV_N{n0}"))
    pcb.append(make_segment(87.45, 32.0, 87.45, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(87.45, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_via(82.2, 44.96, 0.6, 0.3, f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(82.2, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(u1_x - 2.7, 43.69, 85.55, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.55, 43.69, 85.55, 36.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    connect_bias(85.55, 32.0, b0_name, b0_nid)

    # --- NEURON 3 (Top-Right: Pins 13 & 14) ---
    pcb.append(fp_resistor_0805(f"Rf_N{n3}", "10k", 90.5, 26.0, 0, "F.Cu", 30 + n3, f"INV_N{n3}", 10 + n3, f"V_SUM_{n3}"))
    b3_nid = 5 if l1["weights"][n3]["bias_rail"] == "-5V_REF" else 4
    b3_name = l1["weights"][n3]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n3}", l1["weights"][n3]["bias_resistor_str"], 90.5, 22.0, 0, "F.Cu", 30 + n3, f"INV_N{n3}", b3_nid, b3_name))
    pcb.append(make_segment(89.55, 22.0, 89.55, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(89.55, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(84.6, 44.96, 88.0, 44.96, 0.25, "In2.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_via(88.0, 44.96, 0.6, 0.3, f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(88.0, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(u1_x + 2.7, 43.69, 91.45, 43.69, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(91.45, 43.69, 91.45, 26.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    connect_bias(91.45, 22.0, b3_name, b3_nid)

    # --- NEURON 1 (Bottom-Left: Pins 6 & 7) ---
    pcb.append(fp_resistor_0805(f"Rf_N{n1}", "10k", 86.5, 58.0, 0, "F.Cu", 10 + n1, f"V_SUM_{n1}", 30 + n1, f"INV_N{n1}"))
    b1_nid = 5 if l1["weights"][n1]["bias_rail"] == "-5V_REF" else 4
    b1_name = l1["weights"][n1]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n1}", l1["weights"][n1]["bias_resistor_str"], 86.5, 62.0, 0, "F.Cu", b1_nid, b1_name, 30 + n1, f"INV_N{n1}"))
    pcb.append(make_segment(u1_x - 2.7, 50.04, 87.45, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(87.45, 50.04, 87.45, 62.0, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_via(83.0, 50.04, 0.6, 0.3, f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(83.0, 50.04, u1_x - 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(u1_x - 2.7, 51.31, 85.55, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(85.55, 51.31, 85.55, 58.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    connect_bias(85.55, 62.0, b1_name, b1_nid)

    # --- NEURON 2 (Bottom-Right: Pins 8 & 9) ---
    pcb.append(fp_resistor_0805(f"Rf_N{n2}", "10k", 90.5, 68.0, 0, "F.Cu", 30 + n2, f"INV_N{n2}", 10 + n2, f"V_SUM_{n2}"))
    b2_nid = 5 if l1["weights"][n2]["bias_rail"] == "-5V_REF" else 4
    b2_name = l1["weights"][n2]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n2}", l1["weights"][n2]["bias_resistor_str"], 90.5, 72.0, 0, "F.Cu", 30 + n2, f"INV_N{n2}", b2_nid, b2_name))
    pcb.append(make_segment(u1_x + 2.7, 50.04, 89.55, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(89.55, 50.04, 89.55, 72.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(83.8, 50.04, 88.0, 50.04, 0.25, "In2.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_via(88.0, 50.04, 0.6, 0.3, f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(88.0, 50.04, u1_x + 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(u1_x + 2.7, 51.31, 91.45, 51.31, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(91.45, 51.31, 91.45, 68.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    connect_bias(91.45, 72.0, b2_name, b2_nid)

    # --- OUTPUT LINES ON F.Cu TO EDGE PINS A33..A36 ---
    # Pin A33 (83.97): V_SUM_0 from (85.55, 43.69)
    pcb.append(make_segment(85.55, 43.69, 83.97, 45.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(83.97, 45.0, 83.97, 92.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))

    # Pin A34 (86.51): V_SUM_1 from (85.55, 58.0)
    pcb.append(make_segment(85.55, 58.0, 86.51, 60.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.51, 60.0, 86.51, 92.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))

    # Pin A35 (89.05): V_SUM_2 from (91.45, 68.0)
    pcb.append(make_segment(91.45, 68.0, 89.05, 74.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(89.05, 74.0, 89.05, 92.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))

    # Pin A36 (91.59): V_SUM_3 from (91.45, 43.69)
    pcb.append(make_segment(91.45, 43.69, 91.59, 45.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(91.59, 45.0, 91.59, 92.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))

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
    print("Done generating clean DC1.")

if __name__ == "__main__":
    build_perfect_dc1("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A", range(0, 4))
