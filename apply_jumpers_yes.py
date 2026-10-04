with open("daughtercard1a_weights_l1.kicad_pcb", "r") as f:
    text = f.read()

import re

# 1. Replace (pad "2" thru_hole ... with (pad "1" thru_hole ... inside Jumper_Wire footprints
def fix_jumper(m):
    block = m.group(0)
    block = block.replace('(duplicate_pad_numbers_are_jumpers no)', '(duplicate_pad_numbers_are_jumpers yes)')
    block = block.replace('(pad "2" thru_hole', '(pad "1" thru_hole')
    return block

text = re.sub(r'\(footprint "Jumper_Wire".*?\n\t\)', fix_jumper, text, flags=re.DOTALL)

with open("daughtercard1a_weights_l1.kicad_pcb", "w") as f:
    f.write(text)

print("Updated Jumper_Wire footprints to duplicate_pad_numbers_are_jumpers yes and pad '1'")
