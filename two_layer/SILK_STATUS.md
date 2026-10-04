# Reference silk pass (oct 4)

Generators: repair_differential.py / repair_relu.py now hide the capacitor "Voltage Rating" field (metadata only, not a reference). silk_refs.py hides every non-reference footprint field and audits for any visible one.

DC1a, DC1b, DC1c, DC1d, DC2: silk applied, all refs visible on the correct side, 0 unplaced, strict CLI DRC 0 errors, 0 unconnected, 0 silk_over_copper, 0 silk_overlap (only lib_footprint_issues warnings, intentional custom geometry). Tracks, pads, nets, footprint positions identical before/after. Promoted.

DC3 (weights_l2_wta): promoted in f0e5af2 after the approved placement/reroute. Exactly 30 weight parts in columns 7/8/9 moved into the free right strip, retaining all 163 references at >=0.8 mm. Strict final CLI DRC: 0 errors, 0 unconnected, 0 silk_overlap, 0 silk_over_copper; 163 library warnings remain. Independent geometry audit preserves pad geometry/nets/values, header and outline. Fresh routed model and desired-manifest audits pass. Board SHA256 fc5b97c1068092910be16ea4e342ae0c0c8524affe952ab55fb664f5fcde4a1e. See DC3_SPACING_REPORT.md. Earlier *_silk_FAILED*.json are superseded trial provenance, not the current gate.

audit_final_model.py --routed rerun after the change: all_neural_pad_maps_match true, root originals unchanged. Not fab ready. No Gerbers/quotes.
