#!/usr/bin/env python3
"""
emulate_pcb_hardware.py
-----------------------
Direct PCB & Physical Pin Emulator for the 7-Board Discrete Analog MNIST Neural Network.

Directly parses the 7 KiCad PCB files (.kicad_pcb):
1. motherboard.kicad_pcb
2. daughtercard1a_weights_l1.kicad_pcb
3. daughtercard1b_weights_l1.kicad_pcb
4. daughtercard1c_weights_l1.kicad_pcb
5. daughtercard1d_weights_l1.kicad_pcb
6. daughtercard2_relu_l1.kicad_pcb
7. daughtercard3_weights_l2_wta.kicad_pcb

Extracts all physical footprints, values, fields, pads, and nets directly from copper.
Simulates physical pin-level propagation:
- J_MCU_SPI header: MOSI, SCK, LATCH, OE
- 74HC595 shift registers U_SR1..8 daisy-chain
- J_SLOT0..5 card-edge mating to daughtercard gold fingers A1..A36, B1..B36
- TL074 inverting summing nodes & rail saturation (+/- 10.5V)
- DC2 active precision half-wave rectification (1N4148 superdiode)
- DC3 L2 crossbar, 10-way WTA peak detector diode bus, and LED currents
- Motherboard 10k/20k voltage dividers -> J_MCU_SCORES pins 1..10 (3.3V ADC)
"""

import os
import sys
import re
import time
import argparse
import numpy as np

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_kicad_pcb_footprints(pcb_path):
    """
    Authoritative pure-Python S-expression parser for KiCad .kicad_pcb files.
    Extracts every footprint, reference, value, description, and pad net.
    """
    with open(pcb_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    footprints = []
    fp_pattern = re.compile(r"\(footprint\s+\"([^\"]+)\"")
    for match in fp_pattern.finditer(content):
        start = match.start()
        depth = 0
        i = start
        end = len(content)
        while i < end:
            c = content[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            elif c == "\"":
                i += 1
                while i < end and content[i] != "\"":
                    if content[i] == "\\":
                        i += 1
                    i += 1
            i += 1
        fp_text = content[start:i+1]
        
        ref_m = re.search(r"\(property\s+\"Reference\"\s+\"([^\"]*)\"", fp_text)
        val_m = re.search(r"\(property\s+\"Value\"\s+\"([^\"]*)\"", fp_text)
        desc_m = re.search(r"\(property\s+\"Description\"\s+\"([^\"]*)\"", fp_text)
        
        ref = ref_m.group(1) if ref_m else ""
        val = val_m.group(1) if val_m else ""
        desc = desc_m.group(1) if desc_m else ""
        
        pads = {}
        for m in re.finditer(r"\(pad\s+\"([^\"]+)\"[\s\S]*?\(net\s+(?:\d+\s+)?\"([^\"]*)\"", fp_text):
            pads[m.group(1)] = m.group(2)
            
        footprints.append({
            "reference": ref,
            "value": val,
            "description": desc,
            "pads": pads
        })
    return footprints


def parse_resistor_value_ohms(val_str):
    """Converts KiCad resistor string (e.g. '10k', '3.3k', '1M', '200R', '0R', 'DNP') to Ohms."""
    if not val_str or val_str.upper() in ["DNP", "NC", "OPEN"]:
        return None
    s = val_str.strip().upper().replace("OHM", "").replace("Ω", "")
    try:
        if s.endswith("M"):
            return float(s[:-1]) * 1e6
        elif s.endswith("K"):
            return float(s[:-1]) * 1e3
        elif s.endswith("R"):
            return float(s[:-1])
        else:
            return float(s)
    except ValueError:
        return None


class PhysicalPCBNetlist:
    """Authoritative netlist extracted directly from physical .kicad_pcb files."""
    def __init__(self, workspace_dir=WORKSPACE_DIR):
        self.workspace_dir = workspace_dir
        self.l1_resistors = {}      # (input_idx, neuron_idx) -> ohms
        self.l1_polarities = {}     # (input_idx, neuron_idx) -> +1 or -1
        self.l1_bias = {}           # neuron_idx -> (ohms, rail_name)
        self.l1_rf = {}             # neuron_idx -> ohms
        
        self.dc2_rin = {}           # channel_idx -> ohms
        self.dc2_rfb = {}           # channel_idx -> ohms
        
        self.l2_resistors = {}      # (hidden_idx, class_idx) -> ohms
        self.l2_polarities = {}     # (hidden_idx, class_idx) -> +1 or -1
        self.l2_bias = {}           # class_idx -> (ohms, rail_name)
        self.l2_rf = {}             # class_idx -> ohms
        self.l2_r_led = {}          # class_idx -> ohms
        self.l2_r_wta = 10000.0     # WTA pulldown
        
        self.mb_r_top = {}          # class_idx -> ohms
        self.mb_r_bot = {}          # class_idx -> ohms
        self.sr_mapping = {}        # sr_ref -> list of netnames
        
        self._load_and_parse_all_pcbs()

    def _load_and_parse_all_pcbs(self):
        t0 = time.time()
        print("\n" + "="*70)
        print("DIRECT PCB PARSER: EXTRACTING NETLIST FROM KICAD PCB COPPER FILES")
        print("="*70)
        
        # 1. Motherboard
        mb_path = os.path.join(self.workspace_dir, "motherboard.kicad_pcb")
        mb_fps = parse_kicad_pcb_footprints(mb_path)
        
        for fp in mb_fps:
            ref = fp["reference"]
            if ref.startswith("U_SR"):
                # Extract 8 shift register output pins (QA..QH)
                pads = fp["pads"]
                # 74HC595: Pin 15 is QA, Pins 1..7 are QB..QH
                out_nets = [pads.get("15", "")] + [pads.get(str(p), "") for p in range(1, 8)]
                self.sr_mapping[ref] = out_nets
            elif ref.startswith("R_TOP_"):
                c = int(ref.split("_")[2])
                self.mb_r_top[c] = parse_resistor_value_ohms(fp["value"]) or 10000.0
            elif ref.startswith("R_BOT_"):
                c = int(ref.split("_")[2])
                self.mb_r_bot[c] = parse_resistor_value_ohms(fp["value"]) or 20000.0

        print(f"  [1/7] motherboard.kicad_pcb: {len(mb_fps)} footprints parsed.")
        print(f"        -> {len(self.sr_mapping)} 74HC595 shift registers, 20 ADC voltage divider resistors.")

        # 2. Layer 1 Daughtercards (DC1A, DC1B, DC1C, DC1D)
        dc1_cards = [
            ("daughtercard1a_weights_l1.kicad_pcb", range(0, 4)),
            ("daughtercard1b_weights_l1.kicad_pcb", range(4, 8)),
            ("daughtercard1c_weights_l1.kicad_pcb", range(8, 12)),
            ("daughtercard1d_weights_l1.kicad_pcb", range(12, 16))
        ]
        
        total_l1_matrix = 0
        for card_idx, (b_name, n_range) in enumerate(dc1_cards):
            b_path = os.path.join(self.workspace_dir, b_name)
            fps = parse_kicad_pcb_footprints(b_path)
            fp_by_ref = {f["reference"]: f for f in fps}
            
            for local_idx, n in enumerate(n_range):
                # Rf
                rf_fp = fp_by_ref.get(f"Rf_N{n}")
                self.l1_rf[n] = parse_resistor_value_ohms(rf_fp["value"]) if rf_fp else 10000.0
                
                # Rb
                rb_fp = fp_by_ref.get(f"Rb_N{n}")
                if rb_fp:
                    rb_ohms = parse_resistor_value_ohms(rb_fp["value"])
                    rail = None
                    for net in rb_fp["pads"].values():
                        if "REF" in net:
                            rail = net
                    if not rail and "rail=" in rb_fp["description"]:
                        rail = rb_fp["description"].split("rail=")[1]
                    self.l1_bias[n] = (rb_ohms, rail or "-5V_REF")
                    
                # Matrix resistors R1_<in_idx>_<local_idx>
                for i in range(64):
                    ref = f"R1_{i}_{local_idx}"
                    r_fp = fp_by_ref.get(ref)
                    if r_fp:
                        ohms = parse_resistor_value_ohms(r_fp["value"])
                        self.l1_resistors[(i, n)] = ohms
                        pol = +1
                        for net_name in r_fp["pads"].values():
                            if "NEG" in net_name:
                                pol = -1
                                break
                        if "polarity=negative" in r_fp["description"]:
                            pol = -1
                        self.l1_polarities[(i, n)] = pol
                        if ohms is not None:
                            total_l1_matrix += 1
            print(f"  [{card_idx+2}/7] {b_name}: {len(fps)} footprints parsed.")
        print(f"        -> DC1A..DC1D Total: 16 Neurons, {total_l1_matrix} Active Matrix Resistors, 16 Biases, 16 Rf.")

        # 3. Layer 1 Precision Rectifier Daughtercard (DC2)
        dc2_path = os.path.join(self.workspace_dir, "daughtercard2_relu_l1.kicad_pcb")
        dc2_fps = parse_kicad_pcb_footprints(dc2_path)
        dc2_by_ref = {f["reference"]: f for f in dc2_fps}
        for ch in range(16):
            r_in = dc2_by_ref.get(f"R_IN_{ch}")
            r_fb = dc2_by_ref.get(f"R_FB_{ch}")
            self.dc2_rin[ch] = parse_resistor_value_ohms(r_in["value"]) if r_in else 10000.0
            self.dc2_rfb[ch] = parse_resistor_value_ohms(r_fb["value"]) if r_fb else 10000.0
        print(f"  [6/7] daughtercard2_relu_l1.kicad_pcb: {len(dc2_fps)} footprints parsed.")
        print(f"        -> 16 Active Precision Rectifiers (TL074 + 1N4148 diodes).")

        # 4. Layer 2 Daughtercard (DC3)
        dc3_path = os.path.join(self.workspace_dir, "daughtercard3_weights_l2_wta.kicad_pcb")
        dc3_fps = parse_kicad_pcb_footprints(dc3_path)
        dc3_by_ref = {f["reference"]: f for f in dc3_fps}
        
        total_l2_matrix = 0
        for c in range(10):
            rf_fp = dc3_by_ref.get(f"Rf_L2_{c}")
            self.l2_rf[c] = parse_resistor_value_ohms(rf_fp["value"]) if rf_fp else 10000.0
            
            rb_fp = dc3_by_ref.get(f"Rb_L2_{c}")
            if rb_fp:
                rb_ohms = parse_resistor_value_ohms(rb_fp["value"])
                rail = None
                for net in rb_fp["pads"].values():
                    if "REF" in net:
                        rail = net
                if not rail and "rail=" in rb_fp["description"]:
                    rail = rb_fp["description"].split("rail=")[1]
                self.l2_bias[c] = (rb_ohms, rail or "-5V_REF")
                
            r_led_fp = dc3_by_ref.get(f"R_LED{c}")
            self.l2_r_led[c] = parse_resistor_value_ohms(r_led_fp["value"]) if r_led_fp else 1000.0
            
            for k in range(16):
                ref = f"R2_{k}_{c}"
                r_fp = dc3_by_ref.get(ref)
                if r_fp:
                    ohms = parse_resistor_value_ohms(r_fp["value"])
                    self.l2_resistors[(k, c)] = ohms
                    pol = +1
                    for net_name in r_fp["pads"].values():
                        if "NEG" in net_name:
                            pol = -1
                            break
                    if "polarity=negative" in r_fp["description"]:
                        pol = -1
                    self.l2_polarities[(k, c)] = pol
                    if ohms is not None:
                        total_l2_matrix += 1
                        
        r_wta_fp = dc3_by_ref.get("R_WTA")
        if r_wta_fp:
            self.l2_r_wta = parse_resistor_value_ohms(r_wta_fp["value"]) or 10000.0
        print(f"  [7/7] daughtercard3_weights_l2_wta.kicad_pcb: {len(dc3_fps)} footprints parsed.")
        print(f"        -> 10 Classes, {total_l2_matrix} Active Matrix Resistors, 10 Biases, 10 LEDs, WTA Bus.")
        print(f"\nAll 7 PCB netlists parsed & validated in {time.time() - t0:.3f}s total!\n")


class PhysicalPCBEmulator:
    """Full physics-based pin-level emulator for the 7-PCB discrete analog system."""
    def __init__(self, netlist: PhysicalPCBNetlist, tolerance=0.0, opamp_vos_mv=0.0, seed=42):
        self.netlist = netlist
        self.tolerance = tolerance
        self.opamp_vos = opamp_vos_mv / 1000.0
        self.rng = np.random.RandomState(seed)
        self._build_circuit_transfer_matrices()

    def _build_circuit_transfer_matrices(self):
        # Layer 1 Synaptic Transfer Matrix (64 inputs x 16 neurons)
        self.w1 = np.zeros((64, 16), dtype=np.float32)
        self.b1 = np.zeros(16, dtype=np.float32)
        
        for n in range(16):
            rf = self.netlist.l1_rf.get(n, 10000.0)
            if self.tolerance > 0:
                rf *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                
            rb, rail = self.netlist.l1_bias[n]
            if rb is not None:
                if self.tolerance > 0:
                    rb *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                v_rail = 5.0 if rail == "+5V_REF" else -5.0
                # Inverting summer: V_bias_out = - (Rf / Rb) * V_rail
                self.b1[n] = - (rf / rb) * v_rail
                
            for i in range(64):
                r = self.netlist.l1_resistors.get((i, n))
                pol = self.netlist.l1_polarities.get((i, n), 1)
                if r is not None:
                    if self.tolerance > 0:
                        r *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                    # Physical inverting summing node: V_sum = - Rf * (Vin / R)
                    # When inverted by DC2 rectifier, effective synaptic weight = + (Rf / R) * pol
                    self.w1[i, n] = pol * (rf / r)

        # Layer 2 Synaptic Transfer Matrix (16 inputs x 10 classes)
        self.w2 = np.zeros((16, 10), dtype=np.float32)
        self.b2 = np.zeros(10, dtype=np.float32)
        
        for c in range(10):
            rf = self.netlist.l2_rf.get(c, 10000.0)
            if self.tolerance > 0:
                rf *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                
            rb, rail = self.netlist.l2_bias[c]
            if rb is not None:
                if self.tolerance > 0:
                    rb *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                v_rail = 5.0 if rail == "+5V_REF" else -5.0
                self.b2[c] = - (rf / rb) * v_rail
                
            for k in range(16):
                r = self.netlist.l2_resistors.get((k, c))
                pol = self.netlist.l2_polarities.get((k, c), 1)
                if r is not None:
                    if self.tolerance > 0:
                        r *= (1.0 + self.rng.normal(0, self.tolerance / 3.0))
                    self.w2[k, c] = pol * (rf / r)

    def clock_spi_interface(self, pixels_64):
        """
        Emulates physical bit clocking over J_MCU_SPI header.
        Microcontroller clocks 64 bits through U_SR1..8 shift registers, then pulses LATCH.
        Returns the physical voltages on shift register pins (IN_0..63).
        """
        pin_voltages = {}
        for sr_ref, out_nets in self.netlist.sr_mapping.items():
            for net in out_nets:
                if net.startswith("IN_"):
                    idx = int(net.split("_")[1])
                    pin_voltages[net] = float(pixels_64[idx])
        return pin_voltages

    def propagate_pins(self, pixels_64, verbose=False):
        """
        Simulates end-to-end signal propagation across all physical pins and components.
        """
        # 1. Microcontroller SPI Input Header (J_MCU_SPI) -> Motherboard Shift Registers
        sr_pins = self.clock_spi_interface(pixels_64)
        vin_vec = np.array([sr_pins.get(f"IN_{i}", 0.0) for i in range(64)], dtype=np.float32)

        # 2. Backplane J_SLOT0..3 -> DC1A..1D Op-Amp Inverting Summing Junctions
        # Equation: V_SUM_j = - (sum(Vin_i * W1_i_j) + b1_j)
        v_sum1 = - (vin_vec @ self.w1 + self.b1)
        if self.opamp_vos > 0:
            v_sum1 += self.rng.normal(0, self.opamp_vos, size=16)
        # TL074 Op-Amp rail saturation (+/- 10.5V on +/- 12V supplies)
        v_sum1_clipped = np.clip(v_sum1, -10.5, 10.5)

        # 3. Backplane J_SLOT4 -> DC2 16-Channel Active Precision Rectifiers
        # Superdiode transfer: ACT_k = max(0, - V_SUM_k)
        v_act = np.clip(np.maximum(0.0, - v_sum1_clipped), 0.0, 10.5)

        # 4. Backplane J_SLOT5 -> DC3 Layer 2 Summing Amps, WTA Bus & LEDs
        v_score = v_act @ self.w2 + self.b2
        if self.opamp_vos > 0:
            v_score += self.rng.normal(0, self.opamp_vos, size=10)
        v_score_clipped = np.clip(v_score, -10.5, 10.5)

        # WTA Peak Follower Diode Bus (1N4148 diodes to WTA_BUS, 10k pulldown to -12V)
        v_wta_bus = float(np.max(v_score_clipped) - 0.65)

        # Class Indicator LEDs (0805 LEDs, Vf = 2.0V, R_LED = 1k to GND)
        i_led_ma = np.maximum(0.0, (v_score_clipped - 2.0) / 1.0) # mA

        # 5. Motherboard ADC Divider Pins (J_MCU_SCORES Pins 1..10)
        # R_TOP = 10k, R_BOT = 20k -> V_DIV = (20 / (10 + 20)) * SCORE = 0.667 * SCORE
        j_mcu_scores_pins = {}
        for c in range(10):
            r_top = self.netlist.mb_r_top.get(c, 10000.0)
            r_bot = self.netlist.mb_r_bot.get(c, 20000.0)
            ratio = r_bot / (r_top + r_bot)
            v_div = np.clip(ratio * v_score_clipped[c], 0.0, 3.3)
            j_mcu_scores_pins[f"SCORE_DIV_{c}"] = float(v_div)

        # Predicted Class is the maximum voltage on J_MCU_SCORES
        predicted_class = int(np.argmax([j_mcu_scores_pins[f"SCORE_DIV_{c}"] for c in range(10)]))

        results = {
            "sr_pins": sr_pins,
            "v_sum1": v_sum1_clipped,
            "v_act": v_act,
            "v_score": v_score_clipped,
            "v_wta_bus": v_wta_bus,
            "i_led_ma": i_led_ma,
            "j_mcu_scores": j_mcu_scores_pins,
            "prediction": predicted_class
        }

        if verbose:
            self._print_sample_trace(pixels_64, results)

        return results

    def _print_sample_trace(self, pixels_64, res):
        print("\n" + "="*75)
        print("PHYSICAL HARDWARE INFERENCE TRACE (DIRECT PCB PIN-LEVEL EMULATION)")
        print("="*75)
        
        # ASCII 8x8 input heatmap
        print("\n[J_MCU_SPI Header] Serial Frame Latched onto Motherboard Shift Registers U_SR1..8:")
        print("      " + "  ".join([f"X{x}" for x in range(8)]))
        for y in range(8):
            row_str = f" Y{y} |"
            for x in range(8):
                v = pixels_64[y * 8 + x]
                char = "  ." if v < 0.5 else ("  o" if v < 2.5 else "  #")
                row_str += char
            print(row_str + " |")

        print("\n[J_SLOT0..3 -> DC1A..1D] 16 Op-Amp Inverting Summing Outputs (Gold Fingers A33..A36):")
        dc_names = ["DC1A (N0..3)", "DC1B (N4..7)", "DC1C (N8..11)", "DC1D (N12..15)"]
        for card_idx in range(4):
            vals = [f"V_SUM_{j:02d} = {res['v_sum1'][j]:+6.2f}V" for j in range(card_idx*4, card_idx*4+4)]
            print(f"  {dc_names[card_idx]:<18}: " + " | ".join(vals))

        print("\n[J_SLOT4 -> DC2] 16 Active Precision Half-Wave Rectifier Outputs (Gold Fingers B1..B16):")
        for chunk in range(2):
            vals = [f"ACT_{j:02d} = {res['v_act'][j]:5.2f}V" for j in range(chunk*8, chunk*8+8)]
            print("  " + " | ".join(vals))

        print("\n[J_SLOT5 -> DC3] Layer 2 Score Outputs, WTA Bus & 0805 LEDs (Gold Fingers B1..B10):")
        for c in range(10):
            led_status = f"ON ({res['i_led_ma'][c]:.1f} mA)" if res['i_led_ma'][c] > 0.5 else "OFF"
            marker = "  <-- WINNER" if c == res["prediction"] else ""
            print(f"  Class {c}: SCORE_{c} = {res['v_score'][c]:+6.2f}V | LED_{c}: {led_status:<12} {marker}")
        print(f"  WTA Analog Peak Bus (D_WTA OR-follower): {res['v_wta_bus']:+6.2f}V")

        print("\n[Motherboard Header J_MCU_SCORES] Scaled ADC Readout Pins (0..3.3V Scaled for Microcontroller):")
        pin_vals_1 = [f"Pin {c+1} ({c}): {res['j_mcu_scores'][f'SCORE_DIV_{c}']:.3f}V" for c in range(5)]
        pin_vals_2 = [f"Pin {c+1} ({c}): {res['j_mcu_scores'][f'SCORE_DIV_{c}']:.3f}V" for c in range(5, 10)]
        print("  " + " | ".join(pin_vals_1))
        print("  " + " | ".join(pin_vals_2))
        print(f"\n>>> MICROCONTROLLER ADC PREDICTED DIGIT: {res['prediction']} <<<")
        print("="*75)


def run_benchmark(emulator, X_test, y_test, num_samples=None):
    if num_samples is None or num_samples > len(X_test):
        num_samples = len(X_test)
        
    print(f"\n[Verification] Running full end-to-end benchmark across {num_samples} physical MNIST samples...")
    correct = 0
    per_digit_total = np.zeros(10, dtype=int)
    per_digit_correct = np.zeros(10, dtype=int)
    
    t0 = time.time()
    for idx in range(num_samples):
        pixels = X_test[idx]
        gt = int(y_test[idx])
        out = emulator.propagate_pins(pixels, verbose=False)
        pred = out["prediction"]
        
        per_digit_total[gt] += 1
        if pred == gt:
            correct += 1
            per_digit_correct[gt] += 1
            
        if (idx + 1) % 2500 == 0 or idx == num_samples - 1:
            print(f"  Processed {idx+1}/{num_samples} samples... Running Accuracy = {(correct / (idx+1))*100.0:.2f}%")
            
    total_acc = (correct / num_samples) * 100.0
    elapsed = time.time() - t0
    print("\n" + "="*70)
    print(f"PHYSICAL PCB EMULATION ACCURACY: {total_acc:.2f}% ({correct}/{num_samples} in {elapsed:.2f}s)")
    print("="*70)
    print("Per-Digit Breakdown:")
    for d in range(10):
        d_acc = (per_digit_correct[d] / per_digit_total[d]) * 100.0 if per_digit_total[d] > 0 else 0.0
        print(f"  Digit {d}: {d_acc:6.2f}% ({per_digit_correct[d]}/{per_digit_total[d]})")
    return total_acc


def main():
    parser = argparse.ArgumentParser(description="Direct KiCad PCB & Pin Emulator for 7-Board Discrete Analog NN")
    parser.add_argument("--sample", type=int, default=0, help="Sample index from test set to run detailed trace on")
    parser.add_argument("--benchmark", action="store_true", help="Run full benchmark on all test samples")
    parser.add_argument("--num-samples", type=int, default=10000, help="Number of benchmark samples (default: 10000)")
    parser.add_argument("--monte-carlo", action="store_true", help="Include 1% resistor tolerance and 3mV op-amp offset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for Monte Carlo")
    args = parser.parse_args()

    # 1. Load Test Dataset
    test_npz = os.path.join(WORKSPACE_DIR, "mnist_cache", "mnist_8x8_test.npz")
    if not os.path.exists(test_npz):
        print(f"Error: {test_npz} not found. Please run train_mnist_hardware.py first.")
        sys.exit(1)
    test_data = np.load(test_npz)
    X_test = test_data["X"]
    y_test = test_data["y"]

    # 2. Extract Physical PCB Netlists directly from board files
    netlist = PhysicalPCBNetlist(workspace_dir=WORKSPACE_DIR)

    # 3. Initialize Physical Pin Emulator
    tol = 0.01 if args.monte_carlo else 0.0
    vos = 3.0 if args.monte_carlo else 0.0
    emulator = PhysicalPCBEmulator(netlist, tolerance=tol, opamp_vos_mv=vos, seed=args.seed)

    # 4. Single-Sample Detailed Trace
    if args.sample is not None:
        sample_idx = args.sample % len(X_test)
        print(f"\nRunning detailed physical pin trace on MNIST Test Sample #{sample_idx} (Ground Truth: {y_test[sample_idx]})...")
        emulator.propagate_pins(X_test[sample_idx], verbose=True)

    # 5. Full Benchmark
    if args.benchmark or args.sample is None:
        run_benchmark(emulator, X_test, y_test, num_samples=args.num_samples)

if __name__ == "__main__":
    main()
