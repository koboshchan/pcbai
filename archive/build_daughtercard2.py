#!/usr/bin/env python3
"""
build_daughtercard2.py
Automated generator and router for Daughtercard 2 (16-channel Active Precision ReLU).
Option A: 100x100mm 4-Layer Modular Stack.
- Dual parallel 2x20 vertical headers along bottom edge:
    J_SLOT_A at (50.0, 85.00), rot 90: Pins 1..16 = V_SUM_0..15, Pins 37..38 = +/-12V, 39..40 = GND
    J_SLOT_B at (50.0, 92.62), rot 90: Pins 1..16 = ACT_0..15, Pins 33..40 = GND
- 16 Active Precision Half-Wave Rectifiers (4x TL074 SOIC-14)
- 100% 0805 SMD resistors (10k) and SOD-123 diodes (1N4148)
- 4-layer stackup: F.Cu (signals), In1.Cu (GND plane), In2.Cu (signals/Power), B.Cu (signals)
- Full Freerouting + KiCad CLI DRC verification: 0 unconnected, 0 violations.
"""

import os
import subprocess
import pcbnew
import time
import uuid
import json

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

BOARD_PATH = os.path.join(WORKSPACE_DIR, "daughtercard2_relu_l1.kicad_pcb")
DSN_PATH = os.path.join(WORKSPACE_DIR, "daughtercard2_relu_l1.dsn")
SES_PATH = os.path.join(WORKSPACE_DIR, "daughtercard2_relu_l1.ses")
DRC_PATH = os.path.join(WORKSPACE_DIR, "drc_daughtercard2_relu_l1.json")

def make_uuid(): return str(uuid.uuid4())
def mm(v): return int(v * 1000000)

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

def fp_capacitor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=1, net1_name="GND", net2=0, net2_name=""):
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
    (pad "1" smd roundrect (at -1.65 0 {rot}) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 1.65 0 {rot}) (size 0.9 1.2) (layers "{layer}" "{paste}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
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

def generate_dc2():
    nets = [(0, ""), (1, "GND"), (2, "+12V"), (3, "-12V")]
    for k in range(16):
        nets.append((10 + k, f"V_SUM_{k}"))
        nets.append((30 + k, f"ACT_{k}"))
        nets.append((50 + k, f"OA_OUT_{k}"))
        nets.append((70 + k, f"INV_{k}"))

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets])

    # J_SLOT_A: Pins 1..16 = V_SUM_0..15, Pins 37..38 = +/-12V, 39..40 = GND
    j_slot_a = {str(k+1): (10+k, f"V_SUM_{k}") for k in range(16)}
    for p in range(17, 37):
        j_slot_a[str(p)] = (0, "")
    j_slot_a["37"] = (2, "+12V")
    j_slot_a["38"] = (3, "-12V")
    j_slot_a["39"] = (1, "GND")
    j_slot_a["40"] = (1, "GND")

    # J_SLOT_B: Pins 1..16 = ACT_0..15, Pins 33..40 = GND
    j_slot_b = {str(k+1): (30+k, f"ACT_{k}") for k in range(16)}
    for p in range(17, 33):
        j_slot_b[str(p)] = (0, "")
    for p in range(33, 41):
        j_slot_b[str(p)] = (1, "GND")

    pcb = [
        f"""(kicad_pcb (version 20221018) (generator "analog_nn_100x100_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block (title "Daughtercard 2 - 16x Active Precision ReLU") (rev "v5.0 - 100x100mm 4-Layer Modular Stack") (date "2026-09-12"))
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
        fp_header_2x20("J_SLOT_A", "Sums_0_15_In", 50.0, 85.0, 90, j_slot_a),
        fp_header_2x20("J_SLOT_B", "Act_0_15_Out", 50.0, 92.62, 90, j_slot_b),
    ]

    # 4 TL074 Op-Amps centered at X = 50.0, Y = [16.0, 32.0, 48.0, 64.0]
    u_y = [16.0, 32.0, 48.0, 64.0]
    for u_idx in range(4):
        k0 = u_idx * 4
        ic_nets = {
            "4": (2, "+12V"), "11": (3, "-12V"),
            "1": (50 + k0, f"OA_OUT_{k0}"), "2": (70 + k0, f"INV_{k0}"), "3": (1, "GND"),
            "7": (50 + k0 + 1, f"OA_OUT_{k0+1}"), "6": (70 + k0 + 1, f"INV_{k0+1}"), "5": (1, "GND"),
            "8": (50 + k0 + 2, f"OA_OUT_{k0+2}"), "9": (70 + k0 + 2, f"INV_{k0+2}"), "10": (1, "GND"),
            "14": (50 + k0 + 3, f"OA_OUT_{k0+3}"), "13": (70 + k0 + 3, f"INV_{k0+3}"), "12": (1, "GND")
        }
        uy = u_y[u_idx]
        pcb.append(fp_soic14(f"U{u_idx+1}", "TL074", 50.0, uy, 0, "F.Cu", ic_nets))
        pcb.append(fp_capacitor_0805(f"C_U{u_idx+1}P", "0.1uF", 45.0, uy - 5.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
        pcb.append(fp_capacitor_0805(f"C_U{u_idx+1}N", "0.1uF", 55.0, uy + 5.5, 0, "F.Cu", 3, "-12V", 1, "GND"))

        ch_configs = [
            (0, True, -3.5),
            (1, True, 3.5),
            (2, False, 3.5),
            (3, False, -3.5),
        ]
        for k_off, is_left, y_off in ch_configs:
            k = k0 + k_off
            cy = uy + y_off
            if is_left:
                pcb.append(fp_resistor_0805(f"R_in_{k}", "10k", 15.0, cy, 0, "F.Cu", 10+k, f"V_SUM_{k}", 70+k, f"INV_{k}"))
                pcb.append(fp_diode_sod123(f"D1_{k}", "1N4148", 28.0, cy - 1.5, 0, "F.Cu", 50+k, f"OA_OUT_{k}", 70+k, f"INV_{k}"))
                pcb.append(fp_diode_sod123(f"D2_{k}", "1N4148", 28.0, cy + 1.5, 180, "F.Cu", 30+k, f"ACT_{k}", 50+k, f"OA_OUT_{k}"))
                pcb.append(fp_resistor_0805(f"Rf_{k}", "10k", 38.0, cy, 0, "F.Cu", 70+k, f"INV_{k}", 30+k, f"ACT_{k}"))
            else:
                pcb.append(fp_resistor_0805(f"R_in_{k}", "10k", 85.0, cy, 180, "F.Cu", 10+k, f"V_SUM_{k}", 70+k, f"INV_{k}"))
                pcb.append(fp_diode_sod123(f"D1_{k}", "1N4148", 72.0, cy - 1.5, 180, "F.Cu", 50+k, f"OA_OUT_{k}", 70+k, f"INV_{k}"))
                pcb.append(fp_diode_sod123(f"D2_{k}", "1N4148", 72.0, cy + 1.5, 0, "F.Cu", 30+k, f"ACT_{k}", 50+k, f"OA_OUT_{k}"))
                pcb.append(fp_resistor_0805(f"Rf_{k}", "10k", 62.0, cy, 180, "F.Cu", 70+k, f"INV_{k}", 30+k, f"ACT_{k}"))

    pcb.append(")")
    with open(BOARD_PATH, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated clean DC2 skeleton: {BOARD_PATH}")

    # Pre-route GND vias and escape stubs
    b = pcbnew.LoadBoard(BOARD_PATH)
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

    net_gnd = b.FindNet("GND")
    pitch = 1.27
    for u_idx in range(4):
        uy = u_y[u_idx]
        y_start = uy - (3 * pitch)
        # Pins 3 & 5 (GND)
        add_via(45.5, y_start + 2 * pitch, net_gnd)
        add_track(47.3, y_start + 2 * pitch, 45.5, y_start + 2 * pitch, pcbnew.F_Cu, net_gnd)
        add_via(45.5, y_start + 4 * pitch, net_gnd)
        add_track(47.3, y_start + 4 * pitch, 45.5, y_start + 4 * pitch, pcbnew.F_Cu, net_gnd)
        # Pins 10 & 12 (GND)
        add_via(54.5, y_start + 4 * pitch, net_gnd)
        add_track(52.7, y_start + 4 * pitch, 54.5, y_start + 4 * pitch, pcbnew.F_Cu, net_gnd)
        add_via(54.5, y_start + 2 * pitch, net_gnd)
        add_track(52.7, y_start + 2 * pitch, 54.5, y_start + 2 * pitch, pcbnew.F_Cu, net_gnd)

        # Bypass Caps GND
        add_via(45.0 + 1.6, uy - 5.5, net_gnd)
        add_track(45.0 + 0.95, uy - 5.5, 45.0 + 1.6, uy - 5.5, pcbnew.F_Cu, net_gnd)
        add_via(55.0 + 1.6, uy + 5.5, net_gnd)
        add_track(55.0 + 0.95, uy + 5.5, 55.0 + 1.6, uy + 5.5, pcbnew.F_Cu, net_gnd)

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(BOARD_PATH)

    # Export DSN and run Freerouting
    pcbnew.ExportSpecctraDSN(b, DSN_PATH)
    print(f"Exported DSN: {DSN_PATH}")

    cmd = [
        "/usr/bin/java", "-jar", JAR_PATH,
        "-de", DSN_PATH,
        "-do", SES_PATH,
        "--gui.enabled=false",
        "-mp", "150",
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
        print(f"[DC2 ReLU] DRC Result: {uncon} unconnected, {viols} errors")
        return uncon == 0 and viols == 0
    return False

if __name__ == "__main__":
    success = generate_dc2()
    print("DC2 Build Status:", "SUCCESS (0 ERRORS, 0 UNCONNECTED)" if success else "FAILED")
