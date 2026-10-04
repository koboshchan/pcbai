# ACTIVE, repaired electrical design approved

## Final fabrication quote handoff requirement

Once ALL seven boards have final verified Gerbers, record one row per board here with measured outline dimensions in mm, exactly 2 copper layers, minimum trace width and minimum copper clearance in mm, minimum finished drill in mm, physical hole count split into PTH/NPTH where available, and final Gerber+drill ZIP path. Distinguish configured design-rule minima from measured geometry; do not invent measurements. Count a through-hole once, not once per copper layer. Flag slots separately if present. Until verified export, dimensions/drill/hole counts and ZIP paths remain pending, not quoted as final.

Quote defaults for both JLCPCB and PCBWay are 1.6 mm FR4, 1 oz copper, HASL finish and green solder mask. Do not change these without recording a concrete design reason. Standard production only, no urgent/expedited build options. Quotes shipped to Vancouver, BC, Canada must include economical reasonably timely shipping and available taxes/duties, explicitly identifying any unquoted import charges. Quote board-only and SMD-only assembly; if IC pricing is high, also quote assembly excluding ICs. Quote only, do not order.

Latest definitive instruction supersedes every HOLD and unchanged-netlist note. There are no newer files. The repo-root 76-pin straddle-header boards ARE current; only the README is old. Deliverable must FIX signed weights with physical TL074 inversion stages and ADC offset attenuation plus 1k series and stock 1N4148W SOD123 clamps to 3.3V/GND. Rewrite emulator from actual resistor/pad nets, retrain/requantize as needed, report actual nominal and 5% MC accuracy, fresh-route all repaired boards on kat-box with parallel FreeRouting, reference-only silk, strict truthful DRC and gated Gerbers. Commit and push milestones. Root PCB originals remain untouched; repaired outputs live in two_layer. Interrupted unchanged-netlist first-run files are provenance/feasibility only, not deliverables. No repaired PCB or final DRC yet.

Milestone progress is 1-2 sentences; detailed work notes live here. Training/model worker d7a92737 owns fixed_model; silkscreen worker46b9b12c owns silk_* (older56cc1103 stopped to prevent duplicate edits). Consider minimal signed two-summer topology with one group inverting amplifier feeding final inverting summer, two amplifiers per neuron and no additional backplane input nets. L1 final SUM must be negative desired preactivation for the inverting ReLU; L2 final SCORE must be positive desired score. New physical manifests are required before routing; no sign metadata tricks.

Resource plan kat-box52GB32threadsGPU; 6-8 concurrent routing jobs with measured memory budget, reserve4GB including native overhead, do not combine48GB Java heaps with peak training. Old unchanged jobs terminated. Their ReLU SES was zero bytes and import failed, so even trial routing was not a validated success.

ADC NETLIST MILESTONE ACTUAL: remote KiCad10 successfully generated and reloaded motherboard_adc_repaired_unrouted.kicad_pcb. New10channels220kSCORE/22k3.3V/22kGNDoffsetdividers,1kADCseries,20stock1N4148WSOD123high/lowclamps, dedicatedJ_ADC_REF3.3V/GND, MCUheadernowADC_0..9. Existingrootuntouched. adc_netlist_manifest.json recordsrealnets. Remotecorneraudit adc_corner_audit.json passed poweredinterval0.666627..2.476603V acrossscore±15V,resistors5%,3.3Vreference5%; lowestupperreferenceheadroom0.823005V. Nominalscore±15maps0.857143..2.285714V. Conservativezero-dropMCUoffinjectionbound66.0384uAperchannel660.384uAtotal10. SiliconclampsarenotabsoluteMCUvoltageguaranteeorbackfeedprevention. PowerMCU/referencefirstanaloglast;switchanalogofffirst. ADCacquisitiontimingtargetMCUunknownneedsfirmwareconfig. Layoutisprovisionalunrouted,courtyardsnotyetformed,newfootprintsneedlibrary/rendervalidation. NoDRCsuccessorGerbersclaimed.

GPUverifiednvidia-smiNVIDIAGeForceRTX4070SUPER12282MiB. SystemPythonhastorchmissing; modelworkerownsCUDAvenvinstallationandverification. Trainingmustusetorchcuda;MCbatchphysical5%resistorsetsGPU, notCPU-matrixgaussianfiction.

Signed prototype milestone (not final netlist complete): remote generated+reloaded four DC1 cards and DC3 with local physical group inverters. Independent audit_signed_prototype.py verifies all1184 synapses actual pad-nets and groupamp output/minus/plus nets, no unused TL074 outputs tiedGND. Added7TL074/14raildecouplingcaps/52groupresistors; L1biasrails corrected. See repair_signed.py, five*_signed_prototype_unrouted.kicad_pcb and signed_prototype_audit.json, commit1b62432. Existingjsonweights only exercise topology; intermediate saturation/loading/accuracy and placement not validated. DO NOT ROUTE OR FABRICATE prototypes. Model worker generated differential/binary circuit.json; parent coordination requested to choose one shared physical topology before final CAD/model accuracy. Both differential and two-summer are authorized options. Prototype inverter path is NOT a user-mandated exclusive topology. Coordination file explains both and rectifier load differences; no final accuracy yet.

MilestoneADCtop/bottomrenders remoteCLI1600px now synced two_layer/renders/adc_milestone_top.png and adc_milestone_bottom.png, commit5fceb72. Previewonlyunrouted, models missing oldMacpaths, not fullypopulated. Visualinspection revealsdenseprovisionalADCplacementsinterleavingexistinglogic; needslayoutreworknotfabrication.

Newroute_repaired.py remotecompiledandADCpreparetested DSN successfully, noJavajoblaunched. It takes explicit repaired candidates and freezes repaired electrical identity instead of wrongly enforcing original nets. Preservesoriginalbyteprovenance, router/silk/save-loadassertelectrical identity, checkslayers/trace/via, runstrictDRC, releasefalseunlessseparatefullarchitecture/mechanicalgates. Final trained manifested candidate required, unrelatedoldconvert.pyno longerdeliverableworkflow.


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
