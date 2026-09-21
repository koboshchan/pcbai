#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
import os
import sys
import json
import uuid
import time
import subprocess
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def mm(v): return int(v * 1000000)
def make_uuid(): return str(uuid.uuid4())

COL_X = [16.0, 24.0, 32.0, 40.0, 60.0, 68.0, 76.0, 84.0]
NEURON_Y = [12.0, 27.0, 42.0, 57.0]

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
    pads = []
    pitch = 1.27
    y_start = - (3 * pitch)
    for i in range(7):
        py = y_start + i * pitch
        pin_num = str(i + 1)
        nid, nname = pin_nets.get(pin_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_num}" smd roundrect (at -2.7 {py:.3f} {rot}) (size 1.95 0.6) (layers "{layer}" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
    for i in range(7):
        py = y_start + (6 - i) * pitch
        pin_num = str(i + 8)
        nid, nname = pin_nets.get(pin_num, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_num}" smd roundrect (at 2.7 {py:.3f} {rot}) (size 1.95 0.6) (layers "{layer}" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {nid} "{nname}"))')
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

def run():
    filename = "test_escape_dc1a.kicad_pcb"
    board_path = os.path.join(WORKSPACE_DIR, filename)
    dsn_path = os.path.join(WORKSPACE_DIR, "test_escape_dc1a.dsn")
    ses_path = os.path.join(WORKSPACE_DIR, "test_escape_dc1a.ses")
    drc_path = os.path.join(WORKSPACE_DIR, "drc_test_escape_dc1a.json")
    neuron_range = range(0, 4)

    with open(os.path.join(WORKSPACE_DIR, "weights_layer1.json")) as f:
        l1 = json.load(f)

    nets = [(0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), (5, "-5V_REF"), (6, "+5V_REF")]
    for idx, j in enumerate(neuron_range):
        nets.append((10 + idx, f"V_SUM_{j}"))
        nets.append((20 + idx, f"INV_N{j}"))
    for i in range(64):
        nets.append((100 + i, f"IN_{i}"))

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])

    j_slot_a = {str(i+1): (100+i, f"IN_{i}") for i in range(32)}
    for idx in range(4):
        j_slot_a[str(33 + idx)] = (10 + idx, f"V_SUM_{neuron_range[idx]}")
    j_slot_a["37"] = (2, "+12V")
    j_slot_a["38"] = (3, "-12V")
    j_slot_a["39"] = (6, "+5V_REF")
    j_slot_a["40"] = (5, "-5V_REF")

    j_slot_b = {str(i+1): (132+i, f"IN_{32+i}") for i in range(32)}
    for p in range(33, 41):
        j_slot_b[str(p)] = (1, "GND")

    pcb = [
        f"""(kicad_pcb (version 20221018) (generator "analog_nn_100x100_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block (title "Test Escape DC1A") (rev "v5.0") (date "2026-09-12"))
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
  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (priority 0) (connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))
    (polygon (pts (xy 1.0 1.0) (xy 99.0 1.0) (xy 99.0 99.0) (xy 1.0 99.0)))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at 4.0 4.0) (descr "M3 Mounting Hole") (property "Reference" "H1" (at 0 -4.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at 96.0 4.0) (descr "M3 Mounting Hole") (property "Reference" "H2" (at 0 -4.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )
""",
        fp_header_2x20("J_SLOT_A", "Inputs_0_31_and_Sums", 50.0, 85.0, 90, j_slot_a),
        fp_header_2x20("J_SLOT_B", "Inputs_32_63_and_GND", 50.0, 92.62, 90, j_slot_b),
    ]

    j0 = neuron_range[0]
    ic_pin_nets = {
        "1": (10, f"V_SUM_{j0}"), "2": (20, f"INV_N{j0}"), "3": (1, "GND"),
        "4": (2, "+12V"),
        "5": (1, "GND"), "6": (21, f"INV_N{j0+1}"), "7": (11, f"V_SUM_{j0+1}"),
        "8": (12, f"V_SUM_{j0+2}"), "9": (22, f"INV_N{j0+2}"), "10": (1, "GND"),
        "11": (3, "-12V"),
        "12": (1, "GND"), "13": (23, f"INV_N{j0+3}"), "14": (13, f"V_SUM_{j0+3}")
    }
    pcb.append(fp_soic14("U1", "TL074", 50.0, 40.0, 0, "F.Cu", ic_pin_nets))
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 44.0, 25.0, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(fp_capacitor_0805("C_U1N", "0.1uF", 44.0, 55.0, 0, "F.Cu", 3, "-12V", 1, "GND"))

    for idx, j in enumerate(neuron_range):
        n_info = l1["weights"][j]
        bias_nid = 5 if n_info["bias_rail"] == "-5V_REF" else 6
        bias_name = n_info["bias_rail"]
        rb_str = n_info["bias_resistor_str"]

        if idx == 0:
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", 44.0, 36.19, 0, "F.Cu", 20+idx, f"INV_N{j}", 10+idx, f"V_SUM_{j}"))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, 44.0, 31.0, 90, "F.Cu", 20+idx, f"INV_N{j}", bias_nid, bias_name))
        elif idx == 1:
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", 44.0, 43.81, 0, "F.Cu", 20+idx, f"INV_N{j}", 10+idx, f"V_SUM_{j}"))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, 44.0, 49.0, 90, "F.Cu", bias_nid, bias_name, 20+idx, f"INV_N{j}"))
        elif idx == 2:
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", 56.0, 48.0, 0, "F.Cu", 20+idx, f"INV_N{j}", 10+idx, f"V_SUM_{j}"))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, 56.0, 52.0, 0, "F.Cu", 20+idx, f"INV_N{j}", bias_nid, bias_name))
        elif idx == 3:
            pcb.append(fp_resistor_0805(f"Rf_N{j}", "10k", 56.0, 32.0, 0, "F.Cu", 20+idx, f"INV_N{j}", 10+idx, f"V_SUM_{j}"))
            pcb.append(fp_resistor_0805(f"Rb_N{j}", rb_str, 56.0, 28.0, 0, "F.Cu", 20+idx, f"INV_N{j}", bias_nid, bias_name))

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
                pcb.append(fp_resistor_0805(f"R1_{i}_{j}", r_val_str, rx, ry, 0, "F.Cu", 100+i, f"IN_{i}", 20+idx, f"INV_N{j}"))

    pcb.append(")")
    with open(board_path, "w") as f:
        f.write("\n".join(pcb))

    b = pcbnew.LoadBoard(board_path)
    net_gnd = b.FindNet("GND")

    def add_track(x1, y1, x2, y2, layer, net, width=0.20):
        if abs(x1 - x2) < 1e-4 and abs(y1 - y2) < 1e-4: return
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
        add_track(x_pad, y_pad, x_via, y_via, pcbnew.F_Cu, net_gnd, width=0.25)

    add_gnd_via(47.3, 38.73, 45.5, 38.73)
    add_gnd_via(47.3, 41.27, 45.5, 41.27)
    add_gnd_via(52.7, 41.27, 54.5, 41.27)
    add_gnd_via(52.7, 38.73, 54.5, 38.73)
    add_gnd_via(44.95, 25.0, 46.5, 25.0)
    add_gnd_via(44.95, 55.0, 46.5, 55.0)

    # Clean Staggered Escape for all 256 resistor Pad 1s:
    # Staggered vias at X = COL_X[c] - 2.0 (even r) and X = COL_X[c] - 3.2 (odd r)
    for c in range(8):
        for idx in range(4):
            base_y = NEURON_Y[idx]
            for r in range(8):
                i = c * 8 + r
                net_in = b.FindNet(f"IN_{i}")
                x_pad = COL_X[c] - 0.95
                y_pad = base_y + r * 1.5
                x_via = COL_X[c] - (2.0 if r % 2 == 0 else 3.2)
                add_track(x_pad, y_pad, x_via, y_pad, pcbnew.F_Cu, net_in, width=0.18)
                add_via(x_via, y_pad, net_in, size=0.60, drill=0.30)

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(board_path)

    pcbnew.ExportSpecctraDSN(b, dsn_path)
    print("DSN exported. Running Freerouting...")

    cmd = [
        "/usr/bin/java", "-jar", JAR_PATH,
        "-de", dsn_path,
        "-do", ses_path,
        "--gui.enabled=false",
        "-mp", "150",
        "-mt", "1"
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0
    print(f"Freerouting finished in {elapsed:.1f}s, exit code: {res.returncode}")

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
        print(f"Result: {uncon} unconnected, {viols} errors")
        return uncon == 0 and viols == 0
    return False

if __name__ == "__main__":
    run()
