import pcbnew

b = pcbnew.LoadBoard("motherboard.kicad_pcb")
for fp in b.GetFootprints():
    ref = fp.GetReference()
    pos = fp.GetPosition()
    val = fp.GetValue()
    if ref.startswith("J") or "Header" in str(fp.GetFPID().GetLibItemName()):
        print(f"Header: {ref} val={val} at ({pos.x/1e6:.2f}, {pos.y/1e6:.2f})")
