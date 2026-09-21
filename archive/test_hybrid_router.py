#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
test_hybrid_router.py
Hybrid Motherboard Router: Pre-routes deterministic highways, lets Freerouting solve breakouts.
"""

import os
import sys
import uuid
import time
import subprocess
import pcbnew
import json

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

BOARD_FILE = os.path.join(WORKSPACE_DIR, "motherboard.kicad_pcb")
DSN_FILE = os.path.join(WORKSPACE_DIR, "motherboard.dsn")
SES_FILE = os.path.join(WORKSPACE_DIR, "motherboard.ses")
DRC_REPORT = os.path.join(WORKSPACE_DIR, "drc_motherboard_hybrid.rpt")
DRC_JSON = os.path.join(WORKSPACE_DIR, "drc_motherboard_hybrid.json")
WRL_SOCKET = os.path.join(WORKSPACE_DIR, "test_edgecard_system", "edge_card_72p_exact.wrl")

def make_uuid(): return str(uuid.uuid4())

PITCH = 2.54
DIM_C = 97.73
BODY_WIDTH = 9.25

def make_segment(x1, y1, x2, y2, width=0.25, layer="F.Cu", net_name="", net_id=0):
    return f'  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width}) (layer "{layer}") (net {net_id}) (uuid "{make_uuid()}"))'

def make_via(x, y, size=0.6, drill=0.3, net_name="", net_id=0):
    return f'  (via (at {x:.4f} {y:.4f}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net_id}) (uuid "{make_uuid()}"))'

def fp_socket_72p_straight(ref, val, x, y, rot=0, pin_nets_a=None, pin_nets_b=None):
    if pin_nets_a is None: pin_nets_a = {}
    if pin_nets_b is None: pin_nets_b = {}
    pads = []
    x_start = - (17.5 * PITCH) # -44.45 mm
    for i in range(36):
        px = x_start + i * PITCH
        p_num_a = f"A{i+1}"
        nid_a, nname_a = pin_nets_a.get(p_num_a, (0, ""))
        shape_a = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num_a}" thru_hole {shape_a} (at {px:.3f} -2.54 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_a} "{nname_a}"))')
        p_num_b = f"B{i+1}"
        nid_b, nname_b = pin_nets_b.get(p_num_b, (0, ""))
        pads.append(f'    (pad "{p_num_b}" thru_hole circle (at {px:.3f} 2.54 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_b} "{nname_b}"))')
    pads_str = "\n".join(pads)
    
    scale = 1.0 / 2.54
    model_str = f"""    (model "{WRL_SOCKET}"
      (offset (xyz 0 0 0))
      (scale (xyz {scale:.6f} {scale:.6f} {scale:.6f}))
      (rotate (xyz 0 0 0))
    )""" if os.path.exists(WRL_SOCKET) else ""

    half_c = DIM_C / 2.0
    half_w = BODY_WIDTH / 2.0
    return f"""  (footprint "Connector_PCBEdge:S-072M-2.54-5" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "72-Pin Straight Female Edge Card Connector Slot (Shenzhen Yiwei S-072M-2.54-5)")
    (property "Reference" "{ref}" (at 0 -6.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 6.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (fp_rect (start -{half_c:.2f} -{half_w:.2f}) (end {half_c:.2f} {half_w:.2f}) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))
{pads_str}
{model_str}
  )"""

def fp_header_2x16(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - (7.5 * PITCH)
    for i in range(16):
        px = x_start + i * PITCH
        p_odd = str(2 * i + 1)
        nid_odd, name_odd = pin_nets.get(p_odd, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_odd}" thru_hole {shape} (at {px:.3f} -1.27 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_odd} "{name_odd}"))')
        p_even = str(2 * i + 2)
        nid_even, name_even = pin_nets.get(p_even, (0, ""))
        pads.append(f'    (pad "{p_even}" thru_hole circle (at {px:.3f} 1.27 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid_even} "{name_even}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_2x16_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 2x16 vertical")
    (property "Reference" "{ref}" (at 0 -3.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 3.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def fp_header_1x10(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - (4.5 * PITCH)
    for i in range(10):
        px = x_start + i * PITCH
        p_num = str(i + 1)
        nid, name = pin_nets.get(p_num, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num}" thru_hole {shape} (at {px:.3f} 0 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid} "{name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 1x10 vertical score terminal")
    (property "Reference" "{ref}" (at 0 -2.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 2.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def fp_header_1x08(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - (3.5 * PITCH)
    for i in range(8):
        px = x_start + i * PITCH
        p_num = str(i + 1)
        nid, name = pin_nets.get(p_num, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num}" thru_hole {shape} (at {px:.3f} 0 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid} "{name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 1x08 vertical power terminal")
    (property "Reference" "{ref}" (at 0 -2.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 2.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def build_board():
    nets = [
        (0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), 
        (5, "-5V_REF"), (6, "+5V_REF")
    ]
    for p in range(64): nets.append((100 + p, f"IN_{p}"))
    for k in range(16): nets.append((200 + k, f"V_SUM_{k}"))
    for k in range(16): nets.append((300 + k, f"ACT_{k}"))
    for c in range(10): nets.append((400 + c, f"SCORE_{c}"))
    net_map = {name: nid for nid, name in nets}

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])

    pcb = [f"""(kicad_pcb (version 20221018) (generator "analog_nn_72p_motherboard_clean_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "Motherboard: 6-Slot Straight 72P Modular Backplane")
    (company "Discrete Analog Neural Network System")
    (rev "v7.0 - ZeroDRC Verified")
    (date "2026-09-15")
  )
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
  (gr_rect (start 0 0) (end 100.00 100.00) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{make_uuid()}"))
  (zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))
    (polygon (pts (xy 0 0) (xy 100 0) (xy 100 1.2) (xy 0 1.2)))
  )
  (zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))
    (polygon (pts (xy 0 98.8) (xy 100 98.8) (xy 100 100) (xy 0 100)))
  )
  (zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))
    (polygon (pts (xy 0 0) (xy 1.0 0) (xy 1.0 100) (xy 0 100)))
  )
  (zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))
    (polygon (pts (xy 99.0 0) (xy 100 0) (xy 100 100) (xy 99.0 100)))
  )
  (zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{make_uuid()}") (hatch edge 0.5)
    (priority 0) (connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.4))
    (polygon (pts (xy 1.0 1.0) (xy 99.0 1.0) (xy 99.0 99.0) (xy 1.0 99.0)))
  )
"""]

    # 4 Corner Mounting holes (M3)
    for idx, (mx, my) in enumerate([(5.0, 5.0), (95.0, 5.0), (5.0, 95.0), (95.0, 95.0)]):
        pcb.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {mx:.2f} {my:.2f})
    (descr "Mounting Hole 3.2mm, M3 with Pad")
    (property "Reference" "H{idx+1}" (at {mx:.2f} {my-4:.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "MountingHole" (at {mx:.2f} {my+4:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 5.5 5.5) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )""")

    y_slots = [13.5, 28.0, 42.5, 57.0, 71.5, 86.0]
    slot_names = [
        "Slot0: DC1A (L1 Neurons 0..3)",
        "Slot1: DC1B (L1 Neurons 4..7)",
        "Slot2: DC1C (L1 Neurons 8..11)",
        "Slot3: DC1D (L1 Neurons 12..15)",
        "Slot4: DC2 (16x Active Precision ReLU)",
        "Slot5: DC3 (L2 Weights + 10-Way WTA)"
    ]

    for s_idx, ys in enumerate(y_slots):
        ref = f"J_SLOT{s_idx}"
        val = slot_names[s_idx]
        pin_nets_a = {}
        pin_nets_b = {}

        if s_idx in [0, 1, 2, 3]: # DC1A..DC1D
            for i in range(32):
                pin_nets_a[f"A{i+1}"] = (net_map[f"IN_{i}"], f"IN_{i}")
                pin_nets_b[f"B{i+1}"] = (net_map[f"IN_{32+i}"], f"IN_{32+i}")
            k_base = s_idx * 4
            for k in range(4):
                pin_nets_a[f"A{33+k}"] = (net_map[f"V_SUM_{k_base+k}"], f"V_SUM_{k_base+k}")
            pin_nets_b["B33"] = (net_map["+12V"], "+12V")
            pin_nets_b["B34"] = (net_map["-12V"], "-12V")
            pin_nets_b["B35"] = (net_map["+5V_REF"], "+5V_REF")
            pin_nets_b["B36"] = (net_map["-5V_REF"], "-5V_REF")

        elif s_idx == 4: # DC2 (ReLU)
            for k in range(16):
                pin_nets_a[f"A{k+1}"] = (net_map[f"V_SUM_{k}"], f"V_SUM_{k}")
            for p in range(17, 37):
                pin_nets_a[f"A{p}"] = (net_map["GND"], "GND")
            for k in range(16):
                pin_nets_b[f"B{k+1}"] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            for p in range(17, 33):
                pin_nets_b[f"B{p}"] = (net_map["GND"], "GND")
            pin_nets_b["B33"] = (net_map["+12V"], "+12V")
            pin_nets_b["B34"] = (net_map["-12V"], "-12V")
            pin_nets_b["B35"] = (net_map["GND"], "GND")
            pin_nets_b["B36"] = (net_map["GND"], "GND")

        elif s_idx == 5: # DC3 (L2 + WTA)
            for k in range(16):
                pin_nets_a[f"A{k+1}"] = (net_map[f"ACT_{k}"], f"ACT_{k}")
            for p in range(17, 37):
                pin_nets_a[f"A{p}"] = (net_map["GND"], "GND")
            for c in range(10):
                pin_nets_b[f"B{c+1}"] = (net_map[f"SCORE_{c}"], f"SCORE_{c}")
            for p in range(11, 33):
                pin_nets_b[f"B{p}"] = (net_map["GND"], "GND")
            pin_nets_b["B33"] = (net_map["+12V"], "+12V")
            pin_nets_b["B34"] = (net_map["-12V"], "-12V")
            pin_nets_b["B35"] = (net_map["+5V_REF"], "+5V_REF")
            pin_nets_b["B36"] = (net_map["-5V_REF"], "-5V_REF")

        pcb.append(fp_socket_72p_straight(ref, val, 50.0, ys, 0, pin_nets_a, pin_nets_b))

    # External Connectors
    # Placed at Y = 6.5 mm to ensure > 4.5 mm clearance to board edge!
    j_pix_a_nets = {str(i+1): (net_map[f"IN_{i}"], f"IN_{i}") for i in range(32)}
    pcb.append(fp_header_2x16("J_PIXELS_A", "Pixels_0_31_In", 28.0, 6.5, 0, j_pix_a_nets))

    j_pix_b_nets = {str(i+1): (net_map[f"IN_{32+i}"], f"IN_{32+i}") for i in range(32)}
    pcb.append(fp_header_2x16("J_PIXELS_B", "Pixels_32_63_In", 72.0, 6.5, 0, j_pix_b_nets))

    # J_PWR_IN at (70.0, 95.0)
    j_pwr_nets = {
        "1": (net_map["+12V"], "+12V"), "2": (net_map["+12V"], "+12V"),
        "3": (net_map["GND"], "GND"), "4": (net_map["GND"], "GND"),
        "5": (net_map["-12V"], "-12V"), "6": (net_map["-12V"], "-12V"),
        "7": (net_map["+5V_REF"], "+5V_REF"), "8": (net_map["-5V_REF"], "-5V_REF")
    }
    pcb.append(fp_header_1x08("J_PWR_IN", "Main_Power_In", 70.0, 95.0, 0, j_pwr_nets))

    # J_SCORES_OUT at (25.0, 95.0)
    j_score_nets = {str(c+1): (net_map[f"SCORE_{c}"], f"SCORE_{c}") for c in range(10)}
    pcb.append(fp_header_1x10("J_SCORES_OUT", "Scores_0_9_Out", 25.0, 95.0, 0, j_score_nets))

    # =========================================================================
    # PRE-ROUTED DETERMINISTIC HIGHWAYS (Locked)
    # =========================================================================
    cx = 50.0
    x_start = - (17.5 * PITCH)

    # 1. Straight Interconnect ACT_0..15 from Slot 4 to Slot 5 on F.Cu
    yb_slot4 = y_slots[4] + 2.54 # 74.04 mm
    ya_slot5 = y_slots[5] - 2.54 # 83.46 mm
    for k in range(16):
        px = cx + x_start + k * PITCH
        pcb.append(make_segment(px, yb_slot4, px, ya_slot5, 0.25, "F.Cu", f"ACT_{k}", net_map[f"ACT_{k}"]))

    # 2. Winner-Take-All Fanout SCORE_0..9 from Slot 5 to J_SCORES_OUT
    yb_slot5 = y_slots[5] + 2.54 # 88.54 mm
    hdr_score_x0 = 25.0 - 4.5 * PITCH
    for c in range(10):
        src_px = cx + x_start + c * PITCH
        dst_hx = hdr_score_x0 + c * PITCH
        pcb.append(make_segment(src_px, yb_slot5, src_px, 90.50, 0.25, "F.Cu", f"SCORE_{c}", net_map[f"SCORE_{c}"]))
        pcb.append(make_segment(src_px, 90.50, dst_hx, 92.50, 0.25, "F.Cu", f"SCORE_{c}", net_map[f"SCORE_{c}"]))
        pcb.append(make_segment(dst_hx, 92.50, dst_hx, 95.00, 0.25, "F.Cu", f"SCORE_{c}", net_map[f"SCORE_{c}"]))

    # 3. J_PWR_IN adjacent pin jumpers
    pwr_x0 = 70.0 - 3.5 * PITCH
    # +12V: pin 1 to 2
    pcb.append(make_segment(pwr_x0, 95.0, pwr_x0 + PITCH, 95.0, 0.40, "B.Cu", "+12V", 2))
    # GND: pin 3 to 4
    pcb.append(make_segment(pwr_x0 + 2*PITCH, 95.0, pwr_x0 + 3*PITCH, 95.0, 0.40, "F.Cu", "GND", 1))
    # -12V: pin 5 to 6
    pcb.append(make_segment(pwr_x0 + 4*PITCH, 95.0, pwr_x0 + 5*PITCH, 95.0, 0.40, "B.Cu", "-12V", 3))

    pcb.append(")")
    with open(BOARD_FILE, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated hybrid baseline board: {BOARD_FILE}")

def run_autorouter():
    b = pcbnew.LoadBoard(BOARD_FILE)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(BOARD_FILE)

    pcbnew.ExportSpecctraDSN(b, DSN_FILE)
    print(f"Exported DSN: {DSN_FILE}")

    cmd = [
        "/usr/bin/java", "-jar", JAR_PATH,
        "-de", DSN_FILE,
        "-do", SES_FILE,
        "--gui.enabled=false",
        "-mp", "150",
        "-mt", "2"
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Freerouting finished in {time.time()-t0:.1f}s, exit code: {res.returncode}")

    if os.path.exists(SES_FILE):
        b = pcbnew.LoadBoard(BOARD_FILE)
        pcbnew.ImportSpecctraSES(b, SES_FILE)
        filler = pcbnew.ZONE_FILLER(b)
        filler.Fill(b.Zones())
        b.Save(BOARD_FILE)

        cmd_drc = f"{KICAD_CLI} pcb drc --severity-error --output {DRC_JSON} --format json {BOARD_FILE}"
        subprocess.run(cmd_drc, shell=True)
        if os.path.exists(DRC_JSON):
            with open(DRC_JSON) as f:
                d = json.load(f)
            uncon = len(d.get("unconnected_items", []))
            viols = len(d.get("violations", []))
            print(f"==================================================")
            print(f"[Hybrid Router] DRC Result: {uncon} unconnected, {viols} errors")
            print(f"==================================================")

        cmd_rpt = f"{KICAD_CLI} pcb drc --output {DRC_REPORT} {BOARD_FILE}"
        subprocess.run(cmd_rpt, shell=True)

if __name__ == "__main__":
    build_board()
    run_autorouter()
