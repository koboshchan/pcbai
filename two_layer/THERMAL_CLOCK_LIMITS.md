Conservative clock estimates for the vertical ST L7805CV. The glued coin is optional/recommended, not a required BOM item or routing gate. Its actual effective thermal resistance is unknown. These are engineering estimates, not guaranteed operating ratings. Bare-package calculations use 50C/W with local ambient, design junction 110C and absolute diagnostic 125C. Do not operate at the absolute diagnostic limit.

Python includes TTL37.5mA, filters35.368mA, minimum load6.739mA, ICC0.640mA, actual bias1.091mA and ground9.3mA. CPD190pF is typical, multiplied by1.5 as an engineering margin, not a guaranteed maximum. Dynamic current is 8*190pF*5.25V*f*1.5; serial current is 8*50pF*5.25V*f/2. Dissipation combines +15.75V and4.75V with those current bounds.

P(f)=1.041198W+1.4322e-07W/Hz*f. Estimate f_max=max(0,((110-Tambient)/thetaJA-P0)/P_slope). Measured assembled thetaJA=(Tjunction-Tambient)/P, with junction inferred from a qualified thermal method; a coin surface temperature alone is not junction temperature. Validate at worst supply, actual local ambient, mounting and airflow, with margin. Do not claim measured cooling from coin dimensions.

Bare50C/W continuous limits follow.
At 25C local ambient, design110C estimates 4.600MHz; absolute125C diagnostic 6.695MHz.
At 40C local ambient, design110C estimates 2.505MHz; absolute125C diagnostic 4.600MHz.
At 50C local ambient, design110C estimates 1.109MHz; absolute125C diagnostic 3.203MHz.

An initial conservative test ceiling is 1MHz continuous, bare-package estimate only, with junction/ambient monitoring. This is a thermal test recommendation, NOT an accuracy or unrestricted operation claim. At50C the1MHz CPD-margin estimate is 109.22C junction.

Assumed effective thetaJA values below50C/W in the JSON are diagnostic scenarios only, never claimed coin performance. Thermal overload protection is not a normal operating strategy.

Normal20MHz burst BCM uses6/63 clock duty for the previous4960.317Hz frame schedule and estimates1.230W without CPD margin. Lowering serial clock changes allowable frame scheduling and RC ripple; the previous20MHz accuracy simulation does not establish performance at1MHz. A fresh full PWM/RC coupled-network accuracy simulation is required before accepting lower-clock operation. No changes to trained resistors, filters, reference nets or daughtercards are authorized by this report.

Cooling is not a mechanical routing blocker. Thermal qualification, repaired schematic, signal integrity, part availability and strict final PCB audits remain fabrication-release gates.
