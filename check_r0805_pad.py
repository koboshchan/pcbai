import pcbnew

fp_res_path = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty"
board = pcbnew.BOARD()
r = pcbnew.FootprintLoad(fp_res_path, "R_0805_2012Metric")
p = r.Pads()[0]
sz = p.GetSize()
print(f"Pad size: X={pcbnew.ToMM(sz.x):.4f} mm, Y={pcbnew.ToMM(sz.y):.4f} mm")
