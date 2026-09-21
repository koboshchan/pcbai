import os
import subprocess
import pcbnew
import time
import uuid
import json

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

board_path = os.path.join(WORKSPACE_DIR, "daughtercard2_relu_l1.kicad_pcb")
dsn_path = os.path.join(WORKSPACE_DIR, "daughtercard2_relu_l1.dsn")
ses_path = os.path.join(WORKSPACE_DIR, "daughtercard2_relu_l1.ses")
drc_path = os.path.join(WORKSPACE_DIR, "drc_daughtercard2_relu_l1.json")

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

def fp_diode_sod123(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="K", net2=0, net2_name="A"):
    silk = "F.SilkS" if layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    paste = "F.Paste" if layer == "F.Cu" else "B.Paste"
    mask = "F.Mask" if layer == "F.Cu" else "B.Mask"
    return f"""  (footprint "Diode_SMD:D_SOD-123" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Diode SMD SOD-123")
    (property "Reference" "{ref}" (at 0 -1.8 {rot}) (layer "{silk}") (effects (font (size 0.7 0.7) (thickness 0.1))))
    (property "Value" "{val}" (at 0 1.8 {rot}) (layer "{fab}") (effects (font (size 0.7 0.7) (thickness 0.1))))
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

def generate_dc2_skeleton():
    nets = [(0, ""), (1, "GND"), (2, "+12V"), (3, "-12V")]
    for k in range(16):
        nets.append((10 + k, f"V_SUM_{k}"))
        nets.append((30 + k, f"ACT_{k}"))
        nets.append((50 + k, f"OA_OUT_{k}"))
        nets.append((70 + k, f"INV_{k}"))

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets])

    # J_SLOT_A: Pins 1..16 = V_SUM_0..15, Pins 37..38 = +12V, -12V
    j_slot_a = {str(k+1): (10+k, f"V_SUM_{k}") for k in range(16)}
    for p in range(17, 37):
        j_slot_a[str(p)] = (0, "")
    j_slot_a["37"] = (2, "+12V")
    j_slot_a["38"] = (3, "-12V")
    j_slot_a["39"] = (1, "GND")
    j_slot_a["40"] = (1, "GND")

    # J_SLOT_B at (86.0, 94.0): Pins 1..16 = ACT_0..15, Pins 33..40 = GND
    j_slot_b = {str(k+1): (30+k, f"ACT_{k}") for k in range(16)}
    for p in range(17, 33):
        j_slot_b[str(p)] = (0, "")
    for p in range(33, 41):
        j_slot_b[str(p)] = (1, "GND")

    pcb = [
        f"""(kicad_pcb (version 20221018) (generator "analog_nn_pcb_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block (title "Daughtercard 2 - 16x Active Precision ReLU") (rev "v4.0 - Vertical Blade Direct Plug-In") (date "2026-09-12"))
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
        fp_header_2x20("J_SLOT_A", "Sums_0_15_In", 35.0, 94.0, 90, j_slot_a),
        fp_header_2x20("J_SLOT_B", "Act_0_15_Out", 86.0, 94.0, 90, j_slot_b),
    ]

    # 4 TL074 Op-Amps at Y = [20.0, 38.0, 56.0, 74.0], X = 60.0
    u_y = [20.0, 38.0, 56.0, 74.0]
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
        pcb.append(fp_soic14(f"U{u_idx+1}", "TL074", 60.0, uy, 0, "F.Cu", ic_nets))
        pcb.append(fp_capacitor_0805(f"C_U{u_idx+1}P", "0.1uF", 55.0, uy - 6.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
        pcb.append(fp_capacitor_0805(f"C_U{u_idx+1}N", "0.1uF", 65.0, uy + 6.5, 0, "F.Cu", 3, "-12V", 1, "GND"))

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
                pcb.append(fp_resistor_0805(f"R_in_{k}", "10k", 25.0, cy, 0, "F.Cu", 10+k, f"V_SUM_{k}", 70+k, f"INV_{k}"))
                pcb.append(fp_diode_sod123(f"D1_{k}", "1N4148", 38.0, cy - 1.5, 0, "F.Cu", 50+k, f"OA_OUT_{k}", 70+k, f"INV_{k}"))
                pcb.append(fp_diode_sod123(f"D2_{k}", "1N4148", 38.0, cy + 1.5, 180, "F.Cu", 30+k, f"ACT_{k}", 50+k, f"OA_OUT_{k}"))
                pcb.append(fp_resistor_0805(f"Rf_{k}", "10k", 48.0, cy, 0, "F.Cu", 70+k, f"INV_{k}", 30+k, f"ACT_{k}"))
            else:
                pcb.append(fp_resistor_0805(f"R_in_{k}", "10k", 95.0, cy, 180, "F.Cu", 10+k, f"V_SUM_{k}", 70+k, f"INV_{k}"))
                pcb.append(fp_diode_sod123(f"D1_{k}", "1N4148", 82.0, cy - 1.5, 180, "F.Cu", 50+k, f"OA_OUT_{k}", 70+k, f"INV_{k}"))
                pcb.append(fp_diode_sod123(f"D2_{k}", "1N4148", 82.0, cy + 1.5, 0, "F.Cu", 30+k, f"ACT_{k}", 50+k, f"OA_OUT_{k}"))
                pcb.append(fp_resistor_0805(f"Rf_{k}", "10k", 72.0, cy, 180, "F.Cu", 70+k, f"INV_{k}", 30+k, f"ACT_{k}"))

    pcb.append(")")
    with open(board_path, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated clean DC2 skeleton: {board_path}")

def prepare_dc2_gnd():
    b = pcbnew.LoadBoard(board_path)
    for t in list(b.GetTracks()):
        b.Delete(t)

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
    u_y = [20.0, 38.0, 56.0, 74.0]
    pitch = 1.27

    for u_idx in range(4):
        uy = u_y[u_idx]
        y_start = uy - (3 * pitch)
        # Pins 3, 5: X = 57.3. Via outward at X = 55.5
        add_via(55.5, y_start + 2 * pitch, net_gnd)
        add_track(57.3, y_start + 2 * pitch, 55.5, y_start + 2 * pitch, pcbnew.F_Cu, net_gnd)
        add_via(55.5, y_start + 4 * pitch, net_gnd)
        add_track(57.3, y_start + 4 * pitch, 55.5, y_start + 4 * pitch, pcbnew.F_Cu, net_gnd)
        # Pins 10, 12: X = 62.7. Via outward at X = 64.5
        add_via(64.5, y_start + 4 * pitch, net_gnd)
        add_track(62.7, y_start + 4 * pitch, 64.5, y_start + 4 * pitch, pcbnew.F_Cu, net_gnd)
        add_via(64.5, y_start + 2 * pitch, net_gnd)
        add_track(62.7, y_start + 2 * pitch, 64.5, y_start + 2 * pitch, pcbnew.F_Cu, net_gnd)

        # Caps GND
        # C_U_P at (55.0, uy - 6.5), Pad 2 (GND) at (55.95, uy - 6.5)
        # Place GND via eastward at (57.2, uy - 6.5) away from Pad 1 (+12V)
        add_via(57.2, uy - 6.5, net_gnd)
        add_track(55.95, uy - 6.5, 57.2, uy - 6.5, pcbnew.F_Cu, net_gnd)
        # C_U_N at (65.0, uy + 6.5), Pad 2 (GND) at (65.95, uy + 6.5)
        # Place GND via eastward at (67.2, uy + 6.5) away from Pad 1 (-12V)
        add_via(67.2, uy + 6.5, net_gnd)
        add_track(65.95, uy + 6.5, 67.2, uy + 6.5, pcbnew.F_Cu, net_gnd)

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(board_path)
    print("GND vias placed and zone filled on DC2.")

def route_dc2_freerouting():
    b = pcbnew.LoadBoard(board_path)
    pcbnew.ExportSpecctraDSN(b, dsn_path)
    print(f"Exported DSN: {dsn_path}")

    cmd = [
        "/usr/bin/java", "-jar", JAR_PATH,
        "-de", dsn_path,
        "-do", ses_path,
        "--gui.enabled=false",
        "-mp", "100",
        "-mt", "1"
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Freerouting finished in {time.time()-t0:.1f}s, exit code: {res.returncode}")

    if os.path.exists(ses_path):
        b = pcbnew.LoadBoard(board_path)
        pcbnew.ImportSpecctraSES(b, ses_path)
        filler = pcbnew.ZONE_FILLER(b)
        filler.Fill(b.Zones())
        b.Save(board_path)

        cmd_drc = f"{KICAD_CLI} pcb drc --severity-error --output {drc_path} --format json {board_path}"
        os.system(cmd_drc)
        with open(drc_path) as f:
            d = json.load(f)
        uncon = len(d.get("unconnected_items", []))
        viols = len(d.get("violations", []))
        print(f"[Daughtercard 2] DRC Result: {uncon} unconnected, {viols} errors")
        return uncon == 0 and viols == 0
    return False

if __name__ == "__main__":
    generate_dc2_skeleton()
    prepare_dc2_gnd()
    route_dc2_freerouting()
