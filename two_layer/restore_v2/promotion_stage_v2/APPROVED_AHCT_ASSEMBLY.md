# Current restored hybrid assembly supersedes all historical notes below

Motherboard JLC Economic assembles bottom SMD only. U1 through U8 are Diodes 74AHCT595S16-13 C126402 on top, manually purchased and soldered by Lucas, excluded from JLC BOM/CPL. Every top SMD and every THT part is manual. CRI is 1uF C28323 on bottom. Reference names are reversible by UUID in old_to_new_refs.json. The following earlier SMT-assembly sourcing report is historical only and does not determine current assembly classification.

# Approved Diodes AHCT assembly sourcing

Lucas approved Diodes 74AHCT595S16-13 C126402 for all eight U1–U8 on 2026-10-04. These eight are JLC Extended SMT assembled, not manual/DNP. This supersedes only the old Nexperia C554704 sourcing fallback. Owned plain HC595 parts are not used. Other through-hole parts, daughtercard straddle headers and heatsink remain manual and excluded from SMT assembly.

Exact manufacturer pinout and package comparison is documented in AHCT_STOCK_REVIEW.md: SO-16 3.8–4.0mm body width,9.8–10.0mm length,1.27mm pitch; pins1..16 Q1,Q2,Q3,Q4,Q5,Q6,Q7,GND,Q7S,MR,SHCP,STCP,OE,DS,Q0,VCC. Existing SOIC-16_3.9x9.9mm_P1.27mm unchanged. Fresh exact LCSC/JLC pages were opened; observed410 LCSC /413 JLC /405 JLC orderable, enough8, not a reservation or final quote. Sources are in approved_ahct_sourcing.json and the prior research report.

## What changed and what did not

power_BOM_preliminary.csv, approved_ahct_sourcing.json and the two motherboard generators now identify the approved MPN and sourcing. Generators were edited but NOT EXECUTED. export_sourcing_inventory.py read seven current remote boards and verified SHA256 before/after identical, writing purchasing overlays only. Its manifest covers1249 footprint items including14 mounting holes,1218 SMT items and17 manual parts. All eight registers are included as SMT. Full provisional BOM columns are exactly Comment,Designator,Footprint,LCSC Part #, mechanical holes excluded. Blank LCSC codes deliberately expose unresolved sourcing, not a ready-to-upload assembly claim.

No local or remote PCB geometry, pads, nets, routing, schematic, model circuit.json/trained_circuit.json, weights or historical numerical results were modified. Therefore no changed model SHA or newly simulated Diodes accuracy claim exists. Nexperia-based historical electrical characterization remains historical; package/pinout equivalence alone does not newly qualify Diodes output impedance/VOH under every load.

## Router owner handoff

Motherboard router PIDs22591/22626 were active when work began. Saved board field updates and final CPL are intentionally deferred. apply_approved_ahct_fields.py takes input and DISTINCT output paths and changes only approved quoted values/descriptions/catalog strings; normalizing those replacements must reproduce every original byte. Run only after the router owner finalizes output. Review DNP/BOM flags and apply approved all-eight SMT inclusion, then rerun current model/desired-net audits, DRC, and export final SMD-only CPL from that routed board. Required CPL columns Designator,Mid X,Mid Y,Rotation,Layer with coordinates in mm. No CPL was generated from the stale unrouted motherboard. No Gerbers/fabrication release/order occurred.

## Whole BOM qualification status

sourcing_inventory_provisional.json enumerates every current part, not obsolete root consolidated BOM values. Apart from the eight approved AHCT devices and manual L7805 metadata,1226 nonmechanical footprints had no unambiguous catalog code. Their exact-stock status remains unverified; blank code is not proof of out-of-stock. CURRENT_BOM_STOCK_REVIEW.md is a separately owned in-progress exact-catalog review. Effective capacitance qualification is still required for PWM1uF50V and regulator0.33uF50V at bias. PCBWay part sourcing remains quote-dependent, not catalog-verified. This sourcing change lifts only the AHCT sourcing hold, not remaining qualification/fabrication gates.
