with open("route_dc1_ultimate.py") as f:
    code = f.read()

# 1. INV_N2 route on B.Cu at 59.5 instead of 61.2
old_inv2 = """    # N2: Pin 9 at (57.7, 52.54) -> B.Cu bus at 61.2 up to Y = 48.5
    net_inv2 = nets[f"INV_N{neuron_range[2]}"]
    add_track(57.7, 52.54, 61.2, 52.54, pcbnew.F_Cu, net_inv2, width=0.20)
    add_via(61.2, 52.54, net_inv2, size=0.50, drill=0.30)
    add_track(61.2, 52.54, 61.2, 48.5, pcbnew.B_Cu, net_inv2, width=0.25)
    add_via(61.2, 48.5, net_inv2, size=0.50, drill=0.30)
    add_track(61.2, 48.5, COL_X[4] + 0.95, 48.5, pcbnew.In2_Cu, net_inv2, width=0.25)"""

new_inv2 = """    # N2: Pin 9 at (57.7, 52.54) -> B.Cu bus at 59.5 up to Y = 48.5
    net_inv2 = nets[f"INV_N{neuron_range[2]}"]
    add_track(57.7, 52.54, 59.5, 52.54, pcbnew.F_Cu, net_inv2, width=0.20)
    add_via(59.5, 52.54, net_inv2, size=0.50, drill=0.30)
    add_track(59.5, 52.54, 59.5, 48.5, pcbnew.B_Cu, net_inv2, width=0.25)
    add_via(59.5, 48.5, net_inv2, size=0.50, drill=0.30)
    add_track(59.5, 48.5, COL_X[4] + 0.95, 48.5, pcbnew.In2_Cu, net_inv2, width=0.25)"""

assert old_inv2 in code, "old_inv2 not found"
code = code.replace(old_inv2, new_inv2)

# 2. V_SUM_2 via at 57.45 instead of 57.0 (to avoid -12V bus at 56.59)
old_vs2 = """    # N2: Pin 8 at (57.7, 53.81), Rf Pad 1 at (57.45, 60.5). Pin 35 is odd at (54.05, 95.27)
    net_s2 = nets[f"V_SUM_{neuron_range[2]}"]
    add_track(57.45, 60.5, 57.0, 60.5, pcbnew.F_Cu, net_s2, width=0.25)
    add_via(57.0, 60.5, net_s2, size=0.50, drill=0.30)
    add_track(57.7, 53.81, 57.0, 53.81, pcbnew.F_Cu, net_s2, width=0.20)
    add_via(57.0, 53.81, net_s2, size=0.50, drill=0.30)
    add_track(57.0, 53.81, 57.0, 82.0, pcbnew.B_Cu, net_s2, width=0.25)
    add_via(57.0, 82.0, net_s2, size=0.50, drill=0.30)
    add_track(57.0, 82.0, 52.78, 82.0, pcbnew.F_Cu, net_s2, width=0.25)"""

new_vs2 = """    # N2: Pin 8 at (57.7, 53.81), Rf Pad 1 at (57.45, 60.5). Pin 35 is odd at (54.05, 95.27)
    net_s2 = nets[f"V_SUM_{neuron_range[2]}"]
    add_via(57.45, 60.5, net_s2, size=0.50, drill=0.30)
    add_track(57.7, 53.81, 57.45, 53.81, pcbnew.F_Cu, net_s2, width=0.20)
    add_via(57.45, 53.81, net_s2, size=0.50, drill=0.30)
    add_track(57.45, 53.81, 57.45, 82.0, pcbnew.B_Cu, net_s2, width=0.25)
    add_via(57.45, 82.0, net_s2, size=0.50, drill=0.30)
    add_track(57.45, 82.0, 52.78, 82.0, pcbnew.F_Cu, net_s2, width=0.25)"""

assert old_vs2 in code, "old_vs2 not found"
code = code.replace(old_vs2, new_vs2)

# 3. V_SUM_3 via at 57.45 instead of crossing resistor
old_vs3 = """    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5). Pin 36 is even at (54.05, 92.73)
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_track(57.45, 74.5, 54.05, 74.5, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(54.05, 74.5, net_s3, size=0.50, drill=0.30)
    add_track(57.7, 46.19, 54.05, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(54.05, 46.19, net_s3, size=0.50, drill=0.30)
    add_track(54.05, 46.19, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)"""

new_vs3 = """    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5). Pin 36 is even at (54.05, 92.73)
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_via(57.45, 74.5, net_s3, size=0.50, drill=0.30)
    add_track(57.7, 46.19, 57.45, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(57.45, 46.19, net_s3, size=0.50, drill=0.30)
    add_track(57.45, 46.19, 57.45, 86.0, pcbnew.B_Cu, net_s3, width=0.25)
    add_track(57.45, 86.0, 54.05, 86.0, pcbnew.B_Cu, net_s3, width=0.25)
    add_track(54.05, 86.0, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)"""

assert old_vs3 in code, "old_vs3 not found"
code = code.replace(old_vs3, new_vs3)

# 4. N2 summing bar across central spine at Y = 46.0 to avoid U1 pin 12 GND via at 48.73
old_bar = """        # Single continuous horizontal bus on In2.Cu
        add_track(COL_X[0] + 0.95, y_bar, COL_X[7] + 0.95, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)"""

new_bar = """        # Single continuous horizontal bus on In2.Cu
        if idx == 2:
            # Jog around U1 pin 12 GND via (at 56.4, 48.73) by routing spine crossing at Y = 46.0
            add_track(COL_X[0] + 0.95, y_bar, 50.0, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(50.0, y_bar, 50.0, 46.0, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(50.0, 46.0, 60.5, 46.0, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(60.5, 46.0, 60.5, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(60.5, y_bar, COL_X[7] + 0.95, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)
        else:
            add_track(COL_X[0] + 0.95, y_bar, COL_X[7] + 0.95, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)"""

assert old_bar in code, "old_bar not found"
code = code.replace(old_bar, new_bar)

with open("route_dc1_ultimate.py", "w") as f:
    f.write(code)

print("Applied update_final.py successfully!")
