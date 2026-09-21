#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
generate_motherboard_v8_mcu.py
Motherboard Backplane with Integrated 8x 74HC595D Shift Registers & 10-Ch Voltage Dividers.
100% Face-Side (F.Cu) Component Placement, 100mm x 100mm Form Factor.
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
DRC_REPORT = os.path.join(WORKSPACE_DIR, "drc_motherboard.rpt")
DRC_JSON = os.path.join(WORKSPACE_DIR, "drc_motherboard.json")
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

def fp_soic16(ref, val, x, y, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    for i in range(8):
        # Left side: Pins 1..8
        p_l = str(i + 1)
        nid_l, name_l = pin_nets.get(p_l, (0, ""))
        py_l = -4.445 + i * 1.27
        pads.append(f'    (pad "{p_l}" smd roundrect (at -2.70 {py_l:.3f}) (size 1.55 0.6) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.25) (net {nid_l} "{name_l}"))')
        
        # Right side: Pins 16..9
        p_r = str(16 - i)
        nid_r, name_r = pin_nets.get(p_r, (0, ""))
        py_r = -4.445 + i * 1.27
        pads.append(f'    (pad "{p_r}" smd roundrect (at 2.70 {py_r:.3f}) (size 1.55 0.6) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.25) (net {nid_r} "{name_r}"))')
    pads_str = "\n".join(pads)

    model_str = f"""    (model "${{KICAD8_3DMODEL_DIR}}/Package_SO.3dshapes/SOIC-16_3.9x9.9mm_P1.27mm.step"
      (offset (xyz 0 0 0))
      (scale (xyz 1 1 1))
      (rotate (xyz 0 0 0))
    )"""

    return f"""  (footprint "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "16-lead SOIC 3.9x9.9mm 1.27mm pitch")
    (property "Reference" "{ref}" (at 0 -5.8 {rot}) (layer "F.SilkS") (effects (font (size 0.9 0.9) (thickness 0.13))))
    (property "Value" "{val}" (at 0 5.8 {rot}) (layer "F.Fab") (effects (font (size 0.9 0.9) (thickness 0.13))))
    (fp_line (start -2.0 -5.0) (end 2.0 -5.0) (stroke (width 0.12) (type default)) (layer "F.SilkS"))
    (fp_line (start -2.0 5.0) (end 2.0 5.0) (stroke (width 0.12) (type default)) (layer "F.SilkS"))
    (fp_circle (center -3.0 -4.5) (end -2.8 -4.5) (stroke (width 0.15) (type default)) (fill solid) (layer "F.SilkS"))
{pads_str}
{model_str}
  )"""

def fp_resistor_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    model_str = f"""    (model "${{KICAD8_3DMODEL_DIR}}/Resistor_SMD.3dshapes/R_0805_2012Metric.step"
      (offset (xyz 0 0 0))
      (scale (xyz 1 1 1))
      (rotate (xyz 0 0 0))
    )"""
    return f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Resistor SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.11))))
    (property "Value" "{val}" (at 0 1.5) (layer "F.Fab") (effects (font (size 0.7 0.7) (thickness 0.11))))
    (fp_rect (start -1 -0.6) (end 1 0.6) (stroke (width 0.12) (type default)) (fill none) (layer "F.SilkS"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "{layer}" "{layer[0]}.Mask") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "{layer}" "{layer[0]}.Mask") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
{model_str}
  )"""

def fp_cap_0805(ref, val, x, y, rot=0, layer="F.Cu", net1=0, net1_name="", net2=0, net2_name=""):
    model_str = f"""    (model "${{KICAD8_3DMODEL_DIR}}/Capacitor_SMD.3dshapes/C_0805_2012Metric.step"
      (offset (xyz 0 0 0))
      (scale (xyz 1 1 1))
      (rotate (xyz 0 0 0))
    )"""
    return f"""  (footprint "Capacitor_SMD:C_0805_2012Metric" (layer "{layer}")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Capacitor SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.11))))
    (property "Value" "{val}" (at 0 1.5) (layer "F.Fab") (effects (font (size 0.7 0.7) (thickness 0.11))))
    (fp_rect (start -1 -0.6) (end 1 0.6) (stroke (width 0.12) (type default)) (fill none) (layer "F.SilkS"))
    (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "{layer}" "{layer[0]}.Mask") (roundrect_rratio 0.25) (net {net1} "{net1_name}"))
    (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "{layer}" "{layer[0]}.Mask") (roundrect_rratio 0.25) (net {net2} "{net2_name}"))
{model_str}
  )"""

def fp_header_1x(ref, val, x, y, pin_count, rot=0, pin_nets=None):
    if pin_nets is None: pin_nets = {}
    pads = []
    x_start = - ((pin_count - 1) / 2.0 * PITCH)
    for i in range(pin_count):
        px = x_start + i * PITCH
        p_num = str(i + 1)
        nid, name = pin_nets.get(p_num, (0, ""))
        shape = "rect" if i == 0 else "circle"
        pads.append(f'    (pad "{p_num}" thru_hole {shape} (at {px:.3f} 0 {rot}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {nid} "{name}"))')
    pads_str = "\n".join(pads)
    return f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x{pin_count:02d}_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.3f} {y:.3f} {rot})
    (descr "Pin Header 2.54mm 1x{pin_count:02d} vertical")
    (property "Reference" "{ref}" (at 0 -2.5 {rot}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{val}" (at 0 2.5 {rot}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{pads_str}
  )"""

def build_board():
    nets = [
        (0, ""), (1, "GND"), (2, "+12V"), (3, "-12V"), 
        (5, "-5V_REF"), (6, "+5V_REF"), (7, "+5V"),
        (8, "SPI_MOSI"), (9, "SPI_SCK"), (10, "SPI_LATCH"), (11, "SPI_OE")
    ]
    for c in range(1, 8): nets.append((11 + c, f"SR_CHAIN_{c}"))
    for p in range(64): nets.append((100 + p, f"IN_{p}"))
    for k in range(16): nets.append((200 + k, f"V_SUM_{k}"))
    for k in range(16): nets.append((300 + k, f"ACT_{k}"))
    for c in range(10): nets.append((400 + c, f"SCORE_{c}"))
    for c in range(10): nets.append((500 + c, f"SCORE_DIV_{c}"))
    net_map = {name: nid for nid, name in nets}

    net_lines = "\n".join([f'  (net {nid} "{name}")' for nid, name in nets if nid > 0])

    pcb = [f"""(kicad_pcb (version 20221018) (generator "analog_nn_72p_motherboard_v8_generator")
  (general (thickness 1.6))
  (paper "A4")
  (title_block
    (title "Motherboard: 6-Slot 72P Backplane with Integrated 74HC595 & Output Voltage Dividers")
    (company "Discrete Analog Neural Network System")
    (rev "v8.0 - Integrated MCU Interface")
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

    # Compacted 6 Slots: 11.0mm pitch starting at Y = 32.0 mm
    y_slots = [32.0, 43.0, 54.0, 65.0, 76.0, 87.0]
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

    # =========================================================================
    # TOP SECTION: 8x 74HC595D Shift Registers & MCU SPI Header
    # =========================================================================
    # J_MCU_SPI at (50.0, 4.0): 1x06 Header [ +5V, GND, MOSI, SCK, LATCH, OE ]
    j_spi_nets = {
        "1": (net_map["+5V"], "+5V"),
        "2": (net_map["GND"], "GND"),
        "3": (net_map["SPI_MOSI"], "SPI_MOSI"),
        "4": (net_map["SPI_SCK"], "SPI_SCK"),
        "5": (net_map["SPI_LATCH"], "SPI_LATCH"),
        "6": (net_map["SPI_OE"], "SPI_OE")
    }
    pcb.append(fp_header_1x("J_MCU_SPI", "MCU_SPI_In", 50.0, 4.0, 6, 0, j_spi_nets))

    # Row 1: U_SR1..4 at Y = 11.5 mm, generating IN_0..31
    # Row 2: U_SR5..8 at Y = 22.0 mm, generating IN_32..63
    # X coordinates: 20.0, 40.0, 60.0, 80.0 mm
    sr_xs = [20.0, 40.0, 60.0, 80.0]
    
    for idx in range(8):
        ref = f"U_SR{idx+1}"
        row = idx // 4 # 0 for U1..4, 1 for U5..8
        if row == 0:
            col = idx
            p_base = idx * 8 # 0, 8, 16, 24 (IN_0..31)
        else:
            col = 3 - (idx - 4) # 3, 2, 1, 0
            p_base = 32 + col * 8 # 56, 48, 40, 32 (IN_32..63 aligned with columns!)
            
        cx = sr_xs[col]
        cy = 11.5 if row == 0 else 22.0

        ser_in_net = (net_map["SPI_MOSI"], "SPI_MOSI") if idx == 0 else (net_map[f"SR_CHAIN_{idx}"], f"SR_CHAIN_{idx}")
        ser_out_net = (net_map[f"SR_CHAIN_{idx+1}"], f"SR_CHAIN_{idx+1}") if idx < 7 else (0, "")

        sr_nets = {
            "1": (net_map[f"IN_{p_base+1}"], f"IN_{p_base+1}"), # QB
            "2": (net_map[f"IN_{p_base+2}"], f"IN_{p_base+2}"), # QC
            "3": (net_map[f"IN_{p_base+3}"], f"IN_{p_base+3}"), # QD
            "4": (net_map[f"IN_{p_base+4}"], f"IN_{p_base+4}"), # QE
            "5": (net_map[f"IN_{p_base+5}"], f"IN_{p_base+5}"), # QF
            "6": (net_map[f"IN_{p_base+6}"], f"IN_{p_base+6}"), # QG
            "7": (net_map[f"IN_{p_base+7}"], f"IN_{p_base+7}"), # QH
            "8": (net_map["GND"], "GND"),
            "9": ser_out_net,                                    # QH'
            "10": (net_map["+5V"], "+5V"),                       # SRCLR#
            "11": (net_map["SPI_SCK"], "SPI_SCK"),               # SRCLK
            "12": (net_map["SPI_LATCH"], "SPI_LATCH"),           # RCLK
            "13": (net_map["SPI_OE"], "SPI_OE"),                 # OE#
            "14": ser_in_net,                                    # SER
            "15": (net_map[f"IN_{p_base+0}"], f"IN_{p_base+0}"), # QA
            "16": (net_map["+5V"], "+5V")                        # VCC
        }
        pcb.append(fp_soic16(ref, "74HC595D", cx, cy, 0, sr_nets))

        # Decoupling Cap C_SR1..8 next to Pin 16 at (cx + 6.0, cy - 4.0)
        pcb.append(fp_cap_0805(f"C_SR{idx+1}", "0.1uF", cx + 6.0, cy - 4.0, 0, "F.Cu", 7, "+5V", 1, "GND"))

        # Dedicated GND drops to In1.Cu plane for Pin 8 and C_SR Pad 2:
        pcb.append(make_via(cx - 4.2, cy + 4.445, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(cx - 2.7, cy + 4.445, cx - 4.2, cy + 4.445, 0.25, "F.Cu", "GND", 1))
        pcb.append(make_via(cx + 8.2, cy - 4.0, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(cx + 6.95, cy - 4.0, cx + 8.2, cy - 4.0, 0.25, "F.Cu", "GND", 1))

    # =========================================================================
    # BOTTOM SECTION: 10-Ch Voltage Dividers, J_MCU_SCORES, J_PWR_IN
    # =========================================================================
    # 10 Pairs of Voltage Divider Resistors spaced by 3.8 mm across X in [14.0 .. 48.2]
    div_x0 = 14.0
    for c in range(10):
        xc = div_x0 + c * 3.8
        # R_TOP: connects SCORE_DIV_c (pad 1, bot) to SCORE_c (pad 2, top)
        pcb.append(fp_resistor_0805(f"R_TOP_{c}", "10k", xc - 0.9, 93.0, 90, "F.Cu",
                                   net_map[f"SCORE_DIV_{c}"], f"SCORE_DIV_{c}",
                                   net_map[f"SCORE_{c}"], f"SCORE_{c}"))
        # R_BOT: connects SCORE_DIV_c (pad 1, bot) to GND (pad 2, top)
        pcb.append(fp_resistor_0805(f"R_BOT_{c}", "20k", xc + 0.9, 93.0, 90, "F.Cu",
                                   net_map[f"SCORE_DIV_{c}"], f"SCORE_DIV_{c}",
                                   1, "GND"))
        # Short bridge connecting Pad 1 of R_TOP and Pad 1 of R_BOT on SCORE_DIV_c
        pcb.append(make_segment(xc - 0.9, 93.95, xc + 0.9, 93.95, 0.25, "F.Cu", f"SCORE_DIV_{c}", net_map[f"SCORE_DIV_{c}"]))
        # Dedicated GND drop to In1.Cu plane for R_BOT Pad 2 (at y=92.05):
        pcb.append(make_via(xc + 1.9, 92.05, 0.6, 0.3, "GND", 1))
        pcb.append(make_segment(xc + 0.9, 92.05, xc + 1.9, 92.05, 0.25, "F.Cu", "GND", 1))

    # J_MCU_SCORES at (31.1, 96.2): 1x12 Header [ SCORE_DIV_0..9, GND, GND ]
    j_score_nets = {str(c+1): (net_map[f"SCORE_DIV_{c}"], f"SCORE_DIV_{c}") for c in range(10)}
    j_score_nets["11"] = (net_map["GND"], "GND")
    j_score_nets["12"] = (net_map["GND"], "GND")
    pcb.append(fp_header_1x("J_MCU_SCORES", "Scores_DIV_3V3_Out", 31.1, 96.2, 12, 0, j_score_nets))

    # J_PWR_IN at (72.0, 96.0): 1x08 Header
    # Pin 1,2: +12V; Pin 3,4: GND; Pin 5,6: -12V; Pin 7: +5V_REF; Pin 8: -5V_REF
    j_pwr_nets = {
        "1": (net_map["+12V"], "+12V"), "2": (net_map["+12V"], "+12V"),
        "3": (net_map["GND"], "GND"), "4": (net_map["GND"], "GND"),
        "5": (net_map["-12V"], "-12V"), "6": (net_map["-12V"], "-12V"),
        "7": (net_map["+5V_REF"], "+5V_REF"), "8": (net_map["-5V_REF"], "-5V_REF")
    }
    pcb.append(fp_header_1x("J_PWR_IN", "Main_Power_In", 72.0, 96.0, 8, 0, j_pwr_nets))

    # Tie +5V_REF to +5V via zero-ohm / link jumper R_PWR5 at (53.0, 96.0)
    pcb.append(fp_resistor_0805("R_PWR5", "0R", 53.0, 96.0, 0, "F.Cu", 6, "+5V_REF", 7, "+5V"))

    # =========================================================================
    # PRE-ROUTED DETERMINISTIC HIGHWAYS (Locked)
    # =========================================================================
    cx = 50.0
    x_start = - (17.5 * PITCH)

    # 1. Straight Interconnect ACT_0..15 from Slot 4 to Slot 5 on F.Cu
    yb_slot4 = y_slots[4] + 2.54 # 78.54 mm
    ya_slot5 = y_slots[5] - 2.54 # 84.46 mm
    for k in range(16):
        px = cx + x_start + k * PITCH
        pcb.append(make_segment(px, yb_slot4, px, ya_slot5, 0.25, "F.Cu", f"ACT_{k}", net_map[f"ACT_{k}"]))

    # 2. J_PWR_IN adjacent pin jumpers
    pwr_x0 = 72.0 - 3.5 * PITCH
    # +12V: pin 1 to 2
    pcb.append(make_segment(pwr_x0, 96.0, pwr_x0 + PITCH, 96.0, 0.40, "B.Cu", "+12V", 2))
    # GND: pin 3 to 4
    pcb.append(make_segment(pwr_x0 + 2*PITCH, 96.0, pwr_x0 + 3*PITCH, 96.0, 0.40, "F.Cu", "GND", 1))
    # -12V: pin 5 to 6
    pcb.append(make_segment(pwr_x0 + 4*PITCH, 96.0, pwr_x0 + 5*PITCH, 96.0, 0.40, "B.Cu", "-12V", 3))

    pcb.append(")")
    with open(BOARD_FILE, "w") as f:
        f.write("\n".join(pcb))
    print(f"Generated new face-side motherboard baseline board: {BOARD_FILE}")

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
        "-mp", "250",
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
            print(f"[Motherboard v8] DRC Result: {uncon} unconnected, {viols} errors")
            print(f"==================================================")

        cmd_rpt = f"{KICAD_CLI} pcb drc --output {DRC_REPORT} {BOARD_FILE}"
        subprocess.run(cmd_rpt, shell=True)

if __name__ == "__main__":
    build_board()
    run_autorouter()
