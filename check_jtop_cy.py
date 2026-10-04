import pcbnew
fp_hdr_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty'
j_top = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
print('J_TOP courtyard shape items:')
for g in j_top.GraphicalItems():
    if g.GetLayer() == pcbnew.F_CrtYd:
        print(g.GetShapeStr(), g.GetStart(), g.GetEnd())
