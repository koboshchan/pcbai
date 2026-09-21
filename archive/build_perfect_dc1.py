#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
import os
import sys
import json
import uuid
import subprocess
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def mm(v): return int(v * 1000000)
def make_uuid(): return str(uuid.uuid4())

COL_X = [14.5, 24.5, 34.5, 44.5, 65.5, 75.5, 85.5, 95.5]
NEURON_Y = [18.0, 34.0, 50.0, 66.0]

# 4 Quadrants for Feedback & Bias Resistors
FB_COORDS = [
    (49.5, 36.0, 49.5, 39.0),  # N0 (top-left)
    (49.5, 58.0, 49.5, 61.0),  # N1 (bottom-left)
    (60.5, 58.0, 60.5, 61.0),  # N2 (bottom-right)
    (60.5, 36.0, 60.5, 39.0),  # N3 (top-right)
]

def fp_resistor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=1, net1_name="GND", net2=0, net2_name=""):
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
    (pad "1" smd roundrect (at -0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
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
    (pad "1" smd roundrect (at -0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0 {rot}) (size 1.0 1.3) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
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
    (at {x:.3f} {y:.3f} {rot})
    (descr "SOIC, 14 Pin, 3.9x8.7mm body, 1.27mm pitch")
    (property "Reference" "{ref}" (at 0 -5.5 {rot}) (layer "{silk}") (effects (font (size 0.8 0.8) (thickness 0.1))))
    (property "Value" "{val}" (at 0 5.5 {rot}) (layer "{fab}") (effects (font (size 0.8 0.8) (thickness 0.1))))
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

def generate_dc1_board(filename, title, neuron_range):
    board_file = os.path.join(WORKSPACE_DIR, filename)
    w1_file = os.path.join(WORKSPACE_DIR, "weights_layer1.json")
    with open(w1_file) as f:
        l1 = json.load(f)

    nets = [(0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), (5, "-5V_REF"), (6, "+5V_REF")]
    for j in neuron_range:
        nets.append((10 + j, f"V_SUM_{j}"))
        nets.append((30 + j, f"INV_N{j}"))
    for i in range(64):
        nets.append((100 + i, f"IN_{i}"))

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets])

    # J_SLOT_A: Inputs 0..31 + Sums + Power
    j_slot_a = {str(i+1): (100+i, f"IN_{i}") for i in range(32)}
    for idx in range(4):
        j_slot_a[str(33 + idx)] = (10 + neuron_range[idx], f"V_SUM_{neuron_range[idx]}")
    j_slot_a["37"] = (2, "+12V")
    j_slot_a["38"] = (3, "-12V")
    j_slot_a["39"] = (6, "+5V_REF")
    j_slot_a["40"] = (5, "-5V_REF")

    # J_SLOT_B: Inputs 32..63 + GND
    j_slot_b = {str(i+1): (132+i, f"IN_{32+i}") for i in range(32)}
    for p in range(33, 41):
        j_slot_b[str(p)] = (1, "GND")

    pcb = [
        f"""(kicad_pcb (version 20221018) (generator "analog_nn_perfect_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block (title "{title}") (rev "v4.0 - Vertical Blade Direct Plug-In") (date "2026-09-12"))
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
  (gr_rect (start 0 0) (end 120 100) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{make_uuid()}"))
  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (priority 0) (connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))
    (polygon (pts (xy 1.0 1.0) (xy 119.0 1.0) (xy 119.0 99.0) (xy 1.0 99.0)))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at 5.0 5.0) (descr "M3 Mounting Hole") (property "Reference" "H1" (at 0 -4.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 6.0 6.0) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at 115.0 5.0) (descr "M3 Mounting Hole") (property "Reference" "H2" (at 0 -4.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 6.0 6.0) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )
""",
        fp_header_2x20("J_SLOT_A", "Inputs_0_31_and_Sums", 35.0, 94.0, 90, j_slot_a),
        fp_header_2x20("J_SLOT_B", "Inputs_32_63_and_GND", 86.0, 94.0, 90, j_slot_b),
    ]

    # Central Spine: U1 at X = 55.0, Y = 50.0
    j0 = neuron_range[0]
    ic_pin_nets = {
        "1": (10 + j0, f"V_SUM_{j0}"), "2": (30 + j0, f"INV_N{j0}"), "3": (1, "GND"),
        "4": (2, "+12V"),
        "5": (1, "GND"), "6": (30 + j0 + 1, f"INV_N{j0+1}"), "7": (10 + j0 + 1, f"V_SUM_{j0+1}"),
        "8": (10 + j0 + 2, f"V_SUM_{j0+2}"), "9": (30 + j0 + 2, f"INV_N{j0+2}"), "10": (1, "GND"),
        "11": (3, "-12V"),
        "12": (1, "GND"), "13": (30 + j0 + 3, f"INV_N{j0+3}"), "14": (10 + j0 + 3, f"V_SUM_{j0+3}")
    }
    pcb.append(fp_soic14("U1", "TL074", 55.0, 50.0, 0, "F.Cu", ic_pin_nets))
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 55.0, 42.0, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 55.0, 58.0, 0, "F.Cu", 3, "-12V", 1, "GND"))

    for idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        bias_nid = 5 if n_info["bias_rail"] == "-5V_REF" else 6
        bias_name = n_info["bias_rail"]
        rb_str = n_info["bias_resistor_str"]
        rf_x, rf_y, rb_x, rb_y = FB_COORDS[idx]

        if idx < 2:
            # Left side (N0, N1): Pad 1 (left) = V_SUM / Bias, Pad 2 (right) = INV_N
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", rf_x, rf_y, 0, "F.Cu", 10+j, f"V_SUM_{j}", 30+j, f"INV_N{j}"))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, rb_x, rb_y, 0, "F.Cu", bias_nid, bias_name, 30+j, f"INV_N{j}"))
        else:
            # Right side (N2, N3): Pad 1 (left) = INV_N, Pad 2 (right) = V_SUM / Bias
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", rf_x, rf_y, 0, "F.Cu", 30+j, f"INV_N{j}", 10+j, f"V_SUM_{j}"))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, rb_x, rb_y, 0, "F.Cu", 30+j, f"INV_N{j}", bias_nid, bias_name))

    # 256 Synaptic 0805 Resistors
    for idx, j in enumerate(neuron_range):
        base_y = NEURON_Y[idx]
        n_info = l1["weights"][j]
        for c in range(8):
            rx = COL_X[c]
            for r in range(8):
                i = c * 8 + r
                inp_info = n_info["inputs"][i]
                r_val_str = inp_info["resistor_str"]
                ry = base_y + r * 1.5
                pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val_str, rx, ry, 0, "F.Cu", 100+i, f"IN_{i}", 30+j, f"INV_N{j}"))

    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated clean board skeleton: {board_file}")
    return board_file

def route_dc1_board(board_path, neuron_range):
    b = pcbnew.LoadBoard(board_path)

    for t in list(b.GetTracks()):
        b.Delete(t)

    w1_file = os.path.join(WORKSPACE_DIR, "weights_layer1.json")
    with open(w1_file) as f:
        l1 = json.load(f)

    def add_track(x1, y1, x2, y2, layer, net, width=0.20):
        if abs(x1 - x2) < 1e-4 and abs(y1 - y2) < 1e-4: return
        trk = pcbnew.PCB_TRACK(b)
        trk.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        trk.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        trk.SetWidth(mm(width))
        trk.SetLayer(layer)
        trk.SetNet(net)
        b.Add(trk)

    def add_via(x, y, net, size=0.50, drill=0.30):
        via = pcbnew.PCB_VIA(b)
        via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        via.SetWidth(mm(size))
        via.SetDrill(mm(drill))
        via.SetNet(net)
        b.Add(via)

    nets = {b.FindNet(i).GetNetname(): b.FindNet(i) for i in range(b.GetNetCount()) if b.FindNet(i)}
    net_gnd = nets["GND"]
    net_p12 = nets["+12V"]
    net_n12 = nets["-12V"]
    net_p5v = nets["+5V_REF"]
    net_n5v = nets["-5V_REF"]

    # =========================================================================
    # 1. 64 INPUTS ROUTING (PLANAR MONOTONIC PEELING, PITCH 0.60mm)
    # =========================================================================
    for c in range(8):
        c_local = c % 4
        x_base = 10.87 if c < 4 else 61.87
        x_pin0 = x_base + c_local * 10.16
        x_bus_start = COL_X[c] - 6.00
        bus_pitch = 0.60

        for r in range(8):
            i = c * 8 + r
            net_in = nets[f"IN_{i}"]
            x_bus = x_bus_start + r * bus_pitch
            x_pad1 = COL_X[c] - 0.95
            y_first = NEURON_Y[0] + r * 1.5

            # Connect 4 neuron resistor Pad 1s on F.Cu to the via on the vertical bus
            for idx in range(4):
                y_res = NEURON_Y[idx] + r * 1.5
                add_track(x_pad1, y_res, x_bus, y_res, pcbnew.F_Cu, net_in, width=0.20)
                add_via(x_bus, y_res, net_in, size=0.50, drill=0.30)

            # Connector routing
            p = r // 2
            x_pin = x_pin0 + p * 2.54

            if r % 2 == 1:
                # ODD row -> EVEN pin at (x_pin, 92.73) on B.Cu
                y_turn = 85.5 + (3 - p) * 1.5
                add_track(x_bus, y_first, x_bus, y_turn, pcbnew.B_Cu, net_in, width=0.20)
                add_track(x_bus, y_turn, x_pin, y_turn, pcbnew.B_Cu, net_in, width=0.20)
                add_track(x_pin, y_turn, x_pin, 92.73, pcbnew.B_Cu, net_in, width=0.20)
            else:
                # EVEN row -> ODD pin at (x_pin, 95.27) on In2.Cu
                y_turn = 78.5 + (3 - p) * 1.5
                x_corridor = x_pin + 1.27
                add_track(x_bus, y_first, x_bus, y_turn, pcbnew.B_Cu, net_in, width=0.20)
                add_via(x_bus, y_turn, net_in, size=0.50, drill=0.30)
                add_track(x_bus, y_turn, x_corridor, y_turn, pcbnew.In2_Cu, net_in, width=0.20)
                add_track(x_corridor, y_turn, x_corridor, 97.5, pcbnew.In2_Cu, net_in, width=0.20)
                add_track(x_corridor, 97.5, x_pin, 97.5, pcbnew.In2_Cu, net_in, width=0.20)
                add_track(x_pin, 97.5, x_pin, 95.27, pcbnew.In2_Cu, net_in, width=0.20)

    # =========================================================================
    # 2. ROUTE SUMMING NODES (INV_N0..INV_N3)
    # =========================================================================
    fb_inv_pads = [
        (49.5 + 0.95, 36.0),  # N0: Rf Pad 2 (50.45)
        (49.5 + 0.95, 58.0),  # N1: Rf Pad 2 (50.45)
        (60.5 - 0.95, 58.0),  # N2: Rf Pad 1 (59.55)
        (60.5 - 0.95, 36.0),  # N3: Rf Pad 1 (59.55)
    ]
    u1_inv_pins = [
        (52.3, 47.46),  # pin 2 (N0)
        (52.3, 52.54),  # pin 6 (N1)
        (57.7, 52.54),  # pin 9 (N2)
        (57.7, 47.46),  # pin 13 (N3)
    ]

    for idx, j in enumerate(neuron_range):
        net_inv = nets[f"INV_N{j}"]
        base_y = NEURON_Y[idx]
        y_bar = base_y - 1.5

        for c in range(8):
            rx_pad2 = COL_X[c] + 0.95
            add_track(rx_pad2, base_y, rx_pad2, base_y + 7 * 1.5, pcbnew.F_Cu, net_inv, width=0.25)
            add_track(rx_pad2, base_y, rx_pad2, y_bar, pcbnew.F_Cu, net_inv, width=0.25)
            add_via(rx_pad2, y_bar, net_inv, size=0.50, drill=0.30)

        # Horizontal highway on In2.Cu: Column 0 to Column 7
        add_track(COL_X[0] + 0.95, y_bar, COL_X[7] + 0.95, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)

        inv_x, inv_y = fb_inv_pads[idx]
        rb_y = inv_y + 3.0
        ux, uy = u1_inv_pins[idx]

        # Connect horizontal highway on In2.Cu to the feedback loop
        add_via(inv_x, y_bar, net_inv, size=0.50, drill=0.30)
        add_track(inv_x, y_bar, inv_x, inv_y, pcbnew.In2_Cu, net_inv, width=0.25)
        add_via(inv_x, inv_y, net_inv, size=0.50, drill=0.30)

        # On F.Cu, connect Rf Pad to Rb Pad and U1 inverting pin
        add_track(inv_x, inv_y, inv_x, rb_y, pcbnew.F_Cu, net_inv, width=0.25)
        add_track(inv_x, inv_y, ux, uy, pcbnew.F_Cu, net_inv, width=0.20)

    # =========================================================================
    # 3. ROUTE OP-AMP OUTPUTS (V_SUM_0..3)
    # =========================================================================
    net_s0 = nets[f"V_SUM_{neuron_range[0]}"]
    net_s1 = nets[f"V_SUM_{neuron_range[1]}"]
    net_s2 = nets[f"V_SUM_{neuron_range[2]}"]
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]

    # N0: Pin 1 at (52.3, 46.19), Rf Pad 1 at (48.55, 36.0) -> Pin 33 odd at (51.51, 95.27)
    add_track(48.55, 36.0, 48.0, 36.0, pcbnew.F_Cu, net_s0, width=0.25)
    add_via(48.0, 36.0, net_s0, size=0.50, drill=0.30)
    add_track(52.3, 46.19, 48.0, 46.19, pcbnew.F_Cu, net_s0, width=0.20)
    add_via(48.0, 46.19, net_s0, size=0.50, drill=0.30)
    add_track(48.0, 36.0, 48.0, 80.0, pcbnew.B_Cu, net_s0, width=0.25)
    add_via(48.0, 80.0, net_s0, size=0.50, drill=0.30)
    add_track(48.0, 80.0, 48.0, 97.5, pcbnew.In2_Cu, net_s0, width=0.25)
    add_track(48.0, 97.5, 51.51, 97.5, pcbnew.In2_Cu, net_s0, width=0.25)
    add_track(51.51, 97.5, 51.51, 95.27, pcbnew.In2_Cu, net_s0, width=0.25)

    # N1: Pin 7 at (52.3, 53.81), Rf Pad 1 at (48.55, 58.0) -> Pin 34 even at (51.51, 92.73)
    add_track(48.55, 58.0, 51.51, 58.0, pcbnew.F_Cu, net_s1, width=0.25)
    add_via(51.51, 58.0, net_s1, size=0.50, drill=0.30)
    add_track(52.3, 53.81, 51.51, 53.81, pcbnew.F_Cu, net_s1, width=0.20)
    add_via(51.51, 53.81, net_s1, size=0.50, drill=0.30)
    add_track(51.51, 53.81, 51.51, 92.73, pcbnew.B_Cu, net_s1, width=0.25)

    # N2: Pin 8 at (57.7, 53.81), Rf Pad 2 at (61.45, 58.0) -> Pin 35 odd at (54.05, 95.27)
    add_track(61.45, 58.0, 54.05, 58.0, pcbnew.F_Cu, net_s2, width=0.25)
    add_via(54.05, 58.0, net_s2, size=0.50, drill=0.30)
    add_track(57.7, 53.81, 54.05, 53.81, pcbnew.F_Cu, net_s2, width=0.20)
    add_via(54.05, 53.81, net_s2, size=0.50, drill=0.30)
    add_track(54.05, 53.81, 54.05, 80.0, pcbnew.B_Cu, net_s2, width=0.25)
    add_via(54.05, 80.0, net_s2, size=0.50, drill=0.30)
    add_track(54.05, 80.0, 53.0, 80.0, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(53.0, 80.0, 53.0, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(53.0, 97.5, 54.05, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(54.05, 97.5, 54.05, 95.27, pcbnew.In2_Cu, net_s2, width=0.25)

    # N3: Pin 14 at (57.7, 46.19), Rf Pad 2 at (61.45, 36.0) -> Pin 36 even at (54.05, 92.73)
    add_track(61.45, 36.0, 54.05, 36.0, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(54.05, 36.0, net_s3, size=0.50, drill=0.30)
    add_track(57.7, 46.19, 54.05, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(54.05, 46.19, net_s3, size=0.50, drill=0.30)
    add_track(54.05, 36.0, 54.05, 52.0, pcbnew.B_Cu, net_s3, width=0.25)
    # Via jump across N2 pin 8
    add_via(54.05, 52.0, net_s3, size=0.50, drill=0.30)
    add_track(54.05, 52.0, 54.05, 55.0, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(54.05, 55.0, net_s3, size=0.50, drill=0.30)
    add_track(54.05, 55.0, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)

    # =========================================================================
    # 4. ROUTE POWER & BIAS RAILS
    # =========================================================================
    # +12V: Pin 37 odd at (56.59, 95.27) -> In2.Cu bus at X = 55.5
    # Connect to C_U1P Pad 1 at (54.05, 42.0) and U1 Pin 4 at (52.3, 50.0)
    add_track(54.05, 42.0, 55.5, 42.0, pcbnew.F_Cu, net_p12, width=0.35)
    add_via(55.5, 42.0, net_p12, size=0.50, drill=0.30)
    add_track(52.3, 50.0, 55.5, 50.0, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(55.5, 50.0, net_p12, size=0.50, drill=0.30)
    add_track(55.5, 42.0, 55.5, 97.5, pcbnew.In2_Cu, net_p12, width=0.35)
    add_track(55.5, 97.5, 56.59, 97.5, pcbnew.In2_Cu, net_p12, width=0.35)
    add_track(56.59, 97.5, 56.59, 95.27, pcbnew.In2_Cu, net_p12, width=0.35)

    # -12V: Pin 38 even at (56.59, 92.73) -> B.Cu bus at X = 56.59
    # Connect to C_U1N Pad 1 at (54.05, 58.0) and U1 Pin 11 at (57.7, 50.0)
    add_track(54.05, 58.0, 56.59, 58.0, pcbnew.F_Cu, net_n12, width=0.35)
    add_via(56.59, 58.0, net_n12, size=0.50, drill=0.30)
    add_track(57.7, 50.0, 56.59, 50.0, pcbnew.F_Cu, net_n12, width=0.30)
    add_via(56.59, 50.0, net_n12, size=0.50, drill=0.30)
    add_track(56.59, 50.0, 56.59, 92.73, pcbnew.B_Cu, net_n12, width=0.35)

    # +5V_REF: Pin 39 odd at (59.13, 95.27) -> In2.Cu bus at X = 57.86
    add_track(57.86, 30.0, 57.86, 97.5, pcbnew.In2_Cu, net_p5v, width=0.25)
    add_track(57.86, 97.5, 59.13, 97.5, pcbnew.In2_Cu, net_p5v, width=0.25)
    add_track(59.13, 97.5, 59.13, 95.27, pcbnew.In2_Cu, net_p5v, width=0.25)

    # -5V_REF: Pin 40 even at (59.13, 92.73) -> B.Cu bus at X = 59.13
    add_track(59.13, 30.0, 59.13, 92.73, pcbnew.B_Cu, net_n5v, width=0.25)

    # Bias connections to Rb resistors
    for idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        rail = n_info["bias_rail"]
        net_bias = net_p5v if rail == "+5V_REF" else net_n5v
        bias_layer = pcbnew.In2_Cu if rail == "+5V_REF" else pcbnew.B_Cu
        bus_x = 57.86 if rail == "+5V_REF" else 59.13
        rf_x, rf_y, rb_x, rb_y = FB_COORDS[idx]

        pad_x = rb_x - 0.95 if idx < 2 else rb_x + 0.95
        add_via(pad_x, rb_y, net_bias, size=0.50, drill=0.30)
        add_track(pad_x, rb_y, bus_x, rb_y, bias_layer, net_bias, width=0.20)

    # =========================================================================
    # 5. GND CONNECTIONS TO GROUND PLANE (In1.Cu)
    # =========================================================================
    # U1 GND pins: Pin 3 (48.73), Pin 5 (51.27), Pin 10 (51.27), Pin 12 (48.73)
    add_via(50.5, 48.73, net_gnd, size=0.50, drill=0.30)
    add_track(52.3, 48.73, 50.5, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(50.5, 51.27, net_gnd, size=0.50, drill=0.30)
    add_track(52.3, 51.27, 50.5, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)

    add_via(59.5, 51.27, net_gnd, size=0.50, drill=0.30)
    add_track(57.7, 51.27, 59.5, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(59.5, 48.73, net_gnd, size=0.50, drill=0.30)
    add_track(57.7, 48.73, 59.5, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)

    # Decoupling Caps Pad 2:
    # C_U1P Pad 2 at (55.95, 42.0), C_U1N Pad 2 at (55.95, 58.0)
    add_via(57.5, 42.0, net_gnd, size=0.50, drill=0.30)
    add_track(55.95, 42.0, 57.5, 42.0, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(57.5, 58.0, net_gnd, size=0.50, drill=0.30)
    add_track(55.95, 58.0, 57.5, 58.0, pcbnew.F_Cu, net_gnd, width=0.25)

    # Refill ground copper zone
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())

    b.Save(board_path)
    print(f"Saved perfectly routed: {board_path}")

if __name__ == "__main__":
    generate_dc1_board("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A - L1 Neurons 0..3", range(0, 4))
    route_dc1_board(os.path.join(WORKSPACE_DIR, "daughtercard1a_weights_l1.kicad_pcb"), range(0, 4))
