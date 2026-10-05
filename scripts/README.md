Run these scripts on KAT-BOX with the required Python packages and KiCad 10. The cleanup only checked syntax and paths; no training, simulation, CAD export or rendering was run.

export_fabrication.py exports current boards into a fresh out/fabrication directory. Set KICAD_CLI if kicad-cli is not on PATH. Use --board to select designs and --output for a different fresh output directory. Existing paid ZIPs under boards/ are authoritative. Exported geometry is not a new fabrication qualification or an assembly BOM; DC1 requires its population CSVs.

audit_board_dimensions.py checks the current board dimensions and copper-layer count. kicad_symbols.py is the retained schematic-symbol helper.

overlay/extract.py reads final board geometry into out/overlay/geom.json. Then overlay/render.py or overlay/render_rot.py uses the current boards/bom CSVs to write tiled value guides into that output directory. These utilities use the corrected reference-based DC1 mapping and POPULATION values. The already-corrected overview PDFs under pdfs/ are the current release documents. Set OVERLAY_DIR to change the work directory. Requires KiCad pcbnew and matplotlib.

bom/build_pdf.py uses preserved boards/bom/bom_data.json and pdfs/motherboard_placement.pdf, writing a new PDF under out/. Intermediate outputs default to out/bom; BOM_DIR changes that intermediate directory. Requires reportlab and pypdf.

emulator/prepare.py extracts the paid-board copper and applies the four DC1 population files, checking the release hashes. emulator/run.py compares the first 100 official MNIST test images with and without the motherboard bodge, using the same original matched-baseline harness. Install the separate pcb-emu package and set PCB_EMU_DIR to its checkout with examples/mnist_stack.py, official gzip MNIST test files under data/, and the original runs/matched_adaptive.json fixture. The fixture must report 958 correct with zero solver failures. EMU_OUT changes the default out/v2_emu_100 output directory. This is averaged PWM with ideal intra-board copper, not full-parasitic or transient simulation.
