# Grayscale milestone previews (NOT routed, NOT fabrication-ready)

Rendered 2026-10-04 with remote kicad-cli 10.0.6 (`pcb render --width 1600 --height 1200 --quality basic --side top|bottom`) from snapshot copies in kat-box:/tmp/render_gray. Originals and live routing candidates untouched.

Model identity: commit 9c4091c, two_layer/fixed_model/circuit.json sha256 cef9d5bf6279044d949073792a5d3995ccf8cdafc47dba25630f1cbce9394dfe (grayscale 6-bit PWM; binary archive not used). Repo HEAD at render: 351a6c6.

Snapshot sources (sha256):
- daughtercard1b_weights_l1_differential_repaired_unrouted.kicad_pcb ded6a1c54e9cd7d1ebd508c2a3a12300cc949f2255aa58e23d9aa9e11fcf31c1
- daughtercard2_relu_l1_buffered_repaired_unrouted.kicad_pcb 36636f2b45d11333cc7da1707b726ed013bc67eb504cc10b8b9a3ea75fbef05b
- daughtercard3_weights_l2_wta_differential_repaired_unrouted.kicad_pcb bc081a5c71e1c610898f2a0a98594859485534ff0c0a91daa0c76108b0bc6dbc

Caveats (verified by inspecting the PNGs): unrouted (no copper tracks), footprints show bare pads only because 3D models are absent, bottom sides show only straddle-header pads and mounting holes, silkscreen reference text overlaps (e.g. D_CLAMP/D_RECT on DC2). The 0.4 mm pad-setback freerouting run may replace these boards. Motherboard not rendered yet (waiting for power_audit.json / regulator worker).
