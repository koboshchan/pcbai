# Economic motherboard revision

Unrouted placement SHA256 9f5510139d42ebc33c149f6d501c4caa0f98b091a723ec1e8a2e5959cfb14a77.

All eight U_SR1..8 Diodes 74AHCT595S16-13 C126402 remain bottom at unchanged XY. C_RAIL_N remains at (84,28) mm. C_REG_IN remains Samsung CL21B105KBFNNNE C28323, 1uF 50V X7R 0805. No old generator was executed.

Lucas approved moving C_SR1..8 100nF 0805 to bottom beside their corresponding AHCT VCC pin16. Only these eight footprint placements changed from the previous approved bottom-AHCT placement. Exact pad-number/net/library identity, all values, all other footprint placements/orientations, THT slots, regulator/cooling area and root originals were checked unchanged. Source backups and corresponding reports are in backups/economic_motherboard_before_caps_bottom. The helper is economic_motherboard_caps.py and uses that immutable backup, not an old generator.

The local search prioritizes distance to VCC while minimizing the sum of the two supply-pad connections, avoiding copper pads, AHCT body, board edge and existing labels. C_SR1..5,7,8 cap pad1 to AHCT pin16 straight-line centre distance is 1.775528mm and cap pad2 to pin8 distance is 9.791762mm. C_SR6 distances are 1.884808mm and 10.500410mm, respectively, due to existing label clearance. Pin16 and pin8 are at opposite package corners; these are geometric distances, not routed lengths or proof of low-impedance bypass performance. The search is a discrete local optimum, not a global placement optimum. Routed bypass/ground-loop quality remains a review gate.

Bottom JLC assembly now has 153 SMD footprints. Top manual soldering has exactly 60 SMD footprints, R_TOP_0..9 (220k,0805), R_BOT_0..9 and R_REF_0..9 (22k,0805), R_ADC_0..9 (1k,0805), and D_HI_0..9/D_LO_0..9 (1N4148W,SOD123). Exact reference/value/footprint lists are in economic_motherboard_placement.json. Exclude top manual parts and all THT/mechanical parts from JLC BOM/CPL. Classification uses actual pad attributes, not inaccurate old footprint flags.

Placement strict DRC has 0 errors, 499 unrouted connections and 68 footprint-library warnings. All 228 reference fields have minimum 0.8mm height and 0.12mm stroke and pass the fresh conservative component-side text/pad/edge/reference bounding-box audit. Only the eight capacitor reference positions changed. Existing PWM labels retain their previous clean positions but displacement up to approximately 24.2mm means populated visual association review is still required. No readability/association claim follows merely from nonoverlap.

Fresh bounded four-pass FreeRouting is running remotely with Python31446 and Java31479 using this revised placement. Stale SES was removed from the active path before starting. Final routing/strict DRC, routed identity, bypass-loop/clock/signal/thermal validation and renders remain pending. No fabrication release is authorized.
