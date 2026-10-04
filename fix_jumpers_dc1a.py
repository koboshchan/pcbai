with open("daughtercard1a_weights_l1.kicad_pcb", "r") as f:
    text = f.read()

# Replace pad "2" with pad "1" in JUMPER footprints
# and add (duplicate_pad_numbers_are_jumpers yes)
import re

def fix_jumper(match):
    chunk = match.group(0)
    chunk = chunk.replace('(pad "2" thru_hole', '(pad "1" thru_hole')
    if '(duplicate_pad_numbers_are_jumpers yes)' not in chunk:
        chunk = chunk.replace('(tags "net tie")', '(tags "net tie")\n\t\t(duplicate_pad_numbers_are_jumpers yes)')
    return chunk

text = re.sub(r'\(footprint ""\s+\(layer "F\.Cu"\).*?\(property "Value" "JUMPER".*?\n\t\)', fix_jumper, text, flags=re.DOTALL)

with open("daughtercard1a_weights_l1.kicad_pcb", "w") as f:
    f.write(text)

print("Updated daughtercard1a with duplicate_pad_numbers_are_jumpers yes")
