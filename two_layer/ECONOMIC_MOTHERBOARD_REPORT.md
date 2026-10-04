# Economic motherboard revision

Unrouted placement SHA256 97d6a6da4fdec36a46d509b74ea1dd32ca2d020ad9ea75884412242826e7301e.

All eight U_SR1..8 Diodes 74AHCT595S16-13 C126402 are flipped to bottom at unchanged XY coordinates. Only C_RAIL_N moves from (84,25) to (84,28) mm to resolve a real pad short beneath U_SR5. C_REG_IN saved metadata is Samsung CL21B105KBFNNNE C28323, 1uF 50V X7R 0805. No obsolete generator was executed.

All footprint identities and pad-number/net mappings are preserved. Non-AHCT placements were checked unchanged before the one documented capacitor movement. THT slots, vertical regulator, outboard cooling exclusion, outline, and root originals are unchanged. Backup is backups/economic_motherboard_before_bottom/motherboard_adc_repaired_unrouted.kicad_pcb.

Bottom JLC assembly has 145 SMD footprints. Top manual soldering has 68 SMD footprints. Exact reference/value/library footprint lists are in economic_motherboard_placement.json. Top manual parts are C_SR1..8 (0.1uF,0805), R_TOP_0..9 (220k,0805), R_BOT_0..9 and R_REF_0..9 (22k,0805), R_ADC_0..9 (1k,0805), and D_HI_0..9/D_LO_0..9 (1N4148W,SOD123). Exclude these top parts and all THT/mechanical parts from JLC BOM/CPL. Classification uses actual pad attributes because old cloned resistors lack correct footprint SMD flags.

Placement strict DRC has 0 errors, 499 unrouted connections, and 68 footprint-library warnings. All 228 reference fields have at least 0.8mm height and 0.12mm stroke, are visible on their component side, and pass conservative text/pad/edge/reference bounding-box audit. No silk graphics or other visible fields remain. Dense PWM labels needed wider displacement, up to approximately 24.2mm; populated render review of label-to-component association is still required. No claim of intuitive association is made solely from nonoverlap DRC.

Bounded four-pass remote FreeRouting started with Python30918/Java30951. economic_motherboard_route.py preserves the audited silkscreen rather than rerunning the inadequate local-only placement search. Final routing/strict DRC, routed pad invariants, clock/signal/thermal validation, and renders remain pending. No fabrication release or purchasing is authorized.
