#!/usr/bin/env python3
"""
emulate_test_board.py
---------------------
Direct hardware emulator for the 70x100 mm Analog Neural Network Test Board.
Simulates all 16 input binary combinations (0000_2 to 1111_2) and computes
expected voltages at every physical test point and pin on the board:
  - TP_X0 .. TP_X3 (Inputs)
  - TP_SUM0, TP_SUM1 (Neuron summing nodes)
  - TP_ACT0, TP_ACT1 (ReLU activation outputs)
  - TP_OUT0, TP_OUT1 (Output summing stages)
  - J_OUT.2 (CMP_OUT0) & J_OUT.3 (CMP_OUT1) (WTA Winner-Take-All comparators)
  - LED1 (Red, Vertical) & LED0 (Green, Horizontal) indicator states

Use this table on the lab bench with a digital multimeter (DMM) or oscilloscope
to verify circuit operation.
"""

import sys

def simulate_board():
    # Board component values
    V_CC = 12.0
    V_EE = -12.0
    V_IN_HIGH = 5.0
    V_IN_LOW = 0.0

    # Neuron 0 & 1 Summing Resistors
    R_in = 10000.0    # 10k
    R_f1 = 10000.0    # 10k
    R_b1 = 18000.0    # 18k to -12V

    # Output Summing Resistors
    R_f2 = 10000.0    # 10k
    R_2_act0 = 10000.0 # 10k
    R_2_act1 = 10000.0 # 10k
    R_b2_0 = 15000.0  # 15k to -12V
    R_b2_1 = 22000.0  # 22k to -12V (reference threshold)

    # TL074 Op-amp saturation limits with +/-12V supply
    V_SAT_POS = 10.5
    V_SAT_NEG = -10.5

    results = []

    for state in range(16):
        x0 = 1 if (state & 8) else 0
        x1 = 1 if (state & 4) else 0
        x2 = 1 if (state & 2) else 0
        x3 = 1 if (state & 1) else 0

        vx0 = V_IN_HIGH if x0 else V_IN_LOW
        vx1 = V_IN_HIGH if x1 else V_IN_LOW
        vx2 = V_IN_HIGH if x2 else V_IN_LOW
        vx3 = V_IN_HIGH if x3 else V_IN_LOW

        # 1. Neuron 0 Summing Node (Vertical Feature Detector: X0 & X1)
        # I_sum0 = vx0/R_in + vx1/R_in + V_EE/R_b1
        # V_SUM0 = - R_f1 * I_sum0
        i_sum0 = (vx0 / R_in) + (vx1 / R_in) + (V_EE / R_b1)
        v_sum0 = - R_f1 * i_sum0

        # 2. Neuron 0 Rectifier (Precision Inverting Half-Wave ReLU)
        # V_ACT0 = max(0.0, -v_sum0)
        v_act0 = max(0.0, -v_sum0)

        # 3. Neuron 1 Summing Node (Horizontal Feature Detector: X2 & X3)
        i_sum1 = (vx2 / R_in) + (vx3 / R_in) + (V_EE / R_b1)
        v_sum1 = - R_f1 * i_sum1
        v_act1 = max(0.0, -v_sum1)

        # 4. Output Summing Stages
        # Output 0 (Vertical Class):
        i_sum2_0 = (v_act0 / R_2_act0) + (v_act1 / R_2_act1) + (V_EE / R_b2_0)
        v_out0 = - R_f2 * i_sum2_0
        v_out0 = max(V_SAT_NEG, min(V_SAT_POS, v_out0))

        # Output 1 (Horizontal / Fixed Reference Class):
        i_sum2_1 = (V_EE / R_b2_1)
        v_out1 = - R_f2 * i_sum2_1
        v_out1 = max(V_SAT_NEG, min(V_SAT_POS, v_out1))

        # 5. WTA Differential Comparators
        cmp0 = V_SAT_POS if (v_out0 > v_out1) else V_SAT_NEG
        cmp1 = V_SAT_POS if (v_out1 > v_out0) else V_SAT_NEG

        led_red = "ON" if cmp0 > 0 else "OFF"
        led_grn = "ON" if cmp1 > 0 else "OFF"
        winner = "VERT (RED)" if cmp0 > 0 else "HORIZ (GRN)"

        results.append({
            "bin": f"{x0}{x1}{x2}{x3}",
            "vx": (vx0, vx1, vx2, vx3),
            "v_sum0": v_sum0,
            "v_act0": v_act0,
            "v_sum1": v_sum1,
            "v_act1": v_act1,
            "v_out0": v_out0,
            "v_out1": v_out1,
            "cmp0": cmp0,
            "cmp1": cmp1,
            "led_red": led_red,
            "led_grn": led_grn,
            "winner": winner
        })

    return results

def print_table(results):
    print("=" * 105)
    print("  ANALOG NEURAL NETWORK TEST BOARD (70x100mm) - HARDWARE EMULATION & VERIFICATION TABLE")
    print("=" * 105)
    header = (
        f"{'BIN':<6} | {'X0..X3 (V)':<14} | {'V_SUM0':<7} | {'V_ACT0':<7} | "
        f"{'V_SUM1':<7} | {'V_ACT1':<7} | {'V_OUT0':<7} | {'V_OUT1':<7} | "
        f"{'CMP0':<6} | {'CMP1':<6} | {'RED':<4} | {'GRN':<4} | {'WINNER'}"
    )
    print(header)
    print("-" * 105)
    for r in results:
        vxs = f"{int(r['vx'][0])},{int(r['vx'][1])},{int(r['vx'][2])},{int(r['vx'][3])}"
        row = (
            f"{r['bin']:<6} | {vxs:<14} | {r['v_sum0']:>6.2f}V | {r['v_act0']:>6.2f}V | "
            f"{r['v_sum1']:>6.2f}V | {r['v_act1']:>6.2f}V | {r['v_out0']:>6.2f}V | {r['v_out1']:>6.2f}V | "
            f"{r['cmp0']:>5.1f}V | {r['cmp1']:>5.1f}V | {r['led_red']:<4} | {r['led_grn']:<4} | {r['winner']}"
        )
        print(row)
    print("=" * 105)

if __name__ == "__main__":
    res = simulate_board()
    print_table(res)
