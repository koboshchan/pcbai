import pcbnew

board = pcbnew.LoadBoard("daughtercard1a_weights_l1.kicad_pcb")

print("IN_0 tracks:")
for t in board.GetTracks():
    if t.GetNetname() == "IN_0":
        s = t.GetStart()
        e = t.GetEnd()
        print(f"  ({pcbnew.ToMM(s.x):.4f}, {pcbnew.ToMM(s.y):.4f}) -> ({pcbnew.ToMM(e.x):.4f}, {pcbnew.ToMM(e.y):.4f}) len={pcbnew.ToMM(t.GetLength()):.4f}")

print("\nIN_0 jumper pads:")
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == "IN_0":
            pos = p.GetPosition()
            print(f"  FP {fp.GetReference()} Pad {p.GetNumber()}: ({pcbnew.ToMM(pos.x):.4f}, {pcbnew.ToMM(pos.y):.4f})")
