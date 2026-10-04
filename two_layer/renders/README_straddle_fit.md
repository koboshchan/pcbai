# Straddle header render fix (DC1a, DC1c)

Render-only. Saved boards unchanged (sha256 in straddle_fit_audit.json). Old root model 3dmodels/pin_header_2x38_straddle.wrl left alone; the new one is model_assets/pin_header_2x38_straddle_corrected.wrl.

Measured footprint: 38 pads on F.Cu and 38 on B.Cu, 2.54 mm pitch, x from -46.99 to +46.99 (local), F and B aligned, pads 1.5 x 4.1 mm starting 0.4 mm in from the edge. The model puts one gold 0.64 mm square pin on every pad centre, both faces, with the black bar just outside the edge.

Fit: a standard 2-row header has 2.54 mm row spacing and 0.64 mm pins (Samtec TSW, GCT BG040, FCI BergStik), so the gap between rows is 1.905 mm. The board is 1.6 mm, about 1.67 mm with copper. Centred, that leaves about 0.12 mm of air between each pin row and its pads. **The pins won't touch the pads on their own.** You'd need to squeeze the rows in a bit, clamp them, or fill the gap with solder. The model shows that gap; row spacing was not shrunk to fake a flush fit. Exact SKU unknown, so this is nominal, not qualified.

Pins overlap about 2.6 mm of the 4.1 mm pads (assumes a generic ~3 mm tail).

Files: routed_grayscale_DC1{a,c}_{top,bottom}_straddle_corrected.png, routed_grayscale_DC1{a,c}_straddle_edge_closeup.png, straddle_fit_cross_section.png.
