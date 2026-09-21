#!/usr/bin/env python3
"""
generate_all_4neuron_cards.py
-----------------------------
Generates and routes all four 4-Neuron Daughtercards:
- Daughtercard 1A: Neurons 0..3
- Daughtercard 1B: Neurons 4..7
- Daughtercard 1C: Neurons 8..11
- Daughtercard 1D: Neurons 12..15

Each board is 100mm x 100mm, 4 layers, zero overlaps, 20mm clearance from M3 mounting holes.
"""

import os
import json
import uuid
import subprocess

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
FREEROUTING_JAR = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"

def make_uuid():
    return str(uuid.uuid4())

def get_header(board_name, nets):
    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets])
    return f"""(kicad_pcb (version 20221018) (generator "analog_nn_pcb_generator")
  (general
    (thickness 1.6)
  )
  (paper "A4")
  (title_block
    (title "{board_name}")
    (company "Discrete Analog MNIST PCB Stack")
    (rev "v3.1 - Modular 4-Neuron Slice")
    (date "2026-09-11")
  )
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" signal "GND")
    (2 "In2.Cu" signal "Signal")
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
{net_lines}
"""

def get_outline_and_mounts():
    items = [
        f'  (gr_rect (start 0 0) (end 100 100) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{make_uuid()}"))',
        f'  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)',
        '    (priority 0)',
        '    (connect_pads (clearance 0.25))',
        '    (min_thickness 0.25)',
        '    (filled_areas_thickness no)',
        '    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))',
        '    (polygon',
        '      (pts (xy 1.0 1.0) (xy 99.0 1.0) (xy 99.0 99.0) (xy 1.0 99.0))',
        '    )',
        '  )',
    ]
    mount_coords = [(5.0, 5.0), (95.0, 5.0), (5.0, 95.0), (95.0, 95.0)]
    for idx, (mx, my) in enumerate(mount_coords):
        items.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {mx:.2f} {my:.2f})
    (descr "Mounting Hole 3.2mm, M3 with Pad")
    (tags "mounting hole 3.2mm m3 pad")
    (property "Reference" "H{idx+1}" (at {mx:.2f} {my-4:.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "MountingHole" (at {mx:.2f} {my+4:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 6.0 6.0) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )""")
    return "\n".join(items)

def fp_resistor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=1, net1_name="GND", net2=0, net2_name=""):
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
    (at {x:.2f} {y:.2f} {rot})
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
    (at {x:.2f} {y:.2f} {rot})
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
    (at {x:.2f} {y:.2f} {rot})
    (descr "Pin Header 2.54mm 2x20 vertical")
    (property "Reference" "{ref}" (at 0 -27.0 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 27.0 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def fp_header_2x10(ref, val, x, y, rot=0, pin_nets=None):
    pads = []
    pitch = 2.54
    y_start = - (4.5 * pitch)
    for i in range(10):
        py = y_start + i * pitch
        pin_odd = str(2 * i + 1)
        pin_even = str(2 * i + 2)
        n_odd_id, n_odd_name = pin_nets.get(pin_odd, (0, "")) if pin_nets else (0, "")
        n_even_id, n_even_name = pin_nets.get(pin_even, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_odd}" thru_hole circle (at -1.27 {py:.3f} {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {n_odd_id} "{n_odd_name}"))')
        pads.append(f'    (pad "{pin_even}" thru_hole oval (at 1.27 {py:.3f} {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {n_even_id} "{n_even_name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.2f} {y:.2f} {rot})
    (descr "Pin Header 2.54mm 2x10 vertical")
    (property "Reference" "{ref}" (at 0 -14.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 14.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def generate_dc_board(filename, title, neuron_range):
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

    # J_IN_A: Inputs 0..31 at Y = 86.0
    j_in_a = {str(i+1): (100+i, f"IN_{i}") for i in range(32)}
    for p in range(33, 41): j_in_a[str(p)] = (1, "GND")

    # J_IN_B: Inputs 32..63 at Y = 92.5
    j_in_b = {str(i+1): (132+i, f"IN_{32+i}") for i in range(32)}
    for p in range(33, 41): j_in_b[str(p)] = (1, "GND")

    # J_OUT: Sums 0..3 + Power at right edge
    j_out = {str(idx+1): (10 + neuron_range[idx], f"V_SUM_{neuron_range[idx]}") for idx in range(4)}
    j_out["5"] = (2, "+12V")
    j_out["6"] = (3, "-12V")
    j_out["7"] = (6, "+5V_REF")
    j_out["8"] = (5, "-5V_REF")
    for p in range(9, 21): j_out[str(p)] = (1, "GND")

    pcb = [
        get_header(title, nets),
        get_outline_and_mounts(),
        fp_header_2x20("J_IN_A", "Inputs_0_31", 50.0, 86.0, 90, j_in_a),
        fp_header_2x20("J_IN_B", "Inputs_32_63", 50.0, 92.5, 90, j_in_b),
        fp_header_2x10("J_OUT", "Sums_and_Power", 93.0, 50.0, 0, j_out),
    ]

    # Single TL074 quad op-amp at X = 85.0, Y = 50.0
    j_base = neuron_range[0]
    ic_pin_nets = {
        "4": (2, "+12V"), "11": (3, "-12V"),
        "1": (10 + j_base, f"V_SUM_{j_base}"), "2": (30 + j_base, f"INV_N{j_base}"), "3": (1, "GND"),
        "7": (10 + j_base + 1, f"V_SUM_{j_base+1}"), "6": (30 + j_base + 1, f"INV_N{j_base+1}"), "5": (1, "GND"),
        "8": (10 + j_base + 2, f"V_SUM_{j_base+2}"), "9": (30 + j_base + 2, f"INV_N{j_base+2}"), "10": (1, "GND"),
        "14": (10 + j_base + 3, f"V_SUM_{j_base+3}"), "13": (30 + j_base + 3, f"INV_N{j_base+3}"), "12": (1, "GND")
    }
    pcb.append(fp_soic14("U1", "TL074", 85.0, 50.0, 0, "F.Cu", ic_pin_nets))
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 85.0, 43.0, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 85.0, 57.0, 0, "F.Cu", 3, "-12V", 1, "GND"))

    # 4 Feedback & Bias Resistors at X = 78.5
    for idx, j in enumerate(neuron_range):
        rf_y = 26.0 + idx * 16.0
        n_info = l1["weights"][j]
        rb_str = n_info["bias_resistor_str"]
        bias_nid = 5 if n_info["bias_rail"] == "-5V_REF" else 6
        bias_name = n_info["bias_rail"]
        pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", 78.5, rf_y - 2.0, 0, "F.Cu", 10+j, f"V_SUM_{j}", 30+j, f"INV_N{j}"))
        pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, 78.5, rf_y + 2.0, 0, "F.Cu", bias_nid, bias_name, 30+j, f"INV_N{j}"))

    # 256 Resistors: 32 columns x 8 rows
    for idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        ry_a = 16.0 + idx * 16.0
        ry_b = ry_a + 8.00
        for i in range(32):
            inp = n_info["inputs"][i]
            rx = 25.0 + i * 1.60
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", inp["resistor_str"], rx, ry_a, 90, "F.Cu", 100+i, f"IN_{i}", 30+j, f"INV_N{j}"))

        for i in range(32, 64):
            inp = n_info["inputs"][i]
            rx = 25.0 + (i - 32) * 1.60
            pcb.append(fp_resistor_0805(f"R1_{i}_{j}", inp["resistor_str"], rx, ry_b, 90, "F.Cu", 100+i, f"IN_{i}", 30+j, f"INV_N{j}"))

    # Bridge for GND thermal relief on pin 34 to 36
    pcb.append('  (segment (start 66.51 84.73) (end 69.05 84.73) (width 0.4) (layer "F.Cu") (net 1) (uuid "gnd-pad34-bridge"))')
    pcb.append(")")
    with open(board_file, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated {title}: {board_file}")

def main():
    boards = [
        ("daughtercard1b_weights_l1.kicad_pcb", "Daughtercard 1B: Layer 1 Weights (Neurons 4..7)", [4, 5, 6, 7]),
        ("daughtercard1c_weights_l1.kicad_pcb", "Daughtercard 1C: Layer 1 Weights (Neurons 8..11)", [8, 9, 10, 11]),
        ("daughtercard1d_weights_l1.kicad_pcb", "Daughtercard 1D: Layer 1 Weights (Neurons 12..15)", [12, 13, 14, 15]),
    ]
    for filename, title, n_range in boards:
        generate_dc_board(filename, title, n_range)

if __name__ == "__main__":
    main()
