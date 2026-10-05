pcbai is an analog MNIST classifier built from discrete PCB neural-network boards.

boards/ contains only the final paid v2 sources, matching fabrication ZIPs and the current ADS carrier v3. boards/SHA256.json records exact source hashes. DC1 is four-layer and universal; build four copies using its separate DC1a through DC1d population CSVs. boards/bom/ holds the current assembly data and CSVs.

The motherboard needs the mandatory bottom bodge wire from JS1 B7 at (18.25, 44.27) mm to JS2 B7 at (18.25, 55.27) mm. Fit it before powering the stack. See boards/README.md for release-source and model-path notes.

scripts/ holds the current fabrication exporter, dimensions audit, corrected overlay utilities, BOM PDF builder and paid-board emulator harness. training/ holds MNIST training code, model checkpoints, layer weights, physical-model evaluations and required provenance inputs. The emulator itself lives separately at https://github.com/koboshchan/pcb-emu and is not vendored here.

renders/ contains current board images and the final v2 stack renders. pdfs/ contains the current BOM, corrected normal and clockwise/text-upright overview overlays, motherboard placement input and ADS etch mask. footprints/, 3dmodels/ and fp-lib-table retain the custom connector assets.

Old designs, routing experiments and stale outputs were deleted from the working tree, not archived. They remain available in Git history.

Run heavy training, simulation, CAD exports and rendering on KAT-BOX only. Generated output goes under ignored out/. Release sources and paid fabrication ZIPs are never overwritten by the exporter.
