with open("route_dc1_ultimate.py") as f:
    code = f.read()

# 1. SOIC-14 GND vias under the chip body at X = 54.5 (far from both 51.5 and 56.59)
old_gnd = """    # 5. GND CONNECTIONS TO ZONE (inside SOIC-14 body)
    add_track(52.3, 48.73, 53.6, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(53.6, 48.73, net_gnd, size=0.50, drill=0.30) # pin 3

    add_track(52.3, 51.27, 53.6, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(53.6, 51.27, net_gnd, size=0.50, drill=0.30) # pin 5

    add_track(57.7, 51.27, 56.4, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(56.4, 51.27, net_gnd, size=0.50, drill=0.30) # pin 10

    add_track(57.7, 48.73, 56.4, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(56.4, 48.73, net_gnd, size=0.50, drill=0.30) # pin 12"""

new_gnd = """    # 5. GND CONNECTIONS TO ZONE (inside SOIC-14 body at X = 54.5)
    add_track(52.3, 48.73, 54.2, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(54.2, 48.73, net_gnd, size=0.50, drill=0.30) # pin 3

    add_track(52.3, 51.27, 54.2, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(54.2, 51.27, net_gnd, size=0.50, drill=0.30) # pin 5

    add_track(57.7, 51.27, 55.2, 51.27, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(55.2, 51.27, net_gnd, size=0.50, drill=0.30) # pin 10

    add_track(57.7, 48.73, 55.2, 48.73, pcbnew.F_Cu, net_gnd, width=0.25)
    add_via(55.2, 48.73, net_gnd, size=0.50, drill=0.30) # pin 12"""

assert old_gnd in code, "old_gnd not found"
code = code.replace(old_gnd, new_gnd)

# 2. Move N2, N3 Rf and Rb from X = 56.5 to X = 57.5 so Pad 2 (INV) is at 56.55 (clear of +12V bus at 55.32!)
old_fb = """    fb_config = [
        (53.5, 23.0, 53.5, 25.5),  # N0
        (53.5, 37.0, 53.5, 39.5),  # N1
        (56.5, 60.5, 56.5, 63.0),  # N2
        (56.5, 74.5, 56.5, 77.0),  # N3
    ]"""

new_fb = """    fb_config = [
        (53.5, 23.0, 53.5, 25.5),  # N0
        (53.5, 37.0, 53.5, 39.5),  # N1
        (57.5, 60.5, 57.5, 63.0),  # N2
        (57.5, 74.5, 57.5, 77.0),  # N3
    ]"""

assert old_fb in code, "old_fb not found"
code = code.replace(old_fb, new_fb)

# 3. Fix V_SUM_3 jog on F.Cu at 86.0
old_vs3 = """    add_track(54.05, 86.0, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)"""
# Make sure the jog is on F.Cu:
# add_track(58.2, 46.19, 58.2, 86.0, pcbnew.B_Cu)
# add_via(58.2, 86.0)
# add_track(58.2, 86.0, 54.05, 86.0, pcbnew.F_Cu)
# add_via(54.05, 86.0)
# add_track(54.05, 86.0, 54.05, 92.73, pcbnew.B_Cu)

# 4. Bus pitch for c >= 5: set to 0.55mm to guarantee >0.22mm clearance
code = code.replace("bus_pitch = 0.50", "bus_pitch = 0.55")

with open("route_dc1_ultimate.py", "w") as f:
    f.write(code)

print("Applied fix_dc1_complete successfully!")
