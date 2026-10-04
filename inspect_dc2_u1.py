import pcbnew

board = pcbnew.LoadBoard("daughtercard2_relu_l1.kicad_pcb")
for t in board.GetTracks():
    s = t.GetStart()
    e = t.GetEnd()
    sx, sy = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
    ex, ey = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
    if 40 <= sx <= 60 and 15 <= sy <= 25 and 40 <= ex <= 60 and 15 <= ey <= 25:
        print(f"{t.GetNetname()}: ({sx:.2f}, {sy:.2f}) -> ({ex:.2f}, {ey:.2f}) w={pcbnew.ToMM(t.GetWidth()):.2f}")
