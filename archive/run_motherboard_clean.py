#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
import os
import sys
import subprocess
import pcbnew
import time
import uuid
import json

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

BOARD_PATH = os.path.join(WORKSPACE_DIR, "motherboard.kicad_pcb")
DSN_PATH = os.path.join(WORKSPACE_DIR, "motherboard.dsn")
SES_PATH = os.path.join(WORKSPACE_DIR, "motherboard.ses")
DRC_PATH = os.path.join(WORKSPACE_DIR, "drc_motherboard.json")

def make_uuid(): return str(uuid.uuid4())
def mm(v): return int(v * 1000000)

def fp_socket_2x20(ref, val, x, y, rot=0, pin_nets=None):
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
    return f"""  (footprint "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Socket 2.54mm 2x20 vertical backplane slot")
    (property "Reference" "{ref}" (at 0 -27.0 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 27.0 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
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
    (descr "Pin Header 2.54mm 2x20 vertical input connector")
    (property "Reference" "{ref}" (at 0 -27.0 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 27.0 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def fp_header_2x05(ref, val, x, y, rot=0, pin_nets=None):
    pads = []
    pitch = 2.54
    y_start = - (2.0 * pitch)
    for i in range(5):
        py = y_start + i * pitch
        pin_odd = str(2 * i + 1)
        pin_even = str(2 * i + 2)
        n_odd_id, n_odd_name = pin_nets.get(pin_odd, (0, "")) if pin_nets else (0, "")
        n_even_id, n_even_name = pin_nets.get(pin_even, (0, "")) if pin_nets else (0, "")
        pads.append(f'    (pad "{pin_odd}" thru_hole circle (at -1.27 {py:.3f} {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {n_odd_id} "{n_odd_name}"))')
        pads.append(f'    (pad "{pin_even}" thru_hole oval (at 1.27 {py:.3f} {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {n_even_id} "{n_even_name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 2x05 vertical")
    (property "Reference" "{ref}" (at 0 -8.0 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 8.0 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def generate_skeleton():
    nets = [(0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), (4, "+5V"), (5, "+5V_REF"), (6, "-5V_REF")]
    for p in range(64):
        nets.append((100 + p, f"IN_{p}"))
    for k in range(16):
        nets.append((200 + k, f"V_SUM_{k}"))
    for k in range(16):
        nets.append((300 + k, f"ACT_{k}"))
    for k in range(10):
        nets.append((400 + k, f"SCORE_{k}"))

    net_map = {name: nid for nid, name in nets}
    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])

    slots_pcb = []
    y_slots_a = [12.00, 26.00, 40.00, 54.00, 68.00, 82.00]

    for slot_idx, ya in enumerate(y_slots_a):
        yb = ya + 7.62
        sock_a_nets = {}
        if slot_idx in [0, 1, 2, 3]: # DC1A..DC1D
            for p in range(32):
                sock_a_nets[str(p+1)] = (net_map[f"IN_{p}"], f"IN_{p}")
            k0 = slot_idx * 4
            for k in range(4):
                sock_a_nets[str(33+k)] = (net_map[f"V_SUM_{k0+k}"], f"V_SUM_{k0+k}")
            sock_a_nets["37"] = (net_map["+12V"], "+12V")
            sock_a_nets["38"] = (net_map["-12V"], "-12V")
            sock_a_nets["39"] = (net_map["+5V_REF"], "+5V_REF")
            sock_a_nets["40"] = (net_map["-5V_REF"], "-5V_REF")
        elif slot_idx == 4: # DC2 (ReLU)
            for k in range(16):
                sock_a_nets[str(k+1)] = (net_map[f"V_SUM_{k}"], f"V_SUM_{k}")
            for p in range(17, 37): sock_a_nets[str(p)] = (0, "")
            sock_a_nets["37"] = (net_map["+12V"], "+12V")
            sock_a_nets["38"] = (net_map["-12V"], "-12V")
            sock_a_nets["39"] = (net_map["GND"], "GND")
            sock_a_nets["40"] = (net_map["GND"], "GND")
        elif slot_idx == 5: # DC3 (L2 + WTA)
            for k in range(16):
                sock_a_nets[str(k+1)] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            for p in range(17, 33): sock_a_nets[str(p)] = (0, "")
            sock_a_nets["33"] = (net_map["+5V_REF"], "+5V_REF")
            sock_a_nets["34"] = (net_map["-5V_REF"], "-5V_REF")
            sock_a_nets["35"] = (net_map["+5V"], "+5V")
            sock_a_nets["36"] = (net_map["GND"], "GND")
            sock_a_nets["37"] = (net_map["+12V"], "+12V")
            sock_a_nets["38"] = (net_map["-12V"], "-12V")
            sock_a_nets["39"] = (net_map["GND"], "GND")
            sock_a_nets["40"] = (net_map["GND"], "GND")

        slots_pcb.append(fp_socket_2x20(f"J_SLOT{slot_idx}_A", f"Slot{slot_idx}_A", 50.0, ya, 90, sock_a_nets))

        sock_b_nets = {}
        if slot_idx in [0, 1, 2, 3]: # DC1A..DC1D
            for p in range(32):
                sock_b_nets[str(p+1)] = (net_map[f"IN_{32+p}"], f"IN_{32+p}")
            for p in range(33, 41):
                sock_b_nets[str(p)] = (net_map["GND"], "GND")
        elif slot_idx == 4: # DC2 (ReLU)
            for k in range(16):
                sock_b_nets[str(k+1)] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            for p in range(17, 33): sock_b_nets[str(p)] = (0, "")
            for p in range(33, 41): sock_b_nets[str(p)] = (net_map["GND"], "GND")
        elif slot_idx == 5: # DC3 (L2 + WTA)
            for k in range(10):
                sock_b_nets[str(k+1)] = (net_map[f"SCORE_{k}"], f"SCORE_{k}")
            for p in range(11, 33): sock_b_nets[str(p)] = (0, "")
            for p in range(33, 41): sock_b_nets[str(p)] = (net_map["GND"], "GND")

        slots_pcb.append(fp_socket_2x20(f"J_SLOT{slot_idx}_B", f"Slot{slot_idx}_B", 50.0, yb, 90, sock_b_nets))

    j_pix_a_nets = {str(p+1): (net_map[f"IN_{p}"], f"IN_{p}") for p in range(32)}
    for p in range(33, 41): j_pix_a_nets[str(p)] = (net_map["GND"], "GND")
    j_pix_a = fp_header_2x20("J_PIXELS_A", "Pixels_0_31_In", 12.0, 50.0, 0, j_pix_a_nets)

    j_pix_b_nets = {str(p+1): (net_map[f"IN_{32+p}"], f"IN_{32+p}") for p in range(32)}
    for p in range(33, 41): j_pix_b_nets[str(p)] = (net_map["GND"], "GND")
    j_pix_b = fp_header_2x20("J_PIXELS_B", "Pixels_32_63_In", 88.0, 50.0, 0, j_pix_b_nets)

    j_pwr_nets = {
        "1": (net_map["+12V"], "+12V"), "2": (net_map["-12V"], "-12V"),
        "3": (net_map["+5V"], "+5V"), "4": (net_map["GND"], "GND"),
        "5": (net_map["+5V_REF"], "+5V_REF"), "6": (net_map["-5V_REF"], "-5V_REF"),
        "7": (net_map["GND"], "GND"), "8": (net_map["GND"], "GND"),
        "9": (net_map["GND"], "GND"), "10": (net_map["GND"], "GND")
    }
    j_pwr = fp_header_2x05("J_PWR_IN", "Main_Power_In", 12.0, 10.0, 0, j_pwr_nets)

    j_out_nets = {str(k+1): (net_map[f"SCORE_{k}"], f"SCORE_{k}") for k in range(10)}
    j_out = fp_header_2x05("J_OUT_SCORES", "L2_Scores_Out", 88.0, 90.0, 0, j_out_nets)

    pcb = [
        f"""(kicad_pcb (version 20221018) (generator "analog_nn_100x100_motherboard_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block (title "Analog Neural Network - 6-Slot Modular Backplane") (rev "v5.0 - 100x100mm 4-Layer Modular Stack") (date "2026-09-12"))
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
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at 4.0 96.0) (descr "M3 Mounting Hole") (property "Reference" "H3" (at 0 -4.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu") (uuid "{make_uuid()}")
    (at 96.0 96.0) (descr "M3 Mounting Hole") (property "Reference" "H4" (at 0 -4.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )
""",
        j_pix_a, j_pix_b, j_pwr, j_out,
        *slots_pcb,
        ")"
    ]

    with open(BOARD_PATH, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated clean Motherboard skeleton: {BOARD_PATH}")

def run_routing_flow():
    generate_skeleton()

    b = pcbnew.LoadBoard(BOARD_PATH)

    # Set netclass rules: 0.20 mm width, 0.16 mm clearance
    ns = b.GetDesignSettings().m_NetSettings
    nc = ns.GetDefaultNetclass()
    nc.SetTrackWidth(200000)
    nc.SetClearance(160000)
    b.GetDesignSettings().m_TrackMinWidth = 150000

    # Pre-route ACT_0..15 from Slot 4B (Y=75.62) to Slot 5A (Y=82.00) on F.Cu
    pitch = 2.54
    x_start = 50.0 - 9.5 * pitch
    for k in range(16):
        i = k // 2
        xi = x_start + i * pitch
        is_odd = (k % 2 == 0)
        y_s4 = 75.62 + (1.27 if is_odd else -1.27)
        y_s5 = 82.00 + (1.27 if is_odd else -1.27)
        net_act = b.FindNet(f"ACT_{k}")
        trk = pcbnew.PCB_TRACK(b)
        trk.SetStart(pcbnew.VECTOR2I(mm(xi), mm(y_s4)))
        trk.SetEnd(pcbnew.VECTOR2I(mm(xi), mm(y_s5)))
        trk.SetWidth(mm(0.20))
        trk.SetLayer(pcbnew.F_Cu)
        trk.SetNet(net_act)
        b.Add(trk)

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
        "-mp", "300",
        "-mt", "2"
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Freerouting finished in {time.time()-t0:.1f}s, exit code: {res.returncode}")

    if os.path.exists(SES_PATH):
        # Load fresh board to avoid SWIG reference reuse
        b_final = pcbnew.LoadBoard(BOARD_PATH)
        pcbnew.ImportSpecctraSES(b_final, SES_PATH)
        filler_final = pcbnew.ZONE_FILLER(b_final)
        filler_final.Fill(b_final.Zones())
        b_final.Save(BOARD_PATH)

        cmd_drc = f"{KICAD_CLI} pcb drc --severity-error --output {DRC_PATH} --format json {BOARD_PATH}"
        subprocess.run(cmd_drc, shell=True)
        with open(DRC_PATH) as f:
            d = json.load(f)
        uncon = len(d.get("unconnected_items", []))
        viols = len(d.get("violations", []))
        print(f"[Motherboard Backplane] DRC Result: {uncon} unconnected, {viols} errors")
        return uncon == 0 and viols == 0
    return False

if __name__ == "__main__":
    success = run_routing_flow()
    print("Motherboard Clean Flow Status:", "SUCCESS" if success else "FAILED")
    sys.exit(0 if success else 1)
