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
    (at {x:.4f} {y:.4f} {rot})
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

def fp_diodesod123(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "Diode_SMD:D_SOD-123" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.4f} {y:.4f} {rot})
    (descr "Diode SOD-123")
    (property "Reference" "{ref}" (at 0 -1.8 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.8 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
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
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
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
    (property "Reference" "{ref}" (at 0 -5.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 5.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
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
        '    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND")))',
        f'  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}") (at {width-5.0:.2f} 5.0)',
        '    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND")))'
    ]

def build_perfect_zero_dc3(board_file="daughtercard3_weights_l2_wta.kicad_pcb"):
    w2_file = "weights_layer2.json"
    with open(w2_file) as f:
        l2 = json.load(f)

    # Nets
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

    # Gold Fingers Pin Nets
    pin_nets_a = {f"A{k+1}": (20 + k, f"ACT_{k}") for k in range(16)}
    for p in range(17, 37):
        pin_nets_a[f"A{p}"] = (1, "GND")

    pin_nets_b = {f"B{c+1}": (50 + c, f"SCORE_{c}") for c in range(10)}
    for p in range(11, 33):
        pin_nets_b[f"B{p}"] = (1, "GND")
    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (4, "+5V_REF")
    pin_nets_b["B36"] = (5, "-5V_REF")

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in sorted(nets.items()) if nid > 0])

    header = f"""(kicad_pcb
  (version 20240108)
  (generator "antigravity_perfect_dc3")
  (generator_version "8.0")
  (general
    (thickness 1.6)
    (legacy_edge_clearance 0)
  )
  (paper "A4")
  (title_block
    (title "Daughtercard 3 - L2 Weights & 10-Way Winner-Take-All")
    (company "Discrete Analog Neural Network System")
    (rev "v14.0-ZeroDRC")
    (date "2026-09-15")
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
        # D_LED at (lx[c], 12.0): Pad 1 (-1.05) = SCORE_c, Pad 2 (+1.05) = LED_N_c
        pcb.append(fp_led0805(f"D_LED_{c}", f"Digit_{c}", lx[c], 12.0, 0, "F.Cu", 50 + c, f"SCORE_{c}", 90 + c, f"LED_N_{c}"))
        # R_LED at (lx[c], 15.5): Pad 1 (-0.95) = LED_N_c, Pad 2 (+0.95) = GND
        pcb.append(fp_resistor_0805(f"R_LED_{c}", "1k", lx[c], 15.5, 0, "F.Cu", 90 + c, f"LED_N_{c}", 1, "GND"))
        # Connect Cathode to Resistor Pad 1
        pcb.append(make_segment(lx[c] + 1.05, 12.0, lx[c] + 1.05, 13.8, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))
        pcb.append(make_segment(lx[c] + 1.05, 13.8, lx[c] - 0.95, 13.8, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))
        pcb.append(make_segment(lx[c] - 0.95, 13.8, lx[c] - 0.95, 15.5, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))
        # GND via for Resistor Pad 2
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
            # rot = 90:
            # Pad 1 is at (col_x, ry + 0.95) -> ACT_k
            # Pad 2 is at (col_x, ry - 0.95) -> INV_L2_c
            pcb.append(fp_resistor_0805(f"R2_{k}_{c}", inp["resistor_str"], col_x[k], ry, 90, "F.Cu", 20 + k, f"ACT_{k}", 70 + c, f"INV_L2_{c}"))

    # Matrix Summing Rows Routing (Horizontal on F.Cu at ry - 0.95)
    for c in range(10):
        ry_sum = row_y[c] - 0.95
        inv_name = f"INV_L2_{c}"
        inv_nid = 70 + c
        pcb.append(make_segment(col_x[0], ry_sum, 41.20, ry_sum, 0.25, "F.Cu", inv_name, inv_nid))

    # Matrix Columns Routing (Vertical lines on In2.Cu from finger pads Ak)
    # Offset front finger via by +0.85 mm in X to clear back SCORE tracks!
    for k in range(16):
        kx = col_x[k]
        act_name = f"ACT_{k}"
        act_nid = 20 + k
        kx_via = kx + 0.85
        pcb.append(make_segment(kx, 92.0, kx_via, 90.0, 0.25, "F.Cu", act_name, act_nid))
        pcb.append(make_segment(kx_via, 90.0, kx_via, 88.0, 0.25, "F.Cu", act_name, act_nid))
        pcb.append(make_via(kx_via, 88.0, 0.6, 0.3, act_name, act_nid))
        # On In2.Cu: jog back to kx at Y = 86.5
        pcb.append(make_segment(kx_via, 88.0, kx, 86.5, 0.25, "In2.Cu", act_name, act_nid))
        pcb.append(make_segment(kx, 86.5, kx, row_y[0] + 2.05, 0.25, "In2.Cu", act_name, act_nid))
        for c in range(10):
            vy = row_y[c] + 2.05
            py = row_y[c] + 0.95
            pcb.append(make_via(kx, vy, 0.6, 0.3, act_name, act_nid))
            pcb.append(make_segment(kx, vy, kx, py, 0.25, "F.Cu", act_name, act_nid))

    # -------------------------------------------------------------
    # 3. OP-AMPS (3x TL074 at X = 62.0)
    # -------------------------------------------------------------
    u_x = 62.0
    tier_y = [25.0, 50.0, 75.0]

    for u_idx, yu in enumerate(tier_y):
        u_ref = f"U{u_idx+1}"
        if u_idx < 2:
            c_base = u_idx * 4
            cA = c_base + 0
            cB = c_base + 1
            cD = c_base + 2
            cC = c_base + 3
            ic_pin_nets = {
                "1": (50 + cA, f"SCORE_{cA}"), "2": (70 + cA, f"INV_L2_{cA}"), "3": (1, "GND"),
                "4": (2, "+12V"), "5": (1, "GND"),
                "6": (70 + cB, f"INV_L2_{cB}"), "7": (50 + cB, f"SCORE_{cB}"),
                "8": (50 + cC, f"SCORE_{cC}"), "9": (70 + cC, f"INV_L2_{cC}"), "10": (1, "GND"),
                "11": (3, "-12V"), "12": (1, "GND"),
                "13": (70 + cD, f"INV_L2_{cD}"), "14": (50 + cD, f"SCORE_{cD}")
            }
        else:
            cA = 8
            cB = 9
            ic_pin_nets = {
                "1": (50 + cA, f"SCORE_{cA}"), "2": (70 + cA, f"INV_L2_{cA}"), "3": (1, "GND"),
                "4": (2, "+12V"), "5": (1, "GND"),
                "6": (70 + cB, f"INV_L2_{cB}"), "7": (50 + cB, f"SCORE_{cB}"),
                "8": (1, "GND"), "9": (1, "GND"), "10": (1, "GND"),
                "11": (3, "-12V"), "12": (1, "GND"),
                "13": (1, "GND"), "14": (1, "GND")
            }

        pcb.append(fp_soic14(u_ref, "TL074", u_x, yu, 0, "F.Cu", ic_pin_nets))

        # Ground vias for Pins 3, 5, 10, 12 at X = 56.5 and X = 67.5
        for py in [yu - 1.27, yu + 1.27]:
            pcb.append(make_via(56.5, py, 0.6, 0.3, "GND", 1))
            pcb.append(make_segment(u_x - 2.7, py, 56.5, py, 0.25, "F.Cu", "GND", 1))
            pcb.append(make_via(67.5, py, 0.6, 0.3, "GND", 1))
            pcb.append(make_segment(u_x + 2.7, py, 67.5, py, 0.25, "F.Cu", "GND", 1))

        # Decoupling Caps C_P (+12V) and C_N (-12V)
        pcb.append(fp_capacitor_0805(f"C_{u_ref}P", "0.1uF", 52.0, yu, 0, "F.Cu", 1, "GND", 2, "+12V"))
        pcb.append(make_via(51.05, yu - 1.8, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(51.05, yu, 51.05, yu - 1.8, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_segment(52.95, yu, u_x - 2.7, yu, 0.35, "F.Cu", "+12V", 2))

        pcb.append(fp_capacitor_0805(f"C_{u_ref}N", "0.1uF", 72.0, yu, 0, "F.Cu", 3, "-12V", 1, "GND"))
        pcb.append(make_via(72.95, yu - 1.8, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(72.95, yu, 72.95, yu - 1.8, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_segment(71.05, yu, u_x + 2.7, yu, 0.35, "F.Cu", "-12V", 3))

        # If U3: tie unused pins 8, 9, 13, 14 to GND at (67.5, py)
        if u_idx == 2:
            pcb.append(make_segment(u_x + 2.7, yu - 3.81, 67.5, yu - 1.27, 0.25, "F.Cu", "GND", 1))
            pcb.append(make_segment(u_x + 2.7, yu - 2.54, 67.5, yu - 1.27, 0.25, "F.Cu", "GND", 1))
            pcb.append(make_segment(u_x + 2.7, yu + 2.54, 67.5, yu + 1.27, 0.25, "F.Cu", "GND", 1))
            pcb.append(make_segment(u_x + 2.7, yu + 3.81, 67.5, yu + 1.27, 0.25, "F.Cu", "GND", 1))

    # -------------------------------------------------------------
    # 4. PASSIVES & LOCAL ROUTING FOR EACH CLASS (c = 0..9)
    # -------------------------------------------------------------
    unit_info = {
        0: (0, "A", tier_y[0] - 3.81, tier_y[0] - 2.54),
        1: (0, "B", tier_y[0] + 3.81, tier_y[0] + 2.54),
        2: (0, "D", tier_y[0] - 3.81, tier_y[0] - 2.54),
        3: (0, "C", tier_y[0] + 3.81, tier_y[0] + 2.54),
        4: (1, "A", tier_y[1] - 3.81, tier_y[1] - 2.54),
        5: (1, "B", tier_y[1] + 3.81, tier_y[1] + 2.54),
        6: (1, "D", tier_y[1] - 3.81, tier_y[1] - 2.54),
        7: (1, "C", tier_y[1] + 3.81, tier_y[1] + 2.54),
        8: (2, "A", tier_y[2] - 3.81, tier_y[2] - 2.54),
        9: (2, "B", tier_y[2] + 3.81, tier_y[2] + 2.54),
    }

    west_indices = [0, 1, 4, 5, 8, 9]
    east_indices = [2, 3, 6, 7]

    # Dedicated SCORE trunk X coordinates on In2.Cu:
    # All completely unique and non-overlapping!
    x_trunk_map = {
        0: 51.00, 1: 51.50,
        4: 52.00, 5: 52.50,
        8: 53.00, 9: 53.50,
        2: 71.50, 3: 71.00,
        6: 70.50, 7: 70.00
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
        x_tr = x_trunk_map[c]

        if u_unit in ["A", "B"]:
            # WEST SIDE: Op-Amp pins on West (X = 59.3).
            # Pin OUT at (59.3, y_out), Pin IN- at (59.3, y_in).
            # Place Rf at X = 49.0, Y = y_out: Pad 1 (48.05)=INV, Pad 2 (49.95)=SCORE
            pcb.append(fp_resistor_0805(f"Rf_L2_{c}", "10k", 49.0, y_out, 0, "F.Cu", inv_nid, inv_name, score_nid, score_name))
            # Place Rb at X = 46.0, Y = y_in: Pad 1 (45.05)=BIAS, Pad 2 (46.95)=INV
            pcb.append(fp_resistor_0805(f"Rb_L2_{c}", c_info["bias_resistor_str"], 46.0, y_in, 0, "F.Cu", b_nid, b_rail, inv_nid, inv_name))

            # D_WTA placed in clear space at (56.0, y_out - 2.50 if A else y_out + 2.50):
            y_diode = y_out - 2.50 if u_unit == "A" else y_out + 2.50
            # rot=0: Pad 1 (54.35)=SCORE, Pad 2 (57.65)=WTA_BUS
            pcb.append(fp_diodesod123(f"D_WTA_{c}", "1N4148", 56.0, y_diode, 0, "F.Cu", score_nid, score_name, 6, "WTA_BUS"))

            # 1. INV_L2 on F.Cu:
            # Rb Pad 2 (46.95, y_in) to Rf Pad 1 (48.05, y_out) via (48.05, y_in)
            pcb.append(make_segment(46.95, y_in, 48.05, y_in, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(48.05, y_in, 48.05, y_out, 0.25, "F.Cu", inv_name, inv_nid))
            # Connect to Op-amp Pin IN- (59.3, y_in)
            pcb.append(make_segment(48.05, y_in, u_x - 2.7, y_in, 0.25, "F.Cu", inv_name, inv_nid))

            # Matrix summing row direct on F.Cu:
            # Jog at X = 43.0 to y_in - 0.70 (A) or y_in + 0.70 (B) to clear bias pad!
            y_sum_jog = y_in - 0.70 if u_unit == "A" else y_in + 0.70
            pcb.append(make_segment(41.20, ry_sum, 43.00, ry_sum, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(43.00, ry_sum, 43.00, y_sum_jog, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(43.00, y_sum_jog, 46.95, y_sum_jog, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(46.95, y_sum_jog, 46.95, y_in, 0.25, "F.Cu", inv_name, inv_nid))

            # 2. SCORE on F.Cu:
            # Rf Pad 2 (49.95, y_out) goes EAST to x_tr and Op-amp Pin OUT (59.3, y_out)
            pcb.append(make_segment(49.95, y_out, u_x - 2.7, y_out, 0.25, "F.Cu", score_name, score_nid))
            # Tap up/down to D_WTA Pad 1 (54.35, y_diode)
            pcb.append(make_segment(54.35, y_out, 54.35, y_diode, 0.25, "F.Cu", score_name, score_nid))

            # 3. WTA_BUS drop via at D_WTA Pad 2 (57.65, y_diode)
            pcb.append(make_via(57.65, y_diode, 0.6, 0.3, "WTA_BUS", 6))

            # 4. Bias rail tap for Rb Pad 1 at (45.05, y_in):
            # Via placed at (45.05, y_in + 1.20 if A else y_in - 1.20) in clear space!
            y_bias_via = y_in + 1.20 if u_unit == "A" else y_in - 1.20
            pcb.append(make_via(45.05, y_bias_via, 0.6, 0.3, b_rail, b_nid))
            pcb.append(make_segment(45.05, y_in, 45.05, y_bias_via, 0.25, "F.Cu", b_rail, b_nid))

            # 5. Drop via to SCORE trunk at x_tr on In2.Cu:
            pcb.append(make_via(x_tr, y_out, 0.6, 0.3, score_name, score_nid))

        else:
            # EAST SIDE: Op-Amp pins on East (X = 64.7).
            # Pin OUT at (64.7, y_out), Pin IN- at (64.7, y_in).
            # Place Rf at X = 75.0, Y = y_out: Pad 1 (74.05)=SCORE, Pad 2 (75.95)=INV
            pcb.append(fp_resistor_0805(f"Rf_L2_{c}", "10k", 75.0, y_out, 0, "F.Cu", score_nid, score_name, inv_nid, inv_name))
            # Place Rb at X = 78.0, Y = y_in: Pad 1 (77.05)=INV, Pad 2 (78.95)=BIAS
            pcb.append(fp_resistor_0805(f"Rb_L2_{c}", c_info["bias_resistor_str"], 78.0, y_in, 0, "F.Cu", inv_nid, inv_name, b_nid, b_rail))

            # D_WTA placed in clear space at (68.0, y_out - 2.50 if D else y_out + 2.50):
            y_diode = y_out - 2.50 if u_unit == "D" else y_out + 2.50
            # rot=180: Pad 1 (69.65)=SCORE, Pad 2 (66.35)=WTA_BUS
            pcb.append(fp_diodesod123(f"D_WTA_{c}", "1N4148", 68.0, y_diode, 180, "F.Cu", score_nid, score_name, 6, "WTA_BUS"))

            # 1. INV_L2 on F.Cu:
            # Rb Pad 1 (77.05, y_in) to Rf Pad 2 (75.95, y_out) via (75.95, y_in)
            pcb.append(make_segment(77.05, y_in, 75.95, y_in, 0.25, "F.Cu", inv_name, inv_nid))
            pcb.append(make_segment(75.95, y_in, 75.95, y_out, 0.25, "F.Cu", inv_name, inv_nid))
            # Connect to Op-amp Pin IN- (64.7, y_in)
            pcb.append(make_segment(75.95, y_in, u_x + 2.7, y_in, 0.25, "F.Cu", inv_name, inv_nid))

            # Matrix summing row on F.Cu:
            # For classes 2, 3: cross at ry_sum (32.45, 37.65) in U1/U2 open gap
            # For classes 6, 7: cross at 60.0, 62.0 in U2/U3 open gap
            if c in [2, 3]:
                pcb.append(make_segment(41.20, ry_sum, 77.05, ry_sum, 0.25, "F.Cu", inv_name, inv_nid))
                pcb.append(make_segment(77.05, ry_sum, 77.05, y_in, 0.25, "F.Cu", inv_name, inv_nid))
            else:
                y_cross = 60.0 if c == 6 else 62.0
                pcb.append(make_segment(41.20, ry_sum, 41.20, y_cross, 0.25, "F.Cu", inv_name, inv_nid))
                pcb.append(make_segment(41.20, y_cross, 77.05, y_cross, 0.25, "F.Cu", inv_name, inv_nid))
                pcb.append(make_segment(77.05, y_cross, 77.05, y_in, 0.25, "F.Cu", inv_name, inv_nid))

            # 2. SCORE on F.Cu:
            # Rf Pad 1 (74.05, y_out) goes WEST to x_tr and Op-amp Pin OUT (64.7, y_out)
            pcb.append(make_segment(74.05, y_out, u_x + 2.7, y_out, 0.25, "F.Cu", score_name, score_nid))
            # Tap up/down to D_WTA Pad 1 (69.65, y_diode)
            pcb.append(make_segment(69.65, y_out, 69.65, y_diode, 0.25, "F.Cu", score_name, score_nid))

            # 3. WTA_BUS drop via at D_WTA Pad 2 (66.35, y_diode)
            pcb.append(make_via(66.35, y_diode, 0.6, 0.3, "WTA_BUS", 6))

            # 4. Bias rail tap for Rb Pad 2 at (78.95, y_in):
            y_bias_via = y_in + 1.20 if u_unit == "D" else y_in - 1.20
            pcb.append(make_via(78.95, y_bias_via, 0.6, 0.3, b_rail, b_nid))
            pcb.append(make_segment(78.95, y_in, 78.95, y_bias_via, 0.25, "F.Cu", b_rail, b_nid))

            # 5. Drop via to SCORE trunk at x_tr on In2.Cu:
            pcb.append(make_via(x_tr, y_out, 0.6, 0.3, score_name, score_nid))

    # -------------------------------------------------------------
    # 5. WTA BUS TRUNK & PULL-DOWN RESISTOR
    # -------------------------------------------------------------
    # West trunk on In2.Cu at X = 57.65 from Y = 18.0 to 82.5
    pcb.append(make_segment(57.65, 18.0, 57.65, 82.5, 0.25, "In2.Cu", "WTA_BUS", 6))
    # East trunk on In2.Cu at X = 66.35 from Y = 18.0 to 58.0
    pcb.append(make_segment(66.35, 18.0, 66.35, 58.0, 0.25, "In2.Cu", "WTA_BUS", 6))
    # Horizontal link on In2.Cu at Y = 36.0 (open gap between U1 and U2)
    pcb.append(make_segment(57.65, 36.0, 66.35, 36.0, 0.25, "In2.Cu", "WTA_BUS", 6))

    # R_WTA at (57.65, 84.0) rot=90:
    # rot=90: Pad 1 at Y = 84.95 (net1 = -12V), Pad 2 at Y = 83.05 (net2 = WTA_BUS)
    pcb.append(fp_resistor_0805("R_WTA", "10k", 57.65, 84.0, 90, "F.Cu", 3, "-12V", 6, "WTA_BUS"))
    pcb.append(make_via(57.65, 82.5, 0.6, 0.3, "WTA_BUS", 6))
    pcb.append(make_segment(57.65, 82.5, 57.65, 83.05, 0.25, "F.Cu", "WTA_BUS", 6))
    # Via to B.Cu at (57.65, 84.95)
    pcb.append(make_via(57.65, 84.95, 0.6, 0.3, "-12V", 3))
    # On B.Cu: run south to Y = 88.0, then east to 86.51! (Well south of SCORE turns!)
    pcb.append(make_segment(57.65, 84.95, 57.65, 88.0, 0.25, "B.Cu", "-12V", 3))
    pcb.append(make_segment(57.65, 88.0, 86.51, 88.0, 0.25, "B.Cu", "-12V", 3))

    # -------------------------------------------------------------
    # 6. OUTPUT HIGHWAYS TO LEDS (Strictly planar on In2.Cu)
    # -------------------------------------------------------------
    for c in range(10):
        score_name = f"SCORE_{c}"
        score_nid = 50 + c
        u_idx, u_unit, y_out, y_in = unit_info[c]
        x_tr = x_trunk_map[c]
        y_bus = 17.5 + c * 0.35
        x_led_via = lx[c] - 2.50

        # Run North on In2.Cu from y_out to y_bus
        pcb.append(make_segment(x_tr, y_out, x_tr, y_bus, 0.25, "In2.Cu", score_name, score_nid))
        # Run West on In2.Cu from x_tr to x_led_via
        pcb.append(make_segment(x_tr, y_bus, x_led_via, y_bus, 0.25, "In2.Cu", score_name, score_nid))
        # Run North on In2.Cu to via at (x_led_via, 12.0)
        pcb.append(make_segment(x_led_via, y_bus, x_led_via, 12.0, 0.25, "In2.Cu", score_name, score_nid))

    # -------------------------------------------------------------
    # 7. OUTPUT HIGHWAYS TO EDGE FINGERS B (Strictly planar on B.Cu)
    # -------------------------------------------------------------
    for c in range(10):
        score_name = f"SCORE_{c}"
        score_nid = 50 + c
        u_idx, u_unit, y_out, y_in = unit_info[c]
        px_bc = col_x[c]
        x_tr = x_trunk_map[c]
        y_turn = 80.50 + c * 0.70

        # Run South on In2.Cu from y_out to y_turn:
        pcb.append(make_segment(x_tr, y_out, x_tr, y_turn, 0.25, "In2.Cu", score_name, score_nid))
        # Drop via to B.Cu AT (x_tr, y_turn):
        pcb.append(make_via(x_tr, y_turn, 0.6, 0.3, score_name, score_nid))
        # Run horizontally on B.Cu across to px_bc:
        pcb.append(make_segment(x_tr, y_turn, px_bc, y_turn, 0.25, "B.Cu", score_name, score_nid))
        # Run straight down on B.Cu to edge finger pad at Y = 92.0:
        pcb.append(make_segment(px_bc, y_turn, px_bc, 92.0, 0.25, "B.Cu", score_name, score_nid))

    # -------------------------------------------------------------
    # 8. POWER & BIAS RAILS (Run north at X >= 84.0, zero ground finger overlap)
    # -------------------------------------------------------------
    # 1. +12V from B33 (83.97, 92.0):
    # Via at (83.97, 88.0) to In2.Cu -> trunk at X = 85.0 from Y = 88.0 to Y = 25.0
    pcb.append(make_segment(83.97, 92.0, 83.97, 88.0, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_via(83.97, 88.0, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(83.97, 88.0, 85.0, 88.0, 0.35, "In2.Cu", "+12V", 2))
    pcb.append(make_segment(85.0, 88.0, 85.0, 25.0, 0.35, "In2.Cu", "+12V", 2))
    for yu in tier_y:
        # Tap on In2.Cu at Y = yu from 85.0 to 52.95
        pcb.append(make_segment(85.0, yu, 52.95, yu, 0.35, "In2.Cu", "+12V", 2))
        pcb.append(make_via(52.95, yu, 0.6, 0.3, "+12V", 2))

    # 2. -12V from B34 (86.51, 92.0) on B.Cu:
    # Trunk at X = 86.51 from Y = 92.0 to Y = 25.0
    pcb.append(make_segment(86.51, 92.0, 86.51, 25.0, 0.35, "B.Cu", "-12V", 3))
    for yu in tier_y:
        y_m12 = yu + 1.0
        pcb.append(make_segment(86.51, y_m12, 71.05, y_m12, 0.35, "B.Cu", "-12V", 3))
        pcb.append(make_via(71.05, y_m12, 0.6, 0.3, "-12V", 3))
        pcb.append(make_segment(71.05, y_m12, 71.05, yu, 0.35, "F.Cu", "-12V", 3))

    # 3. +5V_REF from B35 (89.05, 92.0):
    # Via at (89.05, 88.0) to In2.Cu -> trunk at X = 89.05 from Y = 88.0 to Y = 25.0
    pcb.append(make_segment(89.05, 92.0, 89.05, 88.0, 0.35, "B.Cu", "+5V_REF", 4))
    pcb.append(make_via(89.05, 88.0, 0.6, 0.3, "+5V_REF", 4))
    pcb.append(make_segment(89.05, 88.0, 89.05, 25.0, 0.35, "In2.Cu", "+5V_REF", 4))
    # Taps to East bias resistors (+5V_REF: classes 3, 6):
    for c in [3, 6]:
        _, u_unit, _, y_in = unit_info[c]
        y_bv = y_in + 1.20 if u_unit == "D" else y_in - 1.20
        pcb.append(make_via(89.05, y_bv, 0.6, 0.3, "+5V_REF", 4))
        pcb.append(make_segment(89.05, y_bv, 78.95, y_bv, 0.25, "F.Cu", "+5V_REF", 4))
    # Tap to West bias resistor (+5V_REF: class 1 at y_in = 27.54)
    # Cross at Y = 36.0 on F.Cu to (45.05, 36.0), then up to y_bias_via (27.54 - 1.20 = 26.34)
    y_b1_via = unit_info[1][3] - 1.20
    pcb.append(make_via(89.05, 36.0, 0.6, 0.3, "+5V_REF", 4))
    pcb.append(make_segment(89.05, 36.0, 45.05, 36.0, 0.25, "F.Cu", "+5V_REF", 4))
    pcb.append(make_segment(45.05, 36.0, 45.05, y_b1_via, 0.25, "F.Cu", "+5V_REF", 4))

    # 4. -5V_REF from B36 (91.59, 92.0) on B.Cu:
    # Trunk at X = 91.59 from Y = 92.0 to Y = 20.0
    pcb.append(make_segment(91.59, 92.0, 91.59, 20.0, 0.35, "B.Cu", "-5V_REF", 5))
    # Taps to East bias resistors (-5V_REF: classes 2, 7) on B.Cu:
    for c in [2, 7]:
        _, u_unit, _, y_in = unit_info[c]
        y_bv = y_in + 1.20 if u_unit == "D" else y_in - 1.20
        pcb.append(make_segment(91.59, y_bv, 78.95, y_bv, 0.25, "B.Cu", "-5V_REF", 5))
    # Taps to West bias resistors (-5V_REF: class 0 at y_in = 22.46, classes 4, 5, 8, 9 at y_in in [47.46, 77.54])
    # Class 0: cross at Y = 20.0 on F.Cu to clear B.Cu -12V trunk!
    y_b0_via = unit_info[0][3] + 1.20
    pcb.append(make_via(91.59, 20.0, 0.6, 0.3, "-5V_REF", 5))
    pcb.append(make_segment(91.59, 20.0, 45.05, 20.0, 0.25, "F.Cu", "-5V_REF", 5))
    pcb.append(make_segment(45.05, 20.0, 45.05, y_b0_via, 0.25, "F.Cu", "-5V_REF", 5))
    # Classes 4, 5, 8, 9: cross at Y = 61.0 on F.Cu, then drop to B.Cu at X = 45.05
    pcb.append(make_via(91.59, 61.0, 0.6, 0.3, "-5V_REF", 5))
    pcb.append(make_segment(91.59, 61.0, 45.05, 61.0, 0.25, "F.Cu", "-5V_REF", 5))
    pcb.append(make_via(45.05, 61.0, 0.6, 0.3, "-5V_REF", 5))
    # On B.Cu: connect the bias vias at (45.05, y_bv) for c in [4, 5, 8, 9]
    y_b4_via = unit_info[4][3] + 1.20
    y_b9_via = unit_info[9][3] - 1.20
    pcb.append(make_segment(45.05, y_b4_via, 45.05, y_b9_via, 0.25, "B.Cu", "-5V_REF", 5))

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
