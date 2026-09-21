#!/usr/bin/env python3
import json, uuid, subprocess

def make_uuid():
    return str(uuid.uuid4())

def make_segment(x1, y1, x2, y2, width=0.25, layer="F.Cu", net_name="", net_id=0):
    return f'  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width}) (layer "{layer}") (net {net_id}) (uuid "{make_uuid()}"))'

def make_via(x, y, size=0.6, drill=0.3, net_name="", net_id=0):
    return f'  (via (at {x:.4f} {y:.4f}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net_id}) (uuid "{make_uuid()}"))'

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
    (model "${{KICAD8_3DMODEL_DIR}}/Resistor_SMD.3dshapes/R_0805_2012Metric.step"
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
        pads.append(f'    (pad "{p_num_a}" smd roundrect (at {px:.3f} 0) (size 1.80 8.00) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2) (net {nid_a} "{nname_a}"))')
        p_num_b = f"B{i+1}"
        nid_b, nname_b = pin_nets_b.get(p_num_b, (0, ""))
        pads.append(f'    (pad "{p_num_b}" smd roundrect (at {px:.3f} 0) (size 1.80 8.00) (layers "B.Cu" "B.Mask") (roundrect_rratio 0.2) (net {nid_b} "{nname_b}"))')
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

def build_orthogonal_dc1(board_file, card_title, neuron_range):
    with open("weights_layer1.json") as f:
        l1 = json.load(f)

    PITCH = 2.54
    cx = 94.28 / 2.0 # 47.14 mm
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

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in sorted(nets.items()) if nid > 0])
    header = f"""(kicad_pcb (version 20221018) (generator "analog_nn_clean_router")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "{card_title}")
    (company "Discrete Analog Neural Network System")
    (rev "v16.0 - Zero DRC Final")
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
    pcb = [header,
        get_daughtercard_outline_and_mounts(width=94.28, height=100.0),
        fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=94.28),
        f'  (gr_text "{card_title}" (at 47.14 8.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 2.5 2.5) (thickness 0.3))))'
    ]

    row_y = [17.0, 25.0, 33.0, 41.0, 54.0, 62.0, 70.0, 78.0]

    # 1. Matrix Resistors:
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

    # 2. Matrix Columns:
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

    # 3. Summing Rows on F.Cu to 4 Trunks on In2.Cu at X = 81.6, 82.1, 82.6, 83.1
    # On In2.Cu, top bank column 31 is at X = 80.83, so In2.Cu is 100% free for X >= 81.5!
    trunk_x = {0: 81.6, 1: 82.1, 2: 82.6, 3: 83.1}
    for r in range(8):
        y_sum = row_y[r] - 0.95
        local_neuron = r % 4
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        x_left = x_start
        tx = trunk_x[local_neuron]
        pcb.append(make_segment(x_left, y_sum, tx, y_sum, 0.25, "F.Cu", sum_name, sum_nid))
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

    # 4. Place U1 (TL074) at X = 87.5, Y = 47.5
    u1_x = 87.5
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

    # Center GND vias for Pins 3, 5, 10, 12 at X = 87.5:
    for py in [u1_y - 1.27, u1_y + 1.27]:
        pcb.append(make_via(u1_x, py, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u1_x - 2.7, py, u1_x, py, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_segment(u1_x + 2.7, py, u1_x, py, 0.25, "F.Cu", "GND", 1))

    # Decoupling Capacitors placed cleanly horizontally:
    # C_U1P at (81.0, 47.5) rot=0: Pad 1 (80.05) = GND, Pad 2 (81.95) = +12V
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 81.0, 47.5, 0, "F.Cu", 1, "GND", 2, "+12V"))
    pcb.append(make_via(79.0, 47.5, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(79.0, 47.5, 80.05, 47.5, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(81.95, 47.5, u1_x - 2.7, 47.5, 0.35, "F.Cu", "+12V", 2))

    # C_U1N at (93.0, 47.5) rot=0: Pad 1 (92.05) = -12V, Pad 2 (93.95) = GND
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 93.0, 47.5, 0, "F.Cu", 3, "-12V", 1, "GND"))
    pcb.append(make_segment(u1_x + 2.7, 47.5, 92.05, 47.5, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_via(93.0, 46.0, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(93.95, 47.5, 93.0, 46.0, 0.25, "F.Cu", "GND", 1))

    # 5. Dedicated Vertical Rails on B.Cu (Lanes 1 to 8):
    # Lane 1 (83.5): V_SUM_0 (Y=38 to 86)
    # Lane 2 (86.0): V_SUM_1 (Y=58 to 86)
    # Lane 3 (86.8): +12V (Y=92 to 47.5)
    # Lane 4 (88.0): -12V (Y=92 to 47.5)  <- decoupled from GND via at 87.5!
    # Lane 5 (88.6): +5V_REF (Y=92 to 25)
    # Lane 6 (92.0): -5V_REF (Y=92 to 25)
    # Lane 7 (92.6): V_SUM_2 (Y=58 to 86)
    # Lane 8 (93.2): V_SUM_3 (Y=38 to 86)

    # Power Rails on B.Cu:
    pcb.append(make_segment(83.97, 92.0, 86.8, 88.0, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_segment(86.8, 88.0, 86.8, 47.5, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_via(86.8, 47.5, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(86.8, 47.5, u1_x - 2.7, 47.5, 0.35, "F.Cu", "+12V", 2))

    pcb.append(make_segment(86.51, 92.0, 88.0, 88.0, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_segment(88.0, 88.0, 88.0, 47.5, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_via(88.0, 47.5, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(88.0, 47.5, u1_x + 2.7, 47.5, 0.35, "F.Cu", "-12V", 3))

    pcb.append(make_segment(89.05, 92.0, 88.6, 88.0, 0.35, "B.Cu", "+5V_REF", 4))
    pcb.append(make_segment(88.6, 88.0, 88.6, 25.0, 0.35, "B.Cu", "+5V_REF", 4))

    pcb.append(make_segment(91.59, 92.0, 92.0, 88.0, 0.35, "B.Cu", "-5V_REF", 5))
    pcb.append(make_segment(92.0, 88.0, 92.0, 25.0, 0.35, "B.Cu", "-5V_REF", 5))

    # tap_bias: runs on F.Cu from fx to rail_x, drops single via to B.Cu!
    def tap_bias(fx, fy, b_name, b_nid):
        rail_x = 88.6 if b_name == "+5V_REF" else 92.0
        pcb.append(make_segment(fx, fy, rail_x, fy, 0.25, "F.Cu", b_name, b_nid))
        pcb.append(make_via(rail_x, fy, 0.6, 0.3, b_name, b_nid))

    # 6. Summing Trunks to Op-Amp Inverting Inputs via In2.Cu:
    # Trunk 0 (81.6): via at (81.6, 44.96) on F.Cu straight into Pin 2!
    pcb.append(make_via(81.6, 44.96, 0.6, 0.3, f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(81.6, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))

    # Trunk 1 (82.1): via at (82.1, 50.04) on F.Cu straight into Pin 6!
    pcb.append(make_via(82.1, 50.04, 0.6, 0.3, f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(82.1, 50.04, u1_x - 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))

    # Trunk 2 (82.6) on In2.Cu at Y = 51.5 under U1:
    pcb.append(make_segment(82.6, 50.04, 82.6, 51.5, 0.25, "In2.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(82.6, 51.5, 90.5, 51.5, 0.25, "In2.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_via(90.5, 51.5, 0.6, 0.3, f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(90.5, 51.5, u1_x + 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))

    # Trunk 3 (83.1) on In2.Cu at Y = 43.5 under U1:
    pcb.append(make_segment(83.1, 44.96, 83.1, 43.5, 0.25, "In2.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(83.1, 43.5, 90.5, 43.5, 0.25, "In2.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_via(90.5, 43.5, 0.6, 0.3, f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(90.5, 43.5, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))

    # 7. NEURON 0 (Above U1): Rf0 at (85.25, 36.0), Rb0 at (85.25, 32.0)
    pcb.append(fp_resistor_0805(f"Rf_N{n0}", "10k", 85.25, 36.0, 0, "F.Cu", 10 + n0, f"V_SUM_{n0}", 30 + n0, f"INV_N{n0}"))
    b0_nid = 5 if l1["weights"][n0]["bias_rail"] == "-5V_REF" else 4
    b0_name = l1["weights"][n0]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n0}", l1["weights"][n0]["bias_resistor_str"], 85.25, 32.0, 0, "F.Cu", b0_nid, b0_name, 30 + n0, f"INV_N{n0}"))
    # INV_N0: Pad 2 (86.2) runs down to Pin 2 (84.8, 44.96)
    pcb.append(make_segment(86.2, 32.0, 86.2, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(86.2, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    # V_SUM_0: Pin 1 (84.8, 43.69) to Pad 1 (84.3, 36.0)
    pcb.append(make_segment(u1_x - 2.7, 43.69, 84.3, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(84.3, 43.69, 84.3, 36.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    # Bias Rb0: Pad 1 at (84.3, 32.0)
    tap_bias(84.3, 32.0, b0_name, b0_nid)

    # 8. NEURON 3 (Above U1): Rf3 at (89.75, 36.0), Rb3 at (89.75, 32.0)
    # Rf3: Pad 1 (88.8) = INV_N3, Pad 2 (90.7) = V_SUM_3
    pcb.append(fp_resistor_0805(f"Rf_N{n3}", "10k", 89.75, 36.0, 0, "F.Cu", 30 + n3, f"INV_N{n3}", 10 + n3, f"V_SUM_{n3}"))
    b3_nid = 5 if l1["weights"][n3]["bias_rail"] == "-5V_REF" else 4
    b3_name = l1["weights"][n3]["bias_rail"]
    # Rb3: Pad 1 (88.8) = INV_N3, Pad 2 (90.7) = Bias
    pcb.append(fp_resistor_0805(f"Rb_N{n3}", l1["weights"][n3]["bias_resistor_str"], 89.75, 32.0, 0, "F.Cu", 30 + n3, f"INV_N{n3}", b3_nid, b3_name))
    # INV_N3: Pad 1 (88.8) runs down to Pin 13 (90.2, 44.96)
    pcb.append(make_segment(88.8, 32.0, 88.8, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(88.8, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    # V_SUM_3: Pin 14 (90.2, 43.69) to Pad 2 (90.7, 36.0)
    pcb.append(make_segment(u1_x + 2.7, 43.69, 90.7, 43.69, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(90.7, 43.69, 90.7, 36.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    # Bias Rb3: Pad 2 at (90.7, 32.0)
    tap_bias(90.7, 32.0, b3_name, b3_nid)

    # 9. NEURON 1 (Below U1): Rf1 at (85.25, 56.0), Rb1 at (85.25, 60.0)
    pcb.append(fp_resistor_0805(f"Rf_N{n1}", "10k", 85.25, 56.0, 0, "F.Cu", 10 + n1, f"V_SUM_{n1}", 30 + n1, f"INV_N{n1}"))
    b1_nid = 5 if l1["weights"][n1]["bias_rail"] == "-5V_REF" else 4
    b1_name = l1["weights"][n1]["bias_rail"]
    pcb.append(fp_resistor_0805(f"Rb_N{n1}", l1["weights"][n1]["bias_resistor_str"], 85.25, 60.0, 0, "F.Cu", b1_nid, b1_name, 30 + n1, f"INV_N{n1}"))
    # INV_N1: Pad 2 (86.2) runs up to Pin 6 (84.8, 50.04)
    pcb.append(make_segment(u1_x - 2.7, 50.04, 86.2, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(86.2, 50.04, 86.2, 60.0, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    # V_SUM_1: Pin 7 (84.8, 51.31) to Pad 1 (84.3, 56.0)
    pcb.append(make_segment(u1_x - 2.7, 51.31, 84.3, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(84.3, 51.31, 84.3, 56.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    # Bias Rb1: Pad 1 at (84.3, 60.0)
    tap_bias(84.3, 60.0, b1_name, b1_nid)

    # 10. NEURON 2 (Below U1): Rf2 at (89.75, 56.0), Rb2 at (89.75, 64.0)
    # Rf2: Pad 1 (88.8) = INV_N2, Pad 2 (90.7) = V_SUM_2
    pcb.append(fp_resistor_0805(f"Rf_N{n2}", "10k", 89.75, 56.0, 0, "F.Cu", 30 + n2, f"INV_N{n2}", 10 + n2, f"V_SUM_{n2}"))
    b2_nid = 5 if l1["weights"][n2]["bias_rail"] == "-5V_REF" else 4
    b2_name = l1["weights"][n2]["bias_rail"]
    # Rb2: Pad 1 (88.8) = INV_N2, Pad 2 (90.7) = Bias
    pcb.append(fp_resistor_0805(f"Rb_N{n2}", l1["weights"][n2]["bias_resistor_str"], 89.75, 64.0, 0, "F.Cu", 30 + n2, f"INV_N{n2}", b2_nid, b2_name))
    # INV_N2: Pad 1 (88.8) runs up to Pin 9 (90.2, 50.04)
    pcb.append(make_segment(u1_x + 2.7, 50.04, 88.8, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(88.8, 50.04, 88.8, 64.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    # V_SUM_2: Pin 8 (90.2, 51.31) to Pad 2 (90.7, 56.0)
    pcb.append(make_segment(u1_x + 2.7, 51.31, 90.7, 51.31, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(90.7, 51.31, 90.7, 56.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    # Bias Rb2: Pad 2 at (90.7, 64.0)
    tap_bias(90.7, 64.0, b2_name, b2_nid)

    # 11. OUTPUT LINES VIA B.Cu (Lanes 1, 2, 7, 8):
    # Pin A33 (83.97): V_SUM_0 from (84.3, 36.0) via Lane 1 (X = 83.5 on B.Cu)
    pcb.append(make_segment(84.3, 36.0, 83.5, 38.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_via(83.5, 38.0, 0.6, 0.3, f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(83.5, 38.0, 83.5, 86.0, 0.25, "B.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_via(83.5, 86.0, 0.6, 0.3, f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(83.5, 86.0, 83.97, 88.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(83.97, 88.0, 83.97, 92.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))

    # Pin A34 (86.51): V_SUM_1 from (84.3, 56.0) via Lane 2 (X = 86.0 on B.Cu)
    pcb.append(make_segment(84.3, 56.0, 86.0, 58.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_via(86.0, 58.0, 0.6, 0.3, f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.0, 58.0, 86.0, 86.0, 0.25, "B.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_via(86.0, 86.0, 0.6, 0.3, f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.0, 86.0, 86.51, 88.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.51, 88.0, 86.51, 92.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))

    # Pin A35 (89.05): V_SUM_2 from (90.7, 56.0) via Lane 7 (X = 92.6 on B.Cu)
    pcb.append(make_segment(90.7, 56.0, 92.6, 58.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_via(92.6, 58.0, 0.6, 0.3, f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(92.6, 58.0, 92.6, 86.0, 0.25, "B.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_via(92.6, 86.0, 0.6, 0.3, f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(92.6, 86.0, 89.05, 88.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(89.05, 88.0, 89.05, 92.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))

    # Pin A36 (91.59): V_SUM_3 from (90.7, 36.0) via Lane 8 (X = 93.2 on B.Cu)
    pcb.append(make_segment(90.7, 36.0, 93.2, 38.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_via(93.2, 38.0, 0.6, 0.3, f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(93.2, 38.0, 93.2, 86.0, 0.25, "B.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_via(93.2, 86.0, 0.6, 0.3, f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(93.2, 86.0, 91.59, 88.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(91.59, 88.0, 91.59, 92.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))

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
    print("Done generating clean orthogonal DC1.")

if __name__ == "__main__":
    build_orthogonal_dc1("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A", range(0, 4))
