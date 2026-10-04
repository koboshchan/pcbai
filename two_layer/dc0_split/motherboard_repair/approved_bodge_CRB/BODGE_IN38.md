# Required manual IN_38 assembly bodge

Lucas explicitly approved this insulated bottom-side wire on October 4, 2026. The accepted motherboard gate is zero DRC violations of error severity and exactly one raw unconnected item on IN_38. The raw report remains unchanged and visible. This is not a fabricated PCB connection, DRC exclusion, fake trace, or rule relaxation. The bare PCB requires the manual assembly operation below before use.

Solder insulated wire between JS1 B7 at board coordinates (18.25, 44.27) mm and JS2 B7 at (18.25, 55.27) mm. Both plated through-hole pads belong to IN_38. Center-to-center distance is 11.00 mm; begin with approximately 14 mm wire including slack, then fit without tension. Route the wire on the bottom side. Keep the entire middle insulated and strip only the soldered ends. Avoid adjacent pads, exposed copper, and mechanical interference. Verify continuity between the two B7 pads and absence of shorts to neighboring pads before applying power.

The raw F.Cu open is between track endpoints (17.0509, 45.4691) mm and (18.25, 56.07) mm, approximately 10.669 mm apart. The approved wire connects the through-hole pads, not these stubs. No ordinary 0805 part spans that distance.

Reference-only annotated images are /home/kit/renders/in38_jumper/in38_jumper_top.png and /home/kit/renders/in38_jumper/in38_jumper_bottom.png, with meta.json. They predate the CRB footprint change and are not final populated renders.

CRB alone changes to standard Capacitor_SMD:C_0805_2012Metric, 10uF 25V X7R nonpolar ceramic. Exact compatible sourcing remains pending. Shared/global BOM promotion and fabrication release are not authorized by this candidate.
