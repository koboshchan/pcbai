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

def fp_led0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "LED_SMD:LED_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.4f} {y:.4f} {rot})
    (descr "LED SMD 0805 (Pad 1=Anode, Pad 2=Cathode)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -1.05 0 {rot}) (size 1.05 1.25) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.05 0 {rot}) (size 1.05 1.25) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
    (model "${{KICAD8_3DMODEL_DIR}}/LED_SMD.3dshapes/LED_0805_2012Metric.step"
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
        f'  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}") (at 5.0 5.0)',
        '    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND")))',
        f'  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}") (at {width-5.0:.2f} 5.0)',
        '    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND")))'
    ]

def build_step1(board_file="dc3_step1.kicad_pcb"):
    w2_file = "weights_layer2.json"
    with open(w2_file) as f:
        l2 = json.load(f)

    nets = {0: "", 1: "GND", 2: "+12V", 3: "-12V", 4: "+5V_REF", 5: "-5V_REF", 6: "WTA_BUS"}
    for k in range(16): nets[20 + k] = f"ACT_{k}"
    for c in range(10):
        nets[50 + c] = f"SCORE_{c}"
        nets[70 + c] = f"INV_L2_{c}"
        nets[90 + c] = f"LED_N_{c}"

    pin_nets_a = {f"A{k+1}": (20 + k, f"ACT_{k}") for k in range(16)}
    for p in range(17, 37): pin_nets_a[f"A{p}"] = (1, "GND")
    pin_nets_b = {f"B{c+1}": (50 + c, f"SCORE_{c}") for c in range(10)}
    for p in range(11, 33): pin_nets_b[f"B{p}"] = (1, "GND")
    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (4, "+5V_REF")
    pin_nets_b["B36"] = (5, "-5V_REF")

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in sorted(nets.items()) if nid > 0])
    header = f"""(kicad_pcb (version 20221018) (generator "analog_nn_dc3_step1")
  (general (thickness 1.6))
  (paper "A4")
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
  )
  (net 0 "")
{net_lines}
"""
    pcb = [header] + get_daughtercard_outline_and_mounts(width=94.28, height=100.0) + [
        fp_edge_fingers_72p(pin_nets_a, pin_nets_b, card_width=94.28),
    ]

    card_w = 94.28
    cx = card_w / 2.0
    PITCH = 2.54
    x_start = cx - (17.5 * PITCH)

    # 1. Indicator LEDs + Ballast Resistors
    lx = [16.0 + c * 6.40 for c in range(10)]
    for c in range(10):
        pcb.append(fp_led0805(f"D_LED_{c}", f"Digit_{c}", lx[c], 12.0, 0, "F.Cu", 50 + c, f"SCORE_{c}", 90 + c, f"LED_N_{c}"))
        pcb.append(fp_resistor_0805(f"R_LED_{c}", "1k", lx[c], 15.5, 0, "F.Cu", 90 + c, f"LED_N_{c}", 1, "GND"))
        pcb.append(make_segment(lx[c] + 1.05, 12.0, lx[c] + 1.05, 13.8, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))
        pcb.append(make_segment(lx[c] + 1.05, 13.8, lx[c] - 0.95, 13.8, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))
        pcb.append(make_segment(lx[c] - 0.95, 13.8, lx[c] - 0.95, 15.5, 0.25, "F.Cu", f"LED_N_{c}", 90 + c))
        pcb.append(make_via(lx[c] + 2.00, 15.5, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(lx[c] + 0.95, 15.5, lx[c] + 2.00, 15.5, 0.25, "F.Cu", "GND", 1))

    # 2. Resistor Matrix
    row_y = [23.0 + c * 5.20 for c in range(10)]
    col_x = [x_start + k * PITCH for k in range(16)]

    for c in range(10):
        c_info = l2["weights"][c]
        ry = row_y[c]
        for k in range(16):
            inp = c_info["inputs"][k]
            pcb.append(fp_resistor_0805(f"R2_{k}_{c}", inp["resistor_str"], col_x[k], ry, 90, "F.Cu", 20 + k, f"ACT_{k}", 70 + c, f"INV_L2_{c}"))

    # Matrix Summing Rows Routing (Horizontal on F.Cu at ry - 0.95)
    for c in range(10):
        ry_sum = row_y[c] - 0.95
        inv_name = f"INV_L2_{c}"
        inv_nid = 70 + c
        pcb.append(make_segment(col_x[0], ry_sum, col_x[15], ry_sum, 0.25, "F.Cu", inv_name, inv_nid))

    # Matrix Columns Routing (Vertical on In2.Cu from Ak at 92.0)
    for k in range(16):
        kx = col_x[k]
        act_name = f"ACT_{k}"
        act_nid = 20 + k
        pcb.append(make_segment(kx, 92.0, kx, 88.0, 0.25, "F.Cu", act_name, act_nid))
        pcb.append(make_via(kx, 88.0, 0.6, 0.3, act_name, act_nid))
        pcb.append(make_segment(kx, 88.0, kx, row_y[0] + 1.85, 0.25, "In2.Cu", act_name, act_nid))
        for c in range(10):
            vy = row_y[c] + 1.85
            py = row_y[c] + 0.95
            pcb.append(make_via(kx, vy, 0.6, 0.3, act_name, act_nid))
            pcb.append(make_segment(kx, vy, kx, py, 0.25, "F.Cu", act_name, act_nid))

    # Ground shield fingers
    for p in range(17, 33):
        px = x_start + (p - 1) * PITCH
        pcb.append(make_segment(px, 92.0, px, 89.0, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_via(px, 89.0, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(px, 92.0, px, 89.0, 0.25, "B.Cu", "GND", 1))

    px32 = x_start + (32 - 1) * PITCH
    for p in range(33, 37):
        px = x_start + (p - 1) * PITCH
        pcb.append(make_segment(px, 92.0, px, 91.0, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_segment(px, 91.0, px32, 91.0, 0.25, "F.Cu", "GND", 1))

    for p in range(11, 17):
        px = x_start + (p - 1) * PITCH
        pcb.append(make_segment(px, 92.0, px, 91.0, 0.25, "B.Cu", "GND", 1))
        pcb.append(make_segment(px, 91.0, px_start + 16 * PITCH, 91.0, 0.25, "B.Cu", "GND", 1))

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
    print("Step 1 generated and filled.")

if __name__ == "__main__":
    build_step1()
