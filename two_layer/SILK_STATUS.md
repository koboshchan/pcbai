# Reference silk pass (oct 4)

Generators: repair_differential.py / repair_relu.py now hide the capacitor "Voltage Rating" field (metadata only, not a reference). silk_refs.py hides every non-reference footprint field and audits for any visible one.

DC1a, DC1b, DC1c, DC1d, DC2: silk applied, all refs visible on the correct side, 0 unplaced, strict CLI DRC 0 errors, 0 unconnected, 0 silk_over_copper, 0 silk_overlap (only lib_footprint_issues warnings, intentional custom geometry). Tracks, pads, nets, footprint positions identical before/after. Promoted.

DC3 (weights_l2_wta): NOT promoted, board unchanged. 21 refs cannot be placed at >=0.8 mm without overlap: R2_12_4 R2_12_5 R2_5_4..7 R2_7_3 R2_7_4 R2_7_6 R2_8_2..4 R2_8_6 R2_8_7 R2_9_2..8. Candidate gave 30 silk_overlap warnings. See daughtercard3_*_silk_FAILED*.json. Needs a placement or text-size decision.

audit_final_model.py --routed rerun after the change: all_neural_pad_maps_match true, root originals unchanged. Not fab ready. No Gerbers/quotes.
