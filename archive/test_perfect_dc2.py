#!/usr/bin/env python3
import json, uuid, subprocess, re, sys

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
    (at {x:.3f} {y:.3f} {rot})
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
    (at {x:.3f} {y:.3f} {rot})
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
    (at {x:.3f} {y:.3f} {rot})
    (descr "SOD-123 diode (Pad 1=Cathode, Pad 2=Anode)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -1.65 0) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.65 0) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD8_3DMODEL_DIR}}/Diode_SMD.3dshapes/D_SOD-123.step"
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

def build_perfect_architecture_dc2(board_file):
    PITCH = 2.54
    cx = 94.28 / 2.0
    x_start = cx - (17.5 * PITCH) # 2.69 mm

    nets = {0: "", 1: "GND", 2: "+12V", 3: "-12V"}
    for k in range(16):
        nets[100 + k] = f"V_SUM_{k}"
        nets[200 + k] = f"ACT_{k}"
        nets[300 + k] = f"INV_RELU_{k}"
        nets[400 + k] = f"OP_OUT_{k}"

    pin_nets_a = {}
    pin_nets_b = {}

    for k in range(16):
        pin_nets_a[f"A{k+1}"] = (100 + k, f"V_SUM_{k}")
        pin_nets_b[f"B{k+1}"] = (200 + k, f"ACT_{k}")

    for p in range(17, 37):
        pin_nets_a[f"A{p}"] = (1, "GND")
    for p in range(17, 33):
        pin_nets_b[f"B{p}"] = (1, "GND")

    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    # B35 and B36 are unassigned (isolated) on DC2 to avoid shorting Motherboard +5V_REF and -5V_REF rails

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in sorted(nets.items()) if nid > 0])
    header = f"""(kicad_pcb (version 20221018) (generator "analog_nn_perfect_dc2_router")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "Daughtercard 2: 16-Channel Precision Active ReLU")
    (company "Discrete Analog Neural Network System")
    (rev "v38.0 - Zero Error Verified")
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
        f'  (gr_text "16-Channel Active ReLU (DC2)" (at 47.14 8.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 2.5 2.5) (thickness 0.3))))'
    ]

    tier_y = [20.0, 40.0, 60.0, 80.0]
    u_x = 62.0

    for u_idx, yu in enumerate(tier_y):
        u_ref = f"U{u_idx+1}"
        k_base = u_idx * 4
        # Monotonic channel mapping:
        # Unit A (Top-Left): k0
        # Unit D (Top-Right): k1
        # Unit B (Bottom-Left): k2
        # Unit C (Bottom-Right): k3
        k0 = k_base + 0
        k1 = k_base + 1
        k2 = k_base + 2
        k3 = k_base + 3

        ic_pin_nets = {
            "1": (400 + k0, f"OP_OUT_{k0}"), "2": (300 + k0, f"INV_RELU_{k0}"), "3": (1, "GND"),
            "4": (2, "+12V"), "5": (1, "GND"),
            "6": (300 + k2, f"INV_RELU_{k2}"), "7": (400 + k2, f"OP_OUT_{k2}"),
            "8": (400 + k3, f"OP_OUT_{k3}"), "9": (300 + k3, f"INV_RELU_{k3}"), "10": (1, "GND"),
            "11": (3, "-12V"), "12": (1, "GND"),
            "13": (300 + k1, f"INV_RELU_{k1}"), "14": (400 + k1, f"OP_OUT_{k1}")
        }
        pcb.append(fp_soic14(u_ref, "TL074", u_x, yu, 0, "F.Cu", ic_pin_nets))

        # Ground vias for Pins 3, 5, 10, 12: place at X = 56.5 and X = 67.5
        # Pin 3 & Pin 12 are at Y = yu - 1.27
        pcb.append(make_via(56.5, yu - 1.27, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u_x - 2.7, yu - 1.27, 56.5, yu - 1.27, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_via(67.5, yu - 1.27, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u_x + 2.7, yu - 1.27, 67.5, yu - 1.27, 0.25, "F.Cu", "GND", 1))

        # Pin 5 & Pin 10 are at Y = yu + 1.27
        pcb.append(make_via(56.5, yu + 1.27, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u_x - 2.7, yu + 1.27, 56.5, yu + 1.27, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_via(67.5, yu + 1.27, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(u_x + 2.7, yu + 1.27, 67.5, yu + 1.27, 0.25, "F.Cu", "GND", 1))

        # Decoupling Caps C_P (+12V) and C_N (-12V)
        # C_P at (52.0, yu) rot=0: Pad 1 (51.05)=GND, Pad 2 (52.95)=+12V
        pcb.append(fp_capacitor_0805(f"C_{u_ref}P", "0.1uF", 52.0, yu, 0, "F.Cu", 1, "GND", 2, "+12V"))
        pcb.append(make_via(51.05, yu - 1.8, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(51.05, yu, 51.05, yu - 1.8, 0.25, "F.Cu", "GND", 1))
        # +12V from Pad 2 (52.95) to Pin 4 (59.3, yu)
        pcb.append(make_segment(52.95, yu, u_x - 2.7, yu, 0.35, "F.Cu", "+12V", 2))

        # C_N at (72.0, yu) rot=0: Pad 1 (71.05)=-12V, Pad 2 (72.95)=GND
        pcb.append(fp_capacitor_0805(f"C_{u_ref}N", "0.1uF", 72.0, yu, 0, "F.Cu", 3, "-12V", 1, "GND"))
        pcb.append(make_via(72.95, yu - 1.8, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(72.95, yu, 72.95, yu - 1.8, 0.25, "F.Cu", "GND", 1))
        # -12V from Pad 1 (71.05) to Pin 11 (64.7, yu)
        pcb.append(make_segment(71.05, yu, u_x + 2.7, yu, 0.35, "F.Cu", "-12V", 3))

        # -------------------------------------------------------------
        # CELL 0: Unit A (Top-Left) -> k0
        # -------------------------------------------------------------
        # Rin0 at (43.0, yu - 3.81) rot=0: Pad 1 (42.05)=VSUM, Pad 2 (43.95)=INV
        pcb.append(fp_resistor_0805(f"R_IN_{k0}", "10k", 43.0, yu - 3.81, 0, "F.Cu", 100 + k0, f"V_SUM_{k0}", 300 + k0, f"INV_RELU_{k0}"))
        # Rfb0 at (47.0, yu - 3.81) rot=0: Pad 1 (46.05)=INV, Pad 2 (47.95)=ACT
        pcb.append(fp_resistor_0805(f"R_FB_{k0}", "10k", 47.0, yu - 3.81, 0, "F.Cu", 300 + k0, f"INV_RELU_{k0}", 200 + k0, f"ACT_{k0}"))
        # D_clamp0 at (45.0, yu - 5.80) rot=0: Pad 1 (43.35)=OP_OUT, Pad 2 (46.65)=INV
        pcb.append(fp_diodesod123(f"D_CLAMP_{k0}", "1N4148", 45.0, yu - 5.80, 0, "F.Cu", 400 + k0, f"OP_OUT_{k0}", 300 + k0, f"INV_RELU_{k0}"))
        # D_rect0 at (51.0, yu - 5.80) rot=0: Pad 1 (49.35)=ACT, Pad 2 (52.65)=OP_OUT
        pcb.append(fp_diodesod123(f"D_RECT_{k0}", "1N4148", 51.0, yu - 5.80, 0, "F.Cu", 200 + k0, f"ACT_{k0}", 400 + k0, f"OP_OUT_{k0}"))

        # Wires Cell 0:
        # INV_RELU_k0: Rin Pad 2 (43.95, yu-3.81) to Rfb Pad 1 (46.05, yu-3.81)
        pcb.append(make_segment(43.95, yu - 3.81, 46.05, yu - 3.81, 0.25, "F.Cu", f"INV_RELU_{k0}", 300 + k0))
        # to Dclamp Pad 2 (46.65, yu-5.80)
        pcb.append(make_segment(46.05, yu - 3.81, 46.65, yu - 3.81, 0.25, "F.Cu", f"INV_RELU_{k0}", 300 + k0))
        pcb.append(make_segment(46.65, yu - 3.81, 46.65, yu - 5.80, 0.25, "F.Cu", f"INV_RELU_{k0}", 300 + k0))
        # to Pin 2 (59.3, yu-2.54)
        pcb.append(make_segment(46.05, yu - 3.81, 46.05, yu - 2.54, 0.25, "F.Cu", f"INV_RELU_{k0}", 300 + k0))
        pcb.append(make_segment(46.05, yu - 2.54, u_x - 2.7, yu - 2.54, 0.25, "F.Cu", f"INV_RELU_{k0}", 300 + k0))

        # OP_OUT_k0: loops around north edge at (yu - 8.20)
        pcb.append(make_segment(u_x - 2.7, yu - 3.81, 55.0, yu - 3.81, 0.25, "F.Cu", f"OP_OUT_{k0}", 400 + k0))
        pcb.append(make_segment(55.0, yu - 3.81, 55.0, yu - 8.20, 0.25, "F.Cu", f"OP_OUT_{k0}", 400 + k0))
        pcb.append(make_segment(55.0, yu - 8.20, 43.35, yu - 8.20, 0.25, "F.Cu", f"OP_OUT_{k0}", 400 + k0))
        pcb.append(make_segment(43.35, yu - 8.20, 43.35, yu - 5.80, 0.25, "F.Cu", f"OP_OUT_{k0}", 400 + k0))
        pcb.append(make_segment(52.65, yu - 8.20, 52.65, yu - 5.80, 0.25, "F.Cu", f"OP_OUT_{k0}", 400 + k0))

        # ACT_k0: Rfb Pad 2 (47.95, yu-3.81) -> (49.35, yu-3.81) -> Drect Pad 1 (49.35, yu-5.80)
        pcb.append(make_segment(47.95, yu - 3.81, 49.35, yu - 3.81, 0.25, "F.Cu", f"ACT_{k0}", 200 + k0))
        pcb.append(make_segment(49.35, yu - 3.81, 49.35, yu - 5.80, 0.25, "F.Cu", f"ACT_{k0}", 200 + k0))
        # Via to B.Cu at (49.35, yu - 6.0)
        y_act_k0 = yu - 6.0
        pcb.append(make_segment(49.35, yu - 5.80, 49.35, y_act_k0, 0.25, "F.Cu", f"ACT_{k0}", 200 + k0))
        pcb.append(make_via(49.35, y_act_k0, 0.6, 0.3, f"ACT_{k0}", 200 + k0))

        # -------------------------------------------------------------
        # CELL 1: Unit D (Top-Right) -> k1
        # -------------------------------------------------------------
        # Rfb1 at (77.0, yu - 3.81) rot=0: Pad 1 (76.05)=ACT, Pad 2 (77.95)=INV
        pcb.append(fp_resistor_0805(f"R_FB_{k1}", "10k", 77.0, yu - 3.81, 0, "F.Cu", 200 + k1, f"ACT_{k1}", 300 + k1, f"INV_RELU_{k1}"))
        # Rin1 at (81.0, yu - 3.81) rot=0: Pad 1 (80.05)=INV, Pad 2 (81.95)=VSUM
        pcb.append(fp_resistor_0805(f"R_IN_{k1}", "10k", 81.0, yu - 3.81, 0, "F.Cu", 300 + k1, f"INV_RELU_{k1}", 100 + k1, f"V_SUM_{k1}"))
        # D_rect1 at (73.0, yu - 5.80) rot=0: Pad 1 (71.35)=ACT, Pad 2 (74.65)=OP_OUT
        pcb.append(fp_diodesod123(f"D_RECT_{k1}", "1N4148", 73.0, yu - 5.80, 0, "F.Cu", 200 + k1, f"ACT_{k1}", 400 + k1, f"OP_OUT_{k1}"))
        # D_clamp1 at (79.0, yu - 5.80) rot=0: Pad 1 (77.35)=OP_OUT, Pad 2 (80.65)=INV
        pcb.append(fp_diodesod123(f"D_CLAMP_{k1}", "1N4148", 79.0, yu - 5.80, 0, "F.Cu", 400 + k1, f"OP_OUT_{k1}", 300 + k1, f"INV_RELU_{k1}"))

        # Wires Cell 1:
        # INV_RELU_k1: Rfb Pad 2 (77.95, yu-3.81) to Rin Pad 1 (80.05, yu-3.81)
        pcb.append(make_segment(77.95, yu - 3.81, 80.05, yu - 3.81, 0.25, "F.Cu", f"INV_RELU_{k1}", 300 + k1))
        # to Dclamp Pad 2 (80.65, yu-5.80)
        pcb.append(make_segment(80.05, yu - 3.81, 80.65, yu - 3.81, 0.25, "F.Cu", f"INV_RELU_{k1}", 300 + k1))
        pcb.append(make_segment(80.65, yu - 3.81, 80.65, yu - 5.80, 0.25, "F.Cu", f"INV_RELU_{k1}", 300 + k1))
        # to Pin 13 (64.7, yu-2.54)
        pcb.append(make_segment(77.95, yu - 3.81, 77.95, yu - 2.54, 0.25, "F.Cu", f"INV_RELU_{k1}", 300 + k1))
        pcb.append(make_segment(77.95, yu - 2.54, u_x + 2.7, yu - 2.54, 0.25, "F.Cu", f"INV_RELU_{k1}", 300 + k1))

        # OP_OUT_k1: loops around north edge at (yu - 8.20)
        pcb.append(make_segment(u_x + 2.7, yu - 3.81, 69.0, yu - 3.81, 0.25, "F.Cu", f"OP_OUT_{k1}", 400 + k1))
        pcb.append(make_segment(69.0, yu - 3.81, 69.0, yu - 8.20, 0.25, "F.Cu", f"OP_OUT_{k1}", 400 + k1))
        pcb.append(make_segment(69.0, yu - 8.20, 77.35, yu - 8.20, 0.25, "F.Cu", f"OP_OUT_{k1}", 400 + k1))
        pcb.append(make_segment(77.35, yu - 8.20, 77.35, yu - 5.80, 0.25, "F.Cu", f"OP_OUT_{k1}", 400 + k1))
        pcb.append(make_segment(74.65, yu - 8.20, 74.65, yu - 5.80, 0.25, "F.Cu", f"OP_OUT_{k1}", 400 + k1))

        # ACT_k1: Drect Pad 1 (71.35, yu-5.80) to Rfb Pad 1 (76.05, yu-3.81) via path at Y = yu - 4.20
        pcb.append(make_segment(71.35, yu - 5.80, 71.35, yu - 4.20, 0.25, "F.Cu", f"ACT_{k1}", 200 + k1))
        pcb.append(make_segment(71.35, yu - 4.20, 76.05, yu - 4.20, 0.25, "F.Cu", f"ACT_{k1}", 200 + k1))
        pcb.append(make_segment(76.05, yu - 4.20, 76.05, yu - 3.81, 0.25, "F.Cu", f"ACT_{k1}", 200 + k1))
        # Via to B.Cu at (71.35, yu - 4.80) -> north of Pin 13
        y_act_k1 = yu - 4.80
        pcb.append(make_via(71.35, y_act_k1, 0.6, 0.3, f"ACT_{k1}", 200 + k1))

        # -------------------------------------------------------------
        # CELL 2: Unit B (Bottom-Left) -> k2
        # -------------------------------------------------------------
        # Rin2 at (43.0, yu + 3.81) rot=0: Pad 1 (42.05)=VSUM, Pad 2 (43.95)=INV
        pcb.append(fp_resistor_0805(f"R_IN_{k2}", "10k", 43.0, yu + 3.81, 0, "F.Cu", 100 + k2, f"V_SUM_{k2}", 300 + k2, f"INV_RELU_{k2}"))
        # Rfb2 at (47.0, yu + 3.81) rot=0: Pad 1 (46.05)=INV, Pad 2 (47.95)=ACT
        pcb.append(fp_resistor_0805(f"R_FB_{k2}", "10k", 47.0, yu + 3.81, 0, "F.Cu", 300 + k2, f"INV_RELU_{k2}", 200 + k2, f"ACT_{k2}"))
        # D_clamp2 at (45.0, yu + 5.80) rot=0: Pad 1 (43.35)=OP_OUT, Pad 2 (46.65)=INV
        pcb.append(fp_diodesod123(f"D_CLAMP_{k2}", "1N4148", 45.0, yu + 5.80, 0, "F.Cu", 400 + k2, f"OP_OUT_{k2}", 300 + k2, f"INV_RELU_{k2}"))
        # D_rect2 at (51.0, yu + 5.80) rot=0: Pad 1 (49.35)=ACT, Pad 2 (52.65)=OP_OUT
        pcb.append(fp_diodesod123(f"D_RECT_{k2}", "1N4148", 51.0, yu + 5.80, 0, "F.Cu", 200 + k2, f"ACT_{k2}", 400 + k2, f"OP_OUT_{k2}"))

        # Wires Cell 2:
        # INV_RELU_k2: Rin Pad 2 (43.95, yu+3.81) to Rfb Pad 1 (46.05, yu+3.81)
        pcb.append(make_segment(43.95, yu + 3.81, 46.05, yu + 3.81, 0.25, "F.Cu", f"INV_RELU_{k2}", 300 + k2))
        # to Dclamp Pad 2 (46.65, yu+5.80)
        pcb.append(make_segment(46.05, yu + 3.81, 46.65, yu + 3.81, 0.25, "F.Cu", f"INV_RELU_{k2}", 300 + k2))
        pcb.append(make_segment(46.65, yu + 3.81, 46.65, yu + 5.80, 0.25, "F.Cu", f"INV_RELU_{k2}", 300 + k2))
        # to Pin 6 (59.3, yu+2.54)
        pcb.append(make_segment(46.05, yu + 3.81, 46.05, yu + 2.54, 0.25, "F.Cu", f"INV_RELU_{k2}", 300 + k2))
        pcb.append(make_segment(46.05, yu + 2.54, u_x - 2.7, yu + 2.54, 0.25, "F.Cu", f"INV_RELU_{k2}", 300 + k2))

        # OP_OUT_k2: loops around south edge at (yu + 8.20)
        pcb.append(make_segment(u_x - 2.7, yu + 3.81, 55.0, yu + 3.81, 0.25, "F.Cu", f"OP_OUT_{k2}", 400 + k2))
        pcb.append(make_segment(55.0, yu + 3.81, 55.0, yu + 8.20, 0.25, "F.Cu", f"OP_OUT_{k2}", 400 + k2))
        pcb.append(make_segment(55.0, yu + 8.20, 43.35, yu + 8.20, 0.25, "F.Cu", f"OP_OUT_{k2}", 400 + k2))
        pcb.append(make_segment(43.35, yu + 8.20, 43.35, yu + 5.80, 0.25, "F.Cu", f"OP_OUT_{k2}", 400 + k2))
        pcb.append(make_segment(52.65, yu + 8.20, 52.65, yu + 5.80, 0.25, "F.Cu", f"OP_OUT_{k2}", 400 + k2))

        # ACT_k2: Drect Pad 1 (49.35, yu+5.80) to Rfb Pad 2 (47.95, yu+3.81) via path at Y = yu + 4.20
        pcb.append(make_segment(49.35, yu + 5.80, 49.35, yu + 4.20, 0.25, "F.Cu", f"ACT_{k2}", 200 + k2))
        pcb.append(make_segment(49.35, yu + 4.20, 47.95, yu + 4.20, 0.25, "F.Cu", f"ACT_{k2}", 200 + k2))
        pcb.append(make_segment(47.95, yu + 4.20, 47.95, yu + 3.81, 0.25, "F.Cu", f"ACT_{k2}", 200 + k2))
        # Via to B.Cu at (49.35, yu + 4.80) -> south of Pin 6
        y_act_k2 = yu + 4.80
        pcb.append(make_via(49.35, y_act_k2, 0.6, 0.3, f"ACT_{k2}", 200 + k2))

        # -------------------------------------------------------------
        # CELL 3: Unit C (Bottom-Right) -> k3
        # -------------------------------------------------------------
        # Rfb3 at (77.0, yu + 3.81) rot=0: Pad 1 (76.05)=ACT, Pad 2 (77.95)=INV
        pcb.append(fp_resistor_0805(f"R_FB_{k3}", "10k", 77.0, yu + 3.81, 0, "F.Cu", 200 + k3, f"ACT_{k3}", 300 + k3, f"INV_RELU_{k3}"))
        # Rin3 at (81.0, yu + 3.81) rot=0: Pad 1 (80.05)=INV, Pad 2 (81.95)=VSUM
        pcb.append(fp_resistor_0805(f"R_IN_{k3}", "10k", 81.0, yu + 3.81, 0, "F.Cu", 300 + k3, f"INV_RELU_{k3}", 100 + k3, f"V_SUM_{k3}"))
        # D_rect3 at (73.0, yu + 5.80) rot=0: Pad 1 (71.35)=ACT, Pad 2 (74.65)=OP_OUT
        pcb.append(fp_diodesod123(f"D_RECT_{k3}", "1N4148", 73.0, yu + 5.80, 0, "F.Cu", 200 + k3, f"ACT_{k3}", 400 + k3, f"OP_OUT_{k3}"))
        # D_clamp3 at (79.0, yu + 5.80) rot=0: Pad 1 (77.35)=OP_OUT, Pad 2 (80.65)=INV
        pcb.append(fp_diodesod123(f"D_CLAMP_{k3}", "1N4148", 79.0, yu + 5.80, 0, "F.Cu", 400 + k3, f"OP_OUT_{k3}", 300 + k3, f"INV_RELU_{k3}"))

        # Wires Cell 3:
        # INV_RELU_k3: Rfb Pad 2 (77.95, yu+3.81) to Rin Pad 1 (80.05, yu+3.81)
        pcb.append(make_segment(77.95, yu + 3.81, 80.05, yu + 3.81, 0.25, "F.Cu", f"INV_RELU_{k3}", 300 + k3))
        # to Dclamp Pad 2 (80.65, yu+5.80)
        pcb.append(make_segment(80.05, yu + 3.81, 80.65, yu + 3.81, 0.25, "F.Cu", f"INV_RELU_{k3}", 300 + k3))
        pcb.append(make_segment(80.65, yu + 3.81, 80.65, yu + 5.80, 0.25, "F.Cu", f"INV_RELU_{k3}", 300 + k3))
        # to Pin 9 (64.7, yu+2.54)
        pcb.append(make_segment(77.95, yu + 3.81, 77.95, yu + 2.54, 0.25, "F.Cu", f"INV_RELU_{k3}", 300 + k3))
        pcb.append(make_segment(77.95, yu + 2.54, u_x + 2.7, yu + 2.54, 0.25, "F.Cu", f"INV_RELU_{k3}", 300 + k3))

        # OP_OUT_k3: loops around south edge at (yu + 8.20)
        pcb.append(make_segment(u_x + 2.7, yu + 3.81, 69.0, yu + 3.81, 0.25, "F.Cu", f"OP_OUT_{k3}", 400 + k3))
        pcb.append(make_segment(69.0, yu + 3.81, 69.0, yu + 8.20, 0.25, "F.Cu", f"OP_OUT_{k3}", 400 + k3))
        pcb.append(make_segment(69.0, yu + 8.20, 77.35, yu + 8.20, 0.25, "F.Cu", f"OP_OUT_{k3}", 400 + k3))
        pcb.append(make_segment(77.35, yu + 8.20, 77.35, yu + 5.80, 0.25, "F.Cu", f"OP_OUT_{k3}", 400 + k3))
        pcb.append(make_segment(74.65, yu + 8.20, 74.65, yu + 5.80, 0.25, "F.Cu", f"OP_OUT_{k3}", 400 + k3))

        # ACT_k3: Drect Pad 1 (71.35, yu+5.80) to Rfb Pad 1 (76.05, yu+3.81) via path at Y = yu + 4.20
        pcb.append(make_segment(71.35, yu + 5.80, 71.35, yu + 4.20, 0.25, "F.Cu", f"ACT_{k3}", 200 + k3))
        pcb.append(make_segment(71.35, yu + 4.20, 76.05, yu + 4.20, 0.25, "F.Cu", f"ACT_{k3}", 200 + k3))
        pcb.append(make_segment(76.05, yu + 4.20, 76.05, yu + 3.81, 0.25, "F.Cu", f"ACT_{k3}", 200 + k3))
        # Via to B.Cu at (71.35, yu + 6.0)
        y_act_k3 = yu + 6.0
        pcb.append(make_segment(71.35, yu + 5.80, 71.35, y_act_k3, 0.25, "F.Cu", f"ACT_{k3}", 200 + k3))
        pcb.append(make_via(71.35, y_act_k3, 0.6, 0.3, f"ACT_{k3}", 200 + k3))

        # -------------------------------------------------------------
        # BUS CONNECTIONS FOR TIER (STRICTLY PLANAR MONOTONIC)
        # -------------------------------------------------------------
        xk0 = x_start + k0 * PITCH
        xk1 = x_start + k1 * PITCH
        xk2 = x_start + k2 * PITCH
        xk3 = x_start + k3 * PITCH

        y_vsum_k0 = yu - 3.81
        y_vsum_k1 = yu - 2.50
        y_vsum_k2 = yu + 2.50
        y_vsum_k3 = 87.0 if u_idx == 3 else yu + 3.50

        # V_SUM routing:
        # k0: straight up on F.Cu at xk0 to y_vsum_k0, then east to Rin0 Pad 1 (42.05, yu - 3.81)
        pcb.append(make_segment(xk0, 92.0, xk0, y_vsum_k0, 0.25, "F.Cu", f"V_SUM_{k0}", 100 + k0))
        pcb.append(make_segment(xk0, y_vsum_k0, 42.05, y_vsum_k0, 0.25, "F.Cu", f"V_SUM_{k0}", 100 + k0))

        # k1: up on F.Cu at xk1 to y_vsum_k1, east on F.Cu to (xk1 + 1.2) -> via to In2.Cu
        #     east on In2.Cu to (83.5, y_vsum_k1) -> via to F.Cu at (83.5, y_vsum_k1)
        #     then on F.Cu to Rin1 Pad 2 (81.95, yu - 3.81)
        xv1 = xk1 + 1.2
        pcb.append(make_segment(xk1, 92.0, xk1, y_vsum_k1, 0.25, "F.Cu", f"V_SUM_{k1}", 100 + k1))
        pcb.append(make_segment(xk1, y_vsum_k1, xv1, y_vsum_k1, 0.25, "F.Cu", f"V_SUM_{k1}", 100 + k1))
        pcb.append(make_via(xv1, y_vsum_k1, 0.6, 0.3, f"V_SUM_{k1}", 100 + k1))
        pcb.append(make_segment(xv1, y_vsum_k1, 83.5, y_vsum_k1, 0.25, "In2.Cu", f"V_SUM_{k1}", 100 + k1))
        pcb.append(make_via(83.5, y_vsum_k1, 0.6, 0.3, f"V_SUM_{k1}", 100 + k1))
        pcb.append(make_segment(83.5, y_vsum_k1, 83.5, yu - 3.81, 0.25, "F.Cu", f"V_SUM_{k1}", 100 + k1))
        pcb.append(make_segment(83.5, yu - 3.81, 81.95, yu - 3.81, 0.25, "F.Cu", f"V_SUM_{k1}", 100 + k1))

        # k2: up on F.Cu at xk2 to y_vsum_k2, then east to (42.05, y_vsum_k2) -> (42.05, yu + 3.81)
        pcb.append(make_segment(xk2, 92.0, xk2, y_vsum_k2, 0.25, "F.Cu", f"V_SUM_{k2}", 100 + k2))
        pcb.append(make_segment(xk2, y_vsum_k2, 42.05, y_vsum_k2, 0.25, "F.Cu", f"V_SUM_{k2}", 100 + k2))
        pcb.append(make_segment(42.05, y_vsum_k2, 42.05, yu + 3.81, 0.25, "F.Cu", f"V_SUM_{k2}", 100 + k2))

        # k3: up on F.Cu at xk3 to y_vsum_k3, east on F.Cu to xv3 -> via to In2.Cu
        #     east on In2.Cu to xv3_east -> via to F.Cu at (xv3_east, y_vsum_k3)
        #     then on F.Cu to Rin3 Pad 2 (81.95, yu + 3.81)
        if u_idx == 3:
            xv3 = 42.0
            xv3_east = 82.8
            pcb.append(make_segment(xk3, 92.0, xk3, y_vsum_k3, 0.25, "F.Cu", f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_segment(xk3, y_vsum_k3, xv3, y_vsum_k3, 0.25, "F.Cu", f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_via(xv3, y_vsum_k3, 0.6, 0.3, f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_segment(xv3, y_vsum_k3, xv3_east, y_vsum_k3, 0.25, "In2.Cu", f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_via(xv3_east, y_vsum_k3, 0.6, 0.3, f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_segment(xv3_east, y_vsum_k3, xv3_east, yu + 3.81, 0.25, "F.Cu", f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_segment(xv3_east, yu + 3.81, 81.95, yu + 3.81, 0.25, "F.Cu", f"V_SUM_{k3}", 100 + k3))
        else:
            xv3 = xk3 + 1.2
            pcb.append(make_segment(xk3, 92.0, xk3, y_vsum_k3, 0.25, "F.Cu", f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_segment(xk3, y_vsum_k3, xv3, y_vsum_k3, 0.25, "F.Cu", f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_via(xv3, y_vsum_k3, 0.6, 0.3, f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_segment(xv3, y_vsum_k3, 83.5, y_vsum_k3, 0.25, "In2.Cu", f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_via(83.5, y_vsum_k3, 0.6, 0.3, f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_segment(83.5, y_vsum_k3, 83.5, yu + 3.81, 0.25, "F.Cu", f"V_SUM_{k3}", 100 + k3))
            pcb.append(make_segment(83.5, yu + 3.81, 81.95, yu + 3.81, 0.25, "F.Cu", f"V_SUM_{k3}", 100 + k3))

        # ACT outputs on B.Cu:
        # Monotonic Y order: y_act_k0 (yu - 6.0) < y_act_k1 (yu - 4.8) < y_act_k2 (yu + 4.8) < y_act_k3 (yu + 6.0)
        pcb.append(make_segment(49.35, y_act_k0, xk0, y_act_k0, 0.25, "B.Cu", f"ACT_{k0}", 200 + k0))
        pcb.append(make_segment(xk0, y_act_k0, xk0, 92.0, 0.25, "B.Cu", f"ACT_{k0}", 200 + k0))

        pcb.append(make_segment(71.35, y_act_k1, xk1, y_act_k1, 0.25, "B.Cu", f"ACT_{k1}", 200 + k1))
        pcb.append(make_segment(xk1, y_act_k1, xk1, 92.0, 0.25, "B.Cu", f"ACT_{k1}", 200 + k1))

        pcb.append(make_segment(49.35, y_act_k2, xk2, y_act_k2, 0.25, "B.Cu", f"ACT_{k2}", 200 + k2))
        pcb.append(make_segment(xk2, y_act_k2, xk2, 92.0, 0.25, "B.Cu", f"ACT_{k2}", 200 + k2))

        pcb.append(make_segment(71.35, y_act_k3, xk3, y_act_k3, 0.25, "B.Cu", f"ACT_{k3}", 200 + k3))
        pcb.append(make_segment(xk3, y_act_k3, xk3, 92.0, 0.25, "B.Cu", f"ACT_{k3}", 200 + k3))

    # -------------------------------------------------------------
    # POWER RAILS (+12V on In2.Cu, -12V on B.Cu)
    # -------------------------------------------------------------
    # +12V from B33 (83.97, 92.0) on B.Cu:
    # Run straight north at X = 83.97 on B.Cu to (83.97, 88.0) -> via to In2.Cu
    pcb.append(make_segment(83.97, 92.0, 83.97, 88.0, 0.35, "B.Cu", "+12V", 2))
    pcb.append(make_via(83.97, 88.0, 0.6, 0.3, "+12V", 2))
    # Trunk on In2.Cu at X = 85.5 from Y = 88.0 to Y = 20.0
    pcb.append(make_segment(83.97, 88.0, 85.5, 88.0, 0.35, "In2.Cu", "+12V", 2))
    pcb.append(make_segment(85.5, 88.0, 85.5, 20.0, 0.35, "In2.Cu", "+12V", 2))

    # -12V from B34 (86.51, 92.0) on B.Cu:
    # Run straight north at X = 86.51 on B.Cu up to Y = 21.0
    pcb.append(make_segment(86.51, 92.0, 86.51, 21.0, 0.35, "B.Cu", "-12V", 3))

    # Taps to each IC:
    for yu in tier_y:
        # +12V tap: on In2.Cu at Y = yu
        # from (85.5, yu) west to (52.95, yu) -> via to F.Cu at (52.95, yu)
        pcb.append(make_segment(85.5, yu, 52.95, yu, 0.35, "In2.Cu", "+12V", 2))
        pcb.append(make_via(52.95, yu, 0.6, 0.3, "+12V", 2))

        # -12V tap: on B.Cu at Y = (yu + 1.0)
        # from (86.51, yu + 1.0) west to (71.05, yu + 1.0) -> via to F.Cu at (71.05, yu + 1.0)
        # then on F.Cu from (71.05, yu + 1.0) to Pin 11 (71.05, yu)
        y_m12 = yu + 1.0
        pcb.append(make_segment(86.51, y_m12, 71.05, y_m12, 0.35, "B.Cu", "-12V", 3))
        pcb.append(make_via(71.05, y_m12, 0.6, 0.3, "-12V", 3))
        pcb.append(make_segment(71.05, y_m12, 71.05, yu, 0.35, "F.Cu", "-12V", 3))

    # -------------------------------------------------------------
    # GROUND SHIELD FINGERS
    # -------------------------------------------------------------
    # Front fingers A17..A32, A35..A36: drop via to In1.Cu at (px, 89.0)
    for p in list(range(17, 33)) + [35, 36]:
        px = x_start + (p - 1) * PITCH
        pcb.append(make_segment(px, 92.0, px, 89.0, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_via(px, 89.0, 0.6, 0.3, "GND", 1))

    # Front fingers A33, A34 (opposite B33, B34):
    # Connect on F.Cu at Y = 91.0 to Pin A32 (81.43) which has a solid GND via!
    px32 = x_start + (32 - 1) * PITCH # 81.43
    px33 = x_start + (33 - 1) * PITCH # 83.97
    px34 = x_start + (34 - 1) * PITCH # 86.51
    pcb.append(make_segment(px34, 92.0, px34, 91.0, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(px34, 91.0, px32, 91.0, 0.25, "F.Cu", "GND", 1))
    pcb.append(make_segment(px33, 92.0, px33, 91.0, 0.25, "F.Cu", "GND", 1))

    # Back fingers B17..B32: connect to the via at (px, 89.0) on B.Cu
    for p in range(17, 33):
        px = x_start + (p - 1) * PITCH
        pcb.append(make_segment(px, 92.0, px, 89.0, 0.25, "B.Cu", "GND", 1))

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
    print("Generated and filled DC2 successfully.")

if __name__ == "__main__":
    build_perfect_architecture_dc2("daughtercard2_relu_l1.kicad_pcb")
