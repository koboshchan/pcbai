# RESUMED, unchanged electrical design

Lucas corrected the temporary source-revision hold. The repo-root 76-pin straddle-header boards ARE current; only the README is old. Two-layer conversion resumes on kat-box with original values and pad nets preserved. ADC divider safety and negative-weight sign issues remain documented separately and must NOT be changed without approval. Interrupted first-run files remain checkpointed under paused_old_straddle_trial/ for provenance only, not deliverables. No converted board has final DRC yet. Originals remain untouched.

# Two-layer MNIST conversion

Work in progress. NOT fabrication-ready. Original boards in the repository root are untouched.

The repository README is stale. All seven actual PCB files use KiCad 10 and FOUR copper layers, including DC2. Actual connectors are 76-pin straddle headers, not 72-pin card-edge sockets. KiCad 10.0.6 was installed locally before Lucas requested kat-box; all further preparation, routing, DRC and exports run on kat-box in /work/pcbai. Local copies are synchronized for commits.

Baseline original DC2 full CLI DRC has zero electrical errors, zero unconnected and 164 warnings. This does not establish circuit correctness.

CRITICAL original electrical defects found by independent audit: actual ADC divider is 10k top / 20k bottom, resulting in +7V at the nominal +10.5V score and negative ADC voltages for negative scores. No physical clamp was identified. The emulator clips these voltages in software. Negative trained weights (563 L1 and 83 L2) are connected to the same positive input nets as positive weights, with no corresponding sign-inversion circuitry identified. Footprint Description fields lack the polarity metadata expected by the emulator, which defaults signs positive; its L2 sign also disagrees with physical inverting summers. Preserve the original netlist during this conversion but do not label the hardware electrically safe or the original claimed 92.15% accuracy reproduced. The benchmark MNIST cache is absent; original --benchmark cannot execute. See audit_emulator_findings.json and audit_original_manifest.json. Production release requires these architecture/safety issues resolved separately, even after DRC zero/zero.

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
