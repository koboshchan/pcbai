import pcbnew
fp_mh_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty'
for name in ['MountingHole_3.2mm_M3', 'MountingHole_3.2mm_M3_DIN965', 'MountingHole_3.2mm_M3_ISO14580']:
    mh = pcbnew.FootprintLoad(fp_mh_path, name)
    for g in mh.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            print(name, g.GetShapeStr(), g.GetStart(), g.GetEnd())
