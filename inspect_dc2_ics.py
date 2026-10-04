import pcbnew
b = pcbnew.LoadBoard('daughtercard2_relu_l1.kicad_pcb')
for u in ['U1', 'U2', 'U3', 'U4']:
    fp = b.FindFootprintByReference(u)
    pos = fp.GetPosition()
    rot = fp.GetOrientation().AsDegrees()
    print(u, pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y), rot)
