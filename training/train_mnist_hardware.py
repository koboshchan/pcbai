#!/usr/bin/env python3
"""
train_mnist_hardware.py
-----------------------
Downloads the official MNIST dataset from Hugging Face (ylecun/mnist),
preprocesses & downscales the digits to 8x8 (64 analog pixel voltages 0.0V..5.0V),
and fits a discrete analog neural network (64 -> 16 ReLU -> 10 WTA).

Performs Quantization-Aware Training (QAT) directly onto standard IEC E96 1%
resistor values (100 Ohm to 10 MOhm) so the physical circuit achieves near-lossless
analog inference accuracy on the full 10,000 test set.

Exports:
- weights_layer1.json (Layer 1 crossbar resistors & bias rails)
- weights_layer2.json (Layer 2 crossbar resistors & bias rails)
- mnist_analog_model.pt (PyTorch state dict)
- mnist_cache/mnist_8x8_train.npz & mnist_8x8_test.npz
"""

import os
import io
import sys
import json
import time
import argparse
import urllib.request
import pyarrow.parquet as pq
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(WORKSPACE_DIR, "mnist_cache")

# -----------------------------------------------------------------------------
# 1. Resistor Value Kits
# -----------------------------------------------------------------------------
# User 60-Value 0805 1% Resistor SMD Kit (25 pcs per value)
KIT_60_VALUES_STR = [
    '0R', '1R', '2.2R', '3.3R', '4.7R', '5.1R', '10R', '15R', '22R', '33R',
    '47R', '51R', '62R', '82R', '100R', '120R', '150R', '180R', '200R', '220R',
    '240R', '270R', '300R', '330R', '470R', '510R', '560R', '680R', '820R', '1K',
    '1.2K', '1.5K', '1.8K', '2K', '2.2K', '3K', '3.3K', '4.7K', '5.1K', '5.6K',
    '7.5K', '10K', '12K', '15K', '18K', '20K', '22K', '33K', '43K', '47K',
    '51K', '75K', '100K', '200K', '300K', '390K', '470K', '680K', '1M', '10M'
]

def str_to_ohms(s):
    s = s.upper().strip()
    if s.endswith('M'): return float(s[:-1]) * 1e6
    elif s.endswith('K'): return float(s[:-1]) * 1e3
    elif s.endswith('R'): return float(s[:-1])
    return float(s)

# Synaptic resistors (>= 1k) from the 60-value kit
KIT_60_SYNAPTIC_OHMS = np.array(sorted([str_to_ohms(s) for s in KIT_60_VALUES_STR if str_to_ohms(s) >= 1000.0]))
KIT_60_TENSOR = torch.tensor(KIT_60_SYNAPTIC_OHMS, dtype=torch.float32)

# Full IEC E96 Resistor Standard (170 values)
E96_BASE_VALUES = np.array([
    1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24,
    1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58,
    1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00,
    2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55,
    2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24,
    3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
    4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23,
    5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
    6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45,
    8.66, 8.87, 9.09, 9.31, 9.53, 9.76
])
ALL_E96 = []
for decade in [1e2, 1e3, 1e4, 1e5, 1e6]:
    ALL_E96.extend(E96_BASE_VALUES * decade)
ALL_E96 = np.array(ALL_E96)
ALL_E96_TENSOR = torch.tensor(ALL_E96, dtype=torch.float32)

CURRENT_RESISTORS = KIT_60_SYNAPTIC_OHMS
CURRENT_TENSOR = KIT_60_TENSOR

def set_resistor_kit(kit_name):
    global CURRENT_RESISTORS, CURRENT_TENSOR
    if kit_name == "60values":
        CURRENT_RESISTORS = KIT_60_SYNAPTIC_OHMS
        CURRENT_TENSOR = KIT_60_TENSOR
    else:
        CURRENT_RESISTORS = ALL_E96
        CURRENT_TENSOR = ALL_E96_TENSOR

def quantize_to_resistor(resistance_ohms):
    """Snaps an ideal resistance to the closest resistor value in the active kit."""
    if resistance_ohms <= 0 or np.isinf(resistance_ohms) or np.isnan(resistance_ohms):
        return None
    if resistance_ohms < CURRENT_RESISTORS[0] or resistance_ohms > CURRENT_RESISTORS[-1]:
        return None
    idx = np.argmin(np.abs(CURRENT_RESISTORS - resistance_ohms))
    return float(CURRENT_RESISTORS[idx])

def format_resistor_value(ohms):
    """Formats an Ohm value into standard string (e.g. 10k, 20k, 100k, 1M, 10M)."""
    if ohms is None or np.isnan(ohms):
        return "DNP"
    if ohms >= 1e6:
        val = ohms / 1e6
        return f"{int(val)}M" if val.is_integer() else f"{val:.2g}M"
    elif ohms >= 1e3:
        val = ohms / 1e3
        return f"{int(val)}k" if val.is_integer() else f"{val:.2g}k"
    else:
        return f"{int(ohms)}" if float(ohms).is_integer() else f"{ohms:.2g}"

def quantize_weight_tensor(w, rf=10000.0, thresh=0.001):
    """Vectorized quantization for PyTorch tensors."""
    abs_w = torch.abs(w)
    sign_w = torch.sign(w)
    mask = (abs_w >= thresh) & (abs_w <= 100.0)
    ideal_r = rf / torch.clamp(abs_w, min=1e-6)
    diffs = torch.abs(ideal_r.unsqueeze(-1) - CURRENT_TENSOR.to(w.device))
    best_idx = torch.argmin(diffs, dim=-1)
    snapped_r = CURRENT_TENSOR.to(w.device)[best_idx]
    w_quant = sign_w * (rf / snapped_r)
    return torch.where(mask, w_quant, torch.zeros_like(w))

def quantize_bias_tensor(b, rf=10000.0, v_ref=5.0, thresh=0.001):
    """Vectorized bias quantization for PyTorch tensors."""
    abs_b = torch.abs(b)
    sign_b = torch.sign(b)
    mask = (abs_b >= thresh) & (abs_b <= 50.0)
    ideal_r = rf / torch.clamp(abs_b / v_ref, min=1e-6)
    diffs = torch.abs(ideal_r.unsqueeze(-1) - CURRENT_TENSOR.to(b.device))
    best_idx = torch.argmin(diffs, dim=-1)
    snapped_r = CURRENT_TENSOR.to(b.device)[best_idx]
    b_quant = sign_b * (rf / snapped_r) * v_ref
    return torch.where(mask, b_quant, torch.zeros_like(b))



# -----------------------------------------------------------------------------
# 2. Dataset Download & Smart Preprocessing (ylecun/mnist -> 8x8 Voltages)
# -----------------------------------------------------------------------------
HF_TRAIN_URL = "https://huggingface.co/datasets/ylecun/mnist/resolve/main/mnist/train-00000-of-00001.parquet"
HF_TEST_URL = "https://huggingface.co/datasets/ylecun/mnist/resolve/main/mnist/test-00000-of-00001.parquet"


def download_file(url, local_path):
    if not os.path.exists(local_path):
        print(f"Downloading {os.path.basename(local_path)} from Hugging Face...")
        urllib.request.urlretrieve(url, local_path)
        print(f"Downloaded {os.path.basename(local_path)} ({os.path.getsize(local_path) / 1024 / 1024:.1f} MB)")


def preprocess_digit_image(pil_img, pad=2):
    """
    Crops digit to bounding box (with padding) preserving aspect ratio,
    and downsamples to 8x8 using Area/Box pooling.
    Returns 8x8 numpy array normalized to [0.0V, 5.0V].
    """
    arr = np.array(pil_img)
    rows = np.where(arr.max(axis=1) > 20)[0]
    cols = np.where(arr.max(axis=0) > 20)[0]
    if len(rows) == 0 or len(cols) == 0:
        im_proc = pil_img.resize((8, 8), Image.Resampling.BOX)
    else:
        r_min, r_max = max(0, rows[0] - pad), min(arr.shape[0], rows[-1] + 1 + pad)
        c_min, c_max = max(0, cols[0] - pad), min(arr.shape[1], cols[-1] + 1 + pad)
        h = r_max - r_min
        w = c_max - c_min
        diff = abs(h - w)
        if h > w:
            c_min = max(0, c_min - diff // 2)
            c_max = min(arr.shape[1], c_max + (diff - diff // 2))
        elif w > h:
            r_min = max(0, r_min - diff // 2)
            r_max = min(arr.shape[0], r_max + (diff - diff // 2))
        im_proc = pil_img.crop((c_min, r_min, c_max, r_max)).resize((8, 8), Image.Resampling.BOX)
    return np.array(im_proc, dtype=np.float32) / 255.0 * 5.0


def prepare_dataset():
    os.makedirs(CACHE_DIR, exist_ok=True)
    train_parquet = os.path.join(CACHE_DIR, "train.parquet")
    test_parquet = os.path.join(CACHE_DIR, "test.parquet")
    train_npz = os.path.join(CACHE_DIR, "mnist_8x8_train.npz")
    test_npz = os.path.join(CACHE_DIR, "mnist_8x8_test.npz")

    download_file(HF_TRAIN_URL, train_parquet)
    download_file(HF_TEST_URL, test_parquet)

    def process_and_cache(parquet_path, npz_path, name):
        if os.path.exists(npz_path):
            data = np.load(npz_path)
            return torch.tensor(data["X"]), torch.tensor(data["y"])

        print(f"Preprocessing {name} images to 8x8 analog voltage inputs (0..5V)...")
        t0 = time.time()
        tbl = pq.read_table(parquet_path).to_pydict()
        images = tbl["image"]
        labels = np.array(tbl["label"], dtype=np.int64)

        X = []
        for item in images:
            im = Image.open(io.BytesIO(item["bytes"]))
            arr8 = preprocess_digit_image(im)
            X.append(arr8.flatten())

        X = np.array(X, dtype=np.float32)
        np.savez_compressed(npz_path, X=X, y=labels)
        print(f"Finished {name}: {X.shape[0]} samples processed in {time.time() - t0:.2f}s")
        return torch.tensor(X), torch.tensor(labels)

    X_train, y_train = process_and_cache(train_parquet, train_npz, "train")
    X_test, y_test = process_and_cache(test_parquet, test_npz, "test")
    return X_train, y_train, X_test, y_test


# -----------------------------------------------------------------------------
# 3. Discrete Analog Neural Network Model with QAT
# -----------------------------------------------------------------------------
class DiscreteAnalogNN(nn.Module):
    def __init__(self, n_in=64, n_hidden=16, n_out=10, v_sat=10.5):
        super().__init__()
        self.fc1 = nn.Linear(n_in, n_hidden)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(n_hidden, n_out)
        self.v_sat = v_sat
        self.qat_enabled = False

    def forward(self, x):
        w1 = self.fc1.weight
        b1 = self.fc1.bias
        w2 = self.fc2.weight
        b2 = self.fc2.bias

        if self.qat_enabled:
            # Straight-Through Estimator (STE) for E96 resistor lattice
            w1 = w1 + (quantize_weight_tensor(w1) - w1).detach()
            b1 = b1 + (quantize_bias_tensor(b1) - b1).detach()
            w2 = w2 + (quantize_weight_tensor(w2) - w2).detach()
            b2 = b2 + (quantize_bias_tensor(b2) - b2).detach()

        # Physical op-amp summing amplifier with +/- 10.5V saturation
        z1 = torch.clamp(nn.functional.linear(x, w1, b1), -self.v_sat, self.v_sat)
        # DC2 Precision Half-Wave Rectifier
        h = torch.clamp(self.relu(z1), 0.0, self.v_sat)
        # DC3 Class Summing with op-amp saturation
        scores = torch.clamp(nn.functional.linear(h, w2, b2), -self.v_sat, self.v_sat)
        return scores


# -----------------------------------------------------------------------------
# 4. Training & Quantization Pipeline
# -----------------------------------------------------------------------------
def train_and_export(epochs=25, qat_epochs=15, batch_size=256, lr=0.015, seed=42, kit="60values"):
    set_resistor_kit(kit)
    torch.manual_seed(seed)
    np.random.seed(seed)

    print("\n" + "="*70)
    print(f"DISCRETE ANALOG NEURAL NETWORK: MNIST TRAINING & {kit.upper()} QUANTIZATION")
    print("="*70)

    X_train, y_train, X_test, y_test = prepare_dataset()
    print(f"Dataset Loaded: {len(X_train)} training samples, {len(X_test)} testing samples.")
    print("Input Dimensionality: 64 features (8x8 pixel voltages, 0.0V to 5.0V)")
    print("Hardware Architecture: 64 Inputs -> 16 Neurons (TL074 Sum + DC2 ReLU) -> 10 Classes (DC3 WTA)")

    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)
    model = DiscreteAnalogNN(64, 16, 10)
    crit = nn.CrossEntropyLoss()

    # Phase 1: Continuous Training
    print(f"\n[Phase 1] Training Continuous Floating-Point Weights ({epochs} epochs)...")
    opt = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    best_acc = 0.0
    for ep in range(epochs):
        model.train()
        for xb, yb in train_loader:
            opt.zero_grad()
            loss = crit(model(xb), yb)
            loss.backward()
            opt.step()
        scheduler.step()

        if (ep + 1) % 5 == 0 or ep == epochs - 1:
            model.eval()
            with torch.no_grad():
                preds = model(X_test).argmax(dim=1)
                acc = (preds == y_test).float().mean().item() * 100.0
            print(f"  Epoch {ep+1:02d}/{epochs}: Float Test Accuracy = {acc:.2f}%")

    # Phase 2: Quantization-Aware Fine-Tuning (QAT)
    print(f"\n[Phase 2] Quantization-Aware Fine-Tuning on IEC E96 Resistor Lattice ({qat_epochs} epochs)...")
    model.qat_enabled = True
    opt_qat = optim.Adam(model.parameters(), lr=0.002)

    for ep in range(qat_epochs):
        model.train()
        for xb, yb in train_loader:
            opt_qat.zero_grad()
            loss = crit(model(xb), yb)
            loss.backward()
            opt_qat.step()

        if (ep + 1) % 5 == 0 or ep == qat_epochs - 1:
            model.eval()
            with torch.no_grad():
                preds = model(X_test).argmax(dim=1)
                acc_qat = (preds == y_test).float().mean().item() * 100.0
            print(f"  QAT Epoch {ep+1:02d}/{qat_epochs}: Quantized Circuit Accuracy = {acc_qat:.2f}%")

    # -------------------------------------------------------------------------
    # 5. Extract and Validate Physical Resistor Quantization
    # -------------------------------------------------------------------------
    print("\n[Phase 3] Snapping to Physical Standard Resistors & Generating BOM Data...")
    Rf = 10000.0  # 10.0 kOhm feedback
    V_ref = 5.0   # 5.0 V reference rail

    W1 = model.fc1.weight.detach().cpu().numpy()  # (16, 64)
    b1 = model.fc1.bias.detach().cpu().numpy()    # (16,)
    W2 = model.fc2.weight.detach().cpu().numpy()  # (10, 16)
    b2 = model.fc2.bias.detach().cpu().numpy()    # (10,)

    # Layer 1 Mapping
    l1_weights_list = []
    W1_hw = np.zeros_like(W1)
    b1_hw = np.zeros_like(b1)

    for j in range(16):
        neuron_inputs = []
        for i in range(64):
            w = W1[j, i]
            if abs(w) >= 1e-3:
                r_ideal = Rf / abs(w)
                r_val = quantize_to_resistor(r_ideal)
                if r_val is not None:
                    eff_w = np.sign(w) * (Rf / r_val)
                    W1_hw[j, i] = eff_w
                    neuron_inputs.append({
                        "input_idx": i,
                        "neuron_idx": j,
                        "weight_float": float(w),
                        "is_populated": True,
                        "resistor_ohms": float(r_val),
                        "resistor_str": format_resistor_value(r_val),
                        "polarity": "positive" if w > 0 else "negative"
                    })
                    continue
            # DNP
            neuron_inputs.append({
                "input_idx": i,
                "neuron_idx": j,
                "weight_float": float(w),
                "is_populated": False,
                "resistor_ohms": None,
                "resistor_str": "DNP",
                "polarity": "positive" if w >= 0 else "negative"
            })

        b = b1[j]
        rb_val = None
        if abs(b) >= 1e-3:
            rb_ideal = Rf / (abs(b) / V_ref)
            rb_val = quantize_to_resistor(rb_ideal)
            if rb_val is not None:
                b1_hw[j] = np.sign(b) * (Rf / rb_val) * V_ref

        l1_weights_list.append({
            "neuron_idx": j,
            "bias_float": float(b),
            "bias_resistor_ohms": float(rb_val) if rb_val else None,
            "bias_resistor_str": format_resistor_value(rb_val),
            "bias_rail": "-5V_REF" if b > 0 else "+5V_REF",
            "inputs": neuron_inputs
        })

    l1_data = {
        "Rf_ohms": Rf,
        "n_inputs": 64,
        "n_neurons": 16,
        "weights": l1_weights_list
    }

    # Layer 2 Mapping
    l2_weights_list = []
    W2_hw = np.zeros_like(W2)
    b2_hw = np.zeros_like(b2)

    for k in range(10):
        class_inputs = []
        for j in range(16):
            w = W2[k, j]
            if abs(w) >= 1e-3:
                r_ideal = Rf / abs(w)
                r_val = quantize_to_resistor(r_ideal)
                if r_val is not None:
                    eff_w = np.sign(w) * (Rf / r_val)
                    W2_hw[k, j] = eff_w
                    class_inputs.append({
                        "hidden_idx": j,
                        "class_idx": k,
                        "weight_float": float(w),
                        "is_populated": True,
                        "resistor_ohms": float(r_val),
                        "resistor_str": format_resistor_value(r_val),
                        "polarity": "positive" if w > 0 else "negative"
                    })
                    continue
            class_inputs.append({
                "hidden_idx": j,
                "class_idx": k,
                "weight_float": float(w),
                "is_populated": False,
                "resistor_ohms": None,
                "resistor_str": "DNP",
                "polarity": "positive" if w >= 0 else "negative"
            })

        b = b2[k]
        rb_val = None
        if abs(b) >= 1e-3:
            rb_ideal = Rf / (abs(b) / V_ref)
            rb_val = quantize_to_resistor(rb_ideal)
            if rb_val is not None:
                b2_hw[k] = np.sign(b) * (Rf / rb_val) * V_ref

        l2_weights_list.append({
            "class_idx": k,
            "bias_float": float(b),
            "bias_resistor_ohms": float(rb_val) if rb_val else None,
            "bias_resistor_str": format_resistor_value(rb_val),
            "bias_rail": "-5V_REF" if b > 0 else "+5V_REF",
            "inputs": class_inputs
        })

    l2_data = {
        "Rf_ohms": Rf,
        "n_inputs": 16,
        "n_classes": 10,
        "weights": l2_weights_list
    }

    # Save JSON files
    l1_path = os.path.join(WORKSPACE_DIR, "weights_layer1.json")
    l2_path = os.path.join(WORKSPACE_DIR, "weights_layer2.json")
    model_path = os.path.join(WORKSPACE_DIR, "mnist_analog_model.pt")

    with open(l1_path, "w") as f:
        json.dump(l1_data, f, indent=2)
    with open(l2_path, "w") as f:
        json.dump(l2_data, f, indent=2)
    torch.save(model.state_dict(), model_path)

    print(f"Saved {l1_path}")
    print(f"Saved {l2_path}")
    print(f"Saved {model_path}")

    # Final Full Benchmark on Test Set (10,000 samples)
    X_test_np = X_test.numpy()
    y_test_np = y_test.numpy()

    # Exact Hardware forward propagation equations:
    # Layer 1: v_sum1 = X @ W1_hw.T + b1_hw
    # DC2:     v_relu = max(0, v_sum1)
    # Layer 2: v_sum2 = v_relu @ W2_hw.T + b2_hw
    # DC3:     pred   = argmax(v_sum2)
    v_sum1 = np.clip(X_test_np @ W1_hw.T + b1_hw, -10.5, 10.5)
    v_relu = np.clip(np.maximum(0.0, v_sum1), 0.0, 10.5)
    v_sum2 = np.clip(v_relu @ W2_hw.T + b2_hw, -10.5, 10.5)
    preds_hw = np.argmax(v_sum2, axis=1)

    final_correct = int(np.sum(preds_hw == y_test_np))
    final_acc = (final_correct / len(y_test_np)) * 100.0

    print("\n" + "-"*70)
    print(f"FINAL DISCRETE ANALOG E96 HARDWARE ACCURACY: {final_acc:.2f}% ({final_correct}/{len(y_test_np)} samples)")
    print("-"*70)

    # Print Per-Digit Accuracy
    print("Per-Digit Accuracy on 10,000 MNIST Test Set:")
    for digit in range(10):
        mask = (y_test_np == digit)
        digit_acc = (np.sum(preds_hw[mask] == digit) / np.sum(mask)) * 100.0
        total_d = np.sum(mask)
        correct_d = np.sum(preds_hw[mask] == digit)
        print(f"  Digit {digit}: {digit_acc:.2f}% ({correct_d}/{total_d})")

    return final_acc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Discrete Analog NN on MNIST and quantize to standard resistors.")
    parser.add_argument("--kit", choices=["60values", "e96"], default="60values",
                        help="Resistor kit to quantize to: '60values' (user 60-value SMD kit) or 'e96' (full standard E96 1% series)")
    parser.add_argument("--epochs", type=int, default=30, help="Number of continuous training epochs (default: 30)")
    parser.add_argument("--qat-epochs", type=int, default=20, help="Number of QAT fine-tuning epochs (default: 20)")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size (default: 256)")
    parser.add_argument("--lr", type=float, default=0.015, help="Initial learning rate (default: 0.015)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    train_and_export(
        epochs=args.epochs,
        qat_epochs=args.qat_epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
        kit=args.kit
    )
