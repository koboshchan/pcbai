# Discrete Analog Neural Network for MNIST Inference

An end-to-end, fully hardware-realized **discrete analog neural network system** implemented across a modular **7-PCB backplane stack**. The network performs real-time classification of MNIST digits ($8 \times 8$ resolution) using passive resistor crossbars, operational amplifier summing junctions, diode-based precision rectifiers, and analog Winner-Take-All (WTA) maximum detection with visual LED outputs and a 3.3V microcontroller ADC interface.

All 7 printed circuit boards achieve **100% Zero-DRC compliance** in KiCad 10 / 8 (0 electrical violations, 0 unconnected items) within standard **$100\text{ mm} \times 100\text{ mm}$** manufacturing limits. All synaptic and circuit resistors are strictly constrained and rounded to a single commercial **60-value 0805 SMD Resistor Kit**.

---

## 1. System Architecture

The hardware architecture partitions a 2-layer neural network ($64 \rightarrow 16 \rightarrow 10$) across 6 card-edge blades plugged into a central motherboard backplane:

```
                                 7-PCB MODULAR SYSTEM ARCHITECTURE
                                 
  [ Microcontroller SPI ] 
            │
            ▼ J_MCU_SPI (6-Pin Header)
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ MOTHERBOARD v8.0 (100 mm x 100 mm Backplane)                                            │
  │  - 8x 74HC595D Shift Registers (Serpentine chain driving IN_0..63 single-ended 0..5V)  │
  │  - 6x 72-Pin Straight Card-Edge Sockets (J_SLOT0 .. J_SLOT5, 11.0 mm pitch)            │
  │  - 10-Channel Precision Voltage Dividers (R_TOP=22k / R_BOT=10k, scaling 10V -> 3.2V)  │
  │  - J_MCU_SCORES Header (3.3V ADC readout to microcontroller)                            │
  └───────┬──────────────┬──────────────┬──────────────┬──────────────┬─────────────┬──────┘
          │ J_SLOT0      │ J_SLOT1      │ J_SLOT2      │ J_SLOT3      │ J_SLOT4     │ J_SLOT5
          ▼              ▼              ▼              ▼              ▼             ▼
     ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐   ┌─────────┐
     │  DC1A   │    │  DC1B   │    │  DC1C   │    │  DC1D   │    │   DC2   │   │   DC3   │
     │ Neurons │    │ Neurons │    │ Neurons │    │ Neurons │    │ 16-Ch   │   │ Layer 2 │
     │  0 .. 3 │    │  4 .. 7 │    │ 8 .. 11 │    │ 12.. 15 │    │ Active  │   │ Weights │
     │ Synapse │    │ Synapse │    │ Synapse │    │ Synapse │    │ Rectifier│  │  + WTA   │
     │ Matrix  │    │ Matrix  │    │ Matrix  │    │ Matrix  │    │ (ReLU)  │   │ + LEDs  │
     └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘   └────┬────┘
          │              │              │              │              │           │
          └──────────────┴──────┬───────┴──────────────┘              │           │
                     V_SUM_0..15 (Summing Outputs)                    │           │
                                └─────────────────────────────────────┘           │
                                              ACT_0..15 (Hidden Activations)      │
                                                     └────────────────────────────┘
                                                                SCORE_0..9
```

### Physical Signal Flow:
1. **Input Ingestion**: The host MCU clocks 64 binary or analog-conditioned pixels via SPI into 8 daisy-chained `74HC595D` shift registers on the Motherboard. The registers latch and drive physical bus traces `IN_0` .. `IN_63` ($0.0\text{V} \dots 5.0\text{V}$).
2. **Layer 1 Synaptic Summation (DC1A–DC1D)**: Four daughtercards compute 4 hidden neurons each ($64 \text{ inputs} \times 4 = 256$ synapses per card). Each synaptic resistor $R1_{i, j}$ feeds current into a virtual-ground summing junction of a low-noise `TL074` JFET op-amp:
   $$V_{SUM, j} = \text{clip}\left(- R_f \sum_{i=0}^{63} \frac{V_{IN, i} \cdot \text{sgn}(W1_{j, i})}{R1_{i, j}} - \frac{R_f}{Rb_j} V_{rail, j}, -10.5\text{V}, +10.5\text{V}\right)$$
3. **Layer 1 Active Precision Rectification (DC2)**: 16 active superdiode precision half-wave rectifiers (`TL074` + `1N4148`) eliminate the classic diode $0.7\text{V}$ forward threshold:
   $$\text{ACT}_k = \text{clip}\left(\max(0, - V_{SUM, k}), 0.0\text{V}, 10.5\text{V}\right)$$
4. **Layer 2 Synapses, WTA & LEDs (DC3)**: A $16 \times 10$ resistor crossbar sums hidden activations into 10 class outputs (`SCORE_0` .. `SCORE_9`):
   $$SCORE_c = \text{clip}\left(- R_f \sum_{k=0}^{15} \frac{\text{ACT}_k \cdot \text{sgn}(W2_{c, k})}{R2_{k, c}} - \frac{R_f}{Rb_c} V_{rail, c}, -10.5\text{V}, +10.5\text{V}\right)$$
   - **Winner-Take-All Peak Follower**: 10 ultrafast diodes form an analog OR-bus ($V_{WTA} = \max(SCORE) - 0.65\text{V}$).
   - **Visual Digit Indicators**: 10 SMD 0805 LEDs glow proportionally to class score ($I_{LED} \approx (SCORE - 2.0\text{V}) / 1\text{k}\Omega$). The winning digit glows brightest.
5. **Motherboard ADC Readout (`J_MCU_SCORES`)**: Each score passes through a $22\text{k}\Omega / 10\text{k}\Omega$ voltage divider, safely mapping $+10.5\text{V} \rightarrow 3.28\text{V}$ for direct connection to any 3.3V microcontroller ADC.

---

## 2. Hardware Verification & Benchmark Results

The entire physical PCB system was validated using two independent methods:
1. **Authoritative KiCad DRC CLI**: Full geometric and electrical rule verification across all 7 board files.
2. **Direct PCB Pin-Level Emulation** ([`emulate_pcb_hardware.py`](emulate_pcb_hardware.py)): A pure Python S-expression parser extracts every footprint, pad net, and resistor value directly from copper and simulates physical pin signals across 10,000 real MNIST test images.

### Comprehensive Benchmark Matrix (10,000 MNIST Test Samples):

| Evaluation Mode | Accuracy | Correct / Total | Evaluation Time | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Float32 PyTorch Reference** | **95.02%** | 9,502 / 10,000 | — | Trained on official Hugging Face `ylecun/mnist` |
| **Full E96 Resistor Lattice (Ideal)** | **94.93%** | 9,493 / 10,000 | — | Quantization-Aware Training (QAT) |
| **Direct PCB Pin Emulator (Nominal)** | **92.15%** | **9,215 / 10,000** | **0.66 s** | **Directly extracted from .kicad_pcb copper files** |
| **Direct PCB Pin Emulator (Monte Carlo)** | **92.06%** | **9,206 / 10,000** | **1.05 s** | **1% Resistor Tolerance + 3 mV Op-Amp $V_{os}$** |

### Per-Digit Accuracy on Direct PCB Emulation (10,000 Test Set):
```
  Digit 0:  96.94% (950 / 980)
  Digit 1:  94.89% (1,077 / 1,135)
  Digit 2:  92.64% (956 / 1,032)
  Digit 3:  91.58% (925 / 1,010)
  Digit 4:  96.44% (947 / 982)
  Digit 5:  91.03% (812 / 892)
  Digit 6:  95.09% (911 / 958)
  Digit 7:  93.68% (963 / 1,028)
  Digit 8:  94.35% (919 / 974)
  Digit 9:  74.83% (755 / 1,009)
```

---

## 3. KiCad Design Rule Check (DRC) Status

Every board was compiled and verified using `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --severity-all`:

| Board File | Board Function | Dimensions | Layers | Electrical Violations | Unconnected Items | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| [`motherboard.kicad_pcb`](motherboard.kicad_pcb) | Backplane + MCU Interface | 100 × 100 mm | 4 | **0** | **0** | **PASS** |
| [`daughtercard1a_weights_l1.kicad_pcb`](daughtercard1a_weights_l1.kicad_pcb) | Layer 1 Synapses (N0..3) | 94.28 × 100 mm | 4 | **0** | **0** | **PASS** |
| [`daughtercard1b_weights_l1.kicad_pcb`](daughtercard1b_weights_l1.kicad_pcb) | Layer 1 Synapses (N4..7) | 94.28 × 100 mm | 4 | **0** | **0** | **PASS** |
| [`daughtercard1c_weights_l1.kicad_pcb`](daughtercard1c_weights_l1.kicad_pcb) | Layer 1 Synapses (N8..11) | 94.28 × 100 mm | 4 | **0** | **0** | **PASS** |
| [`daughtercard1d_weights_l1.kicad_pcb`](daughtercard1d_weights_l1.kicad_pcb) | Layer 1 Synapses (N12..15) | 94.28 × 100 mm | 4 | **0** | **0** | **PASS** |
| [`daughtercard2_relu_l1.kicad_pcb`](daughtercard2_relu_l1.kicad_pcb) | 16-Channel Precision Rectifier | 94.28 × 100 mm | 2 | **0** | **0** | **PASS** |
| [`daughtercard3_weights_l2_wta.kicad_pcb`](daughtercard3_weights_l2_wta.kicad_pcb) | L2 Weights + WTA + LEDs | 94.28 × 100 mm | 4 | **0** | **0** | **PASS** |

---

## 4. Bill of Materials (BOM) & 60-Value SMD Resistor Kit Coverage

All 1,274 resistors across all 7 PCBs are strictly rounded to values within a standard **commercial 60-value 0805 SMD resistor assortment** (`0R` to `10M`, 25 pcs/value = 1,500 pcs/kit):

| Category | Component / Value | Package | Qty | Key Usage |
| :--- | :--- | :---: | :---: | :--- |
| **Op-Amps** | **TL074** (TL074CDT / TL074IDR) | SOIC-14 | **11** | 4 on DC1A–D, 4 on DC2, 3 on DC3 |
| **Logic ICs** | **74HC595D** (SN74HC595D) | SOIC-16 | **8** | 64-bit serial-in parallel-out digital input registers |
| **Diodes** | **1N4148** (1N4148W) | SOD-123 | **42** | 32 on DC2 (active ReLU), 10 on DC3 (WTA peak bus) |
| **LEDs** | **Class Indicator LEDs** | 0805 | **10** | Digits 0 through 9 on DC3 |
| **Card Sockets**| **72-Pin Card-Edge Female** | 2.54 mm pitch | **6** | Modular daughtercard slots on Motherboard |
| **Headers** | **1x06 Vertical Header** | 2.54 mm pitch | **1** | `J_MCU_SPI` MCU digital control interface |
| **Headers** | **1x12 Vertical Header** | 2.54 mm pitch | **1** | `J_MCU_SCORES` 3.3V-scaled ADC readout |
| **Headers** | **1x08 Vertical Header** | 2.54 mm pitch | **1** | `J_PWR_IN` System power ($\pm 12\text{V}$, $\pm 5\text{V\_REF}$, GND) |
| **Capacitors** | **0.1 µF 50V X7R** | 0805 | **30** | Local IC power rail decoupling |
| **Resistors** | **0805 SMD 1%** (Assorted) | 0805 | **1,274** | Synaptic crossbars, biases, dividers, feedback |

> [!TIP]
> **Procurement Recommendation**: Order **2× kits** of the standard 60-value 0805 assortment (giving 50 pcs per value) plus **8× 100-piece strips** for high-frequency values (`18K`, `22K`, `33K`, `43K`, `51K`, `75K`, `100K`, `200K`) and **1× 100-piece strip of 10K** for 100% complete coverage with ample assembly spares.

See [`BILL_OF_MATERIALS.md`](BILL_OF_MATERIALS.md) for the complete procurement breakdown and [`bom_consolidated.csv`](bom_consolidated.csv) for footprint-by-footprint component assignments.

---

## 5. Repository File Manifest

```
pcbai/
├── motherboard.kicad_pcb               # 6-Slot 72P Backplane with Face-Side MCU SPI & Dividers
├── motherboard.kicad_pro               # KiCad Project file for Motherboard
├── motherboard.kicad_sch               # KiCad Schematic file for Motherboard
├── daughtercard1a_weights_l1.kicad_pcb # DC1A: L1 Synapses (Neurons 0..3)
├── daughtercard1b_weights_l1.kicad_pcb # DC1B: L1 Synapses (Neurons 4..7)
├── daughtercard1c_weights_l1.kicad_pcb # DC1C: L1 Synapses (Neurons 8..11)
├── daughtercard1d_weights_l1.kicad_pcb # DC1D: L1 Synapses (Neurons 12..15)
├── daughtercard2_relu_l1.kicad_pcb     # DC2: 16-Channel Active Precision Rectifier
├── daughtercard3_weights_l2_wta.kicad_pcb # DC3: L2 Weights, WTA Diode Peak Bus & 10 LEDs
├── full_system_assembly.kicad_pcb      # Master 6-Blade Assembled 3D Backplane PCB
├── motherboard_backup_baseline.kicad_pcb # Preserved baseline design backup
│
├── build_full_72p_system.py            # Master builder for the 7-PCB modular system
├── generate_motherboard_v8_mcu.py      # Authoritative generator for Motherboard v8.0
├── generate_perfect_dc3_v29.py         # Authoritative generator for DC3
├── update_pcb_weights.py               # Synchronizes PCB resistor values with trained weights
├── generate_schematics.py              # Generates KiCad schematics (.kicad_sch)
├── kicad_symbols.py                    # Embedded symbol definitions for KiCad
├── export_fabrication.py               # Exports production Gerbers, drill files, and BOMs
├── render_all_boards.py                # Raytraced 3D visual renderer
│
├── train_mnist_hardware.py             # QAT training on Hugging Face MNIST with 60-value kit
├── emulate_pcb_hardware.py             # Authoritative direct PCB & physical pin emulator
├── simulate_ngspice.py                 # Full transistor-level SPICE netlist & transient simulation
├── weights_layer1.json                 # Layer 1 resistor values, polarity, and bias rails
├── weights_layer2.json                 # Layer 2 resistor values, polarity, and bias rails
├── mnist_analog_model.pt               # Trained PyTorch hardware checkpoint
│
├── BILL_OF_MATERIALS.md                # Comprehensive Bill of Materials & Procurement Guide
├── bom_consolidated.csv                # Complete consolidated component list
├── bom_summary.csv                     # Quantity per value procurement summary
├── fabrication/                        # Production Gerbers & drill files (.zip archives)
├── renders/                            # High-resolution 3D board renders
└── archive/                            # Historical routing iteration & exploratory scripts
```

---

## 6. Quick Start & Execution Guide

### Direct PCB Pin-Level Emulation:
```bash
# Run detailed physical pin trace on a single test sample (e.g. sample #0 = Digit 7)
python3 emulate_pcb_hardware.py --sample 0

# Run full 10,000-sample test set benchmark directly through the PCB files
python3 emulate_pcb_hardware.py --benchmark

# Run 10,000-sample test set with 1% resistor tolerance + 3mV op-amp offset (Monte Carlo)
python3 emulate_pcb_hardware.py --benchmark --monte-carlo
```

### Retrain with Hardware Quantization:
```bash
# Train on Hugging Face MNIST with the 60-value SMD kit
python3 train_mnist_hardware.py --kit 60values --epochs 30 --qat-epochs 20

# Update the physical .kicad_pcb files with the newly trained weights and verify DRC
python3 update_pcb_weights.py
```

### Full DRC Verification:
```bash
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --severity-all motherboard.kicad_pcb
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --severity-all daughtercard3_weights_l2_wta.kicad_pcb
```
