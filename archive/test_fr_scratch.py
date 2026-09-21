import os
import subprocess
import json

WORKSPACE = "/Users/lucaszhang/pcbai"
os.system(f"/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 -c 'import test_dc1_v10; test_dc1_v10.generate_dc1_board(\"test_scratch.kicad_pcb\", \"Test Scratch\", range(0, 4))'")
# Copy kicad_pro to test_scratch.kicad_pro so rules are loaded
os.system("cp daughtercard1a_weights_l1.kicad_pro test_scratch.kicad_pro")
