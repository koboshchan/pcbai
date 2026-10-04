import pcbnew

board = pcbnew.LoadBoard("daughtercard2_relu_l1.kicad_pcb")
ds = board.GetDesignSettings()
print("MinClearance:", pcbnew.ToMM(ds.m_MinClearance))
print("TrackMinWidth:", pcbnew.ToMM(ds.m_TrackMinWidth))
