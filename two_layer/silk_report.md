Remote KiCad 10.0.6 silkscreen helper regression, October 3, 2026.

All CAD tests ran on kat-box against disposable /tmp/silk_test copies of /work/pcbai originals. No source PCB, routing candidate, footprint position, pad, track, zone, copper layer count, net assignment or non-silk board drawing was modified. Electrical/placement snapshots were identical before placement, after placement, and after saving/reloading each test board.

The DC2 ReLU board passes with 79 visible component-side references and no unplaced references. DC1a weights passes with 270 references and no unplaced references. Both audits remain clean after serialization.

The motherboard does not pass. All 50 references remain visible, but R_TOP_2 through R_TOP_7 could not be packed within the local placement search without pad/text collisions. These six remain visible at their original anchors and are explicitly listed as unplaced. Its clean and release_ready flags are false before and after serialization. This is a real blocker, not permission to omit the labels. Any redesigned motherboard must be audited independently.

The helper uses GetDrawings where its typemap is available and falls back to the iterable Drawings wrapper on builds that expose a non-iterable SWIG result. Item removal exclusively uses Delete. Decorations on both board and footprint silk layers are removed, values hidden, references visible on their component side with backside mirroring. The audit now explicitly rejects remaining decorative artwork and wrong mirroring. Command-line release_ready includes the saved/reloaded audit rather than trusting the in-memory result alone.

Reference text is at least 0.8 mm high with 0.12 mm stroke. Pad, text and edge gaps are conservatively evaluated with axis-aligned bounding boxes at 0.20, 0.15 and 0.25 mm respectively. Candidate anchors search cardinal placements then a radius-6-mm grid around each part. This is not rendered-glyph inspection, solder-mask opening geometry, or full fabrication DRC. Passing this helper alone never establishes board release readiness.

Regression code is silk_test.py. Detailed test reports and disposable boards remain under /tmp/silk_test on kat-box. Compact result data is silk_results.json. All final routing/sign-fix/ADC-fix candidates still require fresh silk placement and roundtrip audits.
