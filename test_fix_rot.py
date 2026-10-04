import os, sys, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
PCB_PATH  = os.path.join(WORKSPACE, 'test_dc1_stage.kicad_pcb')

# Re-run test_dc1_stage with correct rotations
with open('test_dc1_stage.py') as f:
    code = f.read()

# Replace rotations:
# positive was 90 -> change to -90
code = code.replace("add_res(ref, val_str, xc, 12.5, 90, f'IN_{in_idx}', 'SUM_POS_0')",
                    "add_res(ref, val_str, xc, 12.5, -90, f'IN_{in_idx}', 'SUM_POS_0')")
# negative was 270 -> change to 90
code = code.replace("add_res(ref, val_str, xc, 18.5, 270, f'IN_{in_idx}', 'SUM_NEG_0')",
                    "add_res(ref, val_str, xc, 18.5, 90, f'IN_{in_idx}', 'SUM_NEG_0')")

with open('test_dc1_stage.py', 'w') as f:
    f.write(code)

