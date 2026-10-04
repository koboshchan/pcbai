# Routed DC1a / DC1c renders (oct 4 00:19)
kicad-cli pcb render (KiCad 10, kat-box), 1600 wide, quality basic, top and bottom, rendered from temp copies. Boards were not modified. No 3D models (bare pads).

DC1a sha256 6e323464d18a3aff45fdee8f4e5bec97e7aa1ea549548e81b335c90a20865679 (00:17:54). Status file: 0 errors, 0 unconnected, 202 warnings (197 lib_footprint, 4 silk_over_copper, 1 silk_overlap)
DC1c sha256 12fb3ca999ef644e76bb675cb3a9c21ee04d3adb3a504fd70cf232e2f0164375 (00:17:50). Status file: 0 errors, 0 unconnected, 192 warnings

NOT A FABRICATION RELEASE. Grayscale resistor/amplifier pad agreement is verified by corrected final_model_routed_audit.json from d07b1a4, and its board hashes match these renders. The initial audit incorrectly treated the authorized +12V/-12V to +15V/-15V rail rename as a connector-map change; that test was corrected and both boards pass. Fresh grayscale_routes_04.log records completed routing pipelines. Mechanical contact reach, remaining warnings, motherboard power and full release gates remain pending.

Update (silk pass): DC1a/DC1c PNGs re-rendered from the silk-updated boards (same CLI, 1600 wide, bare pads). Capacitor "Voltage Rating" field now hidden; only reference designators are visible. Track/pad/net geometry verified identical to the pre-silk boards (frozen copy frozen_presilk_1791098480 on kat-box).
