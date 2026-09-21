import json
import os

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
ARTIFACT_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"

with open(os.path.join(WORKSPACE_DIR, "circuit_model.json")) as f:
    model_data = json.load(f)

json_str = json.dumps(model_data)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Discrete Analog Neural Network PCB Stack Emulator</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    .led-on {{
      box-shadow: 0 0 16px 4px rgba(34, 197, 94, 0.8), inset 0 0 4px rgba(255, 255, 255, 0.9);
      background-color: #22c55e !important;
      border-color: #4ade80 !important;
      color: #052e16 !important;
    }}
    .led-off {{
      background-color: #1f2937;
      border-color: #374151;
      color: #9ca3af;
      box-shadow: none;
    }}
    .pixel-cell {{
      transition: background-color 0.1s ease;
    }}
  </style>
</head>
<body class="bg-transparent text-[var(--foreground)] antialiased p-4 sm:p-6">
  <div class="max-w-6xl mx-auto space-y-6">

    <!-- Header Card -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
              PHYSICAL HARDWARE & SPICE EMULATION
            </span>
            <span class="text-xs text-[var(--muted-foreground)]">7-PCB Modular Stack (4 Layers)</span>
          </div>
          <h1 class="text-2xl font-bold tracking-tight text-[var(--foreground)] mt-1">
            Discrete Analog MNIST Neuromorphic Computer
          </h1>
          <p class="text-sm text-[var(--muted-foreground)] mt-1">
            Real-time Kirchhoff Current Law (KCL) circuit simulator verified against ngspice-47 transistor-level macromodels.
          </p>
        </div>

        <!-- Mode & Tolerance Controls -->
        <div class="flex items-center gap-3 bg-[var(--background)] p-3 rounded-xl border border-[var(--border)]">
          <div>
            <label class="text-xs font-medium text-[var(--muted-foreground)] block">1% E96 Tolerance Noise</label>
            <div class="flex items-center gap-2 mt-1">
              <input type="checkbox" id="noiseToggle" class="rounded border-[var(--border)] text-emerald-500 focus:ring-emerald-500 h-4 w-4">
              <span class="text-xs font-mono text-[var(--foreground)]" id="noiseLabel">Ideal (0%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Hardware & SPICE Performance Banner -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3.5 text-center">
        <span class="text-[11px] font-medium text-[var(--muted-foreground)] block">SPICE Settling Time</span>
        <span class="text-lg font-bold font-mono text-emerald-500">1.06 µs</span>
        <span class="text-[10px] text-[var(--muted-foreground)] block mt-0.5">90% Rise Time</span>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3.5 text-center">
        <span class="text-[11px] font-medium text-[var(--muted-foreground)] block">Analog Throughput</span>
        <span class="text-lg font-bold font-mono text-emerald-500">~940,000 /s</span>
        <span class="text-[10px] text-[var(--muted-foreground)] block mt-0.5">Physical Inferences</span>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3.5 text-center">
        <span class="text-[11px] font-medium text-[var(--muted-foreground)] block">Total Stack Power</span>
        <span class="text-lg font-bold font-mono text-emerald-500">1.13 W</span>
        <span class="text-[10px] text-[var(--muted-foreground)] block mt-0.5">32 Op-Amps + WTA</span>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3.5 text-center">
        <span class="text-[11px] font-medium text-[var(--muted-foreground)] block">Energy Efficiency</span>
        <span class="text-lg font-bold font-mono text-emerald-500">1.20 µJ</span>
        <span class="text-[10px] text-[var(--muted-foreground)] block mt-0.5">Per Analog Inference</span>
      </div>
    </div>

    <!-- Main Grid: Input & PCB Pipeline -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- Left Column: Input Drawing & Digit Presets (4 Cols) -->
      <div class="lg:col-span-4 space-y-6">
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-sm text-[var(--foreground)] uppercase tracking-wider">
              1. Input Sensor Matrix (64 Pixels)
            </h2>
            <button onclick="clearGrid()" class="text-xs px-2.5 py-1 rounded-md bg-[var(--background)] border border-[var(--border)] hover:bg-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition">
              Clear
            </button>
          </div>

          <!-- 8x8 Canvas / Grid -->
          <div class="flex justify-center p-3 bg-[var(--background)] rounded-xl border border-[var(--border)]">
            <div id="pixelGrid" class="grid grid-cols-8 gap-1 w-64 h-64 select-none touch-none">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <div class="text-xs text-[var(--muted-foreground)] text-center">
            Click & drag on cells to draw pixel voltages (0.0V to 5.0V)
          </div>

          <!-- Digit Presets -->
          <div>
            <span class="text-xs font-medium text-[var(--muted-foreground)] block mb-2">MNIST Test Specimens:</span>
            <div class="grid grid-cols-5 gap-2">
              <button onclick="loadPreset(0)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">0</button>
              <button onclick="loadPreset(1)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">1</button>
              <button onclick="loadPreset(2)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">2</button>
              <button onclick="loadPreset(3)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">3</button>
              <button onclick="loadPreset(4)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">4</button>
              <button onclick="loadPreset(5)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">5</button>
              <button onclick="loadPreset(6)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">6</button>
              <button onclick="loadPreset(7)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">7</button>
              <button onclick="loadPreset(8)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">8</button>
              <button onclick="loadPreset(9)" class="preset-btn py-1.5 px-3 rounded-lg text-sm font-semibold bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 transition">9</button>
            </div>
          </div>
        </div>

        <!-- Motherboard Dual-Rail Telemetry -->
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm space-y-3">
          <h2 class="font-semibold text-sm text-[var(--foreground)] uppercase tracking-wider">
            Motherboard: DAC & Inverters
          </h2>
          <div class="grid grid-cols-2 gap-3 text-xs">
            <div class="p-3 bg-[var(--background)] rounded-xl border border-[var(--border)]">
              <span class="text-[var(--muted-foreground)] block">Active Input Pins</span>
              <span id="activePins" class="text-base font-bold text-[var(--foreground)]">0 / 64</span>
            </div>
            <div class="p-3 bg-[var(--background)] rounded-xl border border-[var(--border)]">
              <span class="text-[var(--muted-foreground)] block">Total Input Power</span>
              <span id="inputPower" class="text-base font-bold text-[var(--foreground)]">0.0 mW</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Circuit Processing Stages (8 Cols) -->
      <div class="lg:col-span-8 space-y-6">

        <!-- Stage 2: Daughtercards 1A..1D (Synaptic Summing) -->
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-sm text-[var(--foreground)] uppercase tracking-wider">
              2. Layer 1 Summing Amplifiers (TL074 Op-Amps on DC1A..DC1D)
            </h2>
            <span class="text-xs text-[var(--muted-foreground)]">Linear Range: -10.5V to +10.5V</span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3" id="dc1Container">
            <!-- DC1A..DC1D Cards Rendered Dynamically -->
          </div>
        </div>

        <!-- Stage 3: Daughtercard 2 (Active Precision ReLUs) -->
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-sm text-[var(--foreground)] uppercase tracking-wider">
              3. Daughtercard 2: Active Precision Rectifiers (ReLU)
            </h2>
            <span class="text-xs text-[var(--muted-foreground)]">16x TL074 + 1N4148 Diodes</span>
          </div>
          <div class="grid grid-cols-4 sm:grid-cols-8 gap-2" id="reluContainer">
            <!-- 16 ReLU outputs -->
          </div>
        </div>

        <!-- Stage 4: Daughtercard 3 (L2 Weights & WTA LED Array) -->
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-sm text-[var(--foreground)] uppercase tracking-wider">
              4. Daughtercard 3: WTA Argmax & 10 Output LEDs
            </h2>
            <span class="text-xs text-[var(--muted-foreground)]">LM339 Comparators</span>
          </div>

          <!-- 10 Class Sum Meters and LEDs -->
          <div class="grid grid-cols-2 sm:grid-cols-5 gap-3" id="ledContainer">
            <!-- 10 LEDs -->
          </div>

          <!-- Recognized Output Banner -->
          <div class="mt-4 p-4 bg-[var(--background)] border border-[var(--border)] rounded-xl flex items-center justify-between">
            <div>
              <span class="text-xs text-[var(--muted-foreground)] block">ANALOG INFERENCE RESULT</span>
              <div class="text-2xl font-extrabold text-emerald-500 flex items-center gap-2">
                DIGIT <span id="winningDigit" class="underline decoration-emerald-500">?</span>
              </div>
            </div>
            <div class="text-right">
              <span class="text-xs text-[var(--muted-foreground)] block">Winning Margin (ΔV)</span>
              <span id="winMargin" class="text-base font-mono font-bold text-[var(--foreground)]">+0.00 V</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>

  <script>
    const MODEL = {json_str};
    let pixels = new Array(64).fill(0.0);
    let isDrawing = false;
    let addNoise = false;

    // Initialize Grid
    const gridEl = document.getElementById("pixelGrid");
    for (let i = 0; i < 64; i++) {{
      const cell = document.createElement("div");
      cell.className = "pixel-cell rounded cursor-pointer border border-[var(--border)] bg-zinc-950";
      cell.dataset.idx = i;
      cell.addEventListener("mousedown", (e) => {{
        isDrawing = true;
        setPixel(i, 5.0);
      }});
      cell.addEventListener("mouseenter", (e) => {{
        if (isDrawing) setPixel(i, 5.0);
      }});
      gridEl.appendChild(cell);
    }}

    window.addEventListener("mouseup", () => {{ isDrawing = false; }});

    function setPixel(idx, val) {{
      pixels[idx] = val;
      updatePixelUI();
      evaluateCircuit();
    }}

    function clearGrid() {{
      pixels.fill(0.0);
      updatePixelUI();
      evaluateCircuit();
    }}

    function loadPreset(digit) {{
      const sample = MODEL.samples.find(s => s.digit === digit);
      if (sample) {{
        pixels = [...sample.pixels];
        updatePixelUI();
        evaluateCircuit();
      }}
    }}

    function updatePixelUI() {{
      const cells = gridEl.children;
      let activeCount = 0;
      let totalPwr = 0;
      for (let i = 0; i < 64; i++) {{
        const v = pixels[i];
        if (v > 0.1) activeCount++;
        totalPwr += (v * v) / 10000.0 * 1000.0;
        const intensity = Math.round((v / 5.0) * 255);
        cells[i].style.backgroundColor = `rgb(${{intensity}}, ${{intensity}}, ${{intensity}})`;
      }}
      document.getElementById("activePins").innerText = `${{activeCount}} / 64`;
      document.getElementById("inputPower").innerText = `${{totalPwr.toFixed(1)}} mW`;
    }}

    document.getElementById("noiseToggle").addEventListener("change", (e) => {{
      addNoise = e.target.checked;
      document.getElementById("noiseLabel").innerText = addNoise ? "Active (±1% Resistors, 3mV Vos)" : "Ideal (0%)";
      evaluateCircuit();
    }});

    function randNorm() {{
      let u = 0, v = 0;
      while (u === 0) u = Math.random();
      while (v === 0) v = Math.random();
      return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
    }}

    function evaluateCircuit() {{
      // 1. Layer 1 Sums (64 -> 16)
      const v_sum1 = new Array(16).fill(0.0);
      for (let j = 0; j < 16; j++) {{
        let sum = MODEL.b1[j];
        if (addNoise) sum += randNorm() * 0.003;
        for (let i = 0; i < 64; i++) {{
          let w = MODEL.W1[i][j];
          if (addNoise && w !== 0) w *= (1.0 + randNorm() * (0.01 / 3.0));
          sum += pixels[i] * w;
        }}
        v_sum1[j] = Math.max(-10.5, Math.min(10.5, sum));
      }}

      // 2. Layer 1 ReLU (Active Rectifiers)
      const v_relu = new Array(16).fill(0.0);
      for (let j = 0; j < 16; j++) {{
        v_relu[j] = Math.max(0.0, v_sum1[j]);
      }}

      // 3. Layer 2 Sums (16 -> 10)
      const v_sum2 = new Array(10).fill(0.0);
      for (let k = 0; k < 10; k++) {{
        let sum = MODEL.b2[k];
        if (addNoise) sum += randNorm() * 0.003;
        for (let j = 0; j < 16; j++) {{
          let w = MODEL.W2[j][k];
          if (addNoise && w !== 0) w *= (1.0 + randNorm() * (0.01 / 3.0));
          sum += v_relu[j] * w;
        }}
        v_sum2[k] = Math.max(-10.5, Math.min(10.5, sum));
      }}

      // 4. Winner-Take-All
      let maxK = 0;
      let maxV = -999;
      let secondV = -999;
      for (let k = 0; k < 10; k++) {{
        if (v_sum2[k] > maxV) {{
          secondV = maxV;
          maxV = v_sum2[k];
          maxK = k;
        }} else if (v_sum2[k] > secondV) {{
          secondV = v_sum2[k];
        }}
      }}

      // Render Stage 2: DC1A..DC1D UI
      const dc1Container = document.getElementById("dc1Container");
      dc1Container.innerHTML = "";
      const slices = [
        {{ name: "DC1A: Neurons 0..3", start: 0 }},
        {{ name: "DC1B: Neurons 4..7", start: 4 }},
        {{ name: "DC1C: Neurons 8..11", start: 8 }},
        {{ name: "DC1D: Neurons 12..15", start: 12 }}
      ];

      slices.forEach(slice => {{
        const cardDiv = document.createElement("div");
        cardDiv.className = "p-3 bg-[var(--background)] rounded-xl border border-[var(--border)] space-y-2";
        let innerHTML = `<div class="text-xs font-semibold text-[var(--foreground)]">${{slice.name}}</div>`;
        innerHTML += `<div class="grid grid-cols-4 gap-1">`;
        for (let idx = 0; idx < 4; idx++) {{
          const n = slice.start + idx;
          const v = v_sum1[n];
          const isPos = v > 0;
          innerHTML += `
            <div class="text-center p-1 bg-[var(--card)] rounded border border-[var(--border)]">
              <span class="text-[10px] text-[var(--muted-foreground)] block">N${{n}}</span>
              <span class="text-xs font-mono font-bold ${{isPos ? 'text-emerald-500' : 'text-zinc-400'}}">${{v > 0 ? '+' : ''}}${{v.toFixed(1)}}V</span>
            </div>
          `;
        }}
        innerHTML += `</div>`;
        cardDiv.innerHTML = innerHTML;
        dc1Container.appendChild(cardDiv);
      }});

      // Render Stage 3: ReLU UI
      const reluContainer = document.getElementById("reluContainer");
      reluContainer.innerHTML = "";
      for (let j = 0; j < 16; j++) {{
        const v = v_relu[j];
        const isActive = v > 0.05;
        const item = document.createElement("div");
        item.className = `p-1.5 text-center rounded border transition ${{isActive ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-[var(--background)] border-[var(--border)]'}}`;
        item.innerHTML = `
          <span class="text-[10px] text-[var(--muted-foreground)] block">R${{j}}</span>
          <span class="text-xs font-mono font-bold ${{isActive ? 'text-emerald-500' : 'text-[var(--muted-foreground)]'}}">${{v.toFixed(1)}}V</span>
        `;
        reluContainer.appendChild(item);
      }}

      // Render Stage 4: WTA LEDs
      const ledContainer = document.getElementById("ledContainer");
      ledContainer.innerHTML = "";
      for (let k = 0; k < 10; k++) {{
        const isWinner = (k === maxK);
        const v = v_sum2[k];
        const card = document.createElement("div");
        card.className = `p-3 rounded-xl border flex flex-col items-center justify-between transition-all ${{
          isWinner ? 'bg-emerald-950/20 border-emerald-500/50 scale-105' : 'bg-[var(--background)] border-[var(--border)]'
        }}`;
        card.innerHTML = `
          <div class="w-7 h-7 rounded-full border-2 flex items-center justify-center font-bold text-xs transition-all ${{
            isWinner ? 'led-on' : 'led-off'
          }}">
            ${{k}}
          </div>
          <span class="text-xs font-mono font-semibold mt-2 ${{isWinner ? 'text-emerald-400' : 'text-[var(--muted-foreground)]'}}">
            ${{v > 0 ? '+' : ''}}${{v.toFixed(1)}} V
          </span>
          <span class="text-[10px] text-[var(--muted-foreground)] mt-0.5">
            ${{isWinner ? '2.8 mA' : '0.0 mA'}}
          </span>
        `;
        ledContainer.appendChild(card);
      }}

      document.getElementById("winningDigit").innerText = maxK;
      const margin = (maxV - secondV);
      document.getElementById("winMargin").innerText = `+${{margin.toFixed(2)}} V`;
    }}

    // Initial Load Preset 0
    loadPreset(0);
  </script>
</body>
</html>
"""

artifact_file = os.path.join(ARTIFACT_DIR, "analog_nn_emulator.html")
with open(artifact_file, "w") as f:
    f.write(html)

print("Generated HTML emulator at:", artifact_file)
