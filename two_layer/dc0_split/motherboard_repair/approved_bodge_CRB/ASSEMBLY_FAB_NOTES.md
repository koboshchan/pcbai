# Candidate assembly and fabrication notes

This isolated candidate is not globally promoted or fabrication-released. Motherboard raw DRC is zero errors in violations and one unconnected item on IN_38, both before and after CRB. That single net is Lucas's approved manual bodge exception; it must not be mistaken for a complete copper-routed connection. The accepted assembly needs the mandatory bottom insulated JS1 B7 to JS2 B7 wire described in BODGE_IN38.md. Confirm continuity and adjacent-pad isolation before power.

CRB is a nonpolar 10uF 25V X7R ceramic in standard Capacitor_SMD:C_0805_2012Metric. Center remains (83,94) mm and angle remains 180 degrees on B.Cu. Pad 1 remains +5V and pad 2 remains GND. Exact sourcing is pending, and the old electrolytic supplier code is not valid for this ceramic. No polarity orientation is required for the ceramic.

POST_CRB_AUDIT.json and raw post_crb_drc.json/log document the actual board gate. FROZEN_NON_CRB_AUDIT.json proves complete serialized footprint preservation for all 84 non-CRB footprints and preservation of every existing track/via. One local +5V track of 0.25 mm was added for CRB; no global routing or other unlock occurred. Project/rules remain byte-identical. No DRC exclusion was added.

DC0_verified.kicad_pcb is an isolated refilled and reloaded strict 0-error/0-open check copy of immutable DC0_routed.kicad_pcb. Its SHA remains 1196b0d47c1c553b22a4061d3ac7e1c41cbf3d4a35dd5b7f1d4cda102bfdb34a. Its documented scoped straddle-pad exception is retained in DC0_verified.kicad_dru. Motherboard has no new pad exception.

Raw DRC also contains footprint-library warnings, which are disclosed and not counted as errors. No claim of zero warnings is made. Protected original sources, historical joint1, daughters and clearance checker remain unchanged, as recorded in protected_before.json and protected_after.json.

Populate final top/bottom renders from post_crb.kicad_pcb and DC0_verified.kicad_pcb only. Rendering must not change those hashes. No order or fabrication release is authorized.
