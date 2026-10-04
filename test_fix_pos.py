import os, sys, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
PCB_PATH  = os.path.join(WORKSPACE, 'test_dc1_staggered_jumpers.kicad_pcb')

board = pcbnew.LoadBoard(PCB_PATH)
j_top = board.FindFootprintByReference('J_TOP')
j_bot = board.FindFootprintByReference('J_BOT')

j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(10.0)))
j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(90.0)))

board.Save(PCB_PATH)
