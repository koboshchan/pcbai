with open("daughtercard1a_weights_l1.kicad_pcb") as f:
    text = f.read()

import re
m = re.search(r'\(footprint.*?"Reference" "W1".*?\n\t\)', text, re.DOTALL)
if m:
    print(m.group(0))
