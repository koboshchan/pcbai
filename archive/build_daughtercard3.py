#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
build_daughtercard3.py
Deterministic generator and router for Daughtercard 3 (L2 Synaptic Weights + Winner-Take-All).
100.0 x 100.0 mm, 4-layer PCB. Option A Modular Stack.
"""

import os
import sys
import subprocess
import time
import uuid
import json
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

BOARD_PATH = os.path.join(WORKSPACE_DIR, "daughtercard3_weights_l2_wta.kicad_pcb")
DSN_PATH = os.path.join(WORKSPACE_DIR, "daughtercard3_weights_l2_wta.dsn")
SES_PATH = os.path.join(WORKSPACE_DIR, "daughtercard3_weights_l2_wta.ses")
DRC_PATH = os.path.join(WORKSPACE_DIR, "drc_daughtercard3_weights_l2_wta.json")

def make_uuid(): return str(uuid.uuid4())
def mm(v): return int(v * 1000000)

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
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
  )"""

def fp_capacitor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
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
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
  )"""

def fp_led_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "LED_SMD:LED_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "LED SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -1.05 0) (size 1.0 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.05 0) (size 1.0 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
  )"""

def fp_diode_sod123(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "Diode_SMD:D_SOD-123" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Diode SOD-123")
    (property "Reference" "{ref}" (at 0 -1.5 {rot}) (layer "{silk}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 {rot}) (layer "{fab}") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -1.65 0) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.65 0) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
  )"""

def fp_soic14(ref, val, x, y, rot=0, layer="F.Cu", pin_nets=None):
    pads = []
    pitch = 1.27
    y_start = - (3 * pitch)
    for i in range(7):
        py = y_start + i * pitch
        pin_num = str(i + 1)
        nid, nname = pin_nets.get(pin_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_num}" smd roundrect (at -2.7 {py:.3f}) (size 1.95 0.6) (layers "{layer}" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    for i in range(7):
        py = y_start + (6 - i) * pitch
        pin_num = str(i + 8)
        nid, nname = pin_nets.get(pin_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_num}" smd roundrect (at 2.7 {py:.3f}) (size 1.95 0.6) (layers "{layer}" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "SOIC, 14 Pin, 3.9x8.7mm body, 1.27mm pitch")
    (property "Reference" "{ref}" (at 0 -5.5 {rot}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.1))))
    (property "Value" "{val}" (at 0 5.5 {rot}) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.1))))
{pads_str}
  )"""

def fp_header_2x20(ref, val, x, y, rot=0, pin_nets=None):
    pads = []
    pitch = 2.54
    y_start = - (9.5 * pitch)
    for i in range(20):
        py = y_start + i * pitch
        pin_odd = str(2 * i + 1)
        pin_even = str(2 * i + 2)
        n_odd_id, n_odd_name = pin_nets.get(pin_odd, (0, "")) if pin_nets else (0, "")
        n_even_id, n_even_name = pin_nets.get(pin_even, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_odd}" thru_hole circle (at -1.27 {py:.3f} {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {n_odd_id} "{n_odd_name}"))')
        pads.append(f'    (pad "{pin_even}" thru_hole oval (at 1.27 {py:.3f} {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {n_even_id} "{n_even_name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 2x20 vertical")
    (property "Reference" "{ref}" (at 0 -27.0 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 27.0 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def build_dc3():
    with open(os.path.join(WORKSPACE_DIR, "dc3_components_dump.json")) as f:
        dump = json.load(f)

    # Netlist definitions
    net_list = [(0, "")]
    net_to_id = {"": 0}
    std_nets = ["GND", "+12V", "-12V", "+5V", "+5V_REF", "-5V_REF", "V_MAX_BUS"]
    for s in std_nets:
        nid = len(net_list)
        net_list.append((nid, s))
        net_to_id[s] = nid
    for i in range(16):
        nid = len(net_list)
        net_list.append((nid, f"ACT_{i}"))
        net_to_id[f"ACT_{i}"] = nid
    for j in range(10):
        nid = len(net_list)
        net_list.append((nid, f"L2_INV_{j}"))
        net_to_id[f"L2_INV_{j}"] = nid
        nid = len(net_list)
        net_list.append((nid, f"SCORE_{j}"))
        net_to_id[f"SCORE_{j}"] = nid
        nid = len(net_list)
        net_list.append((nid, f"LED_CAT_{j}"))
        net_to_id[f"LED_CAT_{j}"] = nid

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in net_list if nid > 0])

    # Connectors J_SLOT_A at (50.0, 85.00) and J_SLOT_B at (50.0, 92.62)
    j_slot_a = {str(k+1): (net_to_id[f"ACT_{k}"], f"ACT_{k}") for k in range(16)}
    for p in range(17, 33): j_slot_a[str(p)] = (0, "")
    j_slot_a["33"] = (net_to_id["+5V_REF"], "+5V_REF")
    j_slot_a["34"] = (net_to_id["-5V_REF"], "-5V_REF")
    j_slot_a["35"] = (net_to_id["+5V"], "+5V")
    j_slot_a["36"] = (net_to_id["GND"], "GND")
    j_slot_a["37"] = (net_to_id["+12V"], "+12V")
    j_slot_a["38"] = (net_to_id["-12V"], "-12V")
    j_slot_a["39"] = (net_to_id["GND"], "GND")
    j_slot_a["40"] = (net_to_id["GND"], "GND")

    j_slot_b = {str(k+1): (net_to_id[f"SCORE_{k}"], f"SCORE_{k}") for k in range(10)}
    for p in range(11, 33): j_slot_b[str(p)] = (0, "")
    for p in range(33, 41): j_slot_b[str(p)] = (net_to_id["GND"], "GND")

    pcb = [
        f"""(kicad_pcb (version 20221018) (generator "analog_nn_100x100_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block (title "Daughtercard 3 - L2 Synaptic Weights + Winner-Take-All") (rev "v5.0 - 100x100mm 4-Layer Modular Stack") (date "2026-09-12"))
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" power "GND")
    (2 "In2.Cu" signal "Power")
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
  (setup (pad_to_mask_clearance 0.05))
{net_lines}
  (gr_rect (start 0 0) (end 100 100) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{make_uuid()}"))
  (zone (net {net_to_id['GND']}) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (priority 0) (connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))
    (polygon (pts (xy 1.0 1.0) (xy 99.0 1.0) (xy 99.0 99.0) (xy 1.0 99.0)))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at 4.0 4.0) (descr "M3 Mounting Hole") (property "Reference" "H1" (at 0 -4.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net {net_to_id['GND']} "GND"))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at 96.0 4.0) (descr "M3 Mounting Hole") (property "Reference" "H2" (at 0 -4.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net {net_to_id['GND']} "GND"))
  )
""",
        fp_header_2x20("J_SLOT_A", "Act_In_0_15", 50.0, 85.0, 90, j_slot_a),
        fp_header_2x20("J_SLOT_B", "Scores_Out_0_9", 50.0, 92.62, 90, j_slot_b),
    ]

    # 1. TOP: LEDs and current limit resistors
    for j in range(10):
        lx = 16.0 + 7.5 * j
        # LED_j: pad 1 = +5V, pad 2 = LED_CAT_j
        pcb.append(fp_led_0805(f"LED_{j}", f"Digit_{j}", lx, 7.5, 0, "F.Cu",
                               net_to_id["+5V"], "+5V",
                               net_to_id[f"LED_CAT_{j}"], f"LED_CAT_{j}"))
        # Rled_j: pad 1 = +5V, pad 2 = LED_CAT_j
        pcb.append(fp_resistor_0805(f"Rled_{j}", "1k", lx, 13.0, 0, "F.Cu",
                                   net_to_id["+5V"], "+5V",
                                   net_to_id[f"LED_CAT_{j}"], f"LED_CAT_{j}"))

    # 2. MATRIX: 10 rows
    row_y = [21.0 + 4.8 * j for j in range(10)]
    for j in range(10):
        yj = row_y[j]
        # 16 synaptic resistors
        for i in range(16):
            xi = 16.0 + 2.0 * i
            ref = f"R2_{i}_{j}"
            val = dump[ref]["val"]
            # rot 90: pad 1 at (xi, yj + 0.95), pad 2 at (xi, yj - 0.95)
            # pad 1: ACT_i, pad 2: L2_INV_j
            pcb.append(fp_resistor_0805(ref, val, xi, yj, 90, "F.Cu",
                                       net_to_id[f"ACT_{i}"], f"ACT_{i}",
                                       net_to_id[f"L2_INV_{j}"], f"L2_INV_{j}"))

        # Bias resistor Rb2_Cj at (52.0, yj)
        ref_b = f"Rb2_C{j}"
        val_b = dump[ref_b]["val"]
        b_p1_name = dump[ref_b]["pads"]["1"] # +5V_REF or -5V_REF
        pcb.append(fp_resistor_0805(ref_b, val_b, 52.0, yj, 0, "F.Cu",
                                   net_to_id[b_p1_name], b_p1_name,
                                   net_to_id[f"L2_INV_{j}"], f"L2_INV_{j}"))

        # Feedback resistor Rf2_Cj at (57.0, yj), rot 90 so pad 2 (L2_INV) is at yj - 0.95 and pad 1 (SCORE) is at yj + 0.95
        ref_f = f"Rf2_C{j}"
        val_f = dump[ref_f]["val"]
        # rot 90: pad 1 at (57.0, yj + 0.95), pad 2 at (57.0, yj - 0.95)
        pcb.append(fp_resistor_0805(ref_f, val_f, 57.0, yj, 90, "F.Cu",
                                   net_to_id[f"SCORE_{j}"], f"SCORE_{j}",
                                   net_to_id[f"L2_INV_{j}"], f"L2_INV_{j}"))

        # WTA Diode Dwta_j at (63.0, yj)
        ref_d = f"Dwta_{j}"
        val_d = dump[ref_d]["val"]
        # pad 1: SCORE_j, pad 2: V_MAX_BUS
        pcb.append(fp_diode_sod123(ref_d, val_d, 63.0, yj, 0, "F.Cu",
                                  net_to_id[f"SCORE_{j}"], f"SCORE_{j}",
                                  net_to_id["V_MAX_BUS"], "V_MAX_BUS"))

    # 3. Summing Op-Amps U1..U3 and Bypass Caps at X = 73.5
    u_y = [28.2, 47.4, 61.8]
    for idx, uy in enumerate(u_y):
        u_ref = f"U{idx+1}"
        u_val = dump[u_ref]["val"]
        pin_nets = {}
        for pnum, pname in dump[u_ref]["pads"].items():
            if pname:
                pin_nets[pnum] = (net_to_id[pname], pname)
        pcb.append(fp_soic14(u_ref, u_val, 73.5, uy, 0, "F.Cu", pin_nets))

        # Bypass caps
        cp_ref = f"C_U{idx+1}P"
        cn_ref = f"C_U{idx+1}N"
        pcb.append(fp_capacitor_0805(cp_ref, "0.1uF", 73.5, uy - 5.5, 0, "F.Cu",
                                    net_to_id["+12V"], "+12V",
                                    net_to_id["GND"], "GND"))
        pcb.append(fp_capacitor_0805(cn_ref, "0.1uF", 73.5, uy + 5.5, 0, "F.Cu",
                                    net_to_id["-12V"], "-12V",
                                    net_to_id["GND"], "GND"))

    # 4. WTA Comparators U4..U6 at X = 87.5
    for idx, uy in enumerate(u_y):
        u_ref = f"U{idx+4}"
        u_val = dump[u_ref]["val"]
        pin_nets = {}
        for pnum, pname in dump[u_ref]["pads"].items():
            if pname:
                pin_nets[pnum] = (net_to_id[pname], pname)
        pcb.append(fp_soic14(u_ref, u_val, 87.5, uy, 0, "F.Cu", pin_nets))

    pcb.append(")")
    with open(BOARD_PATH, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated clean DC3 board skeleton: {BOARD_PATH}")

    # Load Board in pcbnew for deterministic pre-routing
    b = pcbnew.LoadBoard(BOARD_PATH)
    net_gnd = b.FindNet("GND")

    def add_track(x1, y1, x2, y2, layer, net, width=0.25):
        trk = pcbnew.PCB_TRACK(b)
        trk.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        trk.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        trk.SetWidth(mm(width))
        trk.SetLayer(layer)
        trk.SetNet(net)
        b.Add(trk)

    def add_via(x, y, net, size=0.65, drill=0.30):
        via = pcbnew.PCB_VIA(b)
        via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        via.SetWidth(mm(size))
        via.SetDrill(mm(drill))
        via.SetNet(net)
        b.Add(via)

    def add_gnd_via(x_pad, y_pad, x_via, y_via):
        add_via(x_via, y_via, net_gnd)
        add_track(x_pad, y_pad, x_via, y_via, pcbnew.F_Cu, net_gnd)

    # 1. Pre-route horizontal summing lines L2_INV_0..9 on F.Cu
    # Connects Pad 2 of all 16 weights (16.0 to 46.0 at yj - 0.95), plus connects to Rb2_Cj and Rf2_Cj
    for j in range(10):
        yj = row_y[j]
        y_sum = yj - 0.95
        net_inv = b.FindNet(f"L2_INV_{j}")
        # Horizontal bus across all 16 weights and continuing past Rb2 and Rf2 (up to 57.0)
        add_track(16.0, y_sum, 57.0, y_sum, pcbnew.F_Cu, net_inv)
        # Link Rb2_Cj pad 2 (52.95, yj) to summing bus (52.95, y_sum)
        add_track(52.95, yj, 52.95, y_sum, pcbnew.F_Cu, net_inv)

    # 2. Pre-route column buses ACT_0..15 on B.Cu
    for i in range(16):
        xi = 16.0 + 2.0 * i
        net_act = b.FindNet(f"ACT_{i}")
        for j in range(10):
            yj = row_y[j]
            # Via at (xi, yj + 1.8)
            add_via(xi, yj + 1.8, net_act)
            # Short stub on F.Cu from pad 1 (xi, yj + 0.95) to via
            add_track(xi, yj + 0.95, xi, yj + 1.8, pcbnew.F_Cu, net_act)
        # Vertical spine on B.Cu connecting all 10 row taps
        add_track(xi, row_y[0] + 1.8, xi, row_y[9] + 1.8, pcbnew.B_Cu, net_act)

    # 3. GND Vias for U1..U3 (SOIC-14 pins 3, 5 on left; pins 10, 12 on right for U1 & U2 only)
    pitch_ic = 1.27
    y_ic_start = - (3 * pitch_ic)
    for idx, uy in enumerate(u_y):
        # Pin 3, 5 GND on left side at X = 73.5 - 2.7 = 70.8
        py3 = uy + y_ic_start + 2 * pitch_ic
        py5 = uy + y_ic_start + 4 * pitch_ic
        add_gnd_via(70.8, py3, 68.5, py3)
        add_gnd_via(70.8, py5, 68.5, py5)
        # Pin 10, 12 GND on right side at X = 73.5 + 2.7 = 76.2 (ONLY for U1 and U2)
        if idx < 2:
            py10 = uy + y_ic_start + (6 - 2) * pitch_ic
            py12 = uy + y_ic_start + (6 - 4) * pitch_ic
            add_gnd_via(76.2, py10, 78.5, py10)
            add_gnd_via(76.2, py12, 78.5, py12)
        # Bypass cap GND pads (pad 2 at 74.45)
        add_gnd_via(74.45, uy - 5.5, 76.0, uy - 5.5)
        add_gnd_via(74.45, uy + 5.5, 76.0, uy + 5.5)

    # 4. GND Vias for U4..U6 (pin 12 at 87.5 + 2.7 = 90.2)
    for uy in u_y:
        py12 = uy + y_ic_start + (6 - 4) * pitch_ic
        add_gnd_via(90.2, py12, 92.5, py12)

    # 5. Pre-route +5V rail for LEDs at top on B.Cu
    net_5v = b.FindNet("+5V")
    for j in range(10):
        lx = 16.0 + 7.5 * j
        # LED_j pad 1 (+5V) at (lx - 1.05, 7.5)
        add_via(lx - 2.2, 7.5, net_5v)
        add_track(lx - 1.05, 7.5, lx - 2.2, 7.5, pcbnew.F_Cu, net_5v)
        # Rled_j pad 1 (+5V) at (lx - 0.95, 13.0)
        add_via(lx - 2.2, 13.0, net_5v)
        add_track(lx - 0.95, 13.0, lx - 2.2, 13.0, pcbnew.F_Cu, net_5v)
        # Vertical link between LED and Rled +5V vias on B.Cu
        add_track(lx - 2.2, 7.5, lx - 2.2, 13.0, pcbnew.B_Cu, net_5v)
    # Horizontal bus connecting all LED +5V vias across the top on B.Cu
    add_track(16.0 - 2.2, 7.5, 83.5 - 2.2, 7.5, pcbnew.B_Cu, net_5v)

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(BOARD_PATH)

    pcbnew.ExportSpecctraDSN(b, DSN_PATH)
    print(f"Exported DSN: {DSN_PATH}")

    cmd = [
        "/usr/bin/java", "-jar", JAR_PATH,
        "-de", DSN_PATH,
        "-do", SES_PATH,
        "--gui.enabled=false",
        "-mp", "200",
        "-mt", "1"
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Freerouting finished in {time.time()-t0:.1f}s, exit code: {res.returncode}")

    if os.path.exists(SES_PATH):
        b = pcbnew.LoadBoard(BOARD_PATH)
        pcbnew.ImportSpecctraSES(b, SES_PATH)
        filler = pcbnew.ZONE_FILLER(b)
        filler.Fill(b.Zones())
        b.Save(BOARD_PATH)

        cmd_drc = f"{KICAD_CLI} pcb drc --severity-error --output {DRC_PATH} --format json {BOARD_PATH}"
        subprocess.run(cmd_drc, shell=True)
        with open(DRC_PATH) as f:
            d = json.load(f)
        uncon = len(d.get("unconnected_items", []))
        viols = len(d.get("violations", []))
        print(f"[DC3 L2+WTA] DRC Result: {uncon} unconnected, {viols} errors")
        return uncon == 0 and viols == 0
    return False

if __name__ == "__main__":
    success = build_dc3()
    print("DC3 Build Status:", "SUCCESS (0 ERRORS, 0 UNCONNECTED)" if success else "FAILED")
    sys.exit(0 if success else 1)
