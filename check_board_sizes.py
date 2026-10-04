import pcbnew

for path in ["daughtercard2_relu_l1.kicad_pcb", "daughtercard3_weights_l2_wta.kicad_pcb", "motherboard.kicad_pcb"]:
    try:
        b = pcbnew.LoadBoard(path)
        bb = b.GetBoardEdgesBoundingBox()
        fps = [fp.GetReference() for fp in b.GetFootprints()]
        print(f"{path}:")
        print(f"  Size: {bb.GetWidth()/1e6:.1f} x {bb.GetHeight()/1e6:.1f} mm")
        print(f"  Footprints: {len(fps)} (sample: {fps[:5]})")
    except Exception as e:
        print(f"{path}: error {e}")
