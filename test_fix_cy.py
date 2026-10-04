with open('test_dc1_stage.py') as f:
    code = f.read()

code = code.replace("add_jumper(xc, 10.5, xc, 20.5, f'IN_{in_idx}')",
                    "add_jumper(xc, 9.5, xc, 21.5, f'IN_{in_idx}')")
code = code.replace("add_track(xc, 8.0, xc, 10.5, f'IN_{in_idx}')",
                    "add_track(xc, 8.0, xc, 9.5, f'IN_{in_idx}')")
code = code.replace("add_track(xc, 10.5, xc, 11.5875, f'IN_{in_idx}')",
                    "add_track(xc, 9.5, xc, 11.5875, f'IN_{in_idx}')")
code = code.replace("add_track(xc, 19.4125, xc, 20.5, f'IN_{in_idx}')",
                    "add_track(xc, 19.4125, xc, 21.5, f'IN_{in_idx}')")

with open('test_dc1_stage.py', 'w') as f:
    f.write(code)
