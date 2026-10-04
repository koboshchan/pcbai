import pcbnew

board = pcbnew.LoadBoard("daughtercard1a_weights_l1.kicad_pcb")

r = board.FindFootprintByReference("R1_0_3")
p1 = [p for p in r.Pads() if p.GetNumber() == "1"][0]
p2 = [p for p in r.Pads() if p.GetNumber() == "2"][0]

print(f"R1_0_3 pos: ({pcbnew.ToMM(r.GetPosition().x):.4f}, {pcbnew.ToMM(r.GetPosition().y):.4f})")
print(f"P1: ({pcbnew.ToMM(p1.GetPosition().x):.4f}, {pcbnew.ToMM(p1.GetPosition().y):.4f}), net: {p1.GetNetname()}")
print(f"P2: ({pcbnew.ToMM(p2.GetPosition().x):.4f}, {pcbnew.ToMM(p2.GetPosition().y):.4f}), net: {p2.GetNetname()}")

for t in board.GetTracks():
    if t.GetNetname() == "IN_0":
        s = t.GetStart()
        e = t.GetEnd()
        print(f"Track IN_0: ({pcbnew.ToMM(s.x):.4f}, {pcbnew.ToMM(s.y):.4f}) -> ({pcbnew.ToMM(e.x):.4f}, {pcbnew.ToMM(e.y):.4f})")
