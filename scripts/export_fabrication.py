#!/usr/bin/env python3
"""Re-export current PCB Gerbers/drills into out/fabrication, never release ZIPs.

Requires KiCad CLI. Universal DC1 assembly must use boards/dc1 population CSVs,
not the generic component values embedded in the universal PCB.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BOARDS = {
    'dc0': 'boards/dc0/DC0_verified.kicad_pcb',
    'dc1': 'boards/dc1/board.kicad_pcb',
    'dc2': 'boards/dc2/daughtercard2_relu_l1_buffered_repaired.kicad_pcb',
    'dc3': 'boards/dc3/dc3_universal.kicad_pcb',
    'motherboard': 'boards/motherboard/post_crb.kicad_pcb',
    'ads_carrier': 'boards/ads_carrier/targeted.kicad_pcb',
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', choices=sorted(BOARDS), action='append')
    parser.add_argument('--output', type=Path, default=ROOT / 'out/fabrication')
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT / 'boards' == output or ROOT / 'boards' in output.parents:
        parser.error('output must not overwrite release board files')
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
    if not cli:
        parser.error('kicad-cli not found; set KICAD_CLI')
    for name in args.board or BOARDS:
        pcb = ROOT / BOARDS[name]
        target = output / name
        if target.exists():
            parser.error(f'{target} already exists; choose a fresh output directory')
        target.mkdir(parents=True)
        layers = 'F.Cu,In1.Cu,In2.Cu,B.Cu' if name == 'dc1' else 'F.Cu,B.Cu'
        layers += ',F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts'
        subprocess.run([cli, 'pcb', 'export', 'gerbers', '--check-zones',
                        '--subtract-soldermask', '--layers', layers,
                        '-o', str(target) + '/', str(pcb)], check=True)
        subprocess.run([cli, 'pcb', 'export', 'drill', '--excellon-units', 'mm',
                        '--excellon-separate-th', '--drill-origin', 'absolute',
                        '-o', str(target) + '/', str(pcb)], check=True)
        with zipfile.ZipFile(output / (name + '.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(target.iterdir()):
                if path.is_file():
                    archive.write(path, path.name)
        print(output / (name + '.zip'))

if __name__ == '__main__':
    main()
