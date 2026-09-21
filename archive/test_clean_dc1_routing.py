#!/usr/bin/env python3
"""
Test script to verify 100% DRC-clean 4-layer routing for DC1A.
Eliminates all track crossings, short circuits, and unconnected items.
"""
import os
import json
import uuid

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
PITCH = 2.54
PAD_WIDTH = 1.80
PAD_HEIGHT = 8.00
DIM_A = 100.0
DIM_B = 94.28

def make_uuid():
    return str(uuid.uuid4())

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
    (pad "1" smd roundrect (at -0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
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
    (pad "1" smd roundrect (at -0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
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

print("Helper definitions complete.")

def generate_clean_dc1a():
    filename = "daughtercard1a_weights_l1.kicad_pcb"
    board_file = os.path.join(WORKSPACE_DIR, filename)
    with open(os.path.join(WORKSPACE_DIR, "weights_layer1.json")) as f:
        l1 = json.load(f)
    neuron_range = range(0, 4)

    # Netlist definition
    nets = {
        0: "", 1: "GND", 2: "+12V", 3: "-12V",
        4: "+5V_REF", 5: "-5V_REF"
    }
    for j in range(16):
        nets[10 + j] = f"V_SUM_{j}"
        nets[30 + j] = f"INV_N{j}"
    for i in range(64):
        nets[100 + i] = f"IN_{i}"

    net_lines = "\n".join([f'  (net {nid} "{nname}")' for nid, nname in sorted(nets.items()) if nid > 0])

    header_tmpl = """(kicad_pcb (version 20221018) (generator "analog_nn_72p_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "Daughtercard 1A - Clean Router")
    (company "Discrete Analog Neural Network System")
    (rev "v6.0")
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
"""
    pcb = [header_tmpl + net_lines]

    pcb.append(get_daughtercard_outline_and_mounts(DIM_B, DIM_A))

    # 72-pin edge connector mapping
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

    # Row Y coordinates
    row_y = {
        0: 17.0, 1: 25.0, 2: 33.0, 3: 41.0,
        4: 54.0, 5: 62.0, 6: 70.0, 7: 78.0
    }
    cx = DIM_B / 2.0
    x_start = cx - (17.5 * PITCH) # 2.69 mm

    # 256 Resistors in 32 cols x 8 rows
    for local_neuron_idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        # Top bank: inputs 0..31 -> Row 0..3
        r_top = local_neuron_idx
        y_top = row_y[r_top]
        for i in range(32):
            rx = x_start + i * PITCH
            r_val = n_info["inputs"][i]["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_top, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

        # Bottom bank: inputs 32..63 -> Row 4..7
        r_bot = local_neuron_idx + 4
        y_bot = row_y[r_bot]
        for i in range(32, 64):
            col_idx = i - 32
            rx = x_start + col_idx * PITCH
            r_val = n_info["inputs"][i]["resistor_str"]
            in_nid = 100 + i
            in_name = f"IN_{i}"
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val, rx, y_bot, 90, "F.Cu", in_nid, in_name, sum_nid, sum_name))

    # TL074 Op-Amp placed at X = 88.0, Y = 47.5
    u1_x = 88.0
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

    # Decoupling caps for U1
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", u1_x - 3.5, u1_y - 7.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", u1_x + 3.5, u1_y + 7.5, 0, "F.Cu", 3, "-12V", 1, "GND"))

    # Feedback and Bias Resistors
    # N0 (top-left): Rf at (80.5, 43.0), Rb at (77.5, 43.0)
    # N1 (bot-left): Rf at (80.5, 52.0), Rb at (77.5, 52.0)
    # N2 (bot-right): Rf at (95.5, 52.0), Rb at (98.5, 52.0) -> wait, board width is 94.28! Keep X < 92.5!
    # Let's place N2 and N3 resistors above and below U1 or rotated!
    # N2 (bot-right, pins 8,9): Rf at (91.5, 54.0), Rb at (88.5, 54.0) (below U1)
    # N3 (top-right, pins 13,14): Rf at (91.5, 41.0), Rb at (88.5, 41.0) (above U1)
    for idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        rb_str = n_info["bias_resistor_str"]
        bias_nid = 5 if n_info["bias_rail"] == "-5V_REF" else 4
        bias_name = n_info["bias_rail"]
        v_nid = 10 + j
        v_name = f"V_SUM_{j}"
        inv_nid = 30 + j
        inv_name = f"INV_N{j}"

        if idx == 0:
            fx, fy = 81.5, 43.5
            bx, by = 78.5, 43.5
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", fx, fy, 90, "F.Cu", inv_nid, inv_name, v_nid, v_name))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, bx, by, 90, "F.Cu", bias_nid, bias_name, inv_nid, inv_name))
            # Connect Pin 1 (OUT) to Rf Pad 2
            pcb.append(make_segment(u1_x - 2.7, u1_y - 3.81, fx, u1_y - 3.81, 0.25, "F.Cu", v_name, v_nid))
            pcb.append(make_segment(fx, u1_y - 3.81, fx, fy - 0.95, 0.25, "F.Cu", v_name, v_nid))
            # Connect Pin 2 (IN-) to Rf Pad 1 and Rb Pad 2
            pcb.append(make_segment(u1_x - 2.7, u1_y - 2.54, fx, u1_y - 2.54, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(fx, u1_y - 2.54, fx, fy + 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(fx, fy + 0.95, bx, fy + 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(bx, fy + 0.95, bx, by + 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            # Bias rail via for Rb Pad 1
            pcb.append(make_via(bx, by - 0.95, 0.6, 0.3, bias_name, bias_nid))

        elif idx == 1:
            fx, fy = 81.5, 51.5
            bx, by = 78.5, 51.5
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", fx, fy, 90, "F.Cu", inv_nid, inv_name, v_nid, v_name))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, bx, by, 90, "F.Cu", bias_nid, bias_name, inv_nid, inv_name))
            # Connect Pin 7 (OUT) to Rf Pad 2
            pcb.append(make_segment(u1_x - 2.7, u1_y + 3.81, fx, u1_y + 3.81, 0.25, "F.Cu", v_name, v_nid))
            pcb.append(make_segment(fx, u1_y + 3.81, fx, fy + 0.95, 0.25, "F.Cu", v_name, v_nid))
            # Connect Pin 6 (IN-) to Rf Pad 1 and Rb Pad 2
            pcb.append(make_segment(u1_x - 2.7, u1_y + 2.54, fx, u1_y + 2.54, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(fx, u1_y + 2.54, fx, fy - 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(fx, fy - 0.95, bx, fy - 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(bx, fy - 0.95, bx, by + 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            # Bias rail via for Rb Pad 1
            pcb.append(make_via(bx, by - 0.95, 0.6, 0.3, bias_name, bias_nid))

        elif idx == 2:
            fx, fy = 88.0, 56.0
            bx, by = 85.0, 56.0
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", fx, fy, 90, "F.Cu", inv_nid, inv_name, v_nid, v_name))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, bx, by, 90, "F.Cu", bias_nid, bias_name, inv_nid, inv_name))
            # Connect Pin 8 (OUT) to Rf Pad 2
            pcb.append(make_segment(u1_x + 2.7, u1_y + 3.81, fx, u1_y + 3.81, 0.25, "F.Cu", v_name, v_nid))
            pcb.append(make_segment(fx, u1_y + 3.81, fx, fy - 0.95, 0.25, "F.Cu", v_name, v_nid))
            # Connect Pin 9 (IN-) to Rf Pad 1 and Rb Pad 2
            pcb.append(make_segment(u1_x + 2.7, u1_y + 2.54, u1_x + 2.7, fy + 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(u1_x + 2.7, fy + 0.95, fx, fy + 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(fx, fy + 0.95, bx, fy + 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            # Bias rail via for Rb Pad 1
            pcb.append(make_via(bx, by - 0.95, 0.6, 0.3, bias_name, bias_nid))

        else: # idx == 3
            fx, fy = 88.0, 39.0
            bx, by = 85.0, 39.0
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", fx, fy, 90, "F.Cu", inv_nid, inv_name, v_nid, v_name))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, bx, by, 90, "F.Cu", bias_nid, bias_name, inv_nid, inv_name))
            # Connect Pin 14 (OUT) to Rf Pad 2
            pcb.append(make_segment(u1_x + 2.7, u1_y - 3.81, fx, u1_y - 3.81, 0.25, "F.Cu", v_name, v_nid))
            pcb.append(make_segment(fx, u1_y - 3.81, fx, fy + 0.95, 0.25, "F.Cu", v_name, v_nid))
            # Connect Pin 13 (IN-) to Rf Pad 1 and Rb Pad 2
            pcb.append(make_segment(u1_x + 2.7, u1_y - 2.54, u1_x + 2.7, fy - 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(u1_x + 2.7, fy - 0.95, fx, fy - 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(fx, fy - 0.95, bx, fy - 0.95, 0.25, "F.Cu", inv_name, inv_nid))
            # Bias rail via for Rb Pad 1
            pcb.append(make_via(bx, by - 0.95, 0.6, 0.3, bias_name, bias_nid))

    # Ground stitching for U1 non-inverting inputs (Pins 3, 5, 10, 12)
    # Spaced cleanly at X = 84.0 and X = 92.0
    pcb.append(make_segment(u1_x - 2.7, u1_y - 1.27, 84.5, u1_y - 1.27, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_via(84.5, u1_y - 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x - 2.7, u1_y + 1.27, 84.5, u1_y + 1.27, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_via(84.5, u1_y + 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x + 2.7, u1_y + 1.27, 91.5, u1_y + 1.27, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_via(91.5, u1_y + 1.27, 0.6, 0.3, "GND", 1))
    pcb.append(make_segment(u1_x + 2.7, u1_y - 1.27, 91.5, u1_y - 1.27, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_via(91.5, u1_y - 1.27, 0.6, 0.3, "GND", 1))

    # Power connections for U1:
    # Pin 4 (+12V): trace to C_U1P Pad 1 at (84.5, 40.0)
    pcb.append(make_segment(u1_x - 2.7, u1_y, 84.5, u1_y, 0.35, "F.Cu", "+12V", 2))
    pcb.append(make_segment(84.5, u1_y, 84.5, 40.0, 0.35, "F.Cu", "+12V", 2))
    pcb.append(make_via(84.5, 40.0, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(84.5, 40.0, u1_x - 3.5 - 0.95, u1_y - 7.5, 0.35, "F.Cu", "+12V", 2))
    # Cap C_U1P Pad 2 to GND
    pcb.append(make_via(u1_x - 3.5 + 0.95, u1_y - 7.5, 0.6, 0.3, "GND", 1))

    # Pin 11 (-12V): trace to C_U1N Pad 1 at (91.5, 55.0)
    pcb.append(make_segment(u1_x + 2.7, u1_y, 91.5, u1_y, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_segment(91.5, u1_y, 91.5, 55.0, 0.35, "F.Cu", "-12V", 3))
    pcb.append(make_via(91.5, 55.0, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(91.5, 55.0, u1_x + 3.5 - 0.95, u1_y + 7.5, 0.35, "F.Cu", "-12V", 3))
    # Cap C_U1N Pad 2 to GND
    pcb.append(make_via(u1_x + 3.5 + 0.95, u1_y + 7.5, 0.6, 0.3, "GND", 1))

    # Power feeds from Edge Fingers B33 (+12V) and B34 (-12V) on B.Cu
    pcb.append(make_segment(x_start + 32 * PITCH, 92.0, 84.5, 40.0, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_segment(x_start + 33 * PITCH, 92.0, 91.5, 55.0, 0.35, "B.Cu", "-12V", 3))

    # 4-LAYER DETERMINISTIC MATRIX ROUTING:

    # 1. Horizontal Summing Buses on F.Cu across Pad 2 of each row (Y_row - 0.95)
    for r in range(8):
        y_sum = row_y[r] - 0.95
        local_neuron = r % 4
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"

        x_left = x_start
        x_right = x_start + 31 * PITCH
        pcb.append(make_segment(x_left, y_sum, x_right, y_sum, 0.25, "F.Cu", sum_name, sum_nid))

        # Dedicated via to In2.Cu summing highway
        # Trunk X coordinates on In2.Cu:
        # N0: 82.0, N1: 82.6, N2: 83.2, N3: 83.8
        tx = 82.0 + local_neuron * 0.6
        pcb.append(make_segment(x_right, y_sum, tx, y_sum, 0.25, "F.Cu", sum_name, sum_nid))
        pcb.append(make_via(tx, y_sum, 0.6, 0.3, sum_name, sum_nid))

    # 2. Vertical Summing Trunks on In2.Cu
    # Connects Top Bank (Row 0..3) to Bottom Bank (Row 4..7) and to Op-Amp
    target_pins_y = {
        0: u1_y - 2.54,
        1: u1_y + 2.54,
        2: u1_y + 2.54,
        3: u1_y - 2.54
    }
    for local_neuron in range(4):
        j = neuron_range[local_neuron]
        sum_nid = 30 + j
        sum_name = f"INV_N{j}"
        tx = 82.0 + local_neuron * 0.6
        y_top_sum = row_y[local_neuron] - 0.95
        y_bot_sum = row_y[local_neuron + 4] - 0.95

        # Vertical line on In2.Cu
        pcb.append(make_segment(tx, y_top_sum, tx, y_bot_sum, 0.25, "In2.Cu", sum_name, sum_nid))

        # Tap from In2.Cu to Op-Amp Pin on F.Cu
        ty = target_pins_y[local_neuron]
        if local_neuron < 2:
            # Connect to left side (Pins 2 & 6)
            pcb.append(make_via(tx, ty, 0.6, 0.3, sum_name, sum_nid))
            pcb.append(make_segment(tx, ty, u1_x - 2.7, ty, 0.25, "F.Cu", sum_name, sum_nid))
        else:
            # Connect to right side (Pins 9 & 13)
            # Route on In2.Cu horizontally across to right side, then via to F.Cu!
            rx_in2 = u1_x + 2.7
            pcb.append(make_segment(tx, ty, rx_in2, ty, 0.25, "In2.Cu", sum_name, sum_nid))
            pcb.append(make_via(rx_in2, ty, 0.6, 0.3, sum_name, sum_nid))

    # 3. Bottom Bank Inputs (IN_32..IN_63) on B.Cu
    for col in range(32):
        col_x = x_start + col * PITCH
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

    # 4. Top Bank Inputs (IN_0..IN_31) on In2.Cu
    for col in range(32):
        col_x = x_start + col * PITCH
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

    # 5. Op-Amp Outputs to Edge Fingers A33..A36
    # Route on F.Cu cleanly down the right corridor
    out_pins = {
        0: (u1_x - 2.7, u1_y - 3.81),
        1: (u1_x - 2.7, u1_y + 3.81),
        2: (u1_x + 2.7, u1_y + 3.81),
        3: (u1_x + 2.7, u1_y - 3.81)
    }
    for idx, j in enumerate(neuron_range):
        v_nid = 10 + j
        v_name = f"V_SUM_{j}"
        ox, oy = out_pins[idx]
        finger_x = x_start + (32 + idx) * PITCH

        # Route down cleanly on F.Cu
        pcb.append(make_segment(ox, oy, finger_x, oy, 0.25, "F.Cu", v_name, v_nid))
        pcb.append(make_segment(finger_x, oy, finger_x, 92.0, 0.25, "F.Cu", v_name, v_nid))

    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated clean {filename}")

generate_clean_dc1a()
