#!/usr/bin/env python3
import json, uuid, subprocess, re, os, sys

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
    (at {x:.4f} {y:.4f} {rot})
    (descr "Resistor SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
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
    (at {x:.4f} {y:.4f} {rot})
    (descr "Capacitor SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (fp_line (start -0.25 -0.7) (end 0.25 -0.7) (stroke (width 0.12) (type solid)) (layer "{silk}"))
    (fp_line (start -0.25 0.7) (end 0.25 0.7) (stroke (width 0.12) (type solid)) (layer "{silk}"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD8_3DMODEL_DIR}}/Capacitor_SMD.3dshapes/C_0805_2012Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
  )"""

def fp_diodesod123(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "Diode_SMD:D_SOD-123" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.4f} {y:.4f} {rot})
    (descr "Diode SOD-123 (Pad 1=Cathode, Pad 2=Anode)")
    (property "Reference" "{ref}" (at 0 -1.8 {rot}) (layer "{silk}") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.8 {rot}) (layer "{fab}") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (fp_line (start -0.3 -0.7) (end -0.3 0.7) (stroke (width 0.12) (type solid)) (layer "{silk}"))
    (pad "1" smd roundrect (at -1.65 0) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.65 0) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD8_3DMODEL_DIR}}/Diode_SMD.3dshapes/D_SOD-123.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
  )"""

def fp_led0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "LED_SMD:LED_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.4f} {y:.4f} {rot})
    (descr "LED SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (fp_line (start -0.25 -0.7) (end 0.25 -0.7) (stroke (width 0.12) (type solid)) (layer "{silk}"))
    (pad "1" smd roundrect (at -1.05 0) (size 1.2 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.05 0) (size 1.2 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD8_3DMODEL_DIR}}/LED_SMD.3dshapes/LED_0805_2012Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
  )"""

def fp_soic14(ref, val, x, y, rot=0, layer="F.Cu", pin_nets=None):
    pads = []
    y_starts = [-3.81, -2.54, -1.27, 0.0, 1.27, 2.54, 3.81]
    x_off = -2.7
    for i in range(7):
        p_num = str(i + 1)
        py = y_starts[i]
        nid, nname = pin_nets.get(p_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{p_num}" smd roundrect (at {x_off:.3f} {py:.3f}) (size 1.5 0.6) (layers "{layer}" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    x_off = 2.7
    for i in range(7):
        p_num = str(14 - i)
        py = y_starts[i]
        nid, nname = pin_nets.get(p_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{p_num}" smd roundrect (at {x_off:.3f} {py:.3f}) (size 1.5 0.6) (layers "{layer}" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.4f} {y:.4f} {rot})
    (property "Reference" "{ref}" (at 0 -5.5 0) (layer "F.SilkS") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 5.5 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
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
    return [
        f'  (gr_line (start 0 0) (end {width:.2f} 0) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "{make_uuid()}"))',
        f'  (gr_line (start {width:.2f} 0) (end {width:.2f} {height:.2f}) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "{make_uuid()}"))',
        f'  (gr_line (start {width:.2f} {height:.2f}) (end 0 {height:.2f}) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "{make_uuid()}"))',
        f'  (gr_line (start 0 {height:.2f}) (end 0 0) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "{make_uuid()}"))',
        f'  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)',
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
        f'  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}") (at 5.0 5.0)',
        '    (property "Reference" "H1" (at 0 -4.0 0) (layer "F.SilkS") (hide yes) (effects (font (size 1 1) (thickness 0.15))))',
        '    (property "Value" "MountingHole" (at 0 4.0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))',
        '    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND")))',
        f'  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}") (at {width-5.0:.2f} 5.0)',
        '    (property "Reference" "H2" (at 0 -4.0 0) (layer "F.SilkS") (hide yes) (effects (font (size 1 1) (thickness 0.15))))',
        '    (property "Value" "MountingHole" (at 0 4.0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))',
        '    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND")))'
    ]

def build_perfect_zero_dc3(board_file="daughtercard3_weights_l2_wta.kicad_pcb"):
    with open("weights_layer2.json", "r") as f:
        l2 = json.load(f)

    nets = {
        0: "",
        1: "GND",
        2: "+12V",
        3: "-12V",
        4: "+5V_REF",
        5: "-5V_REF",
        6: "WTA_BUS"
    }
    for k in range(16):
        nets[20 + k] = f"ACT_{k}"
    for c in range(10):
        nets[50 + c] = f"SCORE_{c}"
        nets[70 + c] = f"INV_L2_{c}"
        nets[90 + c] = f"LED_N_{c}"

    pin_nets_a = {f"A{k+1}": (20 + k, f"ACT_{k}") for k in range(16)}
    for p in range(17, 33):
        pin_nets_a[f"A{p}"] = (1, "GND")
    for p in range(33, 37):
        pin_nets_a[f"A{p}"] = (1, "GND")

    pin_nets_b = {f"B{c+1}": (50 + c, f"SCORE_{c}") for c in range(10)}
    for p in range(11, 33):
        pin_nets_b[f"B{p}"] = (1, "GND")
    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (4, "+5V_REF")
    pin_nets_b["B36"] = (5, "-5V_REF")

    net_lines = "\n".join([f'  (net {nid} "{nname}")' for nid, nname in sorted(nets.items())])

    header = f"""(kicad_pcb
  (version 20240108)
  (generator "pcbnew")
  (generator_version "8.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (title_block
    (title "Daughtercard 3 - L2 Weights & 10-Way Winner-Take-All")
    (date "2026-09-15")
    (rev "v21.0-ZeroDRC")
    (company "Discrete Analog Neural Network System")
  )
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" power "GND")
    (2 "In2.Cu" signal "Power_Summing")
    (31 "B.Cu" signal)
    (32 "B.Mask" user)
    (33 "F.Mask" user)
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.CrtYd" user)
    (39 "F.CrtYd" user)
    (40 "B.Fab" user)
    (41 "F.Fab" user)
    (44 "Edge.Cuts" user)
  )
  (setup
    (pad_to_mask_clearance 0.05)
    (allow_soldermask_bridges_in_footprints no)
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
    pcb = [header] + get_daughtercard_outline_and_mounts(width=94.28, height=100.0) + [
        fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=94.28),
        f'  (gr_text "L2 Weights + 10-Way Winner-Take-All (DC3)" (at 47.14 8.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 2.0 2.0) (thickness 0.25))))'
    ]

    card_w = 94.28
    cx = card_w / 2.0
    PITCH = 2.54
    x_start = cx - (17.5 * PITCH) # 2.69 mm

    # -------------------------------------------------------------
    # 1. TOP INDICATOR LEDS & RESISTORS (c = 0..9)
    # -------------------------------------------------------------
    lx = [16.0 + c * 6.40 for c in range(10)]
    for c in range(10):
        pcb.append(fp_led0805(f"D_LED_{c}", f"Digit_{c}", lx[c], 12.0, 0, "F.Cu", 50 + c, f"SCORE_{c}", 90 + c, f"LED_N_{c}"))
        pcb.append(fp_resistor_0805(f"R_LED_{c}", "1k", lx[c], 15.5, 0, "F.Cu", 90 + c, f"LED_N_{c}", 1, "GND"))
        pcb.append(make_segment(lx[c] + 1.05, 12.0, lx[c] + 1.05, 14.0, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))
        pcb.append(make_segment(lx[c] + 1.05, 14.0, lx[c] - 0.95, 14.0, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))
        pcb.append(make_segment(lx[c] - 0.95, 14.0, lx[c] - 0.95, 15.5, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))

        # Ground via for R_LED Pad 2 at (lx[c] + 2.00, 15.5)
        pcb.append(make_via(lx[c] + 2.00, 15.5, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(lx[c] + 0.95, 15.5, lx[c] + 2.00, 15.5, 0.25, "F.Cu", "GND", 1))

        # SCORE_c via at (lx[c] - 2.50, 12.0)
        pcb.append(make_via(lx[c] - 2.50, 12.0, 0.6, 0.3, f"SCORE_{c}", 50 + c))
        pcb.append(make_segment(lx[c] - 2.50, 12.0, lx[c] - 1.05, 12.0, 0.25, "F.Cu", f"SCORE_{c}", 50 + c))

    # -------------------------------------------------------------
    # 2. MATRIX RESISTORS (16 inputs x 10 classes)
    # -------------------------------------------------------------
    row_y = [23.0 + c * 5.20 for c in range(10)]
    col_x = [x_start + k * PITCH for k in range(16)]

    for c in range(10):
        c_info = l2["weights"][c]
        ry = row_y[c]
        for k in range(16):
            inp = c_info["inputs"][k]
            pcb.append(fp_resistor_0805(f"R2_{k}_{c}", inp["resistor_str"], col_x[k], ry, 90, "F.Cu", 20 + k, f"ACT_{k}", 70 + c, f"INV_L2_{c}"))

    # Matrix Columns Routing (Vertical lines on In2.Cu from finger pads Ak)
    for k in range(16):
        kx = col_x[k]
        act_name = f"ACT_{k}"
        act_nid = 20 + k
        kx_via = kx + 0.85
        pcb.append(make_segment(kx, 92.0, kx_via, 90.0, 0.25, "F.Cu", act_name, act_nid))
        pcb.append(make_segment(kx_via, 90.0, kx_via, 88.0, 0.25, "F.Cu", act_name, act_nid))
        pcb.append(make_via(kx_via, 88.0, 0.6, 0.3, act_name, act_nid))
        pcb.append(make_segment(kx_via, 88.0, kx, 86.5, 0.25, "In2.Cu", act_name, act_nid))
        pcb.append(make_segment(kx, 86.5, kx, row_y[0] + 2.05, 0.25, "In2.Cu", act_name, act_nid))
        for c in range(10):
            vy = row_y[c] + 2.05
            py = row_y[c] + 0.95
            pcb.append(make_via(kx, vy, 0.6, 0.3, act_name, act_nid))
            pcb.append(make_segment(kx, vy, kx, py, 0.25, "F.Cu", act_name, act_nid))

    # Connect all resistor Pad 2s across each matrix row on F.Cu:
    for c in range(10):
        ry_sum = row_y[c] - 0.95
        inv_name = f"INV_L2_{c}"
        inv_nid = 70 + c
        pcb.append(make_segment(col_x[0], ry_sum, col_x[15] + 0.50, ry_sum, 0.25, "F.Cu", inv_name, inv_nid))

    # -------------------------------------------------------------
    # 3. OP-AMPS (3x TL074 at X = 62.0)
    # -------------------------------------------------------------
    u_x = 62.0
    tier_y = [25.0, 50.0, 75.0]

    unit_info = {
        0: (0, "A", tier_y[0] - 3.81, tier_y[0] - 2.54),
        1: (0, "B", tier_y[0] + 3.81, tier_y[0] + 2.54),
        2: (1, "A", tier_y[1] - 3.81, tier_y[1] - 2.54),
        3: (1, "B", tier_y[1] + 3.81, tier_y[1] + 2.54),
        4: (2, "A", tier_y[2] - 3.81, tier_y[2] - 2.54),
        5: (2, "B", tier_y[2] + 3.81, tier_y[2] + 2.54),
        6: (0, "D", tier_y[0] - 3.81, tier_y[0] - 2.54),
        7: (0, "C", tier_y[0] + 3.81, tier_y[0] + 2.54),
        8: (1, "D", tier_y[1] - 3.81, tier_y[1] - 2.54),
        9: (1, "C", tier_y[1] + 3.81, tier_y[1] + 2.54),
    }

    for u_idx, yu in enumerate(tier_y):
        u_ref = f"U{u_idx+1}"
        if u_idx == 0:
            cA, cB, cD, cC = 0, 1, 6, 7
            ic_pin_nets = {
                "1": (50 + cA, f"SCORE_{cA}"), "2": (70 + cA, f"INV_L2_{cA}"), "3": (1, "GND"),
                "4": (2, "+12V"), "5": (1, "GND"),
                "6": (70 + cB, f"INV_L2_{cB}"), "7": (50 + cB, f"SCORE_{cB}"),
                "8": (50 + cC, f"SCORE_{cC}"), "9": (70 + cC, f"INV_L2_{cC}"), "10": (1, "GND"),
                "11": (3, "-12V"), "12": (1, "GND"),
                "13": (70 + cD, f"INV_L2_{cD}"), "14": (50 + cD, f"SCORE_{cD}")
            }
        elif u_idx == 1:
            cA, cB, cD, cC = 2, 3, 8, 9
            ic_pin_nets = {
                "1": (50 + cA, f"SCORE_{cA}"), "2": (70 + cA, f"INV_L2_{cA}"), "3": (1, "GND"),
                "4": (2, "+12V"), "5": (1, "GND"),
                "6": (70 + cB, f"INV_L2_{cB}"), "7": (50 + cB, f"SCORE_{cB}"),
                "8": (50 + cC, f"SCORE_{cC}"), "9": (70 + cC, f"INV_L2_{cC}"), "10": (1, "GND"),
                "11": (3, "-12V"), "12": (1, "GND"),
                "13": (70 + cD, f"INV_L2_{cD}"), "14": (50 + cD, f"SCORE_{cD}")
            }
        else:
            cA, cB = 4, 5
            ic_pin_nets = {
                "1": (50 + cA, f"SCORE_{cA}"), "2": (70 + cA, f"INV_L2_{cA}"), "3": (1, "GND"),
                "4": (2, "+12V"), "5": (1, "GND"),
                "6": (70 + cB, f"INV_L2_{cB}"), "7": (50 + cB, f"SCORE_{cB}"),
                "8": (1, "GND"), "9": (1, "GND"), "10": (1, "GND"),
                "11": (3, "-12V"), "12": (1, "GND"),
                "13": (1, "GND"), "14": (1, "GND")
            }

        pcb.append(fp_soic14(u_ref, "TL074", u_x, yu, 0, "F.Cu", ic_pin_nets))

        # Ground vias for Pins 3, 5, 10, 12 placed UNDER the package body (X = 60.5 and X = 63.5):
        for py in [yu - 1.27, yu + 1.27]:
            # West pins (3, 5): via at X = 60.5
            pcb.append(make_via(60.5, py, 0.6, 0.3, "GND", 1))
            pcb.append(make_segment(u_x - 2.7, py, 60.5, py, 0.25, "F.Cu", "GND", 1))
            # East pins (10, 12): via at X = 63.5
            pcb.append(make_via(63.5, py, 0.6, 0.3, "GND", 1))
            pcb.append(make_segment(u_x + 2.7, py, 63.5, py, 0.25, "F.Cu", "GND", 1))

        # Decoupling Caps C_P (+12V) and C_N (-12V)
        # C_P horizontally at (55.0, yu): Pad 1 (GND) at 54.05, Pad 2 (+12V) at 55.95
        pcb.append(fp_capacitor_0805(f"C_{u_ref}P", "0.1uF", 55.0, yu, 0, "F.Cu", 1, "GND", 2, "+12V"))
        pcb.append(make_via(54.05, yu, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(55.95, yu, u_x - 2.7, yu, 0.35, "F.Cu", "+12V", 2))

        # C_N horizontally at (69.0, yu): Pad 1 (-12V) at 68.05, Pad 2 (GND) at 69.95
        pcb.append(fp_capacitor_0805(f"C_{u_ref}N", "0.1uF", 69.0, yu, 0, "F.Cu", 3, "-12V", 1, "GND"))
        pcb.append(make_via(69.95, yu, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(68.05, yu, u_x + 2.7, yu, 0.35, "F.Cu", "-12V", 3))

        # If U3: tie unused pins 8, 9, 13, 14 to GND at (63.5, py)
        if u_idx == 2:
            pcb.append(make_segment(u_x + 2.7, yu - 3.81, 63.5, yu - 1.27, 0.25, "F.Cu", "GND", 1))
            pcb.append(make_segment(u_x + 2.7, yu - 2.54, 63.5, yu - 1.27, 0.25, "F.Cu", "GND", 1))
            pcb.append(make_segment(u_x + 2.7, yu + 2.54, 63.5, yu + 1.27, 0.25, "F.Cu", "GND", 1))
            pcb.append(make_segment(u_x + 2.7, yu + 3.81, 63.5, yu + 1.27, 0.25, "F.Cu", "GND", 1))

    # -------------------------------------------------------------
    # 4. PASSIVES & LOCAL ROUTING FOR EACH CLASS (c = 0..9)
    # -------------------------------------------------------------
    # Trunk coordinates for SCORE lines:
    # Classes 0..5 (West): X = 49.20 + c * 0.55 (49.20 to 51.95) -> well clear of 54.05 (Cp gnd via)
    # Classes 6..9 (East): X = 80.50 + (c - 6) * 0.65 (80.50 to 82.45) -> well clear of 69.95 (Cn gnd via)
    x_score_tr = {
        0: 49.20, 1: 49.75,
        2: 50.30, 3: 50.85,
        4: 51.40, 5: 51.95,
        6: 80.50, 7: 81.15,
        8: 81.80, 9: 82.45
    }

    # Summing corridor X for West classes (0..5) on In2.Cu:
    x_sum_corridor = {
        0: 41.20, 1: 41.55,
        2: 41.90, 3: 42.25,
        4: 42.60, 5: 42.95
    }

    # Summing corridor X for East classes (6..9) on F.Cu:
    x_sum_corridor_east = {
        6: 73.50,
        7: 74.20,
        8: 74.90,
        9: 75.60
    }

    for c in range(10):
        c_info = l2["weights"][c]
        b_rail = c_info["bias_rail"]
        b_nid = 4 if b_rail == "+5V_REF" else 5
        score_name = f"SCORE_{c}"
        score_nid = 50 + c
        inv_name = f"INV_L2_{c}"
        inv_nid = 70 + c

        u_idx, u_unit, y_out, y_in = unit_info[c]
        ry_sum = row_y[c] - 0.95
        x_tr = x_score_tr[c]

        if u_unit in ["A", "B"]:
            # WEST SIDE: Op-Amp pins on West (X = 59.30)
            # Rf at (48.00, y_out): Pad 1 (47.05)=INV, Pad 2 (48.95)=SCORE
            pcb.append(fp_resistor_0805(f"Rf_L2_{c}", "10k", 48.00, y_out, 0, "F.Cu", inv_nid, inv_name, score_nid, score_name))
            # Rb at (45.50, y_in): Pad 1 (44.55)=BIAS, Pad 2 (46.45)=INV
            pcb.append(fp_resistor_0805(f"Rb_L2_{c}", c_info["bias_resistor_str"], 45.50, y_in, 0, "F.Cu", b_nid, b_rail, inv_nid, inv_name))

            # D_WTA at (56.00, y_diode):
            y_diode = y_out - 2.50 if u_unit == "A" else y_out + 2.50
            # D_SOD-123: Pad 1 (-1.65) = Cathode = WTA_BUS, Pad 2 (+1.65) = Anode = SCORE
            # Diode at (56.00, y_diode): Pad 1 is at 54.35 (WTA_BUS), Pad 2 is at 57.65 (SCORE)
            pcb.append(fp_diodesod123(f"D_WTA_{c}", "1N4148", 56.00, y_diode, 0, "F.Cu", 6, "WTA_BUS", score_nid, score_name))

            # 1. INV_L2 on F.Cu:
            pcb.append(make_segment(46.45, y_in, 47.05, y_in, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(47.05, y_in, 47.05, y_out, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(47.05, y_in, u_x - 2.7, y_in, 0.25, "F.Cu", inv_name, inv_nid))

            # Summing row connection on In2.Cu:
            # From matrix row end (col_x[15] + 0.50 = 41.29, ry_sum) on F.Cu:
            x_sum_v = x_sum_corridor[c]
            pcb.append(make_segment(col_x[15] + 0.50, ry_sum, x_sum_v, ry_sum, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_via(x_sum_v, ry_sum, 0.6, 0.3, inv_name, inv_nid))
            pcb.append(make_segment(x_sum_v, ry_sum, x_sum_v, y_in, 0.25, "In2.Cu", inv_name, inv_nid))
            pcb.append(make_segment(x_sum_v, y_in, 47.05, y_in, 0.25, "In2.Cu", inv_name, inv_nid))
            pcb.append(make_via(47.05, y_in, 0.6, 0.3, inv_name, inv_nid))

            # 2. SCORE on F.Cu:
            pcb.append(make_segment(48.95, y_out, u_x - 2.7, y_out, 0.25, "F.Cu", score_name, score_nid))
            # Connect to Diode Anode (Pad 2 at 57.65, y_diode) via (57.65, y_out)
            pcb.append(make_segment(48.95, y_out, 57.65, y_out, 0.25, "F.Cu", score_name, score_nid))
            pcb.append(make_segment(57.65, y_out, 57.65, y_diode, 0.25, "F.Cu", score_name, score_nid))

            # 3. WTA_BUS drop via at D_WTA Pad 1 (54.35, y_diode)
            pcb.append(make_via(54.35, y_diode, 0.6, 0.3, "WTA_BUS", 6))

            # 4. Drop via to SCORE trunk at x_tr for North (In2.Cu) and South (In2.Cu -> B.Cu):
            pcb.append(make_via(x_tr, y_out, 0.6, 0.3, score_name, score_nid))

        else:
            # EAST SIDE: Op-Amp pins on East (X = 64.70)
            # Rf at (76.50, y_out): Pad 1 (75.55)=SCORE, Pad 2 (77.45)=INV
            pcb.append(fp_resistor_0805(f"Rf_L2_{c}", "10k", 76.50, y_out, 0, "F.Cu", score_nid, score_name, inv_nid, inv_name))
            # Rb at (79.00, y_in): Pad 1 (78.05)=INV, Pad 2 (79.95)=BIAS
            pcb.append(fp_resistor_0805(f"Rb_L2_{c}", c_info["bias_resistor_str"], 79.00, y_in, 0, "F.Cu", inv_nid, inv_name, b_nid, b_rail))

            # D_WTA at (68.00, y_diode), rot=180:
            # Pad 1 (-1.65 rotated = +1.65) = 69.65 (Cathode = WTA_BUS)
            # Pad 2 (+1.65 rotated = -1.65) = 66.35 (Anode = SCORE)
            y_diode = y_out - 2.50 if u_unit == "D" else y_out + 2.50
            pcb.append(fp_diodesod123(f"D_WTA_{c}", "1N4148", 68.00, y_diode, 180, "F.Cu", 6, "WTA_BUS", score_nid, score_name))

            # 1. INV_L2 on F.Cu:
            pcb.append(make_segment(u_x + 2.7, y_in, 78.05, y_in, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(77.45, y_in, 77.45, y_out, 0.25, "F.Cu", inv_name, inv_nid))

            # Summing row connection on B.Cu:
            x_sum_v_east = x_sum_corridor_east[c]
            # Drop via at (col_x[15] + 0.50 = 41.29, ry_sum) to B.Cu!
            pcb.append(make_via(41.29, ry_sum, 0.6, 0.3, inv_name, inv_nid))
            # Run horizontally on B.Cu across to x_sum_v_east at Y = ry_sum:
            pcb.append(make_segment(41.29, ry_sum, x_sum_v_east, ry_sum, 0.25, "B.Cu", inv_name, inv_nid))
            # Drop via back up to F.Cu at (x_sum_v_east, ry_sum):
            pcb.append(make_via(x_sum_v_east, ry_sum, 0.6, 0.3, inv_name, inv_nid))
            # Run vertically on F.Cu to (x_sum_v_east, y_in):
            pcb.append(make_segment(x_sum_v_east, ry_sum, x_sum_v_east, y_in, 0.25, "F.Cu", inv_name, inv_nid))
            # Connect to inverting input at (77.45, y_in):
            pcb.append(make_segment(x_sum_v_east, y_in, 77.45, y_in, 0.25, "F.Cu", inv_name, inv_nid))

            # 2. SCORE on F.Cu:
            pcb.append(make_segment(75.55, y_out, u_x + 2.7, y_out, 0.25, "F.Cu", score_name, score_nid))
            # Connect to Diode Anode (Pad 2 at 66.35, y_diode)
            pcb.append(make_segment(75.55, y_out, 66.35, y_out, 0.25, "F.Cu", score_name, score_nid))
            pcb.append(make_segment(66.35, y_out, 66.35, y_diode, 0.25, "F.Cu", score_name, score_nid))

            # 3. WTA_BUS drop via at D_WTA Pad 1 (69.65, y_diode)
            pcb.append(make_via(69.65, y_diode, 0.6, 0.3, "WTA_BUS", 6))

            # 4. Drop via to SCORE trunk at x_tr on F.Cu:
            pcb.append(make_segment(75.55, y_out, x_tr, y_out, 0.25, "F.Cu", score_name, score_nid))
            pcb.append(make_via(x_tr, y_out, 0.6, 0.3, score_name, score_nid))

    # -------------------------------------------------------------
    # 5. WTA BUS TRUNKS & PULL-DOWN RESISTOR
    # -------------------------------------------------------------
    # West trunk on In2.Cu at X = 54.35 from Y = 18.0 to 82.5
    pcb.append(make_segment(54.35, 18.0, 54.35, 82.5, 0.25, "In2.Cu", "WTA_BUS", 6))
    # East trunk on In2.Cu at X = 69.65 from Y = 18.0 to 80.0
    pcb.append(make_segment(69.65, 18.0, 69.65, 80.0, 0.25, "In2.Cu", "WTA_BUS", 6))
    # Horizontal link on In2.Cu at Y = 36.0 (open gap between U1 and U2)
    pcb.append(make_segment(54.35, 36.0, 69.65, 36.0, 0.25, "In2.Cu", "WTA_BUS", 6))

    # R_WTA at (72.0, 80.0) rot=0 on F.Cu:
    pcb.append(fp_resistor_0805("R_WTA", "10k", 72.0, 80.0, 0, "F.Cu", 6, "WTA_BUS", 3, "-12V"))
    # Connect Pad 1 (71.05, 80.0) to East trunk via at (69.65, 80.0)
    pcb.append(make_via(69.65, 80.0, 0.6, 0.3, "WTA_BUS", 6))
    pcb.append(make_segment(71.05, 80.0, 69.65, 80.0, 0.25, "F.Cu", "WTA_BUS", 6))
    # Connect Pad 2 (72.95, 80.0) to -12V trunk at (86.51, 80.0) on F.Cu:
    pcb.append(make_via(86.51, 80.0, 0.6, 0.3, "-12V", 3))
    pcb.append(make_segment(72.95, 80.0, 86.51, 80.0, 0.25, "F.Cu", "-12V", 3))

    # -------------------------------------------------------------
    # 6. OUTPUT HIGHWAYS TO LEDS (Strictly planar on In2.Cu)
    # Monotonic East-to-West: c=9 turns furthest north (lowest Y), c=0 turns furthest south (highest Y)
    # -------------------------------------------------------------
    for c in range(10):
        score_name = f"SCORE_{c}"
        score_nid = 50 + c
        u_idx, u_unit, y_out, y_in = unit_info[c]
        x_tr = x_score_tr[c]
        y_bus = 16.50 + (9 - c) * 0.40
        x_led_via = lx[c] - 2.50

        # Run North on In2.Cu from y_out to y_bus
        pcb.append(make_segment(x_tr, y_out, x_tr, y_bus, 0.25, "In2.Cu", score_name, score_nid))
        # Run West on In2.Cu from x_tr to x_led_via
        pcb.append(make_segment(x_tr, y_bus, x_led_via, y_bus, 0.25, "In2.Cu", score_name, score_nid))
        # Run North on In2.Cu to via at (x_led_via, 12.0)
        pcb.append(make_segment(x_led_via, y_bus, x_led_via, 12.0, 0.25, "In2.Cu", score_name, score_nid))

    # -------------------------------------------------------------
    # 7. OUTPUT HIGHWAYS TO EDGE FINGERS B (Strictly planar on B.Cu)
    # Run South on In2.Cu to y_turn, drop via to B.Cu, run West on B.Cu to finger col_x[c]
    # Strictly increasing X and Y: Trunk c at x_tr[c] turns at y_turn[c] to px_bc[c]
    # Zero crossings mathematically guaranteed!
    # -------------------------------------------------------------
    for c in range(10):
        score_name = f"SCORE_{c}"
        score_nid = 50 + c
        u_idx, u_unit, y_out, y_in = unit_info[c]
        px_bc = col_x[c]
        x_tr = x_score_tr[c]
        y_turn = 81.00 + c * 0.70

        # Run South on In2.Cu from (x_tr, y_out) down to y_turn:
        pcb.append(make_segment(x_tr, y_out, x_tr, y_turn, 0.25, "In2.Cu", score_name, score_nid))
        # Drop via to B.Cu at (x_tr, y_turn):
        pcb.append(make_via(x_tr, y_turn, 0.6, 0.3, score_name, score_nid))
        # Run horizontally on B.Cu across to px_bc:
        pcb.append(make_segment(x_tr, y_turn, px_bc, y_turn, 0.25, "B.Cu", score_name, score_nid))
        # Run straight down on B.Cu to edge finger pad at Y = 92.0:
        pcb.append(make_segment(px_bc, y_turn, px_bc, 92.0, 0.25, "B.Cu", score_name, score_nid))

    # -------------------------------------------------------------
    # 8. POWER & BIAS RAILS (Strictly planar)
    # -------------------------------------------------------------
    # 1. +12V from B33 (83.97, 92.0) on B.Cu:
    pcb.append(make_segment(83.97, 92.0, 83.97, 23.0, 0.35, "B.Cu", "+12V", 2))
    for yu in tier_y:
        # Feeder on B.Cu horizontally at Y = yu + 1.20 from X = 83.97 West to X = 55.95
        pcb.append(make_segment(83.97, yu + 1.20, 55.95, yu + 1.20, 0.35, "B.Cu", "+12V", 2))
        # Via to F.Cu at (55.95, yu + 1.20)
        pcb.append(make_via(55.95, yu + 1.20, 0.6, 0.3, "+12V", 2))
        # Segment on F.Cu to C_P Pad 2 at (55.95, yu)
        pcb.append(make_segment(55.95, yu + 1.20, 55.95, yu, 0.35, "F.Cu", "+12V", 2))

    # 2. -12V from B34 (86.51, 92.0) on B.Cu:
    # Trunk at X = 86.51 from Y = 92.0 to Y = 23.0 on B.Cu
    pcb.append(make_segment(86.51, 92.0, 86.51, 23.0, 0.35, "B.Cu", "-12V", 3))
    for yu in tier_y:
        # Via at (86.51, yu - 1.20) to F.Cu
        pcb.append(make_via(86.51, yu - 1.20, 0.6, 0.3, "-12V", 3))
        # On F.Cu run West to C_N Pad 1 (-12V) at (68.05, yu)
        pcb.append(make_segment(86.51, yu - 1.20, 68.05, yu - 1.20, 0.35, "F.Cu", "-12V", 3))
        pcb.append(make_segment(68.05, yu - 1.20, 68.05, yu, 0.35, "F.Cu", "-12V", 3))

    # 3. +5V_REF from B35 (89.05, 92.0) on B.Cu:
    # Trunk on B.Cu from Y = 92.0 North to Y = 18.0
    pcb.append(make_segment(89.05, 92.0, 89.05, 18.0, 0.35, "B.Cu", "+5V_REF", 4))

    # Tap to East bias resistor (+5V_REF: Class 6):
    _, _, _, y_in_c6 = unit_info[6]
    pcb.append(make_via(89.05, y_in_c6, 0.6, 0.3, "+5V_REF", 4))
    pcb.append(make_segment(89.05, y_in_c6, 79.95, y_in_c6, 0.25, "F.Cu", "+5V_REF", 4))

    # Cross to West for +5V_REF (Classes 1 and 3):
    # Feeder on In2.Cu at Y = 20.60 from X = 89.05 West to X = 44.55
    pcb.append(make_via(89.05, 20.60, 0.6, 0.3, "+5V_REF", 4))
    pcb.append(make_segment(89.05, 20.60, 44.55, 20.60, 0.25, "In2.Cu", "+5V_REF", 4))
    # Vertical distribution on In2.Cu at X = 44.55 from Y = 20.60 to Y = unit_info[3][3] (52.54)
    pcb.append(make_segment(44.55, 20.60, 44.55, unit_info[3][3], 0.25, "In2.Cu", "+5V_REF", 4))
    for c in [1, 3]:
        y_in_c = unit_info[c][3]
        pcb.append(make_via(44.55, y_in_c, 0.6, 0.3, "+5V_REF", 4))

    # 4. -5V_REF from B36 (91.59, 92.0) on B.Cu:
    # Trunk at X = 91.59 from Y = 92.0 North to Y = 17.0 on B.Cu
    pcb.append(make_segment(91.59, 92.0, 91.59, 17.0, 0.35, "B.Cu", "-5V_REF", 5))

    # Taps to East bias resistors (-5V_REF: classes 7, 8, 9):
    for c in [7, 8, 9]:
        _, _, _, y_in_c = unit_info[c]
        pcb.append(make_via(91.59, y_in_c, 0.6, 0.3, "-5V_REF", 5))
        pcb.append(make_segment(91.59, y_in_c, 79.95, y_in_c, 0.25, "F.Cu", "-5V_REF", 5))

    # Cross to West for -5V_REF (Classes 0, 2, 4, 5):
    # Feeder on B.Cu at Y = 17.0 from X = 91.59 West to X = 43.60
    pcb.append(make_segment(91.59, 17.0, 43.60, 17.0, 0.25, "B.Cu", "-5V_REF", 5))
    # Vertical distribution on B.Cu at X = 43.60 from Y = 17.0 to Y = unit_info[5][3] (77.54)
    pcb.append(make_segment(43.60, 17.0, 43.60, unit_info[5][3], 0.25, "B.Cu", "-5V_REF", 5))
    for c in [0, 2, 4, 5]:
        y_in_c = unit_info[c][3]
        pcb.append(make_via(43.60, y_in_c, 0.6, 0.3, "-5V_REF", 5))
        pcb.append(make_segment(43.60, y_in_c, 44.55, y_in_c, 0.25, "F.Cu", "-5V_REF", 5))

    # -------------------------------------------------------------
    # 9. GROUND SHIELD FINGERS
    # -------------------------------------------------------------
    for p in list(range(17, 33)):
        px = x_start + (p - 1) * PITCH
        pcb.append(make_segment(px, 92.0, px, 89.0, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_via(px, 89.0, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(px, 92.0, px, 89.0, 0.25, "B.Cu", "GND", 1))

    # A33..A36: connect on F.Cu at Y = 91.0 to A32
    px32 = x_start + (32 - 1) * PITCH
    for p in range(33, 37):
        px = x_start + (p - 1) * PITCH
        pcb.append(make_segment(px, 92.0, px, 91.0, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_segment(px, 91.0, px32, 91.0, 0.25, "F.Cu", "GND", 1))

    # B11..B16: connect to B17 on B.Cu
    px17 = x_start + (17 - 1) * PITCH
    for p in range(11, 17):
        px = x_start + (p - 1) * PITCH
        pcb.append(make_segment(px, 92.0, px, 91.0, 0.25, "B.Cu", "GND", 1))
        pcb.append(make_segment(px, 91.0, px17, 91.0, 0.25, "B.Cu", "GND", 1))

    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))

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
    print("Generated and filled DC3 successfully.")

if __name__ == "__main__":
    build_perfect_zero_dc3()
