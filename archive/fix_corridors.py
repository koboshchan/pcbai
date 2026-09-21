with open("/Users/lucaszhang/pcbai/test_dedicated_corridors.py") as f:
    text = f.read()

# 1. Fix C_U1P pads: Pad 1 is +12V (79.05), Pad 2 is GND (80.95)
# In test_dedicated_corridors.py:
old_cu1p = """    # Pin 4 (+12V) is at (u1_x - 2.7, 47.5). Decoupling cap C_U1P at (80.0, 47.5) rot=0
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 80.0, 47.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(make_segment(u1_x - 2.7, 47.5, 80.95, 47.5, 0.35, "F.Cu", "+12V", 2))
    pcb.append(make_via(79.05, 47.5, 0.6, 0.3, "GND", 1))
    # +12V power feed from B33 (x_start + 32 * PITCH) on In2.Cu:
    pcb.append(make_via(80.95, 47.5, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(80.95, 47.5, 80.95, 89.0, 0.35, "In2.Cu", "+12V", 2))
    pcb.append(make_via(80.95, 89.0, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(80.95, 89.0, x_start + 32 * PITCH, 92.0, 0.35, "B.Cu", "+12V", 2))"""

new_cu1p = """    # Pin 4 (+12V) is at (u1_x - 2.7, 47.5). Decoupling cap C_U1P at (80.0, 47.5) rot=0
    # Pad 1 (-0.95) is 79.05 = +12V. Pad 2 (+0.95) is 80.95 = GND.
    # Feed +12V to Pad 1 (79.05). Connect Pad 2 (80.95) to GND via.
    pcb.append(fp_capacitor_0805("C_U1P", "0.1uF", 80.0, 47.5, 0, "F.Cu", 2, "+12V", 1, "GND"))
    pcb.append(make_segment(u1_x - 2.7, 47.5, 79.05, 47.5, 0.35, "F.Cu", "+12V", 2))
    pcb.append(make_via(80.95, 47.5, 0.6, 0.3, "GND", 1))
    # +12V power feed from B33 (x_start + 32 * PITCH) on In2.Cu along X = 80.0
    pcb.append(make_via(79.05, 47.5, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(79.05, 47.5, 79.05, 89.0, 0.35, "In2.Cu", "+12V", 2))
    pcb.append(make_via(79.05, 89.0, 0.6, 0.3, "+12V", 2))
    pcb.append(make_segment(79.05, 89.0, x_start + 32 * PITCH, 92.0, 0.35, "B.Cu", "+12V", 2))"""

text = text.replace(old_cu1p, new_cu1p)

# 2. Fix Rb_N0 bias via X offset: change from 73.05 to 72.0 to avoid IN_28 at 73.21
text = text.replace("pcb.append(fp_resistor_0805(f\"Rb_N{neuron_range[0]}\", l1[\"weights\"][neuron_range[0]][\"bias_resistor_str\"], 74.0, 44.96, 0, \"F.Cu\", b0_nid, b0_name, 30 + neuron_range[0], f\"INV_N{neuron_range[0]}\"))\n    pcb.append(make_segment(74.95, 44.96, 77.05, 44.96, 0.25, \"F.Cu\", f\"INV_N{neuron_range[0]}\", 30 + neuron_range[0]))\n    pcb.append(make_via(73.05, 44.96, 0.6, 0.3, b0_name, b0_nid))",
"""    pcb.append(fp_resistor_0805(f"Rb_N{neuron_range[0]}", l1["weights"][neuron_range[0]]["bias_resistor_str"], 74.5, 44.96, 0, "F.Cu", b0_nid, b0_name, 30 + neuron_range[0], f"INV_N{neuron_range[0]}"))
    pcb.append(make_segment(75.45, 44.96, 77.05, 44.96, 0.25, "F.Cu", f"INV_N{neuron_range[0]}", 30 + neuron_range[0]))
    pcb.append(make_via(72.5, 44.96, 0.6, 0.3, b0_name, b0_nid))
    pcb.append(make_segment(72.5, 44.96, 73.55, 44.96, 0.25, "F.Cu", b0_name, b0_nid))""")

with open("/Users/lucaszhang/pcbai/test_dedicated_corridors.py", "w") as f:
    f.write(text)
print("Updated test_dedicated_corridors.py")
