import pcbnew

board = pcbnew.LoadBoard("daughtercard2_relu_l1.kicad_pcb")

w18 = board.FindFootprintByReference("W18")
p1, p2 = w18.Pads()[0], w18.Pads()[1]
print("W18 P1 pos:", pcbnew.ToMM(p1.GetPosition().x), pcbnew.ToMM(p1.GetPosition().y))
print("W18 P2 pos:", pcbnew.ToMM(p2.GetPosition().x), pcbnew.ToMM(p2.GetPosition().y))

for t in board.GetTracks():
    if t.GetNetname() == "ACT_5":
        s = t.GetStart()
        e = t.GetEnd()
        print(f"ACT_5 track: ({pcbnew.ToMM(s.x):.2f}, {pcbnew.ToMM(s.y):.2f}) -> ({pcbnew.ToMM(e.x):.2f}, {pcbnew.ToMM(e.y):.2f})")
