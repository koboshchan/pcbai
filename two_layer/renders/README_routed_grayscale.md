# Routed DC1a / DC1c renders (oct 4 00:19)
kicad-cli pcb render (KiCad 10, kat-box), 1600 wide, quality basic, top and bottom, rendered from temp copies. Boards were not modified. No 3D models (bare pads).

DC1a sha256 6e323464d18a3aff45fdee8f4e5bec97e7aa1ea549548e81b335c90a20865679 (00:17:54). Status file: 0 errors, 0 unconnected, 202 warnings (197 lib_footprint, 4 silk_over_copper, 1 silk_overlap)
DC1c sha256 12fb3ca999ef644e76bb675cb3a9c21ee04d3adb3a504fd70cf232e2f0164375 (00:17:50). Status file: 0 errors, 0 unconnected, 192 warnings

NOT A FABRICATION RELEASE. These are NOT verified grayscale: final_model_routed_audit.json (00:18:46) matches these hashes but reports "76pin straddle pinmap changed" and model_pad_agreement=false on both boards. grayscale_route_run.json was not found on the remote.
