with open("daughtercard2_relu_l1.kicad_pcb") as f:
    text = f.read()

import re
matches = re.findall(r'\(footprint "Jumper_Wire".*?\n  \)', text, re.DOTALL)
if matches:
    print(matches[0])
