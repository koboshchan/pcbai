# Bill of Materials (BOM): Discrete Analog Neural Network System

Comprehensive, consolidated component list across all 7 PCBs in the discrete analog neural network system (**DC1A, DC1B, DC1C, DC1D, DC2, DC3, and Motherboard v8.0**).

---

## 1. Primary Procurement Summary (Active ICs, Diodes, Connectors, Common Passives)

| Category | Component / Value | Package / Footprint | Quantity | Usage & Description | Where Used |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **Op-Amp IC** | **TL074** (or TL074CD / TL074IDR) | SOIC-14 (3.9×8.7 mm, 1.27 mm pitch) | **11** | Low-noise JFET quad op-amp for neuron summing & active rectification | DC1A (1), DC1B (1), DC1C (1), DC1D (1), DC2 (4), DC3 (3) |
| **Logic IC** | **74HC595D** (or SN74HC595D) | SOP-16 / SOIC-16 (3.9×9.9 mm, 1.27 mm pitch) | **8** | 8-bit serial-in parallel-out shift register (64 digital pixel input array) | Motherboard v8.0 (8) |
| **Diodes** | **1N4148** (or 1N4148W) | SOD-123 | **42** | High-speed switching diode ($t_{rr} = 4\text{ ns}$) for active ReLU and WTA maximum bus | DC2 (32), DC3 (10) |
| **LEDs** | **Class Indicator LEDs** (0805) | 0805 SMD (2.0×1.2 mm) | **10** | Visual output digits 0 through 9 (Green / Blue / Red) | DC3 (10) |
| **Sockets** | **72-Pin Female Card-Edge** | 72P Straight Female, 2.54 mm pitch (Shenzhen Yiwei S-072M-2.54-5 or EDAC 345-072-520-201) | **6** | Modular backplane daughtercard slot connectors | Motherboard v8.0 (6) |
| **Headers** | **1x06 Vertical Pin Header** | 1×06 Pin Header, 2.54 mm pitch | **1** | `J_MCU_SPI` MCU digital interface [ +5V, GND, MOSI, SCK, LATCH, OE ] | Motherboard v8.0 (1) |
| **Headers** | **1x12 Vertical Pin Header** | 1×12 Pin Header, 2.54 mm pitch | **1** | `J_MCU_SCORES` 3.3V-scaled score outputs [ SCORE_DIV_0..9, GND, GND ] | Motherboard v8.0 (1) |
| **Headers** | **1x08 Vertical Pin Header** | 1×08 Pin Header, 2.54 mm pitch | **1** | `J_PWR_IN` Main system power [ ±12V, GND, ±5V_REF ] | Motherboard v8.0 (1) |
| **Capacitors** | **0.1 µF (100 nF) 50V X7R** | 0805 SMD | **30** | Local IC power rail decoupling / bypass | DC1A–D (8), DC2 (8), DC3 (6), Motherboard (8) |
| **Resistors** | **10 kΩ 1%** | 0805 SMD | **72** | Op-amp feedback resistors, ReLU bias networks, WTA pull-downs, voltage dividers | DC1A–D (18), DC2 (32), DC3 (12), Motherboard (10) |
| **Resistors** | **20 kΩ 1%** | 0805 SMD | **15** | Precision voltage divider lower arms ($0\text{–}5\text{V} \rightarrow 0\text{–}3.33\text{V}$) & summing | DC1A (3), DC1B (1), DC1D (1), Motherboard (10) |
| **Resistors** | **1 kΩ 1%** | 0805 SMD | **10** | LED current-limiting resistors for class indicator LEDs | DC3 (10) |
| **Resistors** | **0 Ω (Jumper)** | 0805 SMD | **1** | `R_PWR5` Power bus link jumper (+5V_REF to +5V_DIGITAL) | Motherboard v8.0 (1) |

---

## 2. Board-by-Board Breakdown

### Motherboard v8.0 (100 mm × 100 mm)
- **Active ICs**: 8× `74HC595D` (SOIC-16)
- **Bypass Capacitors**: 8× `0.1µF` (0805)
- **Voltage Dividers**: 10× `10kΩ` (0805), 10× `20kΩ` (0805)
- **Power Jumper**: 1× `0Ω` (0805)
- **Connectors**:
  - 6× 72-Pin Card-Edge Sockets (`S-072M-2.54-5` or equivalent 2.54mm pitch)
  - 1× 1×06 Pin Header (`J_MCU_SPI`)
  - 1× 1×12 Pin Header (`J_MCU_SCORES`)
  - 1× 1×08 Pin Header (`J_PWR_IN`)
- **Mounting**: 4× M3 Mounting Holes

### Daughtercards 1A, 1B, 1C, 1D (Layer 1 Synapses: 64 Inputs $\rightarrow$ 16 Hidden Neurons)
Each daughtercard computes 4 neurons ($64 \text{ inputs} \times 4 = 256 \text{ synapses}$ per card):
- **DC1A (Neurons 0..3)**: 1× `TL074` (SOIC-14), 2× `0.1µF` (0805), 187× E96 Resistors (78 DNP zero-weights)
- **DC1B (Neurons 4..7)**: 1× `TL074` (SOIC-14), 2× `0.1µF` (0805), 240× E96 Resistors (25 DNP zero-weights)
- **DC1C (Neurons 8..11)**: 1× `TL074` (SOIC-14), 2× `0.1µF` (0805), 211× E96 Resistors (54 DNP zero-weights)
- **DC1D (Neurons 12..15)**: 1× `TL074` (SOIC-14), 2× `0.1µF` (0805), 162× E96 Resistors (103 DNP zero-weights)
- **Card-Edge**: Integrated 72-Pin PCB Gold Fingers (2.54 mm pitch) on each board

### Daughtercard 2 (16-Channel Active Precision ReLU Activation)
- **Active ICs**: 4× `TL074` Quad Op-Amps (SOIC-14)
- **Diodes**: 32× `1N4148` Ultrafast Switching Diodes (SOD-123)
- **Bypass Capacitors**: 8× `0.1µF` (0805)
- **Precision Resistors**: 32× `10kΩ` 1% (0805)
- **Card-Edge**: Integrated 72-Pin PCB Gold Fingers (2.54 mm pitch)

### Daughtercard 3 (Layer 2 Synapses: 16 Inputs $\rightarrow$ 10 Classes + Winner-Take-All + LEDs)
- **Active ICs**: 3× `TL074` Quad Op-Amps (SOIC-14)
- **Diodes**: 10× `1N4148` Ultrafast Diodes (SOD-123) for WTA Maximum Bus
- **LEDs**: 10× 0805 SMD LEDs (Digits 0..9)
- **Bypass Capacitors**: 6× `0.1µF` (0805)
- **LED Resistors**: 10× `1kΩ` (0805)
- **WTA & Summing Resistors**: 12× `10kΩ` (0805)
- **Synaptic Resistors**: 151× E96 1% Resistors (28 DNP zero-weights)
- **Card-Edge**: Integrated 72-Pin PCB Gold Fingers (2.54 mm pitch)

---

## 3. Synaptic Resistor Kit Recommendation

The 1,024 synapses in Layer 1 and 160 synapses in Layer 2 use standard **E96 1% 0805 SMD resistors** representing the trained neural network floating-point weights:

> [!TIP]
> **Recommended Purchase**: An **0805 SMD 1% Resistor Sample Book** (typically covering all 170 values from $10\,\Omega$ to $10\text{ M}\Omega$, 50 pcs per value).
> - One standard sample book (cost $\approx \$15\text{–}\$20$ on AliExpress/Amazon/LCSC) will contain 100% of all required resistance values for the entire neural network.
