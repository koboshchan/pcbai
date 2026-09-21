#!/usr/bin/env python3
import os
import sys
import json
import uuid

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
KICAD_PYTHON = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def make_uuid():
    return str(uuid.uuid4())

COL_X = [14.5, 24.5, 34.5, 44.5, 65.5, 75.5, 85.5, 95.5]
NEURON_Y = [18.0, 34.0, 50.0, 66.0]

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

def fp_header_2x20(ref, val, x, y, rot=0, pin_nets=None, is_socket=False):
    fp_name = "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" if is_socket else "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical"
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
    return f"""  (footprint "{fp_name}" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header/Socket 2.54mm 2x20 vertical")
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

    j_slot_a = {str(i+1): (100+i, f"IN_{i}") for i in range(32)}
    for idx in range(4):
        j_slot_a[str(33 + idx)] = (10 + neuron_range[idx], f"V_SUM_{neuron_range[idx]}")
    j_slot_a["37"] = (2, "+12V")
    j_slot_a["38"] = (3, "-12V")
    j_slot_a["39"] = (6, "+5V_REF")
    j_slot_a["40"] = (5, "-5V_REF")

    j_slot_b = {str(i+1): (132+i, f"IN_{32+i}") for i in range(32)}
    for p in range(33, 41):
        j_slot_b[str(p)] = (1, "GND")

    pcb = [
        f"""(kicad_pcb (version 20221018) (generator "analog_nn_pcb_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block (title "{title}") (rev "v4.0 - Vertical Blade Direct Plug-In") (date "2026-09-12"))
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" signal "GND")
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
        fp_header_2x20("J_SLOT_B", "Inputs_32_63_and_GND", 85.0, 94.0, 90, j_slot_b),
    ]

    # TL074 Op-Amp at X = 55.0, Y = 50.0
    j0 = neuron_range[0]
    ic_pin_nets = {
        "4": (2, "+12V"), "11": (3, "-12V"),
        "1": (10 + j0, f"V_SUM_{j0}"), "2": (30 + j0, f"INV_N{j0}"), "3": (1, "GND"),
        "7": (10 + j0 + 1, f"V_SUM_{j0+1}"), "6": (30 + j0 + 1, f"INV_N{j0+1}"), "5": (1, "GND"),
        "8": (10 + j0 + 2, f"V_SUM_{j0+2}"), "9": (30 + j0 + 2, f"INV_N{j0+2}"), "10": (1, "GND"),
        "14": (10 + j0 + 3, f"V_SUM_{j0+3}"), "13": (30 + j0 + 3, f"INV_N{j0+3}"), "12": (1, "GND")
    }
    pcb.append(fp_soic14("U1", "TL074", 55.0, 50.0, 0, "F.Cu", ic_pin_nets))
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 52.0, 43.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 58.0, 56.5, 0, "F.Cu", 3, "-12V", 1, "GND"))

    # Rf and Rb placement:
    # N0 and N1 on LEFT: X = 53.5. Pad 1 at 52.55 (V_SUM), Pad 2 at 54.45 (INV)
    # N2 and N3 on RIGHT: X = 56.5. Pad 1 at 57.45 (V_SUM), Pad 2 at 55.55 (INV)
    fb_config = [
        (53.5, 23.0, 53.5, 25.5),  # N0
        (53.5, 38.0, 53.5, 40.5),  # N1
        (56.5, 59.5, 56.5, 62.0),  # N2
        (56.5, 74.5, 56.5, 77.0),  # N3
    ]
    for idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        bias_nid = 5 if n_info["bias_rail"] == "-5V_REF" else 6
        bias_name = n_info["bias_rail"]
        rb_str = n_info["bias_resistor_str"]
        rf_x, rf_y, rb_x, rb_y = fb_config[idx]

        if idx < 2:
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", rf_x, rf_y, 0, "F.Cu", 10+j, f"V_SUM_{j}", 30+j, f"INV_N{j}"))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, rb_x, rb_y, 0, "F.Cu", bias_nid, bias_name, 30+j, f"INV_N{j}"))
        else:
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", rf_x, rf_y, 180, "F.Cu", 10+j, f"V_SUM_{j}", 30+j, f"INV_N{j}"))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, rb_x, rb_y, 180, "F.Cu", bias_nid, bias_name, 30+j, f"INV_N{j}"))

    # 256 Input Synaptic Resistors: 100% on F.Cu!
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
    return board_file

import pcbnew

def mm(v): return int(v * 1000000)

def route_dc1_board(board_path, neuron_range):
    board_name = os.path.basename(board_path)
    b = pcbnew.LoadBoard(board_path)

    for t in list(b.GetTracks()):
        b.Delete(t)

    w1_file = os.path.join(WORKSPACE_DIR, "weights_layer1.json")
    with open(w1_file) as f:
        l1 = json.load(f)

    def add_track(x1, y1, x2, y2, layer, net, width=0.20):
        if abs(x1 - x2) < 1e-4 and abs(y1 - y2) < 1e-4:
            return
        trk = pcbnew.PCB_TRACK(b)
        trk.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        trk.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        trk.SetWidth(mm(width))
        trk.SetLayer(layer)
        trk.SetNet(net)
        b.Add(trk)

    def add_via(x, y, net, size=0.55, drill=0.3):
        via = pcbnew.PCB_VIA(b)
        via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        via.SetWidth(mm(size))
        via.SetDrill(mm(drill))
        via.SetNet(net)
        b.Add(via)

    nets = {}
    for n in range(b.GetNetCount()):
        net_info = b.FindNet(n)
        if net_info:
            nets[net_info.GetNetname()] = net_info

    net_gnd = nets["GND"]
    net_p12 = nets["+12V"]
    net_n12 = nets["-12V"]
    net_p5v = nets["+5V_REF"]
    net_n5v = nets["-5V_REF"]

    # 1. ROUTE 64 INPUTS (IN_0..IN_63)
    for c in range(8):
        c_local = c % 4
        x_base = 10.87 if c < 4 else 60.87

        # Safe bus placement for each column
        if c == 4:
            bus_start = 61.2
            bus_pitch = 0.40
        elif c == 5:
            bus_start = 71.2
            bus_pitch = 0.40
        else:
            bus_start = COL_X[c] - 5.5
            bus_pitch = 0.55

        for r in range(8):
            i = c * 8 + r
            net_in = nets[f"IN_{i}"]
            x_bus = bus_start + r * bus_pitch
            x_pad1 = COL_X[c] - 0.95

            # Connect 4 neurons horizontally on F.Cu to the via on the vertical bus
            for idx in range(4):
                y_res = NEURON_Y[idx] + r * 1.5
                add_track(x_pad1, y_res, x_bus, y_res, pcbnew.F_Cu, net_in, width=0.20)
                add_via(x_bus, y_res, net_in, size=0.55, drill=0.3)

            p = r // 2
            k = c_local * 4 + p
            x_pin = x_base + k * 2.54
            y_start = NEURON_Y[0] + r * 1.5

            if r % 2 == 1:
                # ODD r -> EVEN PIN at (x_pin, 92.73)
                # Turns on B.Cu at Y = 89.5 - p * 1.5
                y_turn = 89.5 - p * 1.5
                add_track(x_bus, y_start, x_bus, y_turn, pcbnew.B_Cu, net_in, width=0.20)
                add_track(x_bus, y_turn, x_pin, y_turn, pcbnew.B_Cu, net_in, width=0.20)
                add_track(x_pin, y_turn, x_pin, 92.73, pcbnew.B_Cu, net_in, width=0.20)
            else:
                # EVEN r -> ODD PIN at (x_pin, 95.27)
                # Turns on In2.Cu at Y = 84.0 - p * 1.2
                y_turn = 84.0 - p * 1.2
                x_corridor = (x_pin + 1.27) if (c == 4 and p < 3) else (x_pin - 1.27)

                add_track(x_bus, y_start, x_bus, y_turn, pcbnew.B_Cu, net_in, width=0.20)
                add_via(x_bus, y_turn, net_in, size=0.55, drill=0.3)
                add_track(x_bus, y_turn, x_corridor, y_turn, pcbnew.In2_Cu, net_in, width=0.20)
                add_track(x_corridor, y_turn, x_corridor, 97.5, pcbnew.In2_Cu, net_in, width=0.20)
                add_track(x_corridor, 97.5, x_pin, 97.5, pcbnew.In2_Cu, net_in, width=0.20)
                add_track(x_pin, 97.5, x_pin, 95.27, pcbnew.In2_Cu, net_in, width=0.20)

    # 2. ROUTE SUMMING NODES (INV_N{j})
    # Horizontal bus on In2.Cu at Y = NEURON_Y[idx] - 1.5
    u1_inv_pins = {
        0: (52.3, 47.46),  # pin 2
        1: (52.3, 52.54),  # pin 6
        2: (57.7, 52.54),  # pin 9
        3: (57.7, 47.46),  # pin 13
    }
    fb_config = [
        (53.5, 23.0, 53.5, 25.5),  # N0
        (53.5, 38.0, 53.5, 40.5),  # N1
        (56.5, 59.5, 56.5, 62.0),  # N2
        (56.5, 74.5, 56.5, 77.0),  # N3
    ]

    for idx, j in enumerate(neuron_range):
        net_inv = nets[f"INV_N{j}"]
        base_y = NEURON_Y[idx]
        y_bar = base_y - 1.5

        for c in range(8):
            rx_pad2 = COL_X[c] + 0.95
            add_track(rx_pad2, base_y, rx_pad2, base_y + 7 * 1.5, pcbnew.F_Cu, net_inv, width=0.25)
            add_track(rx_pad2, base_y, rx_pad2, y_bar, pcbnew.F_Cu, net_inv, width=0.25)
            add_via(rx_pad2, y_bar, net_inv, size=0.55, drill=0.3)

        # Single continuous horizontal bus on In2.Cu
        add_track(COL_X[0] + 0.95, y_bar, COL_X[7] + 0.95, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)

        rf_x, rf_y, rb_x, rb_y = fb_config[idx]
        ux, uy = u1_inv_pins[idx]

        # Each neuron connects its feedback resistors locally to its own summing bar!
        if idx < 2:
            inv_x = rf_x + 0.95 # 54.45
            add_via(inv_x, y_bar, net_inv, size=0.55, drill=0.3)
            add_track(inv_x, y_bar, inv_x, rf_y, pcbnew.F_Cu, net_inv, width=0.25)
            add_track(inv_x, rf_y, inv_x, rb_y, pcbnew.F_Cu, net_inv, width=0.25)
        else:
            inv_x = rf_x - 0.95 # 55.55
            add_via(inv_x, y_bar, net_inv, size=0.55, drill=0.3)
            add_track(inv_x, y_bar, inv_x, rf_y, pcbnew.F_Cu, net_inv, width=0.25)
            add_track(inv_x, rf_y, inv_x, rb_y, pcbnew.F_Cu, net_inv, width=0.25)

    # Route U1 inverting pins to their respective summing bars on In2.Cu via B.Cu:
    # N0: Pin 2 at (52.3, 47.46) -> B.Cu bus at 49.0 up to Y = 16.5
    net_inv0 = nets[f"INV_N{neuron_range[0]}"]
    add_track(52.3, 47.46, 49.0, 47.46, pcbnew.F_Cu, net_inv0, width=0.20)
    add_via(49.0, 47.46, net_inv0, size=0.55, drill=0.3)
    add_track(49.0, 47.46, 49.0, 16.5, pcbnew.B_Cu, net_inv0, width=0.25)
    add_via(49.0, 16.5, net_inv0, size=0.55, drill=0.3)
    add_track(49.0, 16.5, COL_X[3] + 0.95, 16.5, pcbnew.In2_Cu, net_inv0, width=0.25)

    # N1: Pin 6 at (52.3, 52.54) -> B.Cu bus at 49.5 up to Y = 32.5
    net_inv1 = nets[f"INV_N{neuron_range[1]}"]
    add_track(52.3, 52.54, 49.5, 52.54, pcbnew.F_Cu, net_inv1, width=0.20)
    add_via(49.5, 52.54, net_inv1, size=0.55, drill=0.3)
    add_track(49.5, 52.54, 49.5, 32.5, pcbnew.B_Cu, net_inv1, width=0.25)
    add_via(49.5, 32.5, net_inv1, size=0.55, drill=0.3)
    add_track(49.5, 32.5, COL_X[3] + 0.95, 32.5, pcbnew.In2_Cu, net_inv1, width=0.25)

    # N2: Pin 9 at (57.7, 52.54) -> B.Cu bus at 60.5 up to Y = 48.5
    net_inv2 = nets[f"INV_N{neuron_range[2]}"]
    add_track(57.7, 52.54, 60.5, 52.54, pcbnew.F_Cu, net_inv2, width=0.20)
    add_via(60.5, 52.54, net_inv2, size=0.55, drill=0.3)
    add_track(60.5, 52.54, 60.5, 48.5, pcbnew.B_Cu, net_inv2, width=0.25)
    add_via(60.5, 48.5, net_inv2, size=0.55, drill=0.3)
    add_track(60.5, 48.5, COL_X[4] + 0.95, 48.5, pcbnew.In2_Cu, net_inv2, width=0.25)

    # N3: Pin 13 at (57.7, 47.46) -> B.Cu bus at 60.0 down to Y = 64.5
    net_inv3 = nets[f"INV_N{neuron_range[3]}"]
    add_track(57.7, 47.46, 60.0, 47.46, pcbnew.F_Cu, net_inv3, width=0.20)
    add_via(60.0, 47.46, net_inv3, size=0.55, drill=0.3)
    add_track(60.0, 47.46, 60.0, 64.5, pcbnew.B_Cu, net_inv3, width=0.25)
    add_via(60.0, 64.5, net_inv3, size=0.55, drill=0.3)
    add_track(60.0, 64.5, COL_X[4] + 0.95, 64.5, pcbnew.In2_Cu, net_inv3, width=0.25)

    # 3. ROUTE OP-AMP OUTPUTS (V_SUM_{j})
    # All vertical spine runs on B.Cu! Drop to In2.Cu only below Y = 80.0!

    # N0: Pin 1 at (52.3, 46.19), Rf Pad 1 at (52.55, 23.0). Pin 33 is odd at (51.51, 95.27)
    net_s0 = nets[f"V_SUM_{neuron_range[0]}"]
    add_track(52.55, 23.0, 50.24, 23.0, pcbnew.F_Cu, net_s0, width=0.25)
    add_via(50.24, 23.0, net_s0, size=0.55, drill=0.3)
    add_track(52.3, 46.19, 50.24, 46.19, pcbnew.F_Cu, net_s0, width=0.20)
    add_via(50.24, 46.19, net_s0, size=0.55, drill=0.3)
    # Run vertically on B.Cu to 80.0, then via to In2.Cu
    add_track(50.24, 23.0, 50.24, 80.0, pcbnew.B_Cu, net_s0, width=0.25)
    add_via(50.24, 80.0, net_s0, size=0.55, drill=0.3)
    add_track(50.24, 80.0, 50.24, 97.5, pcbnew.In2_Cu, net_s0, width=0.25)
    add_track(50.24, 97.5, 51.51, 97.5, pcbnew.In2_Cu, net_s0, width=0.25)
    add_track(51.51, 97.5, 51.51, 95.27, pcbnew.In2_Cu, net_s0, width=0.25)

    # N1: Pin 7 at (52.3, 53.81), Rf Pad 1 at (52.55, 38.0). Pin 34 is even at (51.51, 92.73)
    net_s1 = nets[f"V_SUM_{neuron_range[1]}"]
    add_track(52.55, 38.0, 51.51, 38.0, pcbnew.F_Cu, net_s1, width=0.25)
    add_via(51.51, 38.0, net_s1, size=0.55, drill=0.3)
    add_track(52.3, 53.81, 51.51, 53.81, pcbnew.F_Cu, net_s1, width=0.20)
    add_via(51.51, 53.81, net_s1, size=0.55, drill=0.3)
    add_track(51.51, 38.0, 51.51, 92.73, pcbnew.B_Cu, net_s1, width=0.25)

    # N2: Pin 8 at (57.7, 53.81), Rf Pad 1 at (57.45, 59.5). Pin 35 is odd at (54.05, 95.27)
    net_s2 = nets[f"V_SUM_{neuron_range[2]}"]
    add_track(57.45, 59.5, 52.78, 59.5, pcbnew.F_Cu, net_s2, width=0.25)
    add_via(52.78, 59.5, net_s2, size=0.55, drill=0.3)
    add_track(57.7, 53.81, 52.78, 53.81, pcbnew.F_Cu, net_s2, width=0.20)
    add_via(52.78, 53.81, net_s2, size=0.55, drill=0.3)
    # Run on B.Cu to 80.0, then via to In2.Cu
    add_track(52.78, 53.81, 52.78, 80.0, pcbnew.B_Cu, net_s2, width=0.25)
    add_via(52.78, 80.0, net_s2, size=0.55, drill=0.3)
    add_track(52.78, 80.0, 52.78, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(52.78, 97.5, 54.05, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(54.05, 97.5, 54.05, 95.27, pcbnew.In2_Cu, net_s2, width=0.25)

    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5). Pin 36 is even at (54.05, 92.73)
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_track(57.45, 74.5, 54.05, 74.5, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(54.05, 74.5, net_s3, size=0.55, drill=0.3)
    add_track(57.7, 46.19, 54.05, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(54.05, 46.19, net_s3, size=0.55, drill=0.3)
    add_track(54.05, 46.19, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)

    # 4. ROUTE POWER & BIAS RAILS
    # All vertical spine rails on B.Cu down to 80.0!

    # +12V: Pin 37 at (56.59, 95.27, odd). Run on B.Cu at 55.32 down to 80.0, via to In2.Cu
    add_track(52.3, 50.0, 50.8, 50.0, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(50.8, 50.0, net_p12, size=0.55, drill=0.3)
    add_track(51.05, 43.5, 50.8, 43.5, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(50.8, 43.5, net_p12, size=0.55, drill=0.3)
    add_track(50.8, 43.5, 50.8, 50.0, pcbnew.B_Cu, net_p12, width=0.30)
    add_track(50.8, 43.5, 55.32, 43.5, pcbnew.B_Cu, net_p12, width=0.30)
    add_track(55.32, 43.5, 55.32, 80.0, pcbnew.B_Cu, net_p12, width=0.35)
    add_via(55.32, 80.0, net_p12, size=0.55, drill=0.3)
    add_track(55.32, 80.0, 55.32, 97.5, pcbnew.In2_Cu, net_p12, width=0.35)
    add_track(55.32, 97.5, 56.59, 97.5, pcbnew.In2_Cu, net_p12, width=0.35)
    add_track(56.59, 97.5, 56.59, 95.27, pcbnew.In2_Cu, net_p12, width=0.35)

    # -12V: Pin 38 at (56.59, 92.73, even). Straight up on B.Cu at 56.59
    add_track(56.59, 92.73, 56.59, 50.0, pcbnew.B_Cu, net_n12, width=0.35)
    add_track(57.7, 50.0, 56.59, 50.0, pcbnew.F_Cu, net_n12, width=0.30)
    add_via(56.59, 50.0, net_n12, size=0.55, drill=0.3)
    add_track(56.59, 56.5, 57.05, 56.5, pcbnew.F_Cu, net_n12, width=0.30)
    add_via(56.59, 56.5, net_n12, size=0.55, drill=0.3)

    # +5V_REF: Pin 39 at (59.13, 95.27, odd). Run on B.Cu at 57.86 down to 80.0, via to In2.Cu
    add_track(57.86, 20.0, 57.86, 80.0, pcbnew.B_Cu, net_p5v, width=0.25)
    add_via(57.86, 80.0, net_p5v, size=0.55, drill=0.3)
    add_track(57.86, 80.0, 57.86, 97.5, pcbnew.In2_Cu, net_p5v, width=0.25)
    add_track(57.86, 97.5, 59.13, 97.5, pcbnew.In2_Cu, net_p5v, width=0.25)
    add_track(59.13, 97.5, 59.13, 95.27, pcbnew.In2_Cu, net_p5v, width=0.25)

    # -5V_REF: Pin 40 at (59.13, 92.73, even). Straight up on B.Cu at 59.13
    add_track(59.13, 92.73, 59.13, 20.0, pcbnew.B_Cu, net_n5v, width=0.25)

    for idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        rail = n_info["bias_rail"]
        net_bias = net_p5v if rail == "+5V_REF" else net_n5v
        bus_x = 57.86 if rail == "+5V_REF" else 59.13
        rf_x, rf_y, rb_x, rb_y = fb_config[idx]

        rb_pad1_x = (rb_x - 0.95) if idx < 2 else (rb_x + 0.95)
        # Connect Rb Pad 1 horizontally on F.Cu to bus_x with via
        add_track(rb_pad1_x, rb_y, bus_x, rb_y, pcbnew.F_Cu, net_bias, width=0.20)
        add_via(bus_x, rb_y, net_bias, size=0.55, drill=0.3)

    # 5. GND CONNECTIONS TO ZONE
    add_track(52.3, 48.73, 50.5, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(50.5, 48.73, net_gnd, size=0.55, drill=0.3) # pin 3

    add_track(52.3, 51.27, 50.5, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(50.5, 51.27, net_gnd, size=0.55, drill=0.3) # pin 5

    add_track(57.7, 51.27, 58.8, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(58.8, 51.27, net_gnd, size=0.55, drill=0.3) # pin 10

    add_track(57.7, 48.73, 58.8, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(58.8, 48.73, net_gnd, size=0.55, drill=0.3) # pin 12

    # Capacitors C_U1P pad 2 (52.95, 43.5), C_U1N pad 2 (58.95, 56.5)
    add_track(52.95, 43.5, 53.95, 43.5, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(53.95, 43.5, net_gnd, size=0.55, drill=0.3)

    add_track(58.95, 56.5, 59.95, 56.5, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(59.95, 56.5, net_gnd, size=0.55, drill=0.3)

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())

    b.Save(board_path)
    print(f"Routed and filled {board_name} successfully!")

if __name__ == "__main__":
    generate_dc1_board("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A - L1 Neurons 0..3", range(0, 4))
    route_dc1_board(os.path.join(WORKSPACE_DIR, "daughtercard1a_weights_l1.kicad_pcb"), range(0, 4))
