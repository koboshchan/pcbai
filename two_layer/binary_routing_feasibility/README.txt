These four routed binary-model trials are engineering feasibility snapshots only.
They are NOT final grayscale boards and must NOT be fabricated.

DC1a and DC1c have strict zero DRC errors and zero unconnected items.
DC1b and DC1d each have three copper-edge routing errors, zero unconnected items.
Library-footprint warnings remain. No Gerbers or assembly files are released.

Model source was binary trained_circuit.json before approved PWM+RC grayscale
retraining. Final grayscale training and source10050ohm coupled input loading
will change resistor values and connections, requiring regenerated CAD/routers.
Straddle solder-pad tips recessed0.5mm preserve connectorposition and pinpitch;
actual purchased header pinreach still needs mechanical qualification.
