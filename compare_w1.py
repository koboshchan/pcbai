with open("daughtercard2_relu_l1.kicad_pcb") as f:
    text_dc2 = f.read()

with open("daughtercard1a_weights_l1.kicad_pcb") as f:
    text_dc1 = f.read()

import re

m2 = re.search(r'\(footprint.*?"Reference" "W1".*?\n\t\)', text_dc2, re.DOTALL)
m1 = re.search(r'\(footprint.*?"Reference" "W1".*?\n\t\)', text_dc1, re.DOTALL)

print("=== DC2 W1 ===")
if m2: print(m2.group(0))

print("\n=== DC1A W1 ===")
if m1: print(m1.group(0))
