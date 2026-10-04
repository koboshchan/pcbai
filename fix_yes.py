with open("daughtercard1a_weights_l1.kicad_pcb", "r") as f:
    text = f.read()

text = text.replace('(duplicate_pad_numbers_are_jumpers no)', '(duplicate_pad_numbers_are_jumpers yes)')

with open("daughtercard1a_weights_l1.kicad_pcb", "w") as f:
    f.write(text)

print("Replaced all duplicate_pad_numbers_are_jumpers no with yes")
