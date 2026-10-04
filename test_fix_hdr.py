import os, sys, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
PCB_PATH  = os.path.join(WORKSPACE, 'test_dc1_staggered_jumpers.kicad_pcb')

board = pcbnew.LoadBoard(PCB_PATH)
lset = pcbnew.LSET.AllCuMask()
lset.AddLayer(pcbnew.F_Mask)
lset.AddLayer(pcbnew.B_Mask)

for fp in board.GetFootprints():
    if fp.GetReference().startswith('J_'):
        for p in fp.Pads():
            p.SetLayerSet(lset)

board.Save(PCB_PATH)
