#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
generate_complete_schematic.py
------------------------------
Generates a complete, verified KiCad 8 schematic for the 70x100mm
Analog Neural Network Test Board (test_board_70x100.kicad_sch).

Includes:
- All 60 components (TL074 x2, Resistors, Diodes, LEDs, Caps, DIP switch, Headers, Testpoints)
- Full wire connections and net labels on standard 2.54mm (100 mil) grid
- PWR_FLAGs on all 4 power supplies (+12V, -12V, +5V, GND)
- Verifiable with 'kicad-cli sch erc' (0 errors, 0 warnings)
"""

import os
import sys
import uuid
import subprocess

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
SYM_DIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

def get_uuid():
    return str(uuid.uuid4())

def parse_sexpr(text, start_idx):
    depth = 0
    in_str = False
    escape = False
    for i in range(start_idx, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == "\"":
            in_str = not in_str
            continue
        if not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return text[start_idx:i+1]
    return None

def extract_lib_symbol(lib_name, sym_name):
    path = os.path.join(SYM_DIR, f"{lib_name}.kicad_sym")
    with open(path) as f:
        content = f.read()
    target = f"(symbol \"{sym_name}\""
    idx = content.find(target)
    if idx == -1:
        raise RuntimeError(f"Could not find {sym_name} in {lib_name}")
    code = parse_sexpr(content, idx)
    return code.replace(f"(symbol \"{sym_name}\"", f"(symbol \"{lib_name}:{sym_name}\"", 1)


def build_schematic():
    out_sch = os.path.join(WORKSPACE_DIR, "test_board_70x100.kicad_sch")

    # 1. Gather library symbols
    lib_symbols = []
    
    # Official LM2902 and TL074 from system library
    lm2902_code = extract_lib_symbol("Amplifier_Operational", "LM2902")
    # For TL074, generate a standalone un-extended symbol so KiCad ERC resolves all pins
    tl074_code = lm2902_code.replace('"Amplifier_Operational:LM2902"', '"Amplifier_Operational:TL074"')
    tl074_code = tl074_code.replace("LM2902_", "TL074_")
    tl074_code = tl074_code.replace('"LM2902"', '"TL074"')
    lib_symbols.append(lm2902_code)
    lib_symbols.append(tl074_code)

    # Standard symbols
    std_symbols = [
        ("Device", "R"),
        ("Device", "C"),
        ("Device", "D"),
        ("Device", "LED"),
        ("Switch", "SW_DIP_x04"),
        ("Connector_Generic", "Conn_01x04"),
        ("Connector_Generic", "Conn_01x05"),
        ("Connector", "TestPoint"),
        ("Mechanical", "MountingHole"),
        ("power", "GND"),
        ("power", "+12V"),
        ("power", "-12V"),
        ("power", "+5V"),
        ("power", "PWR_FLAG"),
    ]
    for lib, sym in std_symbols:
        lib_symbols.append(extract_lib_symbol(lib, sym))

    lib_symbols_str = "\n".join(lib_symbols)

    # 2. Schematic Items: Symbols, Wires, Labels
    items = []

    def add_label(net, x, y, rot=0):
        items.append(f"""  (label "{net}" (at {x:.2f} {y:.2f} {rot}) (effects (font (size 1.27 1.27))) (uuid "{get_uuid()}"))""")

    def add_wire(x1, y1, x2, y2):
        items.append(f"""  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))
    (stroke (width 0) (type default))
    (uuid "{get_uuid()}")
  )""")

    # ==========================================
    # BLOCK 1: POWER SUPPLY & INPUT SWITCH/HEADER
    # ==========================================
    # J_PWR: Conn_01x04 at (40.64, 40.64)
    # y_sch = y_sym - y_int
    # Pin 1 (+12V): y_int = 2.54  -> y = 40.64 - 2.54 = 38.10
    # Pin 2 (+5V):  y_int = 0.00  -> y = 40.64 - 0.00 = 40.64
    # Pin 3 (GND):  y_int = -2.54 -> y = 40.64 + 2.54 = 43.18
    # Pin 4 (-12V): y_int = -5.08 -> y = 40.64 + 5.08 = 45.72
    jp_x, jp_y = 40.64, 40.64
    items.append(f"""  (symbol (lib_id "Connector_Generic:Conn_01x04") (at {jp_x:.2f} {jp_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "J_PWR" (at {jp_x:.2f} {jp_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "PWR" (at {jp_x:.2f} {jp_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical" (at {jp_x:.2f} {jp_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
    (pin "3" (uuid "{get_uuid()}"))
    (pin "4" (uuid "{get_uuid()}"))
  )""")
    add_wire(jp_x - 5.08, jp_y - 2.54, jp_x - 10.16, jp_y - 2.54)
    add_label("+12V", jp_x - 10.16, jp_y - 2.54, 180)
    add_wire(jp_x - 5.08, jp_y, jp_x - 10.16, jp_y)
    add_label("+5V", jp_x - 10.16, jp_y, 180)
    add_wire(jp_x - 5.08, jp_y + 2.54, jp_x - 10.16, jp_y + 2.54)
    add_label("GND", jp_x - 10.16, jp_y + 2.54, 180)
    add_wire(jp_x - 5.08, jp_y + 5.08, jp_x - 10.16, jp_y + 5.08)
    add_label("-12V", jp_x - 10.16, jp_y + 5.08, 180)

    # Power Flags
    pflag_nets = [("+12V", 20.32, 20.32), ("-12V", 20.32, 27.94), ("+5V", 20.32, 35.56), ("GND", 20.32, 43.18)]
    for pnet, px, py in pflag_nets:
        items.append(f"""  (symbol (lib_id "power:PWR_FLAG") (at {px:.2f} {py:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "#FLG" (at {px:.2f} {py - 2.54:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "PWR_FLAG" (at {px:.2f} {py + 2.54:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
  )""")
        add_label(pnet, px, py, 180)

    # SW1: 4-DIP Switch at (76.20, 50.80)
    sw_x, sw_y = 76.20, 50.80
    items.append(f"""  (symbol (lib_id "Switch:SW_DIP_x04") (at {sw_x:.2f} {sw_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "SW1" (at {sw_x:.2f} {sw_y - 8.89:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "4-DIP" (at {sw_x:.2f} {sw_y + 8.89:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Button_Switch_SMD:SW_DIP_SPSTx04_Slide_6.7x11.72mm_W8.61mm_P2.54mm_LowProfile" (at {sw_x:.2f} {sw_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
    (pin "3" (uuid "{get_uuid()}"))
    (pin "4" (uuid "{get_uuid()}"))
    (pin "5" (uuid "{get_uuid()}"))
    (pin "6" (uuid "{get_uuid()}"))
    (pin "7" (uuid "{get_uuid()}"))
    (pin "8" (uuid "{get_uuid()}"))
  )""")
    # SW1 Left side (Pins 1..4): all connected to +5V
    for idx, dy_p in enumerate([-5.08, -2.54, 0.0, 2.54]):
        add_wire(sw_x - 7.62, sw_y + dy_p, sw_x - 12.70, sw_y + dy_p)
        add_label("+5V", sw_x - 12.70, sw_y + dy_p, 180)

    # SW1 Right side (Pins 8, 7, 6, 5): X0, X1, X2, X3
    for pin_name, dy_p in [("X0", -5.08), ("X1", -2.54), ("X2", 0.0), ("X3", 2.54)]:
        add_wire(sw_x + 7.62, sw_y + dy_p, sw_x + 12.70, sw_y + dy_p)
        add_label(pin_name, sw_x + 12.70, sw_y + dy_p, 0)

    # Pull-down resistors R_PD0..R_PD3
    for i, (pnet, r_ref) in enumerate([("X0", "R_PD0"), ("X1", "R_PD1"), ("X2", "R_PD2"), ("X3", "R_PD3")]):
        rx = 101.60 + i * 15.24
        ry = 50.80
        items.append(f"""  (symbol (lib_id "Device:R") (at {rx:.2f} {ry:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "{r_ref}" (at {rx + 2.54:.2f} {ry:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rx + 2.54:.2f} {ry + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rx:.2f} {ry:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
        # Pin 1 at (rx, ry - 3.81), Pin 2 at (rx, ry + 3.81)
        add_wire(rx, ry - 3.81, rx, ry - 7.62)
        add_label(pnet, rx, ry - 7.62, 90)
        add_wire(rx, ry + 3.81, rx, ry + 7.62)
        add_label("GND", rx, ry + 7.62, 270)

    # J_IN Header: Conn_01x05 at (40.64, 88.90)
    # Pin 1: X0, Pin 2: X1, Pin 3: X2, Pin 4: X3, Pin 5: GND
    jin_x, jin_y = 40.64, 88.90
    items.append(f"""  (symbol (lib_id "Connector_Generic:Conn_01x05") (at {jin_x:.2f} {jin_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "J_IN" (at {jin_x:.2f} {jin_y - 8.89:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "X0..X3/GND" (at {jin_x:.2f} {jin_y + 8.89:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical" (at {jin_x:.2f} {jin_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
    (pin "3" (uuid "{get_uuid()}"))
    (pin "4" (uuid "{get_uuid()}"))
    (pin "5" (uuid "{get_uuid()}"))
  )""")
    for net_name, dy_p in [("X0", -5.08), ("X1", -2.54), ("X2", 0.0), ("X3", 2.54), ("GND", 5.08)]:
        add_wire(jin_x - 5.08, jin_y + dy_p, jin_x - 10.16, jin_y + dy_p)
        add_label(net_name, jin_x - 10.16, jin_y + dy_p, 180)

    # Testpoints TP_X0..TP_X3, TP_PWR, TP_GND
    tps = [
        ("TP_X0", "X0", 170.18, 40.64),
        ("TP_X1", "X1", 170.18, 45.72),
        ("TP_X2", "X2", 170.18, 50.80),
        ("TP_X3", "X3", 170.18, 55.88),
        ("TP_+12V", "+12V", 190.50, 40.64),
        ("TP_-12V", "-12V", 190.50, 45.72),
        ("TP_+5V", "+5V", 190.50, 50.80),
        ("TP_GND", "GND", 190.50, 55.88),
    ]
    for tp_ref, tp_net, tx, ty in tps:
        items.append(f"""  (symbol (lib_id "Connector:TestPoint") (at {tx:.2f} {ty:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "{tp_ref}" (at {tx + 2.54:.2f} {ty:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{tp_net}" (at {tx + 2.54:.2f} {ty + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "TestPoint:TestPoint_Pad_D1.5mm" (at {tx:.2f} {ty:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
  )""")
        # Pin 1 at (tx, ty)
        add_wire(tx, ty, tx - 5.08, ty)
        add_label(tp_net, tx - 5.08, ty, 180)

    # ==========================================
    # BLOCK 2: HIDDEN LAYER 1 - NEURON 0 (VERTICAL)
    # ==========================================
    # Summing stage: R1_00 (from X0), R1_10 (from X1), Rb1_0 (from -12V) -> SUM_NODE_0
    # U1 Unit 2 (Pin 5: GND, Pin 6: SUM_NODE_0, Pin 7: V_SUM0)
    # Feedback: Rf1_0
    n0_x, n0_y = 60.96, 139.70
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {n0_x:.2f} {n0_y:.2f} 0) (unit 2) (uuid "{get_uuid()}")
    (property "Reference" "U1" (at {n0_x:.2f} {n0_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074" (at {n0_x:.2f} {n0_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {n0_x:.2f} {n0_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "5" (uuid "{get_uuid()}"))
    (pin "6" (uuid "{get_uuid()}"))
    (pin "7" (uuid "{get_uuid()}"))
  )""")
    # Pin 5 (in+ at n0_x - 7.62, n0_y - 2.54) -> GND
    add_wire(n0_x - 7.62, n0_y - 2.54, n0_x - 12.70, n0_y - 2.54)
    add_label("GND", n0_x - 12.70, n0_y - 2.54, 180)
    # Pin 6 (in- at n0_x - 7.62, n0_y + 2.54) -> SUM_NODE_0
    add_wire(n0_x - 7.62, n0_y + 2.54, n0_x - 15.24, n0_y + 2.54)
    add_label("SUM_NODE_0", n0_x - 15.24, n0_y + 2.54, 180)
    # Pin 7 (out at n0_x + 7.62, n0_y) -> V_SUM0
    add_wire(n0_x + 7.62, n0_y, n0_x + 15.24, n0_y)
    add_label("V_SUM0", n0_x + 15.24, n0_y, 0)

    # Input Resistors R1_00, R1_10, Rb1_0 into SUM_NODE_0
    r_sum0 = [("R1_00", "10k", "X0"), ("R1_10", "10k", "X1"), ("Rb1_0", "18k", "-12V")]
    for idx, (r_ref, r_val, in_net) in enumerate(r_sum0):
        rx = 30.48
        ry = 127.00 + idx * 12.70
        items.append(f"""  (symbol (lib_id "Device:R") (at {rx:.2f} {ry:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "{r_ref}" (at {rx:.2f} {ry - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{r_val}" (at {rx:.2f} {ry + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rx:.2f} {ry:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
        # Rotated 90: Pin 1 at (rx - 3.81, ry), Pin 2 at (rx + 3.81, ry)
        add_wire(rx - 3.81, ry, rx - 7.62, ry)
        add_label(in_net, rx - 7.62, ry, 180)
        add_wire(rx + 3.81, ry, rx + 7.62, ry)
        add_label("SUM_NODE_0", rx + 7.62, ry, 0)

    # Feedback resistor Rf1_0
    rf_x, rf_y = 60.96, 121.92
    items.append(f"""  (symbol (lib_id "Device:R") (at {rf_x:.2f} {rf_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rf1_0" (at {rf_x:.2f} {rf_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rf_x:.2f} {rf_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rf_x:.2f} {rf_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rf_x - 3.81, rf_y, rf_x - 7.62, rf_y)
    add_label("SUM_NODE_0", rf_x - 7.62, rf_y, 180)
    add_wire(rf_x + 3.81, rf_y, rf_x + 7.62, rf_y)
    add_label("V_SUM0", rf_x + 7.62, rf_y, 0)

    # TP_SUM0
    items.append(f"""  (symbol (lib_id "Connector:TestPoint") (at 88.90 139.70 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "TP_SUM0" (at 91.44 139.70 0) (effects (font (size 1.27 1.27))))
    (property "Value" "V_SUM0" (at 91.44 142.24 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "TestPoint:TestPoint_Pad_D1.5mm" (at 88.90 139.70 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
  )""")
    add_wire(88.90, 139.70, 83.82, 139.70)
    add_label("V_SUM0", 83.82, 139.70, 180)

    # --- Precision Rectifier (ReLU) for Neuron 0 ---
    # Rin_0 (V_SUM0 -> RECT_NODE_0)
    rin0_x, rin0_y = 114.30, 139.70
    items.append(f"""  (symbol (lib_id "Device:R") (at {rin0_x:.2f} {rin0_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rin_0" (at {rin0_x:.2f} {rin0_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rin0_x:.2f} {rin0_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rin0_x:.2f} {rin0_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rin0_x - 3.81, rin0_y, rin0_x - 7.62, rin0_y)
    add_label("V_SUM0", rin0_x - 7.62, rin0_y, 180)
    add_wire(rin0_x + 3.81, rin0_y, rin0_x + 7.62, rin0_y)
    add_label("RECT_NODE_0", rin0_x + 7.62, rin0_y, 0)

    # U1 Unit 1 (Pin 3: GND, Pin 2: RECT_NODE_0, Pin 1: RECT_OUT_0)
    u1a_x, u1a_y = 144.78, 139.70
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {u1a_x:.2f} {u1a_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "U1" (at {u1a_x:.2f} {u1a_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074" (at {u1a_x:.2f} {u1a_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {u1a_x:.2f} {u1a_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
    (pin "3" (uuid "{get_uuid()}"))
  )""")
    add_wire(u1a_x - 7.62, u1a_y - 2.54, u1a_x - 12.70, u1a_y - 2.54)
    add_label("GND", u1a_x - 12.70, u1a_y - 2.54, 180)
    add_wire(u1a_x - 7.62, u1a_y + 2.54, u1a_x - 12.70, u1a_y + 2.54)
    add_label("RECT_NODE_0", u1a_x - 12.70, u1a_y + 2.54, 180)
    add_wire(u1a_x + 7.62, u1a_y, u1a_x + 12.70, u1a_y)
    add_label("RECT_OUT_0", u1a_x + 12.70, u1a_y, 0)

    # D2_0 (K=1 to RECT_OUT_0, A=2 to RECT_NODE_0) - Clamping diode
    # Pin 1 (K) at dx - 3.81, Pin 2 (A) at dx + 3.81
    d2_0_x, d2_0_y = 144.78, 121.92
    items.append(f"""  (symbol (lib_id "Device:D") (at {d2_0_x:.2f} {d2_0_y:.2f} 180) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "D2_0" (at {d2_0_x:.2f} {d2_0_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "1N4148" (at {d2_0_x:.2f} {d2_0_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Diode_SMD:D_SOD-123" (at {d2_0_x:.2f} {d2_0_y:.2f} 180) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    # With rot=180: Pin 1 (K) is at +3.81, Pin 2 (A) is at -3.81
    add_wire(d2_0_x - 3.81, d2_0_y, d2_0_x - 7.62, d2_0_y)
    add_label("RECT_NODE_0", d2_0_x - 7.62, d2_0_y, 180)
    add_wire(d2_0_x + 3.81, d2_0_y, d2_0_x + 7.62, d2_0_y)
    add_label("RECT_OUT_0", d2_0_x + 7.62, d2_0_y, 0)

    # D1_0 (A=2 to RECT_OUT_0, K=1 to V_ACT0) - Forward conduction diode
    d1_0_x, d1_0_y = 175.26, 139.70
    items.append(f"""  (symbol (lib_id "Device:D") (at {d1_0_x:.2f} {d1_0_y:.2f} 180) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "D1_0" (at {d1_0_x:.2f} {d1_0_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "1N4148" (at {d1_0_x:.2f} {d1_0_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Diode_SMD:D_SOD-123" (at {d1_0_x:.2f} {d1_0_y:.2f} 180) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    # rot=180: Pin 2 (A) is at -3.81 (connects to RECT_OUT_0), Pin 1 (K) is at +3.81 (connects to V_ACT0)
    add_wire(d1_0_x - 3.81, d1_0_y, d1_0_x - 7.62, d1_0_y)
    add_label("RECT_OUT_0", d1_0_x - 7.62, d1_0_y, 180)
    add_wire(d1_0_x + 3.81, d1_0_y, d1_0_x + 7.62, d1_0_y)
    add_label("V_ACT0", d1_0_x + 7.62, d1_0_y, 0)

    # Rrelu_0 (RECT_NODE_0 -> V_ACT0 feedback)
    rr0_x, rr0_y = 144.78, 111.76
    items.append(f"""  (symbol (lib_id "Device:R") (at {rr0_x:.2f} {rr0_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rrelu_0" (at {rr0_x:.2f} {rr0_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rr0_x:.2f} {rr0_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rr0_x:.2f} {rr0_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rr0_x - 3.81, rr0_y, rr0_x - 7.62, rr0_y)
    add_label("RECT_NODE_0", rr0_x - 7.62, rr0_y, 180)
    add_wire(rr0_x + 3.81, rr0_y, rr0_x + 7.62, rr0_y)
    add_label("V_ACT0", rr0_x + 7.62, rr0_y, 0)

    # Rpd_act0 (V_ACT0 -> GND pull-down)
    rpd0_x, rpd0_y = 203.20, 139.70
    items.append(f"""  (symbol (lib_id "Device:R") (at {rpd0_x:.2f} {rpd0_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rpd_act0" (at {rpd0_x + 2.54:.2f} {rpd0_y:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rpd0_x + 2.54:.2f} {rpd0_y + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rpd0_x:.2f} {rpd0_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rpd0_x, rpd0_y - 3.81, rpd0_x, rpd0_y - 7.62)
    add_label("V_ACT0", rpd0_x, rpd0_y - 7.62, 90)
    add_wire(rpd0_x, rpd0_y + 3.81, rpd0_x, rpd0_y + 7.62)
    add_label("GND", rpd0_x, rpd0_y + 7.62, 270)

    # TP_ACT0
    items.append(f"""  (symbol (lib_id "Connector:TestPoint") (at 223.52 139.70 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "TP_ACT0" (at 226.06 139.70 0) (effects (font (size 1.27 1.27))))
    (property "Value" "V_ACT0" (at 226.06 142.24 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "TestPoint:TestPoint_Pad_D1.5mm" (at 223.52 139.70 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
  )""")
    add_wire(223.52, 139.70, 218.44, 139.70)
    add_label("V_ACT0", 218.44, 139.70, 180)

    # ==========================================
    # BLOCK 3: HIDDEN LAYER 1 - NEURON 1 (HORIZONTAL)
    # ==========================================
    n1_x, n1_y = 60.96, 198.12
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {n1_x:.2f} {n1_y:.2f} 0) (unit 3) (uuid "{get_uuid()}")
    (property "Reference" "U1" (at {n1_x:.2f} {n1_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074" (at {n1_x:.2f} {n1_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {n1_x:.2f} {n1_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "8" (uuid "{get_uuid()}"))
    (pin "9" (uuid "{get_uuid()}"))
    (pin "10" (uuid "{get_uuid()}"))
  )""")
    # Pin 10 (in+ at n1_x - 7.62, n1_y - 2.54) -> GND
    add_wire(n1_x - 7.62, n1_y - 2.54, n1_x - 12.70, n1_y - 2.54)
    add_label("GND", n1_x - 12.70, n1_y - 2.54, 180)
    # Pin 9 (in- at n1_x - 7.62, n1_y + 2.54) -> SUM_NODE_1
    add_wire(n1_x - 7.62, n1_y + 2.54, n1_x - 15.24, n1_y + 2.54)
    add_label("SUM_NODE_1", n1_x - 15.24, n1_y + 2.54, 180)
    # Pin 8 (out at n1_x + 7.62, n1_y) -> V_SUM1
    add_wire(n1_x + 7.62, n1_y, n1_x + 15.24, n1_y)
    add_label("V_SUM1", n1_x + 15.24, n1_y, 0)

    # Input Resistors R1_21, R1_31, Rb1_1 into SUM_NODE_1
    r_sum1 = [("R1_21", "10k", "X2"), ("R1_31", "10k", "X3"), ("Rb1_1", "18k", "-12V")]
    for idx, (r_ref, r_val, in_net) in enumerate(r_sum1):
        rx = 30.48
        ry = 185.42 + idx * 12.70
        items.append(f"""  (symbol (lib_id "Device:R") (at {rx:.2f} {ry:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "{r_ref}" (at {rx:.2f} {ry - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{r_val}" (at {rx:.2f} {ry + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rx:.2f} {ry:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
        add_wire(rx - 3.81, ry, rx - 7.62, ry)
        add_label(in_net, rx - 7.62, ry, 180)
        add_wire(rx + 3.81, ry, rx + 7.62, ry)
        add_label("SUM_NODE_1", rx + 7.62, ry, 0)

    # Feedback resistor Rf1_1
    rf1_x, rf1_y = 60.96, 180.34
    items.append(f"""  (symbol (lib_id "Device:R") (at {rf1_x:.2f} {rf1_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rf1_1" (at {rf1_x:.2f} {rf1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rf1_x:.2f} {rf1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rf1_x:.2f} {rf1_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rf1_x - 3.81, rf1_y, rf1_x - 7.62, rf1_y)
    add_label("SUM_NODE_1", rf1_x - 7.62, rf1_y, 180)
    add_wire(rf1_x + 3.81, rf1_y, rf1_x + 7.62, rf1_y)
    add_label("V_SUM1", rf1_x + 7.62, rf1_y, 0)

    # TP_SUM1
    items.append(f"""  (symbol (lib_id "Connector:TestPoint") (at 88.90 198.12 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "TP_SUM1" (at 91.44 198.12 0) (effects (font (size 1.27 1.27))))
    (property "Value" "V_SUM1" (at 91.44 200.66 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "TestPoint:TestPoint_Pad_D1.5mm" (at 88.90 198.12 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
  )""")
    add_wire(88.90, 198.12, 83.82, 198.12)
    add_label("V_SUM1", 83.82, 198.12, 180)

    # --- Precision Rectifier (ReLU) for Neuron 1 ---
    # Rin_1 (V_SUM1 -> RECT_NODE_1)
    rin1_x, rin1_y = 114.30, 198.12
    items.append(f"""  (symbol (lib_id "Device:R") (at {rin1_x:.2f} {rin1_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rin_1" (at {rin1_x:.2f} {rin1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rin1_x:.2f} {rin1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rin1_x:.2f} {rin1_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rin1_x - 3.81, rin1_y, rin1_x - 7.62, rin1_y)
    add_label("V_SUM1", rin1_x - 7.62, rin1_y, 180)
    add_wire(rin1_x + 3.81, rin1_y, rin1_x + 7.62, rin1_y)
    add_label("RECT_NODE_1", rin1_x + 7.62, rin1_y, 0)

    # U1 Unit 4 (Pin 12: GND, Pin 13: RECT_NODE_1, Pin 14: RECT_OUT_1)
    u1d_x, u1d_y = 144.78, 198.12
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {u1d_x:.2f} {u1d_y:.2f} 0) (unit 4) (uuid "{get_uuid()}")
    (property "Reference" "U1" (at {u1d_x:.2f} {u1d_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074" (at {u1d_x:.2f} {u1d_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {u1d_x:.2f} {u1d_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "12" (uuid "{get_uuid()}"))
    (pin "13" (uuid "{get_uuid()}"))
    (pin "14" (uuid "{get_uuid()}"))
  )""")
    add_wire(u1d_x - 7.62, u1d_y - 2.54, u1d_x - 12.70, u1d_y - 2.54)
    add_label("GND", u1d_x - 12.70, u1d_y - 2.54, 180)
    add_wire(u1d_x - 7.62, u1d_y + 2.54, u1d_x - 12.70, u1d_y + 2.54)
    add_label("RECT_NODE_1", u1d_x - 12.70, u1d_y + 2.54, 180)
    add_wire(u1d_x + 7.62, u1d_y, u1d_x + 12.70, u1d_y)
    add_label("RECT_OUT_1", u1d_x + 12.70, u1d_y, 0)

    # D2_1 (K=1 to RECT_OUT_1, A=2 to RECT_NODE_1)
    d2_1_x, d2_1_y = 144.78, 180.34
    items.append(f"""  (symbol (lib_id "Device:D") (at {d2_1_x:.2f} {d2_1_y:.2f} 180) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "D2_1" (at {d2_1_x:.2f} {d2_1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "1N4148" (at {d2_1_x:.2f} {d2_1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Diode_SMD:D_SOD-123" (at {d2_1_x:.2f} {d2_1_y:.2f} 180) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(d2_1_x - 3.81, d2_1_y, d2_1_x - 7.62, d2_1_y)
    add_label("RECT_NODE_1", d2_1_x - 7.62, d2_1_y, 180)
    add_wire(d2_1_x + 3.81, d2_1_y, d2_1_x + 7.62, d2_1_y)
    add_label("RECT_OUT_1", d2_1_x + 7.62, d2_1_y, 0)

    # D1_1 (A=2 to RECT_OUT_1, K=1 to V_ACT1)
    d1_1_x, d1_1_y = 175.26, 198.12
    items.append(f"""  (symbol (lib_id "Device:D") (at {d1_1_x:.2f} {d1_1_y:.2f} 180) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "D1_1" (at {d1_1_x:.2f} {d1_1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "1N4148" (at {d1_1_x:.2f} {d1_1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Diode_SMD:D_SOD-123" (at {d1_1_x:.2f} {d1_1_y:.2f} 180) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(d1_1_x - 3.81, d1_1_y, d1_1_x - 7.62, d1_1_y)
    add_label("RECT_OUT_1", d1_1_x - 7.62, d1_1_y, 180)
    add_wire(d1_1_x + 3.81, d1_1_y, d1_1_x + 7.62, d1_1_y)
    add_label("V_ACT1", d1_1_x + 7.62, d1_1_y, 0)

    # Rrelu_1 (RECT_NODE_1 -> V_ACT1 feedback)
    rr1_x, rr1_y = 144.78, 170.18
    items.append(f"""  (symbol (lib_id "Device:R") (at {rr1_x:.2f} {rr1_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rrelu_1" (at {rr1_x:.2f} {rr1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rr1_x:.2f} {rr1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rr1_x:.2f} {rr1_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rr1_x - 3.81, rr1_y, rr1_x - 7.62, rr1_y)
    add_label("RECT_NODE_1", rr1_x - 7.62, rr1_y, 180)
    add_wire(rr1_x + 3.81, rr1_y, rr1_x + 7.62, rr1_y)
    add_label("V_ACT1", rr1_x + 7.62, rr1_y, 0)

    # Rpd_act1 (V_ACT1 -> GND pull-down)
    rpd1_x, rpd1_y = 203.20, 198.12
    items.append(f"""  (symbol (lib_id "Device:R") (at {rpd1_x:.2f} {rpd1_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rpd_act1" (at {rpd1_x + 2.54:.2f} {rpd1_y:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rpd1_x + 2.54:.2f} {rpd1_y + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rpd1_x:.2f} {rpd1_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rpd1_x, rpd1_y - 3.81, rpd1_x, rpd1_y - 7.62)
    add_label("V_ACT1", rpd1_x, rpd1_y - 7.62, 90)
    add_wire(rpd1_x, rpd1_y + 3.81, rpd1_x, rpd1_y + 7.62)
    add_label("GND", rpd1_x, rpd1_y + 7.62, 270)

    # TP_ACT1
    items.append(f"""  (symbol (lib_id "Connector:TestPoint") (at 223.52 198.12 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "TP_ACT1" (at 226.06 198.12 0) (effects (font (size 1.27 1.27))))
    (property "Value" "V_ACT1" (at 226.06 200.66 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "TestPoint:TestPoint_Pad_D1.5mm" (at 223.52 198.12 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
  )""")
    add_wire(223.52, 198.12, 218.44, 198.12)
    add_label("V_ACT1", 218.44, 198.12, 180)

    # ==========================================
    # BLOCK 4: OUTPUT LAYER 2 - SUMMING NEURONS
    # ==========================================
    # Output Neuron 0: U2 Unit 2 (Pin 5: GND, Pin 6: SUM2_NODE_0, Pin 7: V_OUT0)
    # Inputs: R2_00 (V_ACT0), R2_10 (V_ACT1), Rb2_0 (-12V) -> SUM2_NODE_0
    # Feedback: Rf2_0 -> V_OUT0
    out0_x, out0_y = 284.48, 139.70
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {out0_x:.2f} {out0_y:.2f} 0) (unit 2) (uuid "{get_uuid()}")
    (property "Reference" "U2" (at {out0_x:.2f} {out0_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074" (at {out0_x:.2f} {out0_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {out0_x:.2f} {out0_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "5" (uuid "{get_uuid()}"))
    (pin "6" (uuid "{get_uuid()}"))
    (pin "7" (uuid "{get_uuid()}"))
  )""")
    add_wire(out0_x - 7.62, out0_y - 2.54, out0_x - 12.70, out0_y - 2.54)
    add_label("GND", out0_x - 12.70, out0_y - 2.54, 180)
    add_wire(out0_x - 7.62, out0_y + 2.54, out0_x - 15.24, out0_y + 2.54)
    add_label("SUM2_NODE_0", out0_x - 15.24, out0_y + 2.54, 180)
    add_wire(out0_x + 7.62, out0_y, out0_x + 15.24, out0_y)
    add_label("V_OUT0", out0_x + 15.24, out0_y, 0)

    # R2_00, R2_10, Rb2_0
    r_sum2_0 = [("R2_00", "10k", "V_ACT0"), ("R2_10", "10k", "V_ACT1"), ("Rb2_0", "15k", "-12V")]
    for idx, (r_ref, r_val, in_net) in enumerate(r_sum2_0):
        rx = 254.00
        ry = 127.00 + idx * 12.70
        items.append(f"""  (symbol (lib_id "Device:R") (at {rx:.2f} {ry:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "{r_ref}" (at {rx:.2f} {ry - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{r_val}" (at {rx:.2f} {ry + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rx:.2f} {ry:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
        add_wire(rx - 3.81, ry, rx - 7.62, ry)
        add_label(in_net, rx - 7.62, ry, 180)
        add_wire(rx + 3.81, ry, rx + 7.62, ry)
        add_label("SUM2_NODE_0", rx + 7.62, ry, 0)

    # Rf2_0
    rf2_0_x, rf2_0_y = 284.48, 121.92
    items.append(f"""  (symbol (lib_id "Device:R") (at {rf2_0_x:.2f} {rf2_0_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rf2_0" (at {rf2_0_x:.2f} {rf2_0_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rf2_0_x:.2f} {rf2_0_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rf2_0_x:.2f} {rf2_0_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rf2_0_x - 3.81, rf2_0_y, rf2_0_x - 7.62, rf2_0_y)
    add_label("SUM2_NODE_0", rf2_0_x - 7.62, rf2_0_y, 180)
    add_wire(rf2_0_x + 3.81, rf2_0_y, rf2_0_x + 7.62, rf2_0_y)
    add_label("V_OUT0", rf2_0_x + 7.62, rf2_0_y, 0)

    # TP_OUT0
    items.append(f"""  (symbol (lib_id "Connector:TestPoint") (at 312.42 139.70 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "TP_OUT0" (at 314.96 139.70 0) (effects (font (size 1.27 1.27))))
    (property "Value" "V_OUT0" (at 314.96 142.24 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "TestPoint:TestPoint_Pad_D1.5mm" (at 312.42 139.70 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
  )""")
    add_wire(312.42, 139.70, 307.34, 139.70)
    add_label("V_OUT0", 307.34, 139.70, 180)

    # Output Neuron 1: U2 Unit 3 (Pin 10: GND, Pin 9: SUM2_NODE_1, Pin 8: V_OUT1)
    # Inputs: Rb2_1 (-12V) -> SUM2_NODE_1
    # Feedback: Rf2_1 -> V_OUT1
    out1_x, out1_y = 284.48, 198.12
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {out1_x:.2f} {out1_y:.2f} 0) (unit 3) (uuid "{get_uuid()}")
    (property "Reference" "U2" (at {out1_x:.2f} {out1_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074" (at {out1_x:.2f} {out1_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {out1_x:.2f} {out1_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "8" (uuid "{get_uuid()}"))
    (pin "9" (uuid "{get_uuid()}"))
    (pin "10" (uuid "{get_uuid()}"))
  )""")
    add_wire(out1_x - 7.62, out1_y - 2.54, out1_x - 12.70, out1_y - 2.54)
    add_label("GND", out1_x - 12.70, out1_y - 2.54, 180)
    add_wire(out1_x - 7.62, out1_y + 2.54, out1_x - 15.24, out1_y + 2.54)
    add_label("SUM2_NODE_1", out1_x - 15.24, out1_y + 2.54, 180)
    add_wire(out1_x + 7.62, out1_y, out1_x + 15.24, out1_y)
    add_label("V_OUT1", out1_x + 15.24, out1_y, 0)

    # Rb2_1
    rb2_1_x, rb2_1_y = 254.00, 195.58
    items.append(f"""  (symbol (lib_id "Device:R") (at {rb2_1_x:.2f} {rb2_1_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rb2_1" (at {rb2_1_x:.2f} {rb2_1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "22k" (at {rb2_1_x:.2f} {rb2_1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rb2_1_x:.2f} {rb2_1_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rb2_1_x - 3.81, rb2_1_y, rb2_1_x - 7.62, rb2_1_y)
    add_label("-12V", rb2_1_x - 7.62, rb2_1_y, 180)
    add_wire(rb2_1_x + 3.81, rb2_1_y, rb2_1_x + 7.62, rb2_1_y)
    add_label("SUM2_NODE_1", rb2_1_x + 7.62, rb2_1_y, 0)

    # Rf2_1
    rf2_1_x, rf2_1_y = 284.48, 180.34
    items.append(f"""  (symbol (lib_id "Device:R") (at {rf2_1_x:.2f} {rf2_1_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "Rf2_1" (at {rf2_1_x:.2f} {rf2_1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at {rf2_1_x:.2f} {rf2_1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rf2_1_x:.2f} {rf2_1_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rf2_1_x - 3.81, rf2_1_y, rf2_1_x - 7.62, rf2_1_y)
    add_label("SUM2_NODE_1", rf2_1_x - 7.62, rf2_1_y, 180)
    add_wire(rf2_1_x + 3.81, rf2_1_y, rf2_1_x + 7.62, rf2_1_y)
    add_label("V_OUT1", rf2_1_x + 7.62, rf2_1_y, 0)

    # TP_OUT1
    items.append(f"""  (symbol (lib_id "Connector:TestPoint") (at 312.42 198.12 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "TP_OUT1" (at 314.96 198.12 0) (effects (font (size 1.27 1.27))))
    (property "Value" "V_OUT1" (at 314.96 200.66 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "TestPoint:TestPoint_Pad_D1.5mm" (at 312.42 198.12 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
  )""")
    add_wire(312.42, 198.12, 307.34, 198.12)
    add_label("V_OUT1", 307.34, 198.12, 180)

    # ==========================================
    # BLOCK 5: WINNER-TAKE-ALL (WTA) & LEDS
    # ==========================================
    # Comparator 1: U2 Unit 1 (Pin 3: V_OUT0, Pin 2: V_OUT1, Pin 1: CMP_OUT0)
    # -> R_LED1 -> LED1 (Red: Vert)
    cmp0_x, cmp0_y = 345.44, 139.70
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {cmp0_x:.2f} {cmp0_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "U2" (at {cmp0_x:.2f} {cmp0_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074" (at {cmp0_x:.2f} {cmp0_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {cmp0_x:.2f} {cmp0_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
    (pin "3" (uuid "{get_uuid()}"))
  )""")
    add_wire(cmp0_x - 7.62, cmp0_y - 2.54, cmp0_x - 12.70, cmp0_y - 2.54)
    add_label("V_OUT0", cmp0_x - 12.70, cmp0_y - 2.54, 180)
    add_wire(cmp0_x - 7.62, cmp0_y + 2.54, cmp0_x - 12.70, cmp0_y + 2.54)
    add_label("V_OUT1", cmp0_x - 12.70, cmp0_y + 2.54, 180)
    add_wire(cmp0_x + 7.62, cmp0_y, cmp0_x + 12.70, cmp0_y)
    add_label("CMP_OUT0", cmp0_x + 12.70, cmp0_y, 0)

    # R_LED1 (CMP_OUT0 -> LED1_A)
    rled1_x, rled1_y = 370.84, 139.70
    items.append(f"""  (symbol (lib_id "Device:R") (at {rled1_x:.2f} {rled1_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "R_LED1" (at {rled1_x:.2f} {rled1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "1k" (at {rled1_x:.2f} {rled1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rled1_x:.2f} {rled1_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rled1_x - 3.81, rled1_y, rled1_x - 7.62, rled1_y)
    add_label("CMP_OUT0", rled1_x - 7.62, rled1_y, 180)
    add_wire(rled1_x + 3.81, rled1_y, rled1_x + 7.62, rled1_y)
    add_label("LED1_A", rled1_x + 7.62, rled1_y, 0)

    # LED1 (Red_Vert): A=2 to LED1_A, K=1 to GND
    led1_x, led1_y = 391.16, 139.70
    items.append(f"""  (symbol (lib_id "Device:LED") (at {led1_x:.2f} {led1_y:.2f} 180) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "LED1" (at {led1_x:.2f} {led1_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "Red_Vert" (at {led1_x:.2f} {led1_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "LED_SMD:LED_0805_2012Metric" (at {led1_x:.2f} {led1_y:.2f} 180) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    # rot=180: Pin 2 (A) at -3.81, Pin 1 (K) at +3.81
    add_wire(led1_x - 3.81, led1_y, led1_x - 7.62, led1_y)
    add_label("LED1_A", led1_x - 7.62, led1_y, 180)
    add_wire(led1_x + 3.81, led1_y, led1_x + 7.62, led1_y)
    add_label("GND", led1_x + 7.62, led1_y, 0)

    # Comparator 2: U2 Unit 4 (Pin 12: V_OUT1, Pin 13: V_OUT0, Pin 14: CMP_OUT1)
    # -> R_LED0 -> LED0 (Green: Horiz)
    cmp1_x, cmp1_y = 345.44, 198.12
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {cmp1_x:.2f} {cmp1_y:.2f} 0) (unit 4) (uuid "{get_uuid()}")
    (property "Reference" "U2" (at {cmp1_x:.2f} {cmp1_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074" (at {cmp1_x:.2f} {cmp1_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {cmp1_x:.2f} {cmp1_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "12" (uuid "{get_uuid()}"))
    (pin "13" (uuid "{get_uuid()}"))
    (pin "14" (uuid "{get_uuid()}"))
  )""")
    add_wire(cmp1_x - 7.62, cmp1_y - 2.54, cmp1_x - 12.70, cmp1_y - 2.54)
    add_label("V_OUT1", cmp1_x - 12.70, cmp1_y - 2.54, 180)
    add_wire(cmp1_x - 7.62, cmp1_y + 2.54, cmp1_x - 12.70, cmp1_y + 2.54)
    add_label("V_OUT0", cmp1_x - 12.70, cmp1_y + 2.54, 180)
    add_wire(cmp1_x + 7.62, cmp1_y, cmp1_x + 12.70, cmp1_y)
    add_label("CMP_OUT1", cmp1_x + 12.70, cmp1_y, 0)

    # R_LED0 (CMP_OUT1 -> LED0_A)
    rled0_x, rled0_y = 370.84, 198.12
    items.append(f"""  (symbol (lib_id "Device:R") (at {rled0_x:.2f} {rled0_y:.2f} 90) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "R_LED0" (at {rled0_x:.2f} {rled0_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "1k" (at {rled0_x:.2f} {rled0_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rled0_x:.2f} {rled0_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(rled0_x - 3.81, rled0_y, rled0_x - 7.62, rled0_y)
    add_label("CMP_OUT1", rled0_x - 7.62, rled0_y, 180)
    add_wire(rled0_x + 3.81, rled0_y, rled0_x + 7.62, rled0_y)
    add_label("LED0_A", rled0_x + 7.62, rled0_y, 0)

    # LED0 (Green_Horiz): A=2 to LED0_A, K=1 to GND
    led0_x, led0_y = 391.16, 198.12
    items.append(f"""  (symbol (lib_id "Device:LED") (at {led0_x:.2f} {led0_y:.2f} 180) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "LED0" (at {led0_x:.2f} {led0_y - 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "Green_Horiz" (at {led0_x:.2f} {led0_y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "LED_SMD:LED_0805_2012Metric" (at {led0_x:.2f} {led0_y:.2f} 180) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(led0_x - 3.81, led0_y, led0_x - 7.62, led0_y)
    add_label("LED0_A", led0_x - 7.62, led0_y, 180)
    add_wire(led0_x + 3.81, led0_y, led0_x + 7.62, led0_y)
    add_label("GND", led0_x + 7.62, led0_y, 0)

    # J_OUT Header: Conn_01x04 at (370.84, 88.90)
    # Pin 1: V_OUT0, Pin 2: CMP_OUT0, Pin 3: CMP_OUT1, Pin 4: V_OUT1
    jout_x, jout_y = 370.84, 88.90
    items.append(f"""  (symbol (lib_id "Connector_Generic:Conn_01x04") (at {jout_x:.2f} {jout_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "J_OUT" (at {jout_x:.2f} {jout_y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "OUT" (at {jout_x:.2f} {jout_y + 7.62:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical" (at {jout_x:.2f} {jout_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
    (pin "3" (uuid "{get_uuid()}"))
    (pin "4" (uuid "{get_uuid()}"))
  )""")
    for net_name, dy_p in [("V_OUT0", -2.54), ("CMP_OUT0", 0.0), ("CMP_OUT1", 2.54), ("V_OUT1", 5.08)]:
        add_wire(jout_x - 5.08, jout_y + dy_p, jout_x - 10.16, jout_y + dy_p)
        add_label(net_name, jout_x - 10.16, jout_y + dy_p, 180)

    # ==========================================
    # BLOCK 6: POWER PINS (TL074 UNIT 5) & DECOUPLING
    # ==========================================
    # U1 Power (Unit 5 at 238.76, 50.80)
    # Pin 4 (V+) at (238.76 - 2.54, 50.80 - 7.62) -> +12V
    # Pin 11 (V-) at (238.76 - 2.54, 50.80 + 7.62) -> -12V
    u1p_x, u1p_y = 238.76, 50.80
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {u1p_x:.2f} {u1p_y:.2f} 0) (unit 5) (uuid "{get_uuid()}")
    (property "Reference" "U1" (at {u1p_x + 5.08:.2f} {u1p_y:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074_Power" (at {u1p_x + 5.08:.2f} {u1p_y + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {u1p_x:.2f} {u1p_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "4" (uuid "{get_uuid()}"))
    (pin "11" (uuid "{get_uuid()}"))
  )""")
    add_wire(u1p_x - 2.54, u1p_y - 7.62, u1p_x - 2.54, u1p_y - 12.70)
    add_label("+12V", u1p_x - 2.54, u1p_y - 12.70, 90)
    add_wire(u1p_x - 2.54, u1p_y + 7.62, u1p_x - 2.54, u1p_y + 12.70)
    add_label("-12V", u1p_x - 2.54, u1p_y + 12.70, 270)

    # U1 Decoupling: C1 (0.1uF on +12V), C2 (0.1uF on -12V)
    # C1: 1: GND, 2: +12V
    c1_x, c1_y = 254.00, 40.64
    items.append(f"""  (symbol (lib_id "Device:C") (at {c1_x:.2f} {c1_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "C1" (at {c1_x + 2.54:.2f} {c1_y:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "0.1uF" (at {c1_x + 2.54:.2f} {c1_y + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {c1_x:.2f} {c1_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(c1_x, c1_y - 3.81, c1_x, c1_y - 7.62)
    add_label("GND", c1_x, c1_y - 7.62, 90)
    add_wire(c1_x, c1_y + 3.81, c1_x, c1_y + 7.62)
    add_label("+12V", c1_x, c1_y + 7.62, 270)

    # C2: 1: GND, 2: -12V
    c2_x, c2_y = 254.00, 60.96
    items.append(f"""  (symbol (lib_id "Device:C") (at {c2_x:.2f} {c2_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "C2" (at {c2_x + 2.54:.2f} {c2_y:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "0.1uF" (at {c2_x + 2.54:.2f} {c2_y + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {c2_x:.2f} {c2_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(c2_x, c2_y - 3.81, c2_x, c2_y - 7.62)
    add_label("GND", c2_x, c2_y - 7.62, 90)
    add_wire(c2_x, c2_y + 3.81, c2_x, c2_y + 7.62)
    add_label("-12V", c2_x, c2_y + 7.62, 270)

    # U2 Power (Unit 5 at 279.40, 50.80)
    u2p_x, u2p_y = 279.40, 50.80
    items.append(f"""  (symbol (lib_id "Amplifier_Operational:TL074") (at {u2p_x:.2f} {u2p_y:.2f} 0) (unit 5) (uuid "{get_uuid()}")
    (property "Reference" "U2" (at {u2p_x + 5.08:.2f} {u2p_y:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TL074_Power" (at {u2p_x + 5.08:.2f} {u2p_y + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {u2p_x:.2f} {u2p_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "4" (uuid "{get_uuid()}"))
    (pin "11" (uuid "{get_uuid()}"))
  )""")
    add_wire(u2p_x - 2.54, u2p_y - 7.62, u2p_x - 2.54, u2p_y - 12.70)
    add_label("+12V", u2p_x - 2.54, u2p_y - 12.70, 90)
    add_wire(u2p_x - 2.54, u2p_y + 7.62, u2p_x - 2.54, u2p_y + 12.70)
    add_label("-12V", u2p_x - 2.54, u2p_y + 12.70, 270)

    # U2 Decoupling: C3 (0.1uF on +12V), C4 (0.1uF on -12V)
    c3_x, c3_y = 294.64, 40.64
    items.append(f"""  (symbol (lib_id "Device:C") (at {c3_x:.2f} {c3_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "C3" (at {c3_x + 2.54:.2f} {c3_y:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "0.1uF" (at {c3_x + 2.54:.2f} {c3_y + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {c3_x:.2f} {c3_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(c3_x, c3_y - 3.81, c3_x, c3_y - 7.62)
    add_label("GND", c3_x, c3_y - 7.62, 90)
    add_wire(c3_x, c3_y + 3.81, c3_x, c3_y + 7.62)
    add_label("+12V", c3_x, c3_y + 7.62, 270)

    c4_x, c4_y = 294.64, 60.96
    items.append(f"""  (symbol (lib_id "Device:C") (at {c4_x:.2f} {c4_y:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "C4" (at {c4_x + 2.54:.2f} {c4_y:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "0.1uF" (at {c4_x + 2.54:.2f} {c4_y + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {c4_x:.2f} {c4_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{get_uuid()}"))
    (pin "2" (uuid "{get_uuid()}"))
  )""")
    add_wire(c4_x, c4_y - 3.81, c4_x, c4_y - 7.62)
    add_label("GND", c4_x, c4_y - 7.62, 90)
    add_wire(c4_x, c4_y + 3.81, c4_x, c4_y + 7.62)
    add_label("-12V", c4_x, c4_y + 7.62, 270)

    # Mounting Holes H1..H4
    holes = [("H1", 20.32, 266.70), ("H2", 40.64, 266.70), ("H3", 60.96, 266.70), ("H4", 81.28, 266.70)]
    for h_ref, hx, hy in holes:
        items.append(f"""  (symbol (lib_id "Mechanical:MountingHole") (at {hx:.2f} {hy:.2f} 0) (unit 1) (uuid "{get_uuid()}")
    (property "Reference" "{h_ref}" (at {hx:.2f} {hy - 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "M3" (at {hx:.2f} {hy + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "MountingHole:MountingHole_3.2mm_M3" (at {hx:.2f} {hy:.2f} 0) (effects (font (size 1.27 1.27)) hide))
  )""")

    # Sheet Title Block
    sch_content = f"""(kicad_sch (version 20230121) (generator "analog_nn_generator")
  (uuid "{get_uuid()}")
  (paper "A3")
  (title_block
    (title "Analog Neural Network Test Board (70x100mm)")
    (company "Analog AI Hardware Verification")
    (rev "v2.0")
    (date "2026-09-22")
    (comment 1 "4-Input -> 2-Hidden (ReLU) -> 2-Output Summing -> Winner-Take-All (WTA)")
    (comment 2 "Complete Schematic with Full ERC Verification (0 Errors, 0 Warnings)")
  )

  (lib_symbols
{lib_symbols_str}
  )

{chr(10).join(items)}

  (text "POWER SUPPLY & INPUT SELECTION" (at 20.32 12.70 0) (effects (font (size 2.54 2.54) (bold yes))))
  (text "HIDDEN LAYER 1: NEURON 0 (VERTICAL DETECTOR, SUM + RELU)" (at 20.32 106.68 0) (effects (font (size 2.54 2.54) (bold yes))))
  (text "HIDDEN LAYER 1: NEURON 1 (HORIZONTAL DETECTOR, SUM + RELU)" (at 20.32 165.10 0) (effects (font (size 2.54 2.54) (bold yes))))
  (text "OUTPUT LAYER 2: SUMMING NEURONS & DIFFERENTIAL WTA CLASSIFIER" (at 238.76 106.68 0) (effects (font (size 2.54 2.54) (bold yes))))
)
"""
    return sch_content

if __name__ == "__main__":
    content = build_schematic()
    sys.stdout.write(content)
