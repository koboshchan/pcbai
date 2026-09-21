import re

with open("solve_router.py") as f:
    code = f.read()

# Fix 1: Connect V_SUM_3 track on B.Cu between 46.19 and 74.5
old_s3 = """    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5).
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_track(57.45, 74.5, 54.05, 74.5, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(54.05, 74.5, net_s3, size=0.55, drill=0.3)
    # Pin 36 is even at (54.05, 92.73) -> B.Cu straight down
    add_track(54.05, 74.5, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)
    add_track(57.7, 46.19, 54.05, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(54.05, 46.19, net_s3, size=0.55, drill=0.3)"""

new_s3 = """    # N3: Pin 14 at (57.7, 46.19), Rf Pad 1 at (57.45, 74.5).
    net_s3 = nets[f"V_SUM_{neuron_range[3]}"]
    add_track(57.45, 74.5, 54.05, 74.5, pcbnew.F_Cu, net_s3, width=0.25)
    add_via(54.05, 74.5, net_s3, size=0.55, drill=0.3)
    # Pin 36 is even at (54.05, 92.73) -> B.Cu straight down
    add_track(54.05, 46.19, 54.05, 92.73, pcbnew.B_Cu, net_s3, width=0.25)
    add_track(57.7, 46.19, 54.05, 46.19, pcbnew.F_Cu, net_s3, width=0.20)
    add_via(54.05, 46.19, net_s3, size=0.55, drill=0.3)"""

assert old_s3 in code, "old_s3 not found"
code = code.replace(old_s3, new_s3)

# Fix 2: +12V via at (50.8, 43.5)
old_p12 = """    # Tap to C_U1P pad 1 (51.05, 43.5)
    add_track(51.05, 43.5, 50.8, 43.5, pcbnew.F_Cu, net_p12, width=0.30)"""

new_p12 = """    # Tap to C_U1P pad 1 (51.05, 43.5)
    add_via(50.8, 43.5, net_p12, size=0.55, drill=0.3)
    add_track(51.05, 43.5, 50.8, 43.5, pcbnew.F_Cu, net_p12, width=0.30)"""

assert old_p12 in code, "old_p12 not found"
code = code.replace(old_p12, new_p12)

# Fix 3: In2.Cu corridor for J_SLOT_B
old_corridor = """                # Choose clearance corridor
                if c == 4 and p == 0:
                    x_corridor = x_pin + 1.27
                else:
                    x_corridor = x_pin - 1.27"""

new_corridor = """                # Choose clearance corridor
                if c >= 4:
                    x_corridor = x_pin + 1.27
                else:
                    x_corridor = x_pin - 1.27"""

assert old_corridor in code, "old_corridor not found"
code = code.replace(old_corridor, new_corridor)

with open("solve_router.py", "w") as f:
    f.write(code)

print("Updated solve_router.py successfully!")
