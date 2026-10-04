import pcbnew

fp_ic_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_SO.pretty"
board = pcbnew.BOARD()
u1 = pcbnew.FootprintLoad(fp_ic_path, "SOIC-14_3.9x8.7mm_P1.27mm")
u1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25.0), pcbnew.FromMM(60.0)))
board.Add(u1)

for p in sorted(u1.Pads(), key=lambda pad: int(pad.GetNumber())):
    pos = p.GetPosition()
    print(f"Pin {p.GetNumber()}: ({pcbnew.ToMM(pos.x):.4f}, {pcbnew.ToMM(pos.y):.4f})")
