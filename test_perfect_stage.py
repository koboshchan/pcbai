with open('test_dc1_stage.py') as f:
    code = f.read()

# Update positions
code = code.replace("j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(8.0)))",
                    "j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(6.0)))")

code = code.replace("add_track(5.0, 14.5, 87.0, 14.5, 'SUM_POS_0')",
                    "add_track(5.0, 15.5, 87.0, 15.5, 'SUM_POS_0')")
code = code.replace("add_track(5.0, 16.5, 87.0, 16.5, 'SUM_NEG_0')",
                    "add_track(5.0, 17.5, 87.0, 17.5, 'SUM_NEG_0')")

code = code.replace("add_track(xc, 8.0, xc, 9.5, f'IN_{in_idx}')",
                    "add_track(xc, 6.0, xc, 9.5, f'IN_{in_idx}')")

code = code.replace("add_jumper(xc, 9.5, xc, 21.5, f'IN_{in_idx}')",
                    "add_jumper(xc, 9.5, xc, 23.5, f'IN_{in_idx}')")

code = code.replace("add_res(ref, val_str, xc, 12.5, -90, f'IN_{in_idx}', 'SUM_POS_0')",
                    "add_res(ref, val_str, xc, 13.0, -90, f'IN_{in_idx}', 'SUM_POS_0')")
code = code.replace("add_track(xc, 9.5, xc, 11.5875, f'IN_{in_idx}')",
                    "add_track(xc, 9.5, xc, 12.0875, f'IN_{in_idx}')")
code = code.replace("add_track(xc, 13.4125, xc, 14.5, 'SUM_POS_0')",
                    "add_track(xc, 13.9125, xc, 15.5, 'SUM_POS_0')")

code = code.replace("add_res(ref, val_str, xc, 18.5, 90, f'IN_{in_idx}', 'SUM_NEG_0')",
                    "add_res(ref, val_str, xc, 20.0, 90, f'IN_{in_idx}', 'SUM_NEG_0')")
code = code.replace("add_track(xc, 17.5875, xc, 16.5, 'SUM_NEG_0')",
                    "add_track(xc, 19.0875, xc, 17.5, 'SUM_NEG_0')")
code = code.replace("add_track(xc, 19.4125, xc, 21.5, f'IN_{in_idx}')",
                    "add_track(xc, 20.9125, xc, 23.5, f'IN_{in_idx}')")

with open('test_dc1_stage.py', 'w') as f:
    f.write(code)

