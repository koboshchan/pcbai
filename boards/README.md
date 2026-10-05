Current paid v2 board sources and matching fabrication ZIPs live here. PCB bytes are preserved exactly; SHA256.json records source and ZIP hashes. DC1 is the four-layer universal design. Populate four copies using DC1a.csv through DC1d.csv and POPULATION.md. ADS carrier is the current v3 targeted design.

The motherboard requires a bottom bodge wire connecting JS1 B7 at (18.25, 44.27) mm to JS2 B7 at (18.25, 55.27) mm. Fit it before powering the stack.

Only existing matching project/rule files were copied. DC2 and the motherboard final source folders did not contain matching project files. Custom footprints and 3D models are retained at the repository root. Some immutable boards embed the original /Users/lucaszhang/pcbai/3dmodels paths; on other machines provide that path as a symlink or remap models in a separate working copy. Do not edit the release sources just to change model paths.
