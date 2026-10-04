#!/usr/bin/python3
"""Remote KiCad-only regression test. Writes disposable /tmp copies, never sources."""
import json
from pathlib import Path
import pcbnew as p
from silk_refs import apply_silk, audit_silk, board_drawings

ROOT = Path('/work/pcbai')
OUT = Path('/tmp/silk_test')


def point(v):
    return (v.x, v.y)


def electrical_snapshot(b):
    """Snapshot independent of serialization, excluding only text/artwork."""
    footprints = []
    for fp in b.GetFootprints():
        pads = []
        for pad in fp.Pads():
            pads.append((pad.GetNumber(), point(pad.GetPosition()), point(pad.GetSize()),
                         point(pad.GetDrillSize()), pad.GetShape(), pad.GetAttribute(),
                         pad.GetNetname(), pad.GetOrientationDegrees(), pad.GetLayerSet().FmtBin()))
        footprints.append((fp.GetReference(), point(fp.GetPosition()), fp.GetLayer(),
                           fp.GetOrientationDegrees(), sorted(pads)))
    tracks = [(t.GetClass(), point(t.GetStart()), point(t.GetEnd()), (t.GetWidth(t.GetLayer()) if isinstance(t, p.PCB_VIA) else t.GetWidth()),
               t.GetLayer(), t.GetNetname()) for t in b.GetTracks()]
    zones = [(z.GetNetname(), z.GetLayerSet().FmtBin(), z.GetNumCorners(),
              tuple(point(z.GetCornerPosition(i)) for i in range(z.GetNumCorners())))
             for z in b.Zones()]
    non_silk = [(i.GetClass(), i.GetLayer(), i.m_Uuid.AsString()) for i in board_drawings(b)
                if i.GetLayer() not in (p.F_SilkS, p.B_SilkS)]
    return {'footprints': sorted(footprints), 'tracks': sorted(tracks),
            'zones': sorted(zones), 'non_silk_drawings': sorted(non_silk),
            'copper_layers': b.GetCopperLayerCount()}


def run():
    OUT.mkdir(exist_ok=True)
    results = []
    class MissingTypemap:
        def __init__(self, board):
            self.board = board
        def GetDrawings(self):
            return object()  # Equivalent non-iterable SWIG return.
        def Drawings(self):
            return self.board.Drawings()
    for filename in ('daughtercard2_relu_l1.kicad_pcb',
                     'daughtercard1a_weights_l1.kicad_pcb', 'motherboard.kicad_pcb'):
        source = ROOT / filename
        b = p.LoadBoard(str(source))
        assert len(board_drawings(MissingTypemap(b))) == len(board_drawings(b))
        before = electrical_snapshot(b)
        report = apply_silk(b)
        assert electrical_snapshot(b) == before, 'electrical/placement mutation'
        dest = OUT / filename
        p.SaveBoard(str(dest), b)
        reloaded = p.LoadBoard(str(dest))
        assert electrical_snapshot(reloaded) == before, 'roundtrip electrical mutation'
        report['roundtrip_audit'] = audit_silk(reloaded)
        report['release_ready'] = report['release_ready'] and report['roundtrip_audit']['clean']
        report['electrical_and_placement_unchanged'] = True
        (OUT / (source.stem + '.json')).write_text(json.dumps(report, indent=2)+'\n')
        summary = {k: report[k] for k in ('reference_count', 'clean', 'unplaced', 'release_ready')}
        summary['board'] = filename
        summary['roundtrip_clean'] = report['roundtrip_audit']['clean']
        summary['electrical_and_placement_unchanged'] = True
        results.append(summary)
        print(json.dumps(summary), flush=True)
    (OUT / 'summary.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__':
    run()
