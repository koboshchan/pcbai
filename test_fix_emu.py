with open('emulate_pcb_hardware.py') as f:
    code = f.read()

# Fix L1 polarity check:
old_l1 = """                        pol = +1
                        if "polarity=negative" in r_fp["description"]:
                            pol = -1
                        self.l1_polarities[(i, n)] = pol"""

new_l1 = """                        pol = +1
                        for net_name in r_fp["pads"].values():
                            if "NEG" in net_name:
                                pol = -1
                                break
                        if "polarity=negative" in r_fp["description"]:
                            pol = -1
                        self.l1_polarities[(i, n)] = pol"""

assert old_l1 in code, "old_l1 not found"
code = code.replace(old_l1, new_l1)

# Fix L2 polarity check:
old_l2 = """                    pol = +1
                    if "polarity=negative" in r_fp["description"]:
                        pol = -1
                    self.l2_polarities[(k, c)] = pol"""

new_l2 = """                    pol = +1
                    for net_name in r_fp["pads"].values():
                        if "NEG" in net_name:
                            pol = -1
                            break
                    if "polarity=negative" in r_fp["description"]:
                        pol = -1
                    self.l2_polarities[(k, c)] = pol"""

assert old_l2 in code, "old_l2 not found"
code = code.replace(old_l2, new_l2)

with open('emulate_pcb_hardware.py', 'w') as f:
    f.write(code)

print("Updated emulate_pcb_hardware.py")
