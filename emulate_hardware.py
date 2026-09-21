#!/usr/bin/env python3
"""
emulate_hardware.py
-------------------
Discrete Analog Neural Network Hardware Emulator:
Accurately models the electronic circuit behavior of the 7-PCB stack:
- Motherboard: Dual-rail input conditioning (0..5V DAC buffer / inverter)
- DC1A..DC1D: 64x16 Synaptic Resistor Crossbar + TL074 Inverting Summing Amps
- DC2: 16x Active Precision Rectifiers (ReLU) with TL074 + 1N4148 diodes
- DC3: 16x10 Layer 2 Synaptic Crossbar + WTA Argmax Comparators (LM339) + 10 LEDs

Includes:
1. Ideal Circuit Simulation
2. Real-world Non-idealities (1% Resistor Tolerance, Op-Amp Vos, Power Drift)
3. Full Dataset Benchmark (360 test samples)
4. Interactive Single-Sample Inference Visualizer with ASCII Heatmap
"""

import os
import sys
import gzip
import json
import argparse
import numpy as np

MINIFORGE_SITE = "/Users/lucaszhang/miniforge3/lib/python3.13/site-packages"
if MINIFORGE_SITE not in sys.path:
    sys.path.insert(0, MINIFORGE_SITE)

from tqdm import tqdm

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

class AnalogNNHardwareEmulator:
    def __init__(self, tolerance_resistors=0.01, opamp_vos_mv=3.0, monte_carlo=False, seed=42):
        self.rf = 10000.0  # 10.0 kOhm feedback
        self.v_ref_pos = 5.0
        self.v_ref_neg = -5.0
        self.v_rail_pos = 12.0
        self.v_rail_neg = -12.0
        self.v_sat_pos = 10.5
        self.v_sat_neg = -10.5
        
        self.tolerance = tolerance_resistors if monte_carlo else 0.0
        self.vos_scale = (opamp_vos_mv / 1000.0) if monte_carlo else 0.0
        self.rng = np.random.RandomState(seed)

        # Load weights
        with open(os.path.join(WORKSPACE_DIR, "weights_layer1.json")) as f:
            self.l1_json = json.load(f)
        with open(os.path.join(WORKSPACE_DIR, "weights_layer2.json")) as f:
            self.l2_json = json.load(f)

        self._build_circuit_matrices()

    def _build_circuit_matrices(self):
        # Layer 1: W1_eff (64, 16), b1_eff (16)
        self.W1 = np.zeros((64, 16), dtype=float)
        self.b1 = np.zeros(16, dtype=float)
        self.R_W1 = np.zeros((64, 16), dtype=float)
        self.R_b1 = np.zeros(16, dtype=float)

        for j in range(16):
            n_data = self.l1_json["weights"][j]
            # Bias
            rb = n_data["bias_resistor_ohms"]
            rail = n_data["bias_rail"]
            if rb is not None:
                if self.tolerance > 0:
                    rb *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                self.R_b1[j] = rb
                v_rail = self.v_ref_pos if rail == "+5V_REF" else self.v_ref_neg
                # Inverting summer: V_bias_contribution = - Rf * (V_rail / Rb)
                self.b1[j] = - (self.rf / rb) * v_rail

            # Weights
            for inp in n_data["inputs"]:
                i = inp["input_idx"]
                rw = inp["resistor_ohms"]
                pol = inp["polarity"]
                if rw is not None:
                    if self.tolerance > 0:
                        rw *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                    self.R_W1[i, j] = rw
                    # In dual-rail scheme:
                    # Positive weight connects to -Vin: V_out_term = - Rf * (-Vin / R) = + (Rf / R) * Vin
                    # Negative weight connects to +Vin: V_out_term = - Rf * (+Vin / R) = - (Rf / R) * Vin
                    sign = +1.0 if pol == "positive" else -1.0
                    self.W1[i, j] = sign * (self.rf / rw)

        # Layer 2: W2_eff (16, 10), b2_eff (10)
        self.W2 = np.zeros((16, 10), dtype=float)
        self.b2 = np.zeros(10, dtype=float)
        self.R_W2 = np.zeros((16, 10), dtype=float)
        self.R_b2 = np.zeros(10, dtype=float)

        for k in range(10):
            c_data = self.l2_json["weights"][k]
            rb = c_data["bias_resistor_ohms"]
            rail = c_data["bias_rail"]
            if rb is not None:
                if self.tolerance > 0:
                    rb *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                self.R_b2[k] = rb
                v_rail = self.v_ref_pos if rail == "+5V_REF" else self.v_ref_neg
                self.b2[k] = - (self.rf / rb) * v_rail

            for inp in c_data["inputs"]:
                j = inp["hidden_idx"]
                rw = inp["resistor_ohms"]
                pol = inp["polarity"]
                if rw is not None:
                    if self.tolerance > 0:
                        rw *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                    self.R_W2[j, k] = rw
                    sign = +1.0 if pol == "positive" else -1.0
                    self.W2[j, k] = sign * (self.rf / rw)

        # Op-amp offsets
        if self.vos_scale > 0:
            self.vos_l1 = self.rng.normal(0, self.vos_scale, size=16)
            self.vos_relu = self.rng.normal(0, self.vos_scale, size=16)
            self.vos_l2 = self.rng.normal(0, self.vos_scale, size=10)
        else:
            self.vos_l1 = np.zeros(16)
            self.vos_relu = np.zeros(16)
            self.vos_l2 = np.zeros(10)

    def forward_circuit(self, v_in):
        """
        Executes true physical analog forward propagation for a 64-input vector (0..5V).
        Returns full analog telemetry at all stages.
        """
        # Step 1: Motherboard Dual-Rail Generation
        # +V_in: 0..5V, -V_in: -5..0V
        v_in = np.clip(v_in, 0.0, 5.0)

        # Step 2: DC1A..DC1D Summing Amplifiers (TL074)
        # Node equation: V_sum1_j = sum_i (W1_ij * Vin_i) + b1_j + Vos
        v_sum1 = v_in @ self.W1 + self.b1 + self.vos_l1
        # Op-amp saturation
        v_sum1_clipped = np.clip(v_sum1, self.v_sat_neg, self.v_sat_pos)

        # Step 3: DC2 Precision Active Rectifiers (ReLU)
        # Precision half-wave rectifier: V_relu = max(0, V_sum1)
        v_relu = np.maximum(0.0, v_sum1_clipped) + self.vos_relu
        v_relu = np.clip(v_relu, 0.0, self.v_sat_pos)

        # Step 4: DC3 Layer 2 Summing Amplifiers
        v_sum2 = v_relu @ self.W2 + self.b2 + self.vos_l2
        v_sum2_clipped = np.clip(v_sum2, self.v_sat_neg, self.v_sat_pos)

        # Step 5: DC3 Winner-Take-All (WTA) Peak Follower & LED Drivers
        # Peak follower with diode drop: V_peak = max(v_sum2) - 0.6V
        v_peak = np.max(v_sum2_clipped) - 0.6
        predicted_digit = int(np.argmax(v_sum2_clipped))

        # LM339 comparators: channel with max voltage is LOW (LED ON)
        comparator_outputs = np.full(10, 5.0)  # Open-collector pulled to 5V (OFF)
        comparator_outputs[predicted_digit] = 0.2  # Sunk to GND (ON)
        
        # LED currents (mA) through 1k resistor: (5V - 2V_led - 0.2V_comp) / 1k = 2.8mA
        led_currents_ma = np.zeros(10)
        led_currents_ma[predicted_digit] = (5.0 - 2.0 - 0.2) / 1.0  # ~2.8 mA

        # Slice breakdown for Daughtercards 1A..1D
        slice_voltages = {
            "DC1A (Neurons 0..3)": v_sum1_clipped[0:4],
            "DC1B (Neurons 4..7)": v_sum1_clipped[4:8],
            "DC1C (Neurons 8..11)": v_sum1_clipped[8:12],
            "DC1D (Neurons 12..15)": v_sum1_clipped[12:16],
            "DC2_ReLU": v_relu,
            "DC3_ClassSums": v_sum2_clipped,
            "Winning_Digit": predicted_digit,
            "LED_Currents_mA": led_currents_ma
        }
        return slice_voltages

def load_dataset():
    mnist_test_path = os.path.join(WORKSPACE_DIR, "mnist_cache", "mnist_8x8_test.npz")
    if os.path.exists(mnist_test_path):
        data = np.load(mnist_test_path)
        return data["X"], data["y"]
    cache_path = os.path.join(WORKSPACE_DIR, "digits_cache.csv.gz")
    if os.path.exists(cache_path):
        with gzip.GzipFile(cache_path, "rb") as gz:
            raw_data = np.loadtxt(gz, delimiter=",")
        X = (raw_data[:, :-1] / 16.0) * 5.0
        y = raw_data[:, -1].astype(int)
        np.random.seed(1337)
        indices = np.random.permutation(len(X))
        split = int(0.8 * len(X))
        return X[indices[split:]], y[indices[split:]]
    raise FileNotFoundError("No dataset cache found. Run train_mnist_hardware.py first!")

def render_ascii_digit(pixel_voltages):
    """Renders 8x8 input as ASCII art."""
    chars = " .:-=+*#%@"
    grid = []
    for r in range(8):
        row_str = ""
        for c in range(8):
            val = pixel_voltages[r * 8 + c]
            idx = int((val / 5.0) * (len(chars) - 1))
            row_str += chars[idx] * 2
        grid.append(row_str)
    return "\n".join(grid)

def benchmark_full_stack():
    X_test, y_test = load_dataset()
    n_samples = len(X_test)

    print("\n" + "="*68)
    print("DISCRETE ANALOG HARDWARE EMULATION: BENCHMARK SUITE")
    print("="*68)

    # 1. Ideal Hardware Emulator
    emu_ideal = AnalogNNHardwareEmulator(monte_carlo=False)
    correct_ideal = 0
    for i in tqdm(range(n_samples), desc="Ideal Hardware Emulation", unit="sample"):
        res = emu_ideal.forward_circuit(X_test[i])
        if res["Winning_Digit"] == y_test[i]:
            correct_ideal += 1
    acc_ideal = correct_ideal / n_samples * 100.0

    # 2. Monte Carlo 1% Resistor Tolerance + 3mV Op-Amp Vos
    n_mc_runs = 5
    mc_accuracies = []
    print(f"\nRunning Monte Carlo Tolerance Stress Test ({n_mc_runs} random boards)...")
    for mc_idx in range(n_mc_runs):
        emu_mc = AnalogNNHardwareEmulator(tolerance_resistors=0.01, opamp_vos_mv=3.0, monte_carlo=True, seed=100 + mc_idx)
        correct_mc = 0
        for i in range(n_samples):
            res = emu_mc.forward_circuit(X_test[i])
            if res["Winning_Digit"] == y_test[i]:
                correct_mc += 1
        acc_mc = correct_mc / n_samples * 100.0
        mc_accuracies.append(acc_mc)
        print(f"  Board Specimen #{mc_idx+1}: {acc_mc:.2f}% accuracy (1% E96 tolerance + 3mV Vos)")

    print("\n" + "-"*68)
    print(f"Ideal Analog Hardware Accuracy:          {acc_ideal:.2f}% ({correct_ideal}/{n_samples})")
    print(f"Monte Carlo 1% Hardware Tolerance:       {np.mean(mc_accuracies):.2f}% ± {np.std(mc_accuracies):.2f}%")
    print("-"*68)

def inspect_single_sample(sample_idx=0):
    X_test, y_test = load_dataset()
    v_in = X_test[sample_idx]
    actual_label = y_test[sample_idx]

    emu = AnalogNNHardwareEmulator(monte_carlo=False)
    telemetry = emu.forward_circuit(v_in)

    print("\n" + "="*68)
    print(f"ANALOG HARDWARE INFERENCE TRACE: SAMPLE #{sample_idx} (True Label: {actual_label})")
    print("="*68)

    print("\n[INPUT STAGE] 8x8 Pixel Voltage Heatmap (0.0V - 5.0V):")
    print(render_ascii_digit(v_in))

    print("\n[LAYER 1: SYNAPTIC SUMMING AMPLIFIERS] (Daughtercards 1A..1D):")
    for name, volts in [
        ("DC1A (Neurons 0..3)  ", telemetry["DC1A (Neurons 0..3)"]),
        ("DC1B (Neurons 4..7)  ", telemetry["DC1B (Neurons 4..7)"]),
        ("DC1C (Neurons 8..11) ", telemetry["DC1C (Neurons 8..11)"]),
        ("DC1D (Neurons 12..15)", telemetry["DC1D (Neurons 12..15)"]),
    ]:
        v_str = " ".join([f"{v:+6.2f}V" for v in volts])
        print(f"  {name}: [ {v_str} ]")

    print("\n[LAYER 1 ACTIVATION: ACTIVE RECTIFIERS] (Daughtercard 2 ReLU):")
    relu_v = telemetry["DC2_ReLU"]
    v_relu_str1 = " ".join([f"{v:5.2f}V" for v in relu_v[:8]])
    v_relu_str2 = " ".join([f"{v:5.2f}V" for v in relu_v[8:]])
    print(f"  Neurons 0..7 : [ {v_relu_str1} ]")
    print(f"  Neurons 8..15: [ {v_relu_str2} ]")

    print("\n[LAYER 2 & WINNER-TAKE-ALL] (Daughtercard 3):")
    class_sums = telemetry["DC3_ClassSums"]
    winner = telemetry["Winning_Digit"]
    for k in range(10):
        bar_len = int(max(0, class_sums[k]) * 3.5)
        bar = "█" * bar_len
        status = ">>> [LED ON: 2.8mA] <<<" if k == winner else "    [LED OFF: 0mA]"
        print(f"  Digit {k}: {class_sums[k]:+6.2f}V | {bar:<30s} {status}")

    print("\n" + "="*68)
    print(f"FINAL HARDWARE OUTPUT: DIGIT {winner} ({'CORRECT' if winner == actual_label else 'INCORRECT'})")
    print("="*68)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discrete Analog Neural Network Hardware Emulator")
    parser.add_argument("--benchmark", action="store_true", help="Run full test set benchmark")
    parser.add_argument("--sample", type=int, default=0, help="Test specific sample index")
    args = parser.parse_args()

    if args.benchmark:
        benchmark_full_stack()
    else:
        inspect_single_sample(args.sample)
        benchmark_full_stack()
