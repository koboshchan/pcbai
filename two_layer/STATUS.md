# Two-layer MNIST conversion

Work in progress. NOT fabrication-ready. Original boards in the repository root are untouched.

The repository README is stale. All seven actual PCB files declare KiCad 10 format (20260206). The ReLU board also declares four copper layers, contrary to the README. Baseline DRC and copper inventory are pending a KiCad 10 reader. Local KiCad 9 rejects these files; do not silently downgrade their file-format headers.

| Board | Copper layers target | DRC errors | Unconnected | Production ZIP |
|---|---|---|---|---|
| Motherboard | 2 | Not run | Not run | withheld |
| DC1A | 2 | Not run | Not run | withheld |
| DC1B | 2 | Not run | Not run | withheld |
| DC1C | 2 | Not run | Not run | withheld |
| DC1D | 2 | Not run | Not run | withheld |
| DC2 | 2 | Not run | Not run | withheld |
| DC3 | 2 | Not run | Not run | withheld |

Routing constraints: only F.Cu and B.Cu, trace width >=0.2 mm (prefer 0.25 mm), clearance >=0.2 mm, plated vias >=0.6 mm diameter / 0.3 mm drill, board outline <=100 x 100 mm. Preserve every footprint reference, value and pad net unless explicitly documented. Refill B.Cu ground after routing and rerun authoritative CLI DRC. Generate Gerber/drill archives only for zero-error, zero-unconnected boards. Check all copper layers independently, including pad layer masks and vias.

Router compute is available on Lucas's kat-box via SSH port 2222. Use isolated /work/two_layer jobs. Pin-level netlist audit is delegated independently. Resistor/network electrical netlists must be identical before an unchanged nominal accuracy claim is made.

Sources checked: https://www.kicad.org/download/details/ubuntu and https://jlcpcb.com/capabilities/pcb-capabilities . Our geometric constraints are deliberately more conservative than advertised minima.
