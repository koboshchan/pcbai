import pcbnew, os

fp_mh_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty'
for fn in sorted(os.listdir(fp_mh_path)):
    if fn.endswith('.kicad_mod'):
        print(fn)
