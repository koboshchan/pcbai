import pcbnew

board = pcbnew.LoadBoard("daughtercard1a_weights_l1.kicad_pcb")

w = board.FindFootprintByReference("W253")
p1, p2 = w.Pads()[0], w.Pads()[1]
print("W253 P1:", pcbnew.ToMM(p1.GetPosition().x), pcbnew.ToMM(p1.GetPosition().y), p1.GetNetname())
print("W253 P2:", pcbnew.ToMM(p2.GetPosition().x), pcbnew.ToMM(p2.GetPosition().y), p2.GetNetname())

for t in board.GetTracks():
    if t.GetNetname() == "SUM_NEG_3":
        s = t.GetStart()
        e = t.GetEnd()
        print(f"SUM_NEG_3 track: ({pcbnew.ToMM(s.x):.2f}, {pcbnew.ToMM(s.y):.2f}) -> ({pcbnew.ToMM(e.x):.2f}, {pcbnew.ToMM(e.y):.2f}) len={pcbnew.ToMM(t.GetLength()):.2f}")
