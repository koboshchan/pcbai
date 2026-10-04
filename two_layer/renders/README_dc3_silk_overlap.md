# DC3 reference-size inspection preview

The top and cluster PNGs show all 163 references forced to 0.8 mm in a temporary copy of the current routed DC3. Gold represents exposed pads and white represents silk. Red boxes mark the 21 references for which the earlier silk-placement search found no accepted position. All 21 are on F.Silkscreen; no bottom view is needed.

The earlier rejected placement audit did not preserve candidate positions for those 21 references. These images therefore show them at their saved reference positions, enlarged to 0.8 mm, not at invented rejected positions and not as a completed placement solution. The inspection uses a flat export so component bodies do not hide the collisions. It is not a populated 3D render.

The temporary-copy DRC reports 20 silk-overlap and 12 silk-over-copper items. Those counts differ from the historical rejected-placement attempt and must not be presented as its results. Vertical labels in the R2_5, R2_7, R2_8 and R2_9 columns collide with neighboring labels or pads; R2_12_4 and R2_12_5 also touch nearby labels.

The temporary DRC additionally reported 76 copper-edge errors. Inspection of /tmp/dc3s/drc.json shows its newly created project applied a default 0.5000 mm copper-edge rule to the deliberately 0.4000 mm recessed straddle pads. The authoritative route generator sets min_copper_edge_clearance to 0.3 mm in the matched project. This temporary project-rule mismatch is not evidence of changed copper or a new routing regression. No CAD changes are authorized by this preview, and no fabrication signoff is implied.

The worker verified the routed source SHA256 was unchanged before and after rendering, abbreviated 7cf909e5...c03c33. Reference layers, heights and boxes are recorded in dc3_silk_overlap_audit.json. No smaller text, component movement, copper change, rerouting or fabrication export was performed.

Files are dc3_silk_overlap_top.png and dc3_silk_overlap_cluster.png.
