import os, sys, re, subprocess
import pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
PCB_PATH  = os.path.join(WORKSPACE, 'test_dc1_16x16.kicad_pcb')
DSN_PATH  = os.path.join(WORKSPACE, 'test_dc1_16x16.dsn')
SES_PATH  = os.path.join(WORKSPACE, 'test_dc1_16x16.ses')

board = pcbnew.LoadBoard(PCB_PATH)
pcbnew.ExportSpecctraDSN(board, DSN_PATH)

with open(DSN_PATH, 'r') as f:
    dsn = f.read()

# Remove B.Cu from component padstacks
def patch_padstack(match):
    block = match.group(0)
    if 'Via[' in block:
        block = re.sub(r'\(shape\s+\(circle\s+F\.Cu\s+\d+\)\)', '(shape (circle F.Cu 1400))', block)
        block = re.sub(r'\(shape\s+\(circle\s+B\.Cu\s+\d+\)\)', '(shape (circle B.Cu 1400))', block)
        return block
    else:
        block = re.sub(r'\s*\(shape\s+\([^\)]+B\.Cu[^\)]*\)\)', '', block)
        return block

dsn = re.sub(r'\(padstack\s+[^\n]+(?:\n\s+[^\n]+)*?\n\s+\)', patch_padstack, dsn)

# Set global rules + clearances
dsn = re.sub(r'\(width\s+\d+\)', '(width 350)', dsn)
dsn = re.sub(r'\(clearance\s+\d+\)', '(clearance 550)', dsn)
dsn = re.sub(r'\(clearance\s+\d+\s+\(type smd_smd\)\)', '(clearance 550 (type smd_smd))\n      (clearance 550 (type via_smd))\n      (clearance 550 (type via_pin))\n      (clearance 550 (type via_wire))', dsn)

with open(DSN_PATH, 'w') as f:
    f.write(dsn)

print('Exported and patched test_dc1_16x16.dsn')
