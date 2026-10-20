PCBAI resistance probe

A static, per-board nominal DC resistance calculator. Click two pads, vias or tracks, or select exact reference/pin pairs from the probe menus. The back view is horizontally mirrored, as if the board were physically turned over. Scroll to zoom and drag empty board space to pan.

Run from the repository root with Python 3, sexpdata 1.0.2 and Node 18 or newer.

```sh
python3 -m pip install sexpdata==1.0.2
python3 ohm-app/build.py
python3 ohm-app/test_build.py
node ohm-app/test.js
python3 -m http.server 8765 --bind 127.0.0.1 --directory ohm-app
```

Open http://localhost:8765. No server-side calculation, account or API keys are needed. Production hosting should serve only ohm-app, not the repository or .git directory. The quick-tunnel preview is publicly accessible to anyone with its URL, including the derived board connectivity.

Data comes from all six boards/*.kicad_pcb sources. DC1 A/B/C/D use the universal physical layout and the matching DC1 population CSV, keyed by Reference. The universal board has unspecified POPULATION resistor values and is intentionally an open, unpopulated layout. Generated JSON records source SHA-256 values; regenerate after changing PCB files or population tables.

The solver contracts zero-ohm resistors, finds the reachable component and solves its grounded conductance Laplacian with partial-pivot Gaussian elimination. Same-net probes read zero; disconnected probes read open. The current list ranks resistor branches by current under a 1 A test, rather than pretending a parallel network has one series path.

Only fitted resistors are modeled. DNP and blank values are omitted. Capacitors, ICs, op-amps and diodes are open. Connectors join pads only by their existing net name, never across pins. Copper is ideal; no external stack, bodge wire, powered supply impedance or semiconductor protection paths are included. This is a nominal steady-state resistor prediction, not an exact simulation of a real meter or a way to determine whether a joint is soldered.

Regression checks cover series, parallel, disconnected, same-net and zero-ohm networks, DC1 population counts, DC3 U1 pins 6–7 at 100 kΩ through RF1, and the motherboard divider including shared-rail parallel paths. SCORE_DIV_6 to GND is 12.1 kΩ, not 22 kΩ, because RR6 reaches the other nine dividers through the common ADC supply rail.

Keep the board unpowered when using a physical meter. A measured difference can come from tolerances, charging capacitors, semiconductor paths, external connections or solder faults.

