with open('test_dc1_stage.py') as f:
    code = f.read()

# Put J_TOP at Y = 10.0 mm
code = code.replace("j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(6.0)))",
                    "j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(10.0)))")
code = code.replace("add_track(xc, 6.0, xc, 9.5, f'IN_{in_idx}')",
                    "add_track(xc, 10.0, xc, 11.5, f'IN_{in_idx}')")

# Jumper 1 at Y = 11.5 to Y = 23.5
code = code.replace("add_jumper(xc, 9.5, xc, 23.5, f'IN_{in_idx}')",
                    "add_jumper(xc, 11.5, xc, 23.5, f'IN_{in_idx}')")
code = code.replace("add_track(xc, 9.5, xc, 12.0875, f'IN_{in_idx}')",
                    "add_track(xc, 11.5, xc, 12.0875, f'IN_{in_idx}')")

with open('test_dc1_stage.py', 'w') as f:
    f.write(code)

