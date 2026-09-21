#!/usr/bin/env python3
"""
generate_bom.py
---------------
Generates a consolidated Bill of Materials (BOM) CSV for the 4-board
Discrete Analog MNIST Neural Network Stack:
- Reference Designator
- Component Value
- Footprint / Package
- Description
- Quantity
- Board / Subsystem
- LCSC Part Number (for JLCPCB SMT assembly)
"""

import csv
import json
import os
from collections import defaultdict

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

# Standard LCSC Part Numbers for common components
LCSC_MAPPING = {
    "TL074": "C6982",
    "LM339": "C2684873",
    "1N4148": "C81598",
    "0.1uF": "C49678",
    "10uF": "C15850",
    "LM7812": "C31057",
    "LM7912": "C77864",
    "TL431": "C49969",
    "Green": "C2290",
    "Blue": "C2293",
    "Yellow": "C2294",
    "Red": "C2286",
    "10k": "C17414",
    "1k": "C17513",
    "47k": "C17713",
    "Conn_02x20_Odd_Even": "C2938830",
    "Conn_02x10_Odd_Even": "C2938827",
}

# Generic fallback for E96 resistors
def get_lcsc_part(val, footprint, comp_type=""):
    if val in LCSC_MAPPING:
        return LCSC_MAPPING[val]
    if comp_type == "LED" or "Digit_" in val:
        return "C2290"  # Green 0805 LED
    if "Resistor" in footprint or comp_type == "R":
        # E96 0805 1% Resistor series
        return f"C_0805_1%_{val}"
    if "Capacitor" in footprint:
        return "C49678"
    if "Connector" in footprint:
        if "2x20" in footprint:
            return "C2938830"
        return "C2938827"
    return "N/A"


def collect_bom():
    w1_file = os.path.join(WORKSPACE_DIR, "weights_layer1.json")
    w2_file = os.path.join(WORKSPACE_DIR, "weights_layer2.json")
    with open(w1_file) as f:
        l1 = json.load(f)
    with open(w2_file) as f:
        l2 = json.load(f)

    items = []

    # 1. Motherboard
    mb_comps = [
        ("J_PWR_IN", "Power_Input", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Power Input Header", "Motherboard", "C2938827"),
        ("J_PIXELS_A", "Pixels_0_31", "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical", "2x20 Pixel Input Header (0-31)", "Motherboard", "C2938830"),
        ("J_PIXELS_B", "Pixels_32_63", "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical", "2x20 Pixel Input Header (32-63)", "Motherboard", "C2938830"),
        ("J_SLOT1_A", "Slot1_Inputs_A", "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical", "2x20 Card Slot 1 Connector A", "Motherboard", "C2938830"),
        ("J_SLOT1_B", "Slot1_Inputs_B", "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical", "2x20 Card Slot 1 Connector B", "Motherboard", "C2938830"),
        ("J_SLOT1_OUT", "Slot1_Sums_Out", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Card Slot 1 Output Connector", "Motherboard", "C2938827"),
        ("J_SLOT2_IN", "Slot2_Sums_In", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Card Slot 2 Input Connector", "Motherboard", "C2938827"),
        ("J_SLOT2_OUT", "Slot2_Act_Out", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Card Slot 2 Output Connector", "Motherboard", "C2938827"),
        ("J_SLOT3_IN", "Slot3_Act_In", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Card Slot 3 Input Connector", "Motherboard", "C2938827"),
        ("U_REG1", "LM7812", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", "+12V Linear Voltage Regulator", "Motherboard", "C31057"),
        ("U_REG2", "LM7912", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", "-12V Linear Voltage Regulator", "Motherboard", "C77864"),
        ("C_IN1, C_OUT1", "10uF", "Capacitor_SMD:C_0805_2012Metric", "10uF 25V Power Filter Capacitor", "Motherboard", "C15850"),
        ("C_IN2, C_OUT2", "10uF", "Capacitor_SMD:C_0805_2012Metric", "10uF 25V Power Filter Capacitor", "Motherboard", "C15850"),
        ("LED_12P", "Green", "LED_SMD:LED_0805_2012Metric", "+12V Rail Power Status Indicator", "Motherboard", "C2290"),
        ("LED_12N", "Blue", "LED_SMD:LED_0805_2012Metric", "-12V Rail Power Status Indicator", "Motherboard", "C2293"),
        ("LED_5P", "Yellow", "LED_SMD:LED_0805_2012Metric", "+5V Ref Power Status Indicator", "Motherboard", "C2294"),
    ]
    items.extend(mb_comps)

    # 2. Daughtercard 1
    dc1_headers = [
        ("J1_A", "Inputs_0_31", "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical", "2x20 Input Connector A", "Daughtercard 1", "C2938830"),
        ("J1_B", "Inputs_32_63", "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical", "2x20 Input Connector B", "Daughtercard 1", "C2938830"),
        ("J1_OUT", "Sums_Out", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Output Connector", "Daughtercard 1", "C2938827"),
    ]
    items.extend(dc1_headers)
    for u in range(1, 5):
        items.append((f"U{u}", "TL074", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", "Quad JFET Op-Amp (Summing)", "Daughtercard 1", "C6982"))
        items.append((f"C_U{u}P", "0.1uF", "Capacitor_SMD:C_0805_2012Metric", "0.1uF V+ Decoupling", "Daughtercard 1", "C49678"))
        items.append((f"C_U{u}N", "0.1uF", "Capacitor_SMD:C_0805_2012Metric", "0.1uF V- Decoupling", "Daughtercard 1", "C49678"))

    for j in range(16):
        n_info = l1["weights"][j]
        items.append((f"Rf_N{j}", "10k", "Resistor_SMD:R_0805_2012Metric", "Neuron Feedback Resistor 1%", "Daughtercard 1", "C17414"))
        rb_str = n_info["bias_resistor_str"]
        items.append((f"Rb_N{j}", rb_str, "Resistor_SMD:R_0805_2012Metric", f"Neuron Bias Resistor ({n_info['bias_rail']})", "Daughtercard 1", get_lcsc_part(rb_str, "Resistor")))
        for i in range(64):
            inp = n_info["inputs"][i]
            r_str = inp["resistor_str"]
            items.append((f"R1_{i}_{j}", r_str, "Resistor_SMD:R_0805_2012Metric", f"L1 Weight Resistor W({i},{j})", "Daughtercard 1", get_lcsc_part(r_str, "Resistor")))

    # 3. Daughtercard 2
    dc2_headers = [
        ("J2_IN", "Sums_In", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Input Sums Connector", "Daughtercard 2", "C2938827"),
        ("J2_OUT", "Act_Out", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Output Activations Connector", "Daughtercard 2", "C2938827"),
    ]
    items.extend(dc2_headers)
    for u in range(1, 5):
        items.append((f"U{u}", "TL074", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", "Quad JFET Op-Amp (Active Rectifier)", "Daughtercard 2", "C6982"))
        items.append((f"C_U{u}P", "0.1uF", "Capacitor_SMD:C_0805_2012Metric", "0.1uF V+ Decoupling", "Daughtercard 2", "C49678"))
        items.append((f"C_U{u}N", "0.1uF", "Capacitor_SMD:C_0805_2012Metric", "0.1uF V- Decoupling", "Daughtercard 2", "C49678"))

    for j in range(16):
        items.append((f"Rin_{j}", "10k", "Resistor_SMD:R_0805_2012Metric", "Rectifier Input Coupling Resistor 1%", "Daughtercard 2", "C17414"))
        items.append((f"Rrelu_{j}", "10k", "Resistor_SMD:R_0805_2012Metric", "Rectifier Linear Feedback Resistor 1%", "Daughtercard 2", "C17414"))
        items.append((f"D1_{j}", "1N4148", "Diode_SMD:D_SOD-123", "Active Forward Path Diode", "Daughtercard 2", "C81598"))
        items.append((f"D2_{j}", "1N4148", "Diode_SMD:D_SOD-123", "Anti-Saturation Clamping Diode", "Daughtercard 2", "C81598"))

    # 4. Daughtercard 3
    dc3_headers = [
        ("J3_IN", "Act_In", "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical", "2x10 Input Activations Connector", "Daughtercard 3", "C2938827"),
    ]
    items.extend(dc3_headers)
    for u in range(1, 4):
        items.append((f"U{u}", "TL074", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", "Quad JFET Op-Amp (L2 Summing)", "Daughtercard 3", "C6982"))
        items.append((f"C_U{u}P", "0.1uF", "Capacitor_SMD:C_0805_2012Metric", "0.1uF V+ Decoupling", "Daughtercard 3", "C49678"))
        items.append((f"C_U{u}N", "0.1uF", "Capacitor_SMD:C_0805_2012Metric", "0.1uF V- Decoupling", "Daughtercard 3", "C49678"))

    for c in range(4, 7):
        items.append((f"U{c}", "LM339", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", "Quad Voltage Comparator (WTA)", "Daughtercard 3", "C2684873"))

    for k in range(10):
        c_info = l2["weights"][k]
        items.append((f"LED_{k}", f"Digit_{k}", "LED_SMD:LED_0805_2012Metric", f"Digit {k} Winner Indicator LED (Green)", "Daughtercard 3", "C2290"))
        items.append((f"Rled_{k}", "1k", "Resistor_SMD:R_0805_2012Metric", "LED Current Limiting Resistor 1%", "Daughtercard 3", "C17513"))
        items.append((f"Rf2_C{k}", "10k", "Resistor_SMD:R_0805_2012Metric", f"Class {k} Feedback Resistor 1%", "Daughtercard 3", "C17414"))
        rb_str = c_info["bias_resistor_str"]
        items.append((f"Rb2_C{k}", rb_str, "Resistor_SMD:R_0805_2012Metric", f"Class {k} Bias Resistor", "Daughtercard 3", get_lcsc_part(rb_str, "Resistor")))
        items.append((f"Dwta_{k}", "1N4148", "Diode_SMD:D_SOD-123", "WTA Max-Detector Diode", "Daughtercard 3", "C81598"))

        for j in range(16):
            inp = c_info["inputs"][j]
            r_str = inp["resistor_str"]
            items.append((f"R2_{j}_{k}", r_str, "Resistor_SMD:R_0805_2012Metric", f"L2 Weight Resistor W({j},{k})", "Daughtercard 3", get_lcsc_part(r_str, "Resistor")))

    # Output CSV
    csv_path = os.path.join(WORKSPACE_DIR, "bom_consolidated.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Reference", "Value", "Footprint", "Description", "Board", "LCSC_Part_Number"])
        for item in items:
            writer.writerow(item)

    print(f"Exported {len(items)} components to {csv_path}")

    # Summary breakdown
    val_counts = defaultdict(int)
    board_counts = defaultdict(int)
    for ref, val, fp, desc, board, lcsc in items:
        val_counts[(val, fp, lcsc)] += 1
        board_counts[board] += 1

    summary_path = os.path.join(WORKSPACE_DIR, "bom_summary.csv")
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Value", "Footprint", "LCSC_Part_Number", "Total_Quantity"])
        for (val, fp, lcsc), count in sorted(val_counts.items(), key=lambda x: -x[1]):
            writer.writerow([val, fp, lcsc, count])

    print(f"Exported grouped summary to {summary_path}")
    print("Board breakdown:")
    for b, cnt in board_counts.items():
        print(f"  {b}: {cnt} components")


if __name__ == "__main__":
    collect_bom()
