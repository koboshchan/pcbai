import pcbnew

b = pcbnew.LoadBoard("motherboard.kicad_pcb")
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("J_SLOT"):
        pads = list(fp.Pads())
        print(f"{ref}: {fp.GetFPID().GetLibItemName()} num_pads={len(pads)}")
        for p in pads[:4]:
            print(f"  Pad {p.GetNumber()} net={p.GetNetname()} at ({p.GetPosition().x/1e6:.2f}, {p.GetPosition().y/1e6:.2f})")
