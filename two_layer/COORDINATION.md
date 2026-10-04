# Active coordination

User explicitly requests all KiCad DRC, FreeRouting, preparation and exports on kat-box, not locally. KiCad 10.0.6 is installed and verified there. The 76-pin straddle-header boards ARE current, README old. Signed-weight inverter and bipolar ADC repairs ARE explicitly approved and required. Original PCB bytes remain untouched; deliberate repaired netlist differences must be validated against a new manifest. Old unchanged-netlist routes are stopped feasibility/provenance only. Authoritative STATUS.md and ENGINEERING_COORDINATION.md document repairs. Root originals copied to /work/pcbai; remote outputs /work/pcbai/two_layer. Local /home/kit/pcbai/two_layer is synchronization and git commit destination. Forge owns conversion/routing. Generic audit owns audit_*; generic silk owns silk_* and must not edit boards concurrently. New scripts should be copied to kat-box and executed there.

Local KiCad10 installed before user relocation instruction. In 10.0.6 GetDesignSettings() returns unwrapped SwigPyObject, so edit JSON .kicad_pro instead; SetCopperLayerCount, footprint net APIs and ExportSpecctraDSN available.

Silkscreen references required on component side, no decorative titles/slogans/logos. Ref property must be visible. KiCad CLI full checks including silhouette/layout silk audit required before export.

Actual root boards are all KiCad10, 4 layers and 76-pin straddle headers. README is stale, preserve actual pins. Baseline original DC2 full CLI yielded zero electrical errors, zero unconnected, 164 warnings (82 silk-over-copper, 79 missing custom footprint lib, 3 silk-edge). File under baseline_dc2_drc.json.

Status work incomplete and no fabrication zip authorized until 0 errors 0 unconnected. Avoid claiming a 2layer conversion after simply collapsing copper, that produces shorts.
