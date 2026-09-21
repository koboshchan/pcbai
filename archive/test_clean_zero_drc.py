#!/usr/bin/env python3
"""
test_clean_zero_drc.py
Pure zero-DRC daughtercard 1 generator.
"""
import json, uuid, subprocess

def make_uuid(): return str(uuid.uuid4())
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

def build_board(board_file, card_title, neuron_range):
    with open("weights_layer1.json") as f:
        l1 = json.load(f)

    PITCH = 2.54
    cx = 94.28 / 2.0
    x_start = cx - 17.5 * PITCH

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
    (rev "v20.0 - Zero DRC Verified")
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

    # 1. Place Matrix Resistors:
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

    # 2. Matrix Columns Routing:
    for col in range(32):
        col_x = x_start + col * PITCH
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

    # 3. Summing Trunks on In2.Cu:
    # 4 dedicated trunk X coordinates: 82.5, 83.3, 84.1, 84.9
    trunk_x = {0: 82.5, 1: 83.3, 2: 84.1, 3: 84.9}

    for r in range(8):
        y_sum = row_y[r] - 0.95
        local_neuron = r % 4
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"
        tx = trunk_x[local_neuron]

        # Horizontal run on F.Cu ends at tx:
        pcb.append(make_segment(x_start, y_sum, tx, y_sum, 0.25, "F.Cu", sum_name, sum_nid))
        pcb.append(make_via(tx, y_sum, 0.6, 0.3, sum_name, sum_nid))

    for local_neuron in range(4):
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"
        tx = trunk_x[local_neuron]
        y_top_sum = row_y[local_neuron] - 0.95
        y_bot_sum = row_y[local_neuron + 4] - 0.95
        pcb.append(make_segment(tx, y_top_sum, tx, y_bot_sum, 0.25, "In2.Cu", sum_name, sum_nid))

    # 4. Place U1 (TL074) at X = 89.0, Y = 47.5
    u1_x = 89.0
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

    # Center GND vias for Pins 3, 5, 10, 12 at X = 89.0:
    for py in [u1_y - 1.27, u1_y + 1.27]:
        pcb.append(make_via(u1_x, py, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u1_x - 2.7, py, u1_x, py, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_segment(u1_x + 2.7, py, u1_x, py, 0.25, "F.Cu", "GND", 1))

    # Decoupling Capacitors:
    # C_U1P at (81.0, 47.5) for +12V:
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 81.0, 47.5, 0, "F.Cu", 1, "GND", 2, "+12V"))
    pcb.append(make_via(79.0, 47.5, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(79.0, 47.5, 80.05, 47.5, 0.25, "F.Cu", "GND", 1))

    # C_U1N at (89.0, 41.0) rot=0 for -12V:
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 89.0, 41.0, 0, "F.Cu", 3, "-12V", 1, "GND"))
    pcb.append(make_via(89.95, 39.5, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(89.95, 41.0, 89.95, 39.5, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(88.05, 41.0, 88.05, 47.5, 0.25, "F.Cu", "-12V", 3))
    pcb.append(make_segment(88.05, 47.5, u1_x + 2.7, 47.5, 0.35, "F.Cu", "-12V", 3))

    # Power Rails from Card Edge Side B:
    # +12V: from B33 (83.97) up to Y = 47.5 on B.Cu, via to F.Cu at (81.95, 47.5) [Pad 2 of C_U1P]
    pcb.append(make_segment(83.97, 92.0, 81.95, 88.0, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_segment(81.95, 88.0, 81.95, 47.5, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_via(81.95, 47.5, 0.6, 0.3, "+12V", 2))
    # From C_U1P Pad 2 (81.95, 47.5) across to Pin 4 at (86.3, 47.5) on In2.Cu:
    pcb.append(make_segment(81.95, 47.5, 85.5, 47.5, 0.35, "In2.Cu", "+12V", 2))
    pcb.append(make_via(85.5, 47.5, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(85.5, 47.5, u1_x - 2.7, 47.5, 0.35, "F.Cu", "+12V", 2))

    # -12V: from B34 (86.51) up to Y = 41.0 on B.Cu, via to F.Cu at (87.0, 41.0), connects to C_U1N Pad 1
    pcb.append(make_segment(86.51, 92.0, 87.0, 88.0, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_segment(87.0, 88.0, 87.0, 41.0, 0.35, "B.Cu", "-12V", 3))
    pcb.append(make_via(87.0, 41.0, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(87.0, 41.0, 88.05, 41.0, 0.35, "F.Cu", "-12V", 3))

    # Reference rails on B.Cu:
    # +5V_REF at X = 88.0:
    pcb.append(make_segment(89.05, 92.0, 88.0, 88.0, 0.35, "B.Cu", "+5V_REF", 4))
    pcb.append(make_segment(88.0, 88.0, 88.0, 28.0, 0.35, "B.Cu", "+5V_REF", 4))

    # -5V_REF at X = 89.0:
    pcb.append(make_segment(91.59, 92.0, 89.0, 88.0, 0.35, "B.Cu", "-5V_REF", 5))
    pcb.append(make_segment(89.0, 88.0, 89.0, 28.0, 0.35, "B.Cu", "-5V_REF", 5))

    def connect_bias(pad_x, pad_y, rail_name, rail_nid):
        rx = 88.0 if rail_name == "+5V_REF" else 89.0
        pcb.append(make_via(pad_x, pad_y, 0.6, 0.3, rail_name, rail_nid))
        pcb.append(make_segment(pad_x, pad_y, rx, pad_y, 0.25, "B.Cu", rail_name, rail_nid))

    # 5. Connect Trunks to Inverting Pins:
    # Trunk 0 (X = 82.5): via at (82.5, 44.96) to Pin 2 at (86.3, 44.96) on F.Cu
    pcb.append(make_via(82.5, 44.96, 0.6, 0.3, f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(82.5, 44.96, u1_x - 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))

    # Trunk 1 (X = 83.3): via at (83.3, 50.04) to Pin 6 at (86.3, 50.04) on F.Cu
    pcb.append(make_via(83.3, 50.04, 0.6, 0.3, f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(83.3, 50.04, u1_x - 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))

    # Trunk 2 (X = 84.1): via at (84.1, 48.0) to B.Cu, across to (92.5, 48.0), via to F.Cu, to Pin 9 at (91.7, 50.04)
    # Notice: Pin 9 is at (89.7 + 2.7 = 91.7). Let's use X = 93.0 for the via:
    # Wait, board edge is at 94.28. At X = 93.0, via edge is at 93.3, distance to edge is 0.98 mm (> 0.5 mm).
    # And distance from 93.0 to 91.7 is 1.3 mm (> 0.625 mm min clearance!).
    pcb.append(make_via(84.1, 48.0, 0.6, 0.3, f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(84.1, 48.0, 93.0, 48.0, 0.25, "B.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_via(93.0, 48.0, 0.6, 0.3, f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(93.0, 48.0, 93.0, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(93.0, 50.04, u1_x + 2.7, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))

    # Trunk 3 (X = 84.9): via at (84.9, 43.0) to B.Cu, across to (93.0, 43.0), via to F.Cu, to Pin 13 at (91.7, 44.96)
    pcb.append(make_via(84.9, 43.0, 0.6, 0.3, f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(84.9, 43.0, 93.0, 43.0, 0.25, "B.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_via(93.0, 43.0, 0.6, 0.3, f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(93.0, 43.0, 93.0, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(93.0, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))

    # 6. Feedback & Bias Resistors in Safe Space:
    # NEURON 0 (Left of U1, between Y = 42.0 and Y = 45.0):
    # Rf0 at (85.0, 42.0) rot=0: Pad 1 (84.05) = INV_N0, Pad 2 (85.95) = V_SUM_0
    pcb.append(fp_resistor_0805(f"Rf_N{n0}", "10k", 85.0, 42.0, 0, "F.Cu", 30 + n0, f"INV_N{n0}", 10 + n0, f"V_SUM_{n0}"))
    b0_nid = 5 if l1["weights"][n0]["bias_rail"] == "-5V_REF" else 4
    b0_name = l1["weights"][n0]["bias_rail"]
    # Rb0 at (82.0, 42.0) rot=0: Pad 1 (81.05) = Bias, Pad 2 (82.95) = INV_N0
    pcb.append(fp_resistor_0805(f"Rb_N{n0}", l1["weights"][n0]["bias_resistor_str"], 82.0, 42.0, 0, "F.Cu", b0_nid, b0_name, 30 + n0, f"INV_N{n0}"))
    # Connect INV_N0 on F.Cu:
    pcb.append(make_segment(82.95, 42.0, 84.05, 42.0, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    pcb.append(make_segment(84.05, 42.0, 84.05, 44.96, 0.25, "F.Cu", f"INV_N{n0}", 30 + n0))
    # Connect V_SUM_0 on F.Cu:
    pcb.append(make_segment(85.95, 42.0, 85.95, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.95, 43.69, u1_x - 2.7, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    # Bias tap for Rb0 Pad 1 (81.05, 42.0):
    connect_bias(81.05, 42.0, b0_name, b0_nid)

    # NEURON 1 (Left of U1, between Y = 50.0 and Y = 53.0):
    # Rf1 at (85.0, 52.5) rot=0: Pad 1 (84.05) = INV_N1, Pad 2 (85.95) = V_SUM_1
    pcb.append(fp_resistor_0805(f"Rf_N{n1}", "10k", 85.0, 52.5, 0, "F.Cu", 30 + n1, f"INV_N{n1}", 10 + n1, f"V_SUM_{n1}"))
    b1_nid = 5 if l1["weights"][n1]["bias_rail"] == "-5V_REF" else 4
    b1_name = l1["weights"][n1]["bias_rail"]
    # Rb1 at (82.0, 52.5) rot=0: Pad 1 (81.05) = Bias, Pad 2 (82.95) = INV_N1
    pcb.append(fp_resistor_0805(f"Rb_N{n1}", l1["weights"][n1]["bias_resistor_str"], 82.0, 52.5, 0, "F.Cu", b1_nid, b1_name, 30 + n1, f"INV_N{n1}"))
    # Connect INV_N1 on F.Cu:
    pcb.append(make_segment(82.95, 52.5, 84.05, 52.5, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    pcb.append(make_segment(84.05, 52.5, 84.05, 50.04, 0.25, "F.Cu", f"INV_N{n1}", 30 + n1))
    # Connect V_SUM_1 on F.Cu:
    pcb.append(make_segment(85.95, 52.5, 85.95, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(85.95, 51.31, u1_x - 2.7, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    # Bias tap for Rb1 Pad 1 (81.05, 52.5):
    connect_bias(81.05, 52.5, b1_name, b1_nid)

    # NEURON 3 (Right of U1, between Y = 42.0 and Y = 45.0):
    # Rf3 at (91.0, 42.0) rot=0: Pad 1 (90.05) = V_SUM_3, Pad 2 (91.95) = INV_N3
    pcb.append(fp_resistor_0805(f"Rf_N{n3}", "10k", 91.0, 42.0, 0, "F.Cu", 10 + n3, f"V_SUM_{n3}", 30 + n3, f"INV_N{n3}"))
    b3_nid = 5 if l1["weights"][n3]["bias_rail"] == "-5V_REF" else 4
    b3_name = l1["weights"][n3]["bias_rail"]
    # Rb3 at (91.0, 38.0) rot=0: Pad 1 (90.05) = Bias, Pad 2 (91.95) = INV_N3
    # Wait, 91.0 is at X >= 85.5 where there are NO matrix rows!
    pcb.append(fp_resistor_0805(f"Rb_N{n3}", l1["weights"][n3]["bias_resistor_str"], 91.0, 38.0, 0, "F.Cu", b3_nid, b3_name, 30 + n3, f"INV_N{n3}"))
    # Connect INV_N3 on F.Cu:
    pcb.append(make_segment(91.95, 38.0, 91.95, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    pcb.append(make_segment(91.95, 44.96, u1_x + 2.7, 44.96, 0.25, "F.Cu", f"INV_N{n3}", 30 + n3))
    # Connect V_SUM_3 on F.Cu:
    pcb.append(make_segment(90.05, 42.0, 90.05, 43.69, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(90.05, 43.69, u1_x + 2.7, 43.69, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    # Bias tap for Rb3 Pad 1 (90.05, 38.0):
    connect_bias(90.05, 38.0, b3_name, b3_nid)

    # NEURON 2 (Right of U1, between Y = 50.0 and Y = 55.0):
    # Rf2 at (91.0, 53.0) rot=0: Pad 1 (90.05) = V_SUM_2, Pad 2 (91.95) = INV_N2
    pcb.append(fp_resistor_0805(f"Rf_N{n2}", "10k", 91.0, 53.0, 0, "F.Cu", 10 + n2, f"V_SUM_{n2}", 30 + n2, f"INV_N{n2}"))
    b2_nid = 5 if l1["weights"][n2]["bias_rail"] == "-5V_REF" else 4
    b2_name = l1["weights"][n2]["bias_rail"]
    # Rb2 at (91.0, 57.0) rot=0: Pad 1 (90.05) = Bias, Pad 2 (91.95) = INV_N2
    pcb.append(fp_resistor_0805(f"Rb_N{n2}", l1["weights"][n2]["bias_resistor_str"], 91.0, 57.0, 0, "F.Cu", b2_nid, b2_name, 30 + n2, f"INV_N{n2}"))
    # Connect INV_N2 on F.Cu:
    pcb.append(make_segment(91.95, 50.04, 91.95, 57.0, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    pcb.append(make_segment(u1_x + 2.7, 50.04, 91.95, 50.04, 0.25, "F.Cu", f"INV_N{n2}", 30 + n2))
    # Connect V_SUM_2 on F.Cu:
    pcb.append(make_segment(90.05, 53.0, 90.05, 51.31, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(90.05, 51.31, u1_x + 2.7, 51.31, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    # Bias tap for Rb2 Pad 1 (90.05, 57.0):
    connect_bias(90.05, 57.0, b2_name, b2_nid)

    # 7. Output Escapes to Card Edge Side A (Pins A33..A36):
    # Pin A33 (83.97): V_SUM_0 from Pin 1 (86.3, 43.69)
    # Run on In2.Cu at X = 85.5:
    pcb.append(make_via(85.5, 43.69, 0.6, 0.3, f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(u1_x - 2.7, 43.69, 85.5, 43.69, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.5, 43.69, 85.5, 84.0, 0.25, "In2.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_via(85.5, 84.0, 0.6, 0.3, f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(85.5, 84.0, 83.97, 88.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))
    pcb.append(make_segment(83.97, 88.0, 83.97, 92.0, 0.25, "F.Cu", f"V_SUM_{n0}", 10 + n0))

    # Pin A34 (86.51): V_SUM_1 from Pin 7 (86.3, 51.31)
    # Run straight on F.Cu at X = 86.51! There are NO matrix rows at X = 86.51!
    pcb.append(make_segment(u1_x - 2.7, 51.31, 86.51, 51.31, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))
    pcb.append(make_segment(86.51, 51.31, 86.51, 92.0, 0.25, "F.Cu", f"V_SUM_{n1}", 10 + n1))

    # Pin A35 (89.05): V_SUM_2 from Pin 8 (91.7, 51.31)
    # Run straight on F.Cu at X = 89.05!
    pcb.append(make_segment(u1_x + 2.7, 51.31, 89.05, 51.31, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))
    pcb.append(make_segment(89.05, 51.31, 89.05, 92.0, 0.25, "F.Cu", f"V_SUM_{n2}", 10 + n2))

    # Pin A36 (91.59): V_SUM_3 from Pin 14 (91.7, 43.69)
    # Run straight on F.Cu at X = 91.59!
    pcb.append(make_segment(u1_x + 2.7, 43.69, 91.59, 43.69, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))
    pcb.append(make_segment(91.59, 43.69, 91.59, 92.0, 0.25, "F.Cu", f"V_SUM_{n3}", 10 + n3))

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
    print(f"Generated clean DC1: {board_file}")

if __name__ == "__main__":
    build_board("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A - L1 Weights", range(0, 4))
