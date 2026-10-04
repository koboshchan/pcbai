import os, sys, json, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
PCB_IN    = os.path.join(WORKSPACE, 'test_dc1_center_ic.kicad_pcb')
PCB_OUT   = os.path.join(WORKSPACE, 'test_dc1_prerouted.kicad_pcb')

board = pcbnew.LoadBoard(PCB_IN)
fcu_layer = pcbnew.F_Cu
track_w = pcbnew.FromMM(0.40)

# Pre-route 32 top inputs (0..31)
# Header pin at (5.55 + col*2.54, 11.0)
# Top resistors at Y = 15.0..36.0 (or 18.2..39.2)
top_neuron_y = [15.0, 22.0, 29.0, 36.0]
bot_neuron_y = [59.0, 66.0, 73.0, 80.0]

for col in range(32):
    cx = 5.55 + col * 2.54
    in_top = col
    net_top = board.FindNet(f'IN_{in_top}')
    y_offset = 0.0 if (col % 2 == 0) else 3.2
    y_end_top = top_neuron_y[3] + y_offset
    
    # Track from header (Y=11.0) to lowest top resistor Pad 1 (Y=y_end_top)
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(11.0)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(y_end_top)))
    t.SetWidth(track_w)
    t.SetLayer(fcu_layer)
    t.SetNet(net_top)
    board.Add(t)
    
    # Bottom inputs (32..63)
    in_bot = 32 + col
    net_bot = board.FindNet(f'IN_{in_bot}')
    y_start_bot = bot_neuron_y[0] + y_offset
    
    # Track from highest bottom resistor Pad 1 (Y=y_start_bot) to header (Y=89.0)
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(y_start_bot)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(89.0)))
    t.SetWidth(track_w)
    t.SetLayer(fcu_layer)
    t.SetNet(net_bot)
    board.Add(t)

board.Save(PCB_OUT)
print("Saved prerouted board:", PCB_OUT)
