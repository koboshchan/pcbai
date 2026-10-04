import pcbnew

board = pcbnew.BOARD()
fp_res_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty"

for rot in [0, 90, -90, 270]:
    fp = pcbnew.FootprintLoad(fp_res_path, "R_0805_2012Metric")
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10.0), pcbnew.FromMM(20.0)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    board.Add(fp)
    p1 = [p for p in fp.Pads() if p.GetNumber() == "1"][0]
    p2 = [p for p in fp.Pads() if p.GetNumber() == "2"][0]
    print(f"rot={rot}: Pad 1 at ({pcbnew.ToMM(p1.GetPosition().x):.4f}, {pcbnew.ToMM(p1.GetPosition().y):.4f}), Pad 2 at ({pcbnew.ToMM(p2.GetPosition().x):.4f}, {pcbnew.ToMM(p2.GetPosition().y):.4f})")
