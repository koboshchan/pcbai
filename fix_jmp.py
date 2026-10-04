with open('test_full_dc1_generation.py') as f:
    code = f.read()

code = code.replace("add_jumper(xc, cfg['y_top'], cfg['y_bot'], f'IN_{in_idx}')",
                    "add_jumper(xc, cfg['y_top'], xc, cfg['y_bot'], f'IN_{in_idx}')")

with open('test_full_dc1_generation.py', 'w') as f:
    f.write(code)

