with open("route_dc1_ultimate.py") as f:
    code = f.read()

# 1. Separate V_SUM_2 and V_SUM_3 tracks and vias:
# V_SUM_2: runs down on B.Cu at 57.0 to Y = 82.0, jogs on F.Cu at 82.0 to 52.78, down on In2.Cu to Pin 35
# V_SUM_3: runs down on B.Cu at 58.2 to Y = 86.0, jogs on F.Cu at 86.0 to 54.05, down on B.Cu to Pin 36

old_out = """    # N2: Pin 8 at (57.7, 53.81), Rf Pad 1 at (57.45, 60.5). Pin 35 is odd at (54.05, 95.27)
    net_s2 = nets[f"V_SUM_{neuron_range[2]}"]
    add_via(57.45, 60.5, net_s2, size=0.50, drill=0.30)
    add_track(57.7, 53.81, 57.45, 53.81, pcbnew.F_Cu, net_s2, width=0.20)
    add_via(57.45, 53.81, net_s2, size=0.50, drill=0.30)
    add_track(57.45, 53.81, 57.45, 82.0, pcbnew.B_Cu, net_s2, width=0.25)
    add_via(57.45, 82.0, net_s2, size=0.50, drill=0.30)
    add_track(57.45, 82.0, 52.78, 82.0, pcbnew.F_Cu, net_s2, width=0.25)
    add_via(52.78, 82.0, net_s2, size=0.50, drill=0.30)
    add_track(52.78, 82.0, 52.78, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(52.78, 97.5, 54.05, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(54.05, 97.5, 54.05, 95.27, pcbnew.In2_Cu, net_s2, width=0.25)

    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5). Pin 36 is even at (54.05, 92.73)
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_via(57.45, 74.5, net_s3, size=0.50, drill=0.30)
    add_track(57.7, 46.19, 57.45, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(57.45, 46.19, net_s3, size=0.50, drill=0.30)
    add_track(57.45, 46.19, 57.45, 86.0, pcbnew.B_Cu, net_s3, width=0.25)
    add_track(57.45, 86.0, 54.05, 86.0, pcbnew.B_Cu, net_s3, width=0.25)
    add_track(54.05, 86.0, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)"""

new_out = """    # N2: Pin 8 at (57.7, 53.81), Rf Pad 1 at (57.45, 60.5). Pin 35 is odd at (54.05, 95.27)
    net_s2 = nets[f"V_SUM_{neuron_range[2]}"]
    add_track(57.45, 60.5, 57.0, 60.5, pcbnew.F_Cu, net_s2, width=0.25)
    add_via(57.0, 60.5, net_s2, size=0.50, drill=0.30)
    add_track(57.7, 53.81, 57.0, 53.81, pcbnew.F_Cu, net_s2, width=0.20)
    add_via(57.0, 53.81, net_s2, size=0.50, drill=0.30)
    add_track(57.0, 53.81, 57.0, 82.0, pcbnew.B_Cu, net_s2, width=0.25)
    add_via(57.0, 82.0, net_s2, size=0.50, drill=0.30)
    add_track(57.0, 82.0, 52.78, 82.0, pcbnew.F_Cu, net_s2, width=0.25)
    add_via(52.78, 82.0, net_s2, size=0.50, drill=0.30)
    add_track(52.78, 82.0, 52.78, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(52.78, 97.5, 54.05, 97.5, pcbnew.In2_Cu, net_s2, width=0.25)
    add_track(54.05, 97.5, 54.05, 95.27, pcbnew.In2_Cu, net_s2, width=0.25)

    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5). Pin 36 is even at (54.05, 92.73)
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_track(57.45, 74.5, 58.2, 74.5, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(58.2, 74.5, net_s3, size=0.50, drill=0.30)
    add_track(57.7, 46.19, 58.2, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(58.2, 46.19, net_s3, size=0.50, drill=0.30)
    add_track(58.2, 46.19, 58.2, 86.0, pcbnew.B_Cu, net_s3, width=0.25)
    add_via(58.2, 86.0, net_s3, size=0.50, drill=0.30)
    add_track(58.2, 86.0, 54.05, 86.0, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(54.05, 86.0, net_s3, size=0.50, drill=0.30)
    add_track(54.05, 86.0, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)"""

assert old_out in code, "old_out not found"
code = code.replace(old_out, new_out)

# 2. Bias resistor rot 180 for N0, N1 so Pad 1 is at 54.45 and Pad 2 at 52.55
# And connect Pad 1 directly on F.Cu without crossing Pad 2!
old_rb_route = """        # Rb Pad 1:
        # idx < 2 (rot 0): Pad 1 is at 52.55 (connects to bus_x on F.Cu!)
        # idx >= 2 (rot 180): Pad 1 is at 57.45 (connects to bus_x on F.Cu!)
        rb_pad1_x = (rb_x - 0.95) if idx < 2 else (rb_x + 0.95)
        add_track(rb_pad1_x, rb_y, bus_x, rb_y, pcbnew.F_Cu, net_bias, width=0.20)
        add_via(bus_x, rb_y, net_bias, size=0.50, drill=0.30)"""

new_rb_route = """        # Rb Pad 1:
        # idx < 2: Pad 1 at 52.55 -> drop via to In2.Cu, jog at In2.Cu to bus_x
        # idx >= 2: Pad 1 at 57.45 -> drop via to In2.Cu, jog at In2.Cu to bus_x
        rb_pad1_x = (rb_x - 0.95) if idx < 2 else (rb_x + 0.95)
        add_via(rb_pad1_x, rb_y, net_bias, size=0.50, drill=0.30)
        add_track(rb_pad1_x, rb_y, bus_x, rb_y, pcbnew.In2_Cu, net_bias, width=0.20)"""

assert old_rb_route in code, "old_rb_route not found"
code = code.replace(old_rb_route, new_rb_route)

# 3. Connect INV_N2 summing bar to its via at 55.55
old_bar2 = """            add_track(COL_X[0] + 0.95, y_bar, 50.0, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(50.0, y_bar, 50.0, 46.0, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(50.0, 46.0, 60.5, 46.0, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(60.5, 46.0, 60.5, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(60.5, y_bar, COL_X[7] + 0.95, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)"""

new_bar2 = """            add_track(COL_X[0] + 0.95, y_bar, 50.0, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(50.0, y_bar, 50.0, 46.0, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(50.0, 46.0, 60.5, 46.0, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(60.5, 46.0, 60.5, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)
            add_track(60.5, y_bar, COL_X[7] + 0.95, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)
            # Connect the In2.Cu bus at (55.55, 46.0) up to the via at (55.55, y_bar)
            add_track(55.55, 46.0, 55.55, y_bar, pcbnew.In2_Cu, net_inv, width=0.25)"""

assert old_bar2 in code, "old_bar2 not found"
code = code.replace(old_bar2, new_bar2)

with open("route_dc1_ultimate.py", "w") as f:
    f.write(code)

print("Applied fix_all_dc1 successfully!")
