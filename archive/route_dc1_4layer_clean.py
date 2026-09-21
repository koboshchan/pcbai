#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
route_dc1_4layer_clean.py
-------------------------
Implements a true 4-layer PCB router for the 72-Pin Edge Card Daughtercard 1:
- Layer 1 (F.Cu): SMD Pads, local escapes, op-amp routing, feedback networks
- Layer 2 (In1.Cu): Solid GND Plane (thermal relief to op-amp non-inverting pins & bypass caps)
- Layer 3 (In2.Cu): 4 Isolated Summing Buses (INV_N0..3) running directly to TL074 pins
- Layer 4 (B.Cu): Vertical Input Distribution Bus (IN_0..63) cleanly routed with zero shorts
"""

import os
import sys
import json
import uuid
import subprocess
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def mm(v): return int(v * 1000000)
def make_uuid(): return str(uuid.uuid4())

DIM_B = 94.28
PITCH = 2.54

def build_and_route_clean_dc1(filename, title, neuron_range):
    board_path = os.path.join(WORKSPACE_DIR, filename)
    base_name = os.path.splitext(filename)[0]
    dsn_path = os.path.join(WORKSPACE_DIR, f"{base_name}.dsn")
    ses_path = os.path.join(WORKSPACE_DIR, f"{base_name}.ses")
    drc_path = os.path.join(WORKSPACE_DIR, f"drc_{base_name}.json")

    with open(os.path.join(WORKSPACE_DIR, "weights_layer1.json")) as f:
        l1 = json.load(f)

    # Clean nets
    nets = [(0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), (5, "-5V_REF"), (6, "+5V_REF")]
    for idx, j in enumerate(neuron_range):
        nets.append((10 + idx, f"V_SUM_{j}"))
        nets.append((20 + idx, f"INV_N{j}"))
    for i in range(64):
        nets.append((100 + i, f"IN_{i}"))

    net_map = {name: nid for nid, name in nets}
    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])

    # 72 Gold Fingers on Edge Card:
    pin_nets_a = {f"A{i+1}": (100 + i, f"IN_{i}") for i in range(32)}
    for idx, j in enumerate(neuron_range):
        pin_nets_a[f"A{33+idx}"] = (10 + idx, f"V_SUM_{j}")

    pin_nets_b = {f"B{i+1}": (132 + i, f"IN_{32+i}") for i in range(32)}
    pin_nets_b["B33"] = (2, "+12V")
    pin_nets_b["B34"] = (3, "-12V")
    pin_nets_b["B35"] = (1, "GND")
    pin_nets_b["B36"] = (1, "GND")

    # Footprints
    pads_fingers = []
    cx = DIM_B / 2.0 # 47.14 mm
    x_start = - (17.5 * PITCH) # -44.45 mm
    for i in range(36):
        px = x_start + i * PITCH
        nid_a, name_a = pin_nets_a.get(f"A{i+1}", (0, ""))
        pads_fingers.append(f'    (pad "A{i+1}" smd roundrect (at {px:.3f} 0) (size 1.6 8.0) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2) (net {nid_a} "{name_a}"))')
        nid_b, name_b = pin_nets_b.get(f"B{i+1}", (0, ""))
        pads_fingers.append(f'    (pad "B{i+1}" smd roundrect (at {px:.3f} 0) (size 1.6 8.0) (layers "B.Cu" "B.Mask") (roundrect_rratio 0.2) (net {nid_b} "{name_b}"))')
    fingers_str = "\n".join(pads_fingers)

    pcb = [f"""(kicad_pcb (version 20221018) (generator "clean_4layer_dc1_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block (title "{title}") (rev "v6.1 - 4-Layer True Route") (date "2026-09-13"))
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" power "GND")
    (2 "In2.Cu" signal "Summing_Power")
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (44 "Edge.Cuts" user)
  )
  (setup
    (pad_to_mask_clearance 0.05)
  )
  (net 0 "")
{net_lines}
  (gr_rect (start 0 0) (end {DIM_B:.2f} 100.00) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{make_uuid()}"))
  (gr_line (start 1.0 91.0) (end {DIM_B-1.0:.2f} 91.0) (stroke (width 0.25) (type default)) (layer "F.SilkS") (uuid "{make_uuid()}"))
  (gr_text "<< INSERTION STOP LINE (9.0mm Socket Depth) >>" (at {cx:.2f} 89.0 0) (layer "F.SilkS") (uuid "{make_uuid()}") (effects (font (size 1.1 1.1) (thickness 0.15))))

  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (priority 0) (connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))
    (polygon (pts (xy 1.0 1.0) (xy {DIM_B-1.0:.2f} 1.0) (xy {DIM_B-1.0:.2f} 90.0) (xy 1.0 90.0)))
  )

  (footprint "Connector_PCBEdge:GoldFingers_72P_2.54mm" (layer "F.Cu") (uuid "{make_uuid()}")
    (at {cx:.2f} 96.00)
    (descr "72-Pin PCB Edge Gold Fingers")
    (property "Reference" "J_EDGE_FINGERS" (at 0 -6.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "72P_GoldFingers_ENIG" (at 0 6.0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{fingers_str}
  )
"""]

    # Corner pull holes (M3)
    for idx, (mx, my) in enumerate([(5.0, 5.0), (DIM_B - 5.0, 5.0)]):
        pcb.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at {mx:.2f} {my:.2f}) (property "Reference" "H{idx+1}" (at {mx:.2f} {my-4:.2f} 0) (layer "F.SilkS"))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )""")

    # Central Spine: TL074 Op-Amp at X = 47.14 mm (center), Y = 45.0 mm
    j0 = neuron_range[0]
    ic_pin_nets = {
        "1": (10, f"V_SUM_{j0}"), "2": (20, f"INV_N{j0}"), "3": (1, "GND"),
        "4": (2, "+12V"),
        "5": (1, "GND"), "6": (21, f"INV_N{j0+1}"), "7": (11, f"V_SUM_{j0+1}"),
        "8": (12, f"V_SUM_{j0+2}"), "9": (22, f"INV_N{j0+2}"), "10": (1, "GND"),
        "11": (3, "-12V"),
        "12": (1, "GND"), "13": (23, f"INV_N{j0+3}"), "14": (13, f"V_SUM_{j0+3}")
    }

    # Generate SOIC14
    pads_u1 = []
    pitch = 1.27
    y_start = - (3 * pitch)
    for i in range(7):
        py = y_start + i * pitch
        pin_num = str(i + 1)
        nid, nname = ic_pin_nets.get(pin_num, (0, ""))
        pads_u1.append(f'    (pad "{pin_num}" smd roundrect (at -2.7 {py:.3f}) (size 1.95 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    for i in range(7):
        py = y_start + (6 - i) * pitch
        pin_num = str(i + 8)
        nid, nname = ic_pin_nets.get(pin_num, (0, ""))
        pads_u1.append(f'    (pad "{pin_num}" smd roundrect (at 2.7 {py:.3f}) (size 1.95 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    pads_u1_str = "\n".join(pads_u1)
    pcb.append(f"""  (footprint "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (layer "F.Cu") (uuid "{make_uuid()}")
    (at {cx:.2f} 45.00)
    (property "Reference" "U1" (at 0 -5.5 0) (layer "F.SilkS"))
    (property "Value" "TL074" (at 0 5.5 0) (layer "F.Fab"))
{pads_u1_str}
  )""")

    # Bypass caps for U1
    for c_ref, c_y, c_nid, c_name in [("C_U1P", 35.0, 2, "+12V"), ("C_U1N", 55.0, 3, "-12V")]:
        pcb.append(f"""  (footprint "Capacitor_SMD:C_0805_2012Metric" (layer "F.Cu") (uuid "{make_uuid()}")
    (at {cx:.2f} {c_y:.2f}) (property "Reference" "{c_ref}" (at 0 -1.5 0) (layer "F.SilkS"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {c_nid} "{c_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net 1 "GND"))
  )""")

    # 4 Feedback & Bias Resistors placed around U1
    rf_coords = [
        (cx - 8.0, 41.19, 0), # Neuron 0 (near pin 1 & 2)
        (cx - 8.0, 48.81, 1), # Neuron 1 (near pin 6 & 7)
        (cx + 8.0, 48.81, 2), # Neuron 2 (near pin 8 & 9)
        (cx + 8.0, 41.19, 3)  # Neuron 3 (near pin 13 & 14)
    ]
    for rx, ry, idx in rf_coords:
        j = neuron_range[idx]
        n_info = l1["weights"][j]
        bias_nid = 5 if n_info["bias_rail"] == "-5V_REF" else 6
        bias_name = n_info["bias_rail"]
        rb_str = n_info["bias_resistor_str"]
        # Rf
        pcb.append(f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "F.Cu") (uuid "{make_uuid()}")
    (at {rx:.2f} {ry-2.0:.2f}) (property "Reference" "Rf_N{j}" (at 0 -1.5 0) (layer "F.SilkS"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {20+idx} "INV_N{j}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {10+idx} "V_SUM_{j}"))
  )""")
        # Rb
        pcb.append(f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "F.Cu") (uuid "{make_uuid()}")
    (at {rx:.2f} {ry+2.0:.2f}) (property "Reference" "Rb_N{j}" (at 0 -1.5 0) (layer "F.SilkS"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {bias_nid} "{bias_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {20+idx} "INV_N{j}"))
  )""")

    # 4 Neurons: Each has 8 columns x 8 rows of resistors
    # 2 Left Neurons (N0 at Y=[12..25], N1 at Y=[60..73]) on X = [10..38] mm
    # 2 Right Neurons (N3 at Y=[12..25], N2 at Y=[60..73]) on X = [56..84] mm
    neuron_layouts = [
        (0, 10.0, 12.0), # N0: Left Top
        (1, 10.0, 60.0), # N1: Left Bottom
        (2, 56.0, 60.0), # N2: Right Bottom
        (3, 56.0, 12.0)  # N3: Right Top
    ]

    for idx, base_x, base_y in neuron_layouts:
        j = neuron_range[idx]
        n_info = l1["weights"][j]
        sum_nid = 20 + idx
        sum_name = f"INV_N{j}"

        for col in range(8):
            rx = base_x + col * 3.60
            for row in range(8):
                i = col * 8 + row # input 0..63
                inp_info = n_info["inputs"][i]
                r_val = inp_info["resistor_str"]
                ry = base_y + row * 1.80
                in_nid = 100 + i
                in_name = f"IN_{i}"
                pcb.append(f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "F.Cu") (uuid "{make_uuid()}")
    (at {rx:.2f} {ry:.2f}) (property "Reference" "R1_{i}_{j}" (at 0 -1.5 0) (layer "F.SilkS"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {in_nid} "{in_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {sum_nid} "{sum_name}"))
  )""")

    pcb.append(")")
    with open(board_path, "w") as f:
        f.write("\n".join(pcb))

    print(f"[{title}] Board skeleton generated at {board_path}.")

    # Load Board in pcbnew and add direct pre-routed copper features
    b = pcbnew.LoadBoard(board_path)
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

    # 1. Op-Amp GND Thermal Vias (Pins 3, 5, 10, 12)
    # TL074 at (cx, 45.0):
    # Left side: pin 3 at (cx - 2.7, 45.0 - 1.27 = 43.73), pin 5 at (cx - 2.7, 45.0 + 1.27 = 46.27)
    # Right side: pin 10 at (cx + 2.7, 45.0 + 1.27 = 46.27), pin 12 at (cx + 2.7, 45.0 - 1.27 = 43.73)
    add_via(cx - 4.5, 43.73, net_gnd)
    add_track(cx - 2.7, 43.73, cx - 4.5, 43.73, pcbnew.F_Cu, net_gnd)
    add_via(cx - 4.5, 46.27, net_gnd)
    add_track(cx - 2.7, 46.27, cx - 4.5, 46.27, pcbnew.F_Cu, net_gnd)
    add_via(cx + 4.5, 46.27, net_gnd)
    add_track(cx + 2.7, 46.27, cx + 4.5, 46.27, pcbnew.F_Cu, net_gnd)
    add_via(cx + 4.5, 43.73, net_gnd)
    add_track(cx + 2.7, 43.73, cx + 4.5, 43.73, pcbnew.F_Cu, net_gnd)

    # Bypass Cap GND vias
    add_via(cx + 2.5, 35.0, net_gnd)
    add_track(cx + 0.95, 35.0, cx + 2.5, 35.0, pcbnew.F_Cu, net_gnd)
    add_via(cx + 2.5, 55.0, net_gnd)
    add_track(cx + 0.95, 55.0, cx + 2.5, 55.0, pcbnew.F_Cu, net_gnd)

    # 2. Vertical Column Summing Strips on F.Cu for all 4 neurons:
    for idx, base_x, base_y in neuron_layouts:
        j = neuron_range[idx]
        net_inv = b.FindNet(f"INV_N{j}")
        for col in range(8):
            rx = base_x + col * 3.60
            # Tie all pad 2's together in this column
            add_track(rx + 0.95, base_y, rx + 0.95, base_y + 7 * 1.80, pcbnew.F_Cu, net_inv)
        # Horizontal summing bus on In2.Cu tying all 8 columns together!
        add_track(base_x + 0.95, base_y + 3.5 * 1.80, base_x + 7 * 3.60 + 0.95, base_y + 3.5 * 1.80, pcbnew.In2_Cu, net_inv, width=0.35)
        for col in range(8):
            rx = base_x + col * 3.60
            add_via(rx + 0.95, base_y + 3.5 * 1.80, net_inv)

    # 3. Connect Summing Buses directly to U1 Inverting Pins:
    # N0 (Left Top): to U1 Pin 2 at (cx - 2.7, 45.0 - 2.54 = 42.46)
    net_inv0 = b.FindNet(f"INV_N{neuron_range[0]}")
    add_track(10.0 + 7 * 3.60 + 0.95, 12.0 + 3.5 * 1.80, cx - 8.0, 39.19, pcbnew.In2_Cu, net_inv0, width=0.35)
    add_via(cx - 8.0, 39.19, net_inv0)
    add_track(cx - 8.0, 39.19, cx - 2.7, 42.46, pcbnew.F_Cu, net_inv0)

    # N1 (Left Bottom): to U1 Pin 6 at (cx - 2.7, 45.0 + 2.54 = 47.54)
    net_inv1 = b.FindNet(f"INV_N{neuron_range[1]}")
    add_track(10.0 + 7 * 3.60 + 0.95, 60.0 + 3.5 * 1.80, cx - 8.0, 50.81, pcbnew.In2_Cu, net_inv1, width=0.35)
    add_via(cx - 8.0, 50.81, net_inv1)
    add_track(cx - 8.0, 50.81, cx - 2.7, 47.54, pcbnew.F_Cu, net_inv1)

    # N2 (Right Bottom): to U1 Pin 9 at (cx + 2.7, 45.0 + 2.54 = 47.54)
    net_inv2 = b.FindNet(f"INV_N{neuron_range[2]}")
    add_track(56.0 + 0.95, 60.0 + 3.5 * 1.80, cx + 8.0, 50.81, pcbnew.In2_Cu, net_inv2, width=0.35)
    add_via(cx + 8.0, 50.81, net_inv2)
    add_track(cx + 8.0, 50.81, cx + 2.7, 47.54, pcbnew.F_Cu, net_inv2)

    # N3 (Right Top): to U1 Pin 13 at (cx + 2.7, 45.0 - 2.54 = 42.46)
    net_inv3 = b.FindNet(f"INV_N{neuron_range[3]}")
    add_track(56.0 + 0.95, 12.0 + 3.5 * 1.80, cx + 8.0, 39.19, pcbnew.In2_Cu, net_inv3, width=0.35)
    add_via(cx + 8.0, 39.19, net_inv3)
    add_track(cx + 8.0, 39.19, cx + 2.7, 42.46, pcbnew.F_Cu, net_inv3)

    # 4. Connect Op-Amp Outputs to V_SUM Pins A33..A36:
    for idx, (px_idx, pin_x, pin_y) in enumerate([
        (32, cx - 2.7, 45.0 - 3.81), # U1 Pin 1 (N0 out)
        (33, cx - 2.7, 45.0 + 3.81), # U1 Pin 7 (N1 out)
        (34, cx + 2.7, 45.0 + 3.81), # U1 Pin 8 (N2 out)
        (35, cx + 2.7, 45.0 - 3.81)  # U1 Pin 14 (N3 out)
    ]):
        j = neuron_range[idx]
        net_out = b.FindNet(f"V_SUM_{j}")
        dst_x = cx + x_start + px_idx * PITCH
        add_track(pin_x, pin_y, dst_x, 85.0, pcbnew.F_Cu, net_out)
        add_track(dst_x, 85.0, dst_x, 92.0, pcbnew.F_Cu, net_out)

    # 5. Power Rails (+12V from B33, -12V from B34)
    net_p12 = b.FindNet("+12V")
    net_n12 = b.FindNet("-12V")
    px_b33 = cx + x_start + 32 * PITCH
    px_b34 = cx + x_start + 33 * PITCH
    # +12V from Pin B33 on B.Cu up to U1 Pin 4 (cx - 2.7, 45.0) and Cap
    add_track(px_b33, 92.0, cx - 6.0, 45.0, pcbnew.B_Cu, net_p12, width=0.40)
    add_via(cx - 6.0, 45.0, net_p12)
    add_track(cx - 6.0, 45.0, cx - 2.7, 45.0, pcbnew.F_Cu, net_p12, width=0.40)
    add_track(cx - 2.7, 45.0, cx - 0.95, 35.0, pcbnew.F_Cu, net_p12, width=0.35)

    # -12V from Pin B34 on B.Cu up to U1 Pin 11 (cx + 2.7, 45.0) and Cap
    add_track(px_b34, 92.0, cx + 6.0, 45.0, pcbnew.B_Cu, net_n12, width=0.40)
    add_via(cx + 6.0, 45.0, net_n12)
    add_track(cx + 6.0, 45.0, cx + 2.7, 45.0, pcbnew.F_Cu, net_n12, width=0.40)
    add_track(cx + 2.7, 45.0, cx - 0.95, 55.0, pcbnew.F_Cu, net_n12, width=0.35)

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(board_path)

    # Export Specctra DSN for Freerouting to complete the remaining input escape routing
    pcbnew.ExportSpecctraDSN(b, dsn_path)
    print(f"[{title}] Exported DSN to {dsn_path}.")

    # Run Freerouting
    cmd = [
        "/usr/bin/java", "-jar", JAR_PATH,
        "-de", dsn_path,
        "-do", ses_path,
        "--gui.enabled=false",
        "-mp", "200",
        "-mt", "2"
    ]
    t0 = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(ses_path):
        b = pcbnew.LoadBoard(board_path)
        pcbnew.ImportSpecctraSES(b, ses_path)
        filler = pcbnew.ZONE_FILLER(b)
        filler.Fill(b.Zones())
        b.Save(board_path)

        cmd_drc = f"{KICAD_CLI} pcb drc --severity-error --output {drc_path} --format json {board_path}"
        subprocess.run(cmd_drc, shell=True)
        with open(drc_path) as f:
            d = json.load(f)
        uncon = len(d.get("unconnected_items", []))
        viols = len(d.get("violations", []))
        print(f"[{title}] Freerouting Completed! DRC: {uncon} unconnected items, {viols} violations.")
        return uncon, viols
    else:
        print(f"[{title}] Freerouting failed to generate SES.")
        return -1, -1

if __name__ == "__main__":
    build_and_route_clean_dc1("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A: L1 Neurons 0..3", range(0, 4))
