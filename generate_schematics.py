#!/usr/bin/env python3
"""
generate_schematics.py
----------------------
Generates complete KiCad schematics (.kicad_sch) for the 4-board Discrete Analog
MNIST Neural Network Stack:
1. motherboard.kicad_sch
2. daughtercard1_weights_l1.kicad_sch
3. daughtercard2_relu_l1.kicad_sch
4. daughtercard3_weights_l2_wta.kicad_sch
"""

import json
import os
import uuid
from kicad_symbols import LIB_SYMBOLS_COMMON

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))


def make_uuid():
    return str(uuid.uuid4())


def format_res(val):
    if val is None:
        return "DNP"
    if val >= 1e6:
        return f"{val / 1e6:.3g}M"
    elif val >= 1e3:
        return f"{val / 1e3:.3g}k"
    else:
        return f"{val:.3g}"


# =============================================================================
# 1. DAUGHTERCARD 1: Layer 1 Weights (64x16) + Summing Op-Amps
# =============================================================================
def generate_daughtercard1_sch(output_path, weights_path):
    with open(weights_path) as f:
        l1 = json.load(f)

    lines = [
        '(kicad_sch (version 20230121) (generator "analog_nn_generator")',
        f'  (uuid "{make_uuid()}")',
        '  (paper "A0")',
        '  (title_block',
        '    (title "Daughtercard 1: Layer 1 Synaptic Weights & Summing (64x16)")',
        '    (company "Discrete Analog MNIST PCB Stack")',
        '    (rev "v1.0")',
        '    (date "2026-09-11")',
        '  )',
        LIB_SYMBOLS_COMMON,
    ]

    # Power Flags
    for pwr, y in [("+12V", 30), ("-12V", 40), ("GND", 50)]:
        lines.append(f'  (symbol (lib_id "power:{pwr}") (at 20.0 {y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#PWR" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "{pwr}" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')
        lines.append(f'  (symbol (lib_id "power:PWR_FLAG") (at 20.0 {y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#FLG" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "PWR_FLAG" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')

    # Connectors J1_A (Pins 0..31), J1_B (Pins 32..63), J1_OUT (Sums 0..15)
    # J1_A at (40, 100)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x20_Odd_Even") (at 40.0 100.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J1_A" (at 40.0 70.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Inputs_0_31" (at 40.0 73.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical" (at 40.0 100.0 0) (effects (font (size 1.27 1.27)) hide))')
    for pin_idx in range(1, 41):
        lines.append(f'    (pin "{pin_idx}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # J1_B at (100, 100)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x20_Odd_Even") (at 100.0 100.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J1_B" (at 100.0 70.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Inputs_32_63" (at 100.0 73.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical" (at 100.0 100.0 0) (effects (font (size 1.27 1.27)) hide))')
    for pin_idx in range(1, 41):
        lines.append(f'    (pin "{pin_idx}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # J1_OUT at (160, 100)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 160.0 100.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J1_OUT" (at 160.0 85.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "L1_Sums_0_15" (at 160.0 88.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 160.0 100.0 0) (effects (font (size 1.27 1.27)) hide))')
    for pin_idx in range(1, 21):
        lines.append(f'    (pin "{pin_idx}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # Power Decoupling for 4x TL074 (U1..U4)
    # Bulk Caps C_bulk1, C_bulk2
    for b_idx, (b_rail, b_y) in enumerate([("+12V", 35), ("-12V", 45)]):
        lines.append(f'  (symbol (lib_id "Device:C_Polarized") (at 60.0 {b_y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "C_BULK{b_idx+1}" (at 63.0 {b_y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "10uF" (at 63.0 {b_y+2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Capacitor_SMD:CP_Elec_6.3x5.4" (at 60.0 {b_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

    for u_idx in range(4):
        u_num = u_idx + 1
        x_pwr = 80.0 + u_idx * 30.0
        # C_pos
        lines.append(f'  (symbol (lib_id "Device:C") (at {x_pwr:.2f} 35.0 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "C_U{u_num}P" (at {x_pwr+3:.2f} 35.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "0.1uF" (at {x_pwr+3:.2f} 37.54 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {x_pwr:.2f} 35.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')
        # C_neg
        lines.append(f'  (symbol (lib_id "Device:C") (at {x_pwr:.2f} 45.0 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "C_U{u_num}N" (at {x_pwr+3:.2f} 45.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "0.1uF" (at {x_pwr+3:.2f} 47.54 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {x_pwr:.2f} 45.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')
        # TL074 Unit 5 (Power)
        lines.append(f'  (symbol (lib_id "Amplifier_Operational:TL074") (at {x_pwr+15:.2f} 40.0 0) (unit 5) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "U{u_num}" (at {x_pwr+20:.2f} 40.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "TL074" (at {x_pwr+20:.2f} 42.54 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {x_pwr+15:.2f} 40.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "4" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "11" (uuid "{make_uuid()}"))')
        lines.append('  )')

    # 16 Neurons (Summing Op-Amps & Resistors)
    # 4 TL074 ICs x 4 units = 16 op-amps
    pin_mapping = [
        (1, "1", "2", "3"),   # Unit 1: out=1, in-=2, in+=3
        (2, "7", "6", "5"),   # Unit 2: out=7, in-=6, in+=5
        (3, "8", "9", "10"),  # Unit 3: out=8, in-=9, in+=10
        (4, "14", "13", "12") # Unit 4: out=14, in-=13, in+=12
    ]

    base_y = 160.0
    y_step = 60.0
    for j in range(16):
        u_idx = j // 4
        unit_in_ic = (j % 4) + 1
        unit_num, out_pin, inn_pin, inp_pin = pin_mapping[j % 4]
        u_ref = f"U{u_idx + 1}"

        cur_y = base_y + j * y_step
        x_op = 220.0

        # TL074 Op-Amp Unit
        lines.append(f'  (symbol (lib_id "Amplifier_Operational:TL074") (at {x_op:.2f} {cur_y:.2f} 0) (unit {unit_num}) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "{u_ref}" (at {x_op:.2f} {cur_y-7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "TL074" (at {x_op:.2f} {cur_y+7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {x_op:.2f} {cur_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "{out_pin}" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "{inn_pin}" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "{inp_pin}" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Ground on non-inverting input
        lines.append(f'  (symbol (lib_id "power:GND") (at {x_op-7.62:.2f} {cur_y+5.08:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#PWR" (at {x_op-7.62:.2f} {cur_y+5.08:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "GND" (at {x_op-7.62:.2f} {cur_y+7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Feedback resistor Rf = 10k
        rf_x = x_op
        rf_y = cur_y - 12.0
        lines.append(f'  (symbol (lib_id "Device:R") (at {rf_x:.2f} {rf_y:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "Rf_N{j}" (at {rf_x:.2f} {rf_y-4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "10k" (at {rf_x:.2f} {rf_y+4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rf_x:.2f} {rf_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Bias Resistor Rb
        n_info = l1["weights"][j]
        rb_str = n_info["bias_resistor_str"]
        rb_rail = n_info["bias_rail"]
        rb_x = x_op - 40.0
        rb_y = cur_y - 12.0
        lines.append(f'  (symbol (lib_id "Device:R") (at {rb_x:.2f} {rb_y:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "Rb_N{j}" (at {rb_x:.2f} {rb_y-4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "{rb_str}" (at {rb_x:.2f} {rb_y+4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rb_x:.2f} {rb_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Bias reference power label
        lines.append(f'  (global_label "{rb_rail}" (shape input) (at {rb_x-10.0:.2f} {rb_y:.2f} 180) (effects (font (size 1.27 1.27))) (uuid "{make_uuid()}"))')

        # Output label V_SUM_j
        lines.append(f'  (global_label "V_SUM_{j}" (shape output) (at {x_op+15.0:.2f} {cur_y:.2f} 0) (effects (font (size 1.27 1.27))) (uuid "{make_uuid()}"))')

        # 64 Input weight resistors for neuron j
        # Arranged in 8 columns x 8 rows to the left of the summing op-amp
        for i in range(64):
            inp_info = n_info["inputs"][i]
            r_str = inp_info["resistor_str"]
            is_pop = inp_info["is_populated"]
            polarity = inp_info["polarity"]
            in_net = f"-V_IN_{i}" if polarity == "positive" else f"V_IN_{i}"

            col = i % 8
            row = i // 8
            rx = x_op - 180.0 + col * 18.0
            ry = cur_y - 20.0 + row * 6.0

            r_ref = f"R1_{i}_{j}"
            lines.append(f'  (symbol (lib_id "Device:R") (at {rx:.2f} {ry:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
            lines.append(f'    (property "Reference" "{r_ref}" (at {rx:.2f} {ry-2.5:.2f} 0) (effects (font (size 1.0 1.0))))')
            lines.append(f'    (property "Value" "{r_str}" (at {rx:.2f} {ry+2.5:.2f} 0) (effects (font (size 1.0 1.0))))')
            lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rx:.2f} {ry:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
            lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
            lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
            lines.append('  )')

    lines.append('  (sheet_instances (path "/" (page "1")))')
    lines.append(')')

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_path}")


# =============================================================================
# 2. DAUGHTERCARD 2: Layer 1 Rectification & Buffer (16 Precision ReLUs)
# =============================================================================
def generate_daughtercard2_sch(output_path):
    lines = [
        '(kicad_sch (version 20230121) (generator "analog_nn_generator")',
        f'  (uuid "{make_uuid()}")',
        '  (paper "A1")',
        '  (title_block',
        '    (title "Daughtercard 2: Layer 1 Precision Half-Wave Active Rectifiers (ReLU)")',
        '    (company "Discrete Analog MNIST PCB Stack")',
        '    (rev "v1.0")',
        '    (date "2026-09-11")',
        '  )',
        LIB_SYMBOLS_COMMON,
    ]

    # Power Flags
    for pwr, y in [("+12V", 30), ("-12V", 40), ("GND", 50)]:
        lines.append(f'  (symbol (lib_id "power:{pwr}") (at 20.0 {y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#PWR" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "{pwr}" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')
        lines.append(f'  (symbol (lib_id "power:PWR_FLAG") (at 20.0 {y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#FLG" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "PWR_FLAG" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')

    # Connectors J2_IN (Sums from DC1) and J2_OUT (Activations to DC3)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 40.0 100.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J2_IN" (at 40.0 85.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Sums_In" (at 40.0 88.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 40.0 100.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 21):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 100.0 100.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J2_OUT" (at 100.0 85.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Act_Out" (at 100.0 88.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 100.0 100.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 21):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # Decoupling for 4x TL074 (U1..U4)
    for u_idx in range(4):
        u_num = u_idx + 1
        x_pwr = 140.0 + u_idx * 35.0
        lines.append(f'  (symbol (lib_id "Device:C") (at {x_pwr:.2f} 35.0 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "C_U{u_num}P" (at {x_pwr+3:.2f} 35.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "0.1uF" (at {x_pwr+3:.2f} 37.54 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {x_pwr:.2f} 35.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        lines.append(f'  (symbol (lib_id "Device:C") (at {x_pwr:.2f} 45.0 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "C_U{u_num}N" (at {x_pwr+3:.2f} 45.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "0.1uF" (at {x_pwr+3:.2f} 47.54 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {x_pwr:.2f} 45.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        lines.append(f'  (symbol (lib_id "Amplifier_Operational:TL074") (at {x_pwr+15:.2f} 40.0 0) (unit 5) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "U{u_num}" (at {x_pwr+20:.2f} 40.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "TL074" (at {x_pwr+20:.2f} 42.54 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {x_pwr+15:.2f} 40.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "4" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "11" (uuid "{make_uuid()}"))')
        lines.append('  )')

    # 16 Active Rectifier Channels
    pin_mapping = [
        (1, "1", "2", "3"),
        (2, "7", "6", "5"),
        (3, "8", "9", "10"),
        (4, "14", "13", "12")
    ]

    base_y = 150.0
    y_step = 45.0
    for j in range(16):
        u_idx = j // 4
        unit_num, out_pin, inn_pin, inp_pin = pin_mapping[j % 4]
        u_ref = f"U{u_idx + 1}"
        cur_y = base_y + j * y_step

        # Global input label V_SUM_j
        lines.append(f'  (global_label "V_SUM_{j}" (shape input) (at 50.0 {cur_y:.2f} 180) (effects (font (size 1.27 1.27))) (uuid "{make_uuid()}"))')

        # Rin (10k)
        lines.append(f'  (symbol (lib_id "Device:R") (at 75.0 {cur_y:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "Rin_{j}" (at 75.0 {cur_y-4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "10k" (at 75.0 {cur_y+4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at 75.0 {cur_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # TL074 Op-Amp Unit
        x_op = 120.0
        lines.append(f'  (symbol (lib_id "Amplifier_Operational:TL074") (at {x_op:.2f} {cur_y:.2f} 0) (unit {unit_num}) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "{u_ref}" (at {x_op:.2f} {cur_y-7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "TL074" (at {x_op:.2f} {cur_y+7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {x_op:.2f} {cur_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "{out_pin}" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "{inn_pin}" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "{inp_pin}" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Ground on non-inverting input
        lines.append(f'  (symbol (lib_id "power:GND") (at {x_op-7.62:.2f} {cur_y+5.08:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#PWR" (at {x_op-7.62:.2f} {cur_y+5.08:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "GND" (at {x_op-7.62:.2f} {cur_y+7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Clamping Diode D2 (Anode to op-amp output, Cathode to inverting node)
        lines.append(f'  (symbol (lib_id "Device:D") (at 125.0 {cur_y-12.0:.2f} 180) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "D2_{j}" (at 125.0 {cur_y-15.0:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "1N4148" (at 125.0 {cur_y-9.0:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Diode_SMD:D_SOD-123" (at 125.0 {cur_y-12.0:.2f} 180) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Forward Diode D1 (Anode to op-amp output, Cathode to V_act_j)
        lines.append(f'  (symbol (lib_id "Device:D") (at 145.0 {cur_y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "D1_{j}" (at 145.0 {cur_y-4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "1N4148" (at 145.0 {cur_y+4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Diode_SMD:D_SOD-123" (at 145.0 {cur_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Rrelu (10k) linear feedback resistor from V_act_j to inverting node
        lines.append(f'  (symbol (lib_id "Device:R") (at 125.0 {cur_y-20.0:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "Rrelu_{j}" (at 125.0 {cur_y-24:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "10k" (at 125.0 {cur_y-16:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at 125.0 {cur_y-20.0:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Global output label V_ACT_j
        lines.append(f'  (global_label "V_ACT_{j}" (shape output) (at 165.0 {cur_y:.2f} 0) (effects (font (size 1.27 1.27))) (uuid "{make_uuid()}"))')

    lines.append('  (sheet_instances (path "/" (page "1")))')
    lines.append(')')

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_path}")


# =============================================================================
# 3. DAUGHTERCARD 3: Layer 2 Weights (16x10) + Summing + Winner-Take-All + LEDs
# =============================================================================
def generate_daughtercard3_sch(output_path, weights_path):
    with open(weights_path) as f:
        l2 = json.load(f)

    lines = [
        '(kicad_sch (version 20230121) (generator "analog_nn_generator")',
        f'  (uuid "{make_uuid()}")',
        '  (paper "A1")',
        '  (title_block',
        '    (title "Daughtercard 3: Layer 2 Synaptic Weights & Winner-Take-All Argmax")',
        '    (company "Discrete Analog MNIST PCB Stack")',
        '    (rev "v1.0")',
        '    (date "2026-09-11")',
        '  )',
        LIB_SYMBOLS_COMMON,
    ]

    # Power Flags
    for pwr, y in [("+12V", 30), ("-12V", 40), ("+5V", 50), ("GND", 60)]:
        lines.append(f'  (symbol (lib_id "power:{pwr}") (at 20.0 {y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#PWR" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "{pwr}" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')
        lines.append(f'  (symbol (lib_id "power:PWR_FLAG") (at 20.0 {y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#FLG" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "PWR_FLAG" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')

    # Input Connector J3_IN (16 activations from DC2)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 40.0 100.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J3_IN" (at 40.0 85.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Act_In_0_15" (at 40.0 88.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 40.0 100.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 21):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # Decoupling for 3x TL074 (U1..U3) and 3x LM339 (U4..U6)
    for u_idx in range(3):
        u_num = u_idx + 1
        x_pwr = 80.0 + u_idx * 30.0
        # TL074 Power Unit
        lines.append(f'  (symbol (lib_id "Amplifier_Operational:TL074") (at {x_pwr:.2f} 35.0 0) (unit 5) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "U{u_num}" (at {x_pwr:.2f} 30.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "TL074" (at {x_pwr:.2f} 42.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {x_pwr:.2f} 35.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "4" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "11" (uuid "{make_uuid()}"))')
        lines.append('  )')
        # Decoupling Caps
        lines.append(f'  (symbol (lib_id "Device:C") (at {x_pwr+10:.2f} 32.0 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "C_U{u_num}P" (at {x_pwr+12:.2f} 32.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "0.1uF" (at {x_pwr+12:.2f} 34.54 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {x_pwr+10:.2f} 32.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

    for c_idx in range(3):
        cmp_num = c_idx + 4
        x_pwr = 180.0 + c_idx * 30.0
        # LM339 Power Unit
        lines.append(f'  (symbol (lib_id "Comparator:LM339") (at {x_pwr:.2f} 35.0 0) (unit 5) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "U{cmp_num}" (at {x_pwr:.2f} 30.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "LM339" (at {x_pwr:.2f} 42.0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {x_pwr:.2f} 35.0 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "3" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "12" (uuid "{make_uuid()}"))')
        lines.append('  )')

    # 10 Digit Classes: Summing Op-Amps + WTA Comparators + LEDs
    tl074_pins = [
        (1, "1", "2", "3"),
        (2, "7", "6", "5"),
        (3, "8", "9", "10"),
        (4, "14", "13", "12")
    ]
    lm339_pins = [
        (1, "2", "4", "5"),   # out=2, in-=4, in+=5
        (2, "1", "6", "7"),   # out=1, in-=6, in+=7
        (3, "14", "8", "9"),  # out=14, in-=8, in+=9
        (4, "13", "10", "11") # out=13, in-=10, in+=11
    ]

    base_y = 150.0
    y_step = 60.0
    for k in range(10):
        cur_y = base_y + k * y_step

        # Summing Op-Amp (TL074)
        u_idx = k // 4
        unit_num, out_pin, inn_pin, inp_pin = tl074_pins[k % 4]
        u_ref = f"U{u_idx + 1}"
        x_op = 160.0

        lines.append(f'  (symbol (lib_id "Amplifier_Operational:TL074") (at {x_op:.2f} {cur_y:.2f} 0) (unit {unit_num}) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "{u_ref}" (at {x_op:.2f} {cur_y-7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "TL074" (at {x_op:.2f} {cur_y+7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {x_op:.2f} {cur_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "{out_pin}" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "{inn_pin}" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "{inp_pin}" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Ground on non-inverting input
        lines.append(f'  (symbol (lib_id "power:GND") (at {x_op-7.62:.2f} {cur_y+5.08:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#PWR" (at {x_op-7.62:.2f} {cur_y+5.08:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "GND" (at {x_op-7.62:.2f} {cur_y+7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Rf2 = 10k feedback resistor
        rf_x = x_op
        rf_y = cur_y - 12.0
        lines.append(f'  (symbol (lib_id "Device:R") (at {rf_x:.2f} {rf_y:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "Rf2_C{k}" (at {rf_x:.2f} {rf_y-4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "10k" (at {rf_x:.2f} {rf_y+4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rf_x:.2f} {rf_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Bias Resistor Rb2
        c_info = l2["weights"][k]
        rb_str = c_info["bias_resistor_str"]
        rb_rail = c_info["bias_rail"]
        rb_x = x_op - 40.0
        rb_y = cur_y - 12.0
        lines.append(f'  (symbol (lib_id "Device:R") (at {rb_x:.2f} {rb_y:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "Rb2_C{k}" (at {rb_x:.2f} {rb_y-4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "{rb_str}" (at {rb_x:.2f} {rb_y+4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rb_x:.2f} {rb_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')
        lines.append(f'  (global_label "{rb_rail}" (shape input) (at {rb_x-10.0:.2f} {rb_y:.2f} 180) (effects (font (size 1.27 1.27))) (uuid "{make_uuid()}"))')

        # 16 Input weight resistors for Class k
        for j in range(16):
            inp_info = c_info["inputs"][j]
            r_str = inp_info["resistor_str"]
            polarity = inp_info["polarity"]
            in_net = f"-V_ACT_{j}" if polarity == "positive" else f"V_ACT_{j}"

            rx = x_op - 110.0 + (j % 4) * 18.0
            ry = cur_y - 15.0 + (j // 4) * 8.0

            r_ref = f"R2_{j}_{k}"
            lines.append(f'  (symbol (lib_id "Device:R") (at {rx:.2f} {ry:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
            lines.append(f'    (property "Reference" "{r_ref}" (at {rx:.2f} {ry-2.5:.2f} 0) (effects (font (size 1.0 1.0))))')
            lines.append(f'    (property "Value" "{r_str}" (at {rx:.2f} {ry+2.5:.2f} 0) (effects (font (size 1.0 1.0))))')
            lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {rx:.2f} {ry:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
            lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
            lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
            lines.append('  )')

        # Winner-Take-All Stage:
        # Diode to common V_MAX bus
        d_x = x_op + 30.0
        lines.append(f'  (symbol (lib_id "Device:D") (at {d_x:.2f} {cur_y-10.0:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "Dwta_{k}" (at {d_x:.2f} {cur_y-14.0:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "1N4148" (at {d_x:.2f} {cur_y-6.0:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Diode_SMD:D_SOD-123" (at {d_x:.2f} {cur_y-10.0:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')
        lines.append(f'  (global_label "V_MAX_BUS" (shape bidirectional) (at {d_x+8.0:.2f} {cur_y-10.0:.2f} 0) (effects (font (size 1.27 1.27))) (uuid "{make_uuid()}"))')

        # LM339 Comparator
        cmp_idx = k // 4
        cmp_u_num, cmp_out, cmp_inn, cmp_inp = lm339_pins[k % 4]
        cmp_ref = f"U{cmp_idx + 4}"
        x_cmp = x_op + 70.0

        lines.append(f'  (symbol (lib_id "Comparator:LM339") (at {x_cmp:.2f} {cur_y:.2f} 0) (unit {cmp_u_num}) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "{cmp_ref}" (at {x_cmp:.2f} {cur_y-7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "LM339" (at {x_cmp:.2f} {cur_y+7.62:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (at {x_cmp:.2f} {cur_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "{cmp_out}" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "{cmp_inn}" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "{cmp_inp}" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # Indicator LED k + 1k Pullup Resistor to +5V
        x_led = x_cmp + 30.0
        lines.append(f'  (symbol (lib_id "Device:LED") (at {x_led:.2f} {cur_y:.2f} 180) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "LED_{k}" (at {x_led:.2f} {cur_y-4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "Digit_{k}" (at {x_led:.2f} {cur_y+4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "LED_SMD:LED_0805_2012Metric" (at {x_led:.2f} {cur_y:.2f} 180) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')

        # 1k Limiting Resistor to +5V
        lines.append(f'  (symbol (lib_id "Device:R") (at {x_led+15.0:.2f} {cur_y:.2f} 90) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "Rled_{k}" (at {x_led+15.0:.2f} {cur_y-4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "1k" (at {x_led+15.0:.2f} {cur_y+4:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at {x_led+15.0:.2f} {cur_y:.2f} 90) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append(f'    (pin "2" (uuid "{make_uuid()}"))')
        lines.append('  )')
        lines.append(f'  (symbol (lib_id "power:+5V") (at {x_led+25.0:.2f} {cur_y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#PWR" (at {x_led+25.0:.2f} {cur_y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "+5V" (at {x_led+25.0:.2f} {cur_y-3.81:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')

    lines.append('  (sheet_instances (path "/" (page "1")))')
    lines.append(')')

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_path}")


# =============================================================================
# 4. BASEBOARD / MOTHERBOARD: Power Regulation, Pixel Bus, Card Slots
# =============================================================================
def generate_motherboard_sch(output_path):
    lines = [
        '(kicad_sch (version 20230121) (generator "analog_nn_generator")',
        f'  (uuid "{make_uuid()}")',
        '  (paper "A1")',
        '  (title_block',
        '    (title "Baseboard / Motherboard: Dual Power Supply & Card Slots")',
        '    (company "Discrete Analog MNIST PCB Stack")',
        '    (rev "v1.0")',
        '    (date "2026-09-11")',
        '  )',
        LIB_SYMBOLS_COMMON,
    ]

    # Power Flags
    for pwr, y in [("+12V", 30), ("-12V", 40), ("+5V", 50), ("GND", 60)]:
        lines.append(f'  (symbol (lib_id "power:{pwr}") (at 20.0 {y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#PWR" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "{pwr}" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')
        lines.append(f'  (symbol (lib_id "power:PWR_FLAG") (at 20.0 {y:.2f} 0) (unit 1) (uuid "{make_uuid()}")')
        lines.append(f'    (property "Reference" "#FLG" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        lines.append(f'    (property "Value" "PWR_FLAG" (at 20.0 {y:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (pin "1" (uuid "{make_uuid()}"))')
        lines.append('  )')

    # DC Input Power Terminal Block J_PWR_IN at (50, 60)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 50.0 60.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_PWR_IN" (at 50.0 45.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Power_Input" (at 50.0 48.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 50.0 60.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 21):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # Pixel Breakout Headers J_PIXELS_A, J_PIXELS_B
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x20_Odd_Even") (at 100.0 60.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_PIXELS_A" (at 100.0 30.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Pixels_0_31" (at 100.0 33.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical" (at 100.0 60.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 41):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x20_Odd_Even") (at 160.0 60.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_PIXELS_B" (at 160.0 30.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Pixels_32_63" (at 160.0 33.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical" (at 160.0 60.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 41):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # Slot 1: Daughtercard 1 Connectors (J_SLOT1_A, J_SLOT1_B, J_SLOT1_OUT)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x20_Odd_Even") (at 50.0 140.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_SLOT1_A" (at 50.0 110.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Slot1_Inputs_A" (at 50.0 113.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical" (at 50.0 140.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 41):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x20_Odd_Even") (at 100.0 140.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_SLOT1_B" (at 100.0 110.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Slot1_Inputs_B" (at 100.0 113.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical" (at 100.0 140.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 41):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 150.0 140.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_SLOT1_OUT" (at 150.0 125.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Slot1_Sums_Out" (at 150.0 128.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 150.0 140.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 21):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # Slot 2: Daughtercard 2 Connectors (J_SLOT2_IN, J_SLOT2_OUT)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 50.0 200.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_SLOT2_IN" (at 50.0 185.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Slot2_Sums_In" (at 50.0 188.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 50.0 200.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 21):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 100.0 200.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_SLOT2_OUT" (at 100.0 185.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Slot2_Act_Out" (at 100.0 188.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 100.0 200.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 21):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # Slot 3: Daughtercard 3 Connectors (J_SLOT3_IN, J_SLOT3_PWR)
    lines.append(f'  (symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") (at 50.0 260.0 0) (unit 1) (uuid "{make_uuid()}")')
    lines.append('    (property "Reference" "J_SLOT3_IN" (at 50.0 245.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "Slot3_Act_In" (at 50.0 248.0 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical" (at 50.0 260.0 0) (effects (font (size 1.27 1.27)) hide))')
    for p in range(1, 21):
        lines.append(f'    (pin "{p}" (uuid "{make_uuid()}"))')
    lines.append('  )')

    # Inter-Slot Bus Routing Labels
    for j in range(16):
        lines.append(f'  (global_label "V_SUM_{j}" (shape bidirectional) (at 150.0 {180.0+j*3:.2f} 0) (effects (font (size 1.0 1.0))) (uuid "{make_uuid()}"))')
        lines.append(f'  (global_label "V_ACT_{j}" (shape bidirectional) (at 180.0 {180.0+j*3:.2f} 0) (effects (font (size 1.0 1.0))) (uuid "{make_uuid()}"))')

    lines.append('  (sheet_instances (path "/" (page "1")))')
    lines.append(')')

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_path}")


def main():
    w1_file = os.path.join(WORKSPACE_DIR, "weights_layer1.json")
    w2_file = os.path.join(WORKSPACE_DIR, "weights_layer2.json")
    
    generate_motherboard_sch(os.path.join(WORKSPACE_DIR, "motherboard.kicad_sch"))
    generate_daughtercard1_sch(os.path.join(WORKSPACE_DIR, "daughtercard1_weights_l1.kicad_sch"), w1_file)
    generate_daughtercard2_sch(os.path.join(WORKSPACE_DIR, "daughtercard2_relu_l1.kicad_sch"))
    generate_daughtercard3_sch(os.path.join(WORKSPACE_DIR, "daughtercard3_weights_l2_wta.kicad_sch"), w2_file)
    print("All 4 schematics generated successfully!")


if __name__ == "__main__":
    main()
