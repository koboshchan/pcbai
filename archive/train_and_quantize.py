#!/usr/bin/env python3
"""
train_and_quantize.py
---------------------
Trains a 64 -> 16 (ReLU) -> 10 neural network on downscaled 8x8 handwritten digits
(0-9) and maps the resulting synaptic weights and biases to standard IEC E96 1%
resistor values for discrete analog hardware inference.
"""

import gzip
import io
import json
import os
import urllib.request
import numpy as np

# -----------------------------------------------------------------------------
# 1. IEC E96 Resistor Standards
# -----------------------------------------------------------------------------
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

# Multipliers across decades from 100 Ohm to 10 MOhm
ALL_E96_RESISTORS = []
for decade in [1e2, 1e3, 1e4, 1e5, 1e6]:
    ALL_E96_RESISTORS.extend(E96_BASE_VALUES * decade)
ALL_E96_RESISTORS = np.array(ALL_E96_RESISTORS)


def quantize_to_e96(resistance_ohms):
    """Snaps a resistance value to the closest IEC E96 1% standard resistor."""
    if resistance_ohms <= 0 or np.isinf(resistance_ohms) or np.isnan(resistance_ohms):
        return None
    idx = np.argmin(np.abs(ALL_E96_RESISTORS - resistance_ohms))
    return float(ALL_E96_RESISTORS[idx])


def format_resistor_value(ohms):
    """Formats an Ohm value into clean engineering string (e.g. 10k, 20.5k, 1.24M)."""
    if ohms is None or np.isnan(ohms):
        return "DNP"
    if ohms >= 1e6:
        return f"{ohms / 1e6:.3g}M"
    elif ohms >= 1e3:
        return f"{ohms / 1e3:.3g}k"
    else:
        return f"{ohms:.3g}"


# -----------------------------------------------------------------------------
# 2. Dataset Loading (8x8 Handwritten Digits)
# -----------------------------------------------------------------------------
def load_digits_dataset():
    cache_path = os.path.join(os.path.dirname(__file__), "digits_cache.csv.gz")
    if not os.path.exists(cache_path):
        print("Downloading 8x8 digits dataset...")
        url = "https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/sklearn/datasets/data/digits.csv.gz"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data_bytes = resp.read()
        with open(cache_path, "wb") as f:
            f.write(data_bytes)
    else:
        with open(cache_path, "rb") as f:
            data_bytes = f.read()

    with gzip.GzipFile(fileobj=io.BytesIO(data_bytes)) as gz:
        raw_data = np.loadtxt(gz, delimiter=",")

    # 64 pixel features, normalized to [0.0V, 5.0V]
    X = (raw_data[:, :-1] / 16.0) * 5.0
    y = raw_data[:, -1].astype(int)
    return X, y


# -----------------------------------------------------------------------------
# 3. Model Architecture & Training
# -----------------------------------------------------------------------------
def train_model():
    X, y = load_digits_dataset()
    np.random.seed(1337)
    
    # 80/20 train/test split
    indices = np.random.permutation(len(X))
    split = int(0.8 * len(X))
    X_train, X_test = X[indices[:split]], X[indices[split:]]
    y_train, y_test = y[indices[:split]], y[indices[split:]]

    n_in = 64
    n_hidden = 16
    n_out = 10

    # He normal initialization
    W1 = np.random.randn(n_in, n_hidden) * np.sqrt(2.0 / n_in)
    b1 = np.zeros(n_hidden)
    W2 = np.random.randn(n_hidden, n_out) * np.sqrt(2.0 / n_hidden)
    b2 = np.zeros(n_out)

    # Adam optimizer state
    mW1, vW1 = np.zeros_like(W1), np.zeros_like(W1)
    mb1, vb1 = np.zeros_like(b1), np.zeros_like(b1)
    mW2, vW2 = np.zeros_like(W2), np.zeros_like(W2)
    mb2, vb2 = np.zeros_like(b2), np.zeros_like(b2)

    beta1, beta2, eps = 0.9, 0.999, 1e-8
    lr = 0.015
    batch_size = 64
    n_samples = len(X_train)
    t = 0

    print(f"Training discrete analog NN (64 -> 16 -> 10) on {n_samples} samples...")
    for epoch in range(120):
        perm = np.random.permutation(n_samples)
        for i in range(0, n_samples, batch_size):
            t += 1
            batch_idx = perm[i:i + batch_size]
            xb = X_train[batch_idx]
            yb = y_train[batch_idx]
            B = len(xb)

            # Forward
            z1 = xb @ W1 + b1
            a1 = np.maximum(0, z1)
            z2 = a1 @ W2 + b2

            # Stable softmax
            shift_z2 = z2 - np.max(z2, axis=1, keepdims=True)
            exp_z2 = np.exp(shift_z2)
            probs = exp_z2 / np.sum(exp_z2, axis=1, keepdims=True)

            # Backward
            dz2 = probs.copy()
            dz2[np.arange(B), yb] -= 1.0
            dz2 /= B

            dW2 = a1.T @ dz2 + 1e-4 * W2
            db2 = np.sum(dz2, axis=0)

            da1 = dz2 @ W2.T
            dz1 = da1 * (z1 > 0)
            dW1 = xb.T @ dz1 + 1e-4 * W1
            db1 = np.sum(dz1, axis=0)

            # Adam update
            for param, grad, m, v in [
                (W1, dW1, mW1, vW1), (b1, db1, mb1, vb1),
                (W2, dW2, mW2, vW2), (b2, db2, mb2, vb2)
            ]:
                m[:] = beta1 * m + (1 - beta1) * grad
                v[:] = beta2 * v + (1 - beta2) * (grad ** 2)
                m_hat = m / (1 - beta1 ** t)
                v_hat = v / (1 - beta2 ** t)
                param -= lr * m_hat / (np.sqrt(v_hat) + eps)

    # Evaluate floating-point model
    z1_test = X_test @ W1 + b1
    a1_test = np.maximum(0, z1_test)
    z2_test = a1_test @ W2 + b2
    preds_float = np.argmax(z2_test, axis=1)
    acc_float = np.mean(preds_float == y_test)
    print(f"Floating-point test accuracy: {acc_float * 100:.2f}%")

    # -------------------------------------------------------------------------
    # 4. Hardware Mapping & IEC E96 Resistor Quantization
    # -------------------------------------------------------------------------
    Rf = 10000.0  # 10.0 kOhm feedback resistor
    V_ref = 5.0   # 5.0 V reference rail for bias voltages

    # Quantize Layer 1: W1 (64, 16), b1 (16)
    R_W1 = np.full_like(W1, np.nan)
    W1_quant = np.zeros_like(W1)
    for i in range(n_in):
        for j in range(n_hidden):
            w = W1[i, j]
            if abs(w) >= 1e-4:
                r_ideal = Rf / abs(w)
                r_e96 = quantize_to_e96(r_ideal)
                R_W1[i, j] = r_e96
                # Actual effective hardware weight
                W1_quant[i, j] = np.sign(w) * (Rf / r_e96)

    R_b1 = np.full_like(b1, np.nan)
    b1_quant = np.zeros_like(b1)
    for j in range(n_hidden):
        b = b1[j]
        if abs(b) >= 1e-4:
            # Bias voltage rail is +5V or -5V: V_bias_eff = - (Rf / R_bias) * V_rail
            r_ideal = Rf / (abs(b) / V_ref)
            r_e96 = quantize_to_e96(r_ideal)
            R_b1[j] = r_e96
            b1_quant[j] = np.sign(b) * (Rf / r_e96) * V_ref

    # Quantize Layer 2: W2 (16, 10), b2 (10)
    R_W2 = np.full_like(W2, np.nan)
    W2_quant = np.zeros_like(W2)
    for j in range(n_hidden):
        for k in range(n_out):
            w = W2[j, k]
            if abs(w) >= 1e-4:
                r_ideal = Rf / abs(w)
                r_e96 = quantize_to_e96(r_ideal)
                R_W2[j, k] = r_e96
                W2_quant[j, k] = np.sign(w) * (Rf / r_e96)

    R_b2 = np.full_like(b2, np.nan)
    b2_quant = np.zeros_like(b2)
    for k in range(n_out):
        b = b2[k]
        if abs(b) >= 1e-4:
            r_ideal = Rf / (abs(b) / V_ref)
            r_e96 = quantize_to_e96(r_ideal)
            R_b2[k] = r_e96
            b2_quant[k] = np.sign(b) * (Rf / r_e96) * V_ref

    # Evaluate circuit-level quantized model
    z1_hw = X_test @ W1_quant + b1_quant
    a1_hw = np.maximum(0, z1_hw)
    z2_hw = a1_hw @ W2_quant + b2_quant
    preds_hw = np.argmax(z2_hw, axis=1)
    acc_hw = np.mean(preds_hw == y_test)
    print(f"Discrete Analog E96 Hardware Accuracy: {acc_hw * 100:.2f}%")

    # -------------------------------------------------------------------------
    # 5. Export Hardware Configuration
    # -------------------------------------------------------------------------
    output_dir = os.path.dirname(__file__)
    
    # Layer 1 Data
    l1_data = {
        "Rf_ohms": Rf,
        "n_inputs": n_in,
        "n_neurons": n_hidden,
        "weights": []
    }
    for j in range(n_hidden):
        neuron_weights = []
        for i in range(n_in):
            r_val = R_W1[i, j]
            w_val = W1[i, j]
            neuron_weights.append({
                "input_idx": i,
                "neuron_idx": j,
                "weight_float": float(w_val),
                "is_populated": bool(not np.isnan(r_val)),
                "resistor_ohms": float(r_val) if not np.isnan(r_val) else None,
                "resistor_str": format_resistor_value(r_val),
                "polarity": "positive" if w_val > 0 else "negative"
            })
        b_val = b1[j]
        rb_val = R_b1[j]
        l1_data["weights"].append({
            "neuron_idx": j,
            "bias_float": float(b_val),
            "bias_resistor_ohms": float(rb_val) if not np.isnan(rb_val) else None,
            "bias_resistor_str": format_resistor_value(rb_val),
            "bias_rail": "-5V_REF" if b_val > 0 else "+5V_REF",
            "inputs": neuron_weights
        })

    with open(os.path.join(output_dir, "weights_layer1.json"), "w") as f:
        json.dump(l1_data, f, indent=2)

    # Layer 2 Data
    l2_data = {
        "Rf_ohms": Rf,
        "n_inputs": n_hidden,
        "n_classes": n_out,
        "weights": []
    }
    for k in range(n_out):
        class_weights = []
        for j in range(n_hidden):
            r_val = R_W2[j, k]
            w_val = W2[j, k]
            class_weights.append({
                "hidden_idx": j,
                "class_idx": k,
                "weight_float": float(w_val),
                "is_populated": bool(not np.isnan(r_val)),
                "resistor_ohms": float(r_val) if not np.isnan(r_val) else None,
                "resistor_str": format_resistor_value(r_val),
                "polarity": "positive" if w_val > 0 else "negative"
            })
        b_val = b2[k]
        rb_val = R_b2[k]
        l2_data["weights"].append({
            "class_idx": k,
            "bias_float": float(b_val),
            "bias_resistor_ohms": float(rb_val) if not np.isnan(rb_val) else None,
            "bias_resistor_str": format_resistor_value(rb_val),
            "bias_rail": "-5V_REF" if b_val > 0 else "+5V_REF",
            "inputs": class_weights
        })

    with open(os.path.join(output_dir, "weights_layer2.json"), "w") as f:
        json.dump(l2_data, f, indent=2)

    print("Saved weights_layer1.json and weights_layer2.json successfully.")
    return acc_float, acc_hw


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train Discrete Analog NN and quantize to IEC E96 standard resistors.")
    parser.add_argument("--dataset", choices=["mnist", "digits"], default="mnist",
                        help="Dataset to train on: 'mnist' (Hugging Face ylecun/mnist, 70k samples) or 'digits' (legacy 8x8 toy OCR, 1.8k samples)")
    parser.add_argument("--epochs", type=int, default=30, help="Continuous training epochs")
    parser.add_argument("--qat-epochs", type=int, default=20, help="QAT fine-tuning epochs")
    args = parser.parse_args()

    if args.dataset == "mnist":
        from train_mnist_hardware import train_and_export
        train_and_export(epochs=args.epochs, qat_epochs=args.qat_epochs)
    else:
        train_model()

