with open("zero_drc_dc1.py") as f:
    code = f.read()

# 1. Move U1 GND vias under the chip body
old_gnd = """    # 5. GND CONNECTIONS TO ZONE
    add_track(52.3, 48.73, 50.5, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(50.5, 48.73, net_gnd, size=0.50, drill=0.30) # pin 3

    add_track(52.3, 51.27, 50.5, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(50.5, 51.27, net_gnd, size=0.50, drill=0.30) # pin 5

    add_track(57.7, 51.27, 58.8, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(58.8, 51.27, net_gnd, size=0.50, drill=0.30) # pin 10

    add_track(57.7, 48.73, 58.8, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(58.8, 48.73, net_gnd, size=0.50, drill=0.30) # pin 12"""

new_gnd = """    # 5. GND CONNECTIONS TO ZONE (inside SOIC-14 body)
    add_track(52.3, 48.73, 53.6, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(53.6, 48.73, net_gnd, size=0.50, drill=0.30) # pin 3

    add_track(52.3, 51.27, 53.6, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(53.6, 51.27, net_gnd, size=0.50, drill=0.30) # pin 5

    add_track(57.7, 51.27, 56.4, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(56.4, 51.27, net_gnd, size=0.50, drill=0.30) # pin 10

    add_track(57.7, 48.73, 56.4, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(56.4, 48.73, net_gnd, size=0.50, drill=0.30) # pin 12"""

assert old_gnd in code, "old_gnd not found"
code = code.replace(old_gnd, new_gnd)

# 2. Fix +12V track to avoid C_U1P pad 2
old_p12 = """    # +12V: Pin 37 at (56.59, 95.27, odd). Run on B.Cu at 55.32 down to 80.0, via to In2.Cu
    # Local F.Cu connections at U1 pin 4 and C_U1P
    add_track(52.3, 50.0, 50.8, 50.0, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(50.8, 50.0, net_p12, size=0.50, drill=0.30)
    add_track(51.05, 42.5, 50.8, 42.5, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(50.8, 42.5, net_p12, size=0.50, drill=0.30)
    add_track(50.8, 42.5, 50.8, 50.0, pcbnew.B_Cu, net_p12, width=0.30)
    # Jog to 55.32 on F.Cu at Y = 42.5 (completely empty on F.Cu!)
    add_track(50.8, 42.5, 55.32, 42.5, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(55.32, 42.5, net_p12, size=0.50, drill=0.30)"""

new_p12 = """    # +12V: Pin 37 at (56.59, 95.27, odd). Run on B.Cu at 55.32 down to 80.0, via to In2.Cu
    # Local F.Cu connections at U1 pin 4 and C_U1P
    add_track(52.3, 50.0, 50.8, 50.0, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(50.8, 50.0, net_p12, size=0.50, drill=0.30)
    add_track(51.05, 42.5, 50.8, 42.5, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(50.8, 42.5, net_p12, size=0.50, drill=0.30)
    add_track(50.8, 42.5, 50.8, 50.0, pcbnew.B_Cu, net_p12, width=0.30)
    # Jog to 55.32 on F.Cu at Y = 41.2 (above C_U1P, completely empty on F.Cu!)
    add_track(50.8, 42.5, 50.8, 41.2, pcbnew.F_Cu, net_p12, width=0.30)
    add_track(50.8, 41.2, 55.32, 41.2, pcbnew.F_Cu, net_p12, width=0.30)
    add_via(55.32, 41.2, net_p12, size=0.50, drill=0.30)"""

assert old_p12 in code, "old_p12 not found"
code = code.replace(old_p12, new_p12)

# Update the vertical track start from 41.2 instead of 42.5
code = code.replace("add_track(55.32, 42.5, 55.32, 80.0, pcbnew.B_Cu, net_p12, width=0.35)",
                    "add_track(55.32, 41.2, 55.32, 80.0, pcbnew.B_Cu, net_p12, width=0.35)")

# 3. Separate V_SUM_2 jog at 82.0 instead of 80.0
old_vsum2 = """    add_track(57.0, 53.81, 57.0, 80.0, pcbnew.B_Cu, net_s2, width=0.25)
    add_via(57.0, 80.0, net_s2, size=0.50, drill=0.30)
    # On In2.Cu: jog to corridor at 52.78
    add_track(57.0, 80.0, 52.78, 80.0, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(52.78, 80.0, 52.78, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)"""

new_vsum2 = """    add_track(57.0, 53.81, 57.0, 82.0, pcbnew.B_Cu, net_s2, width=0.25)
    add_via(57.0, 82.0, net_s2, size=0.50, drill=0.30)
    # On In2.Cu: jog to corridor at 52.78
    add_track(57.0, 82.0, 52.78, 82.0, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(52.78, 82.0, 52.78, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)"""

assert old_vsum2 in code, "old_vsum2 not found"
code = code.replace(old_vsum2, new_vsum2)

# 4. Fix +5V_REF bus to 57.86 (exact pin corridor)
code = code.replace("bus_x = 58.2 if rail == \"+5V_REF\" else 59.13",
                    "bus_x = 57.86 if rail == \"+5V_REF\" else 59.13")
code = code.replace("add_track(58.2, 20.0, 58.2, 80.0, pcbnew.B_Cu, net_p5v, width=0.25)",
                    "add_track(57.86, 20.0, 57.86, 80.0, pcbnew.B_Cu, net_p5v, width=0.25)")
code = code.replace("add_via(58.2, 80.0, net_p5v, size=0.50, drill=0.30)",
                    "add_via(57.86, 80.0, net_p5v, size=0.50, drill=0.30)")
code = code.replace("add_track(58.2, 80.0, 58.2, 97.5, pcbnew.In2_Cu, net_p5v, width=0.25)",
                    "add_track(57.86, 80.0, 57.86, 97.5, pcbnew.In2_Cu, net_p5v, width=0.25)")
code = code.replace("add_track(58.2, 97.5, 59.13, 97.5, pcbnew.In2_Cu, net_p5v, width=0.25)",
                    "add_track(57.86, 97.5, 59.13, 97.5, pcbnew.In2_Cu, net_p5v, width=0.25)")

# 5. Connect Rb Pad 1 on F.Cu to bus_x
old_rb = """        rb_pad1_x = (rb_x - 0.95) if idx < 2 else (rb_x + 0.95)
        # Connect Rb Pad 1 to bus_x on B.Cu
        add_via(rb_pad1_x, rb_y, net_bias, size=0.50, drill=0.30)
        add_track(rb_pad1_x, rb_y, bus_x, rb_y, pcbnew.B_Cu, net_bias, width=0.20)"""

new_rb = """        rb_pad1_x = (rb_x - 0.95) if idx < 2 else (rb_x + 0.95)
        # Connect Rb Pad 1 to bus_x on F.Cu!
        add_track(rb_pad1_x, rb_y, bus_x, rb_y, pcbnew.F_Cu, net_bias, width=0.20)
        add_via(bus_x, rb_y, net_bias, size=0.50, drill=0.30)"""

assert old_rb in code, "old_rb not found"
code = code.replace(old_rb, new_rb)

# 6. Route V_SUM_3 to the right of Rf_N3 (X = 58.2) instead of crossing through it!
old_vs3 = """    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5). Pin 36 is even at (54.05, 92.73)
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_track(57.45, 74.5, 54.05, 74.5, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(54.05, 74.5, net_s3, size=0.50, drill=0.30)
    add_track(57.7, 46.19, 54.05, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(54.05, 46.19, net_s3, size=0.50, drill=0.30)
    add_track(54.05, 46.19, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)"""

new_vs3 = """    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5). Pin 36 is even at (54.05, 92.73)
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_track(57.45, 74.5, 58.2, 74.5, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(58.2, 74.5, net_s3, size=0.50, drill=0.30)
    add_track(57.7, 46.19, 58.2, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(58.2, 46.19, net_s3, size=0.50, drill=0.30)
    add_track(58.2, 46.19, 58.2, 86.0, pcbnew.B_Cu, net_s3, width=0.25)
    add_track(58.2, 86.0, 54.05, 86.0, pcbnew.B_Cu, net_s3, width=0.25)
    add_track(54.05, 86.0, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)"""

assert old_vs3 in code, "old_vs3 not found"
code = code.replace(old_vs3, new_vs3)

with open("zero_drc_dc1.py", "w") as f:
    f.write(code)

print("Applied fix_spine_dc1 successfully!")
