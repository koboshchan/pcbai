import pcbnew

board = pcbnew.LoadBoard("daughtercard2_relu_l1.kicad_pcb")

# Find a jumper in DC2, e.g. W1 or W18
for fp in board.GetFootprints():
    if fp.GetReference().startswith("W"):
        pads = fp.Pads()
        p1, p2 = pads[0], pads[1]
        print(f"DC2 Jumper {fp.GetReference()}: Pad 1 net={p1.GetNetname()} num={p1.GetNumber()}, Pad 2 net={p2.GetNetname()} num={p2.GetNumber()}")
        break
