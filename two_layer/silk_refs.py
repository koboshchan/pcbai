#!/usr/bin/python3
"""Component-side reference placement. No copper/pad/footprint position changes.

apply_silk(board) mutates an in-memory pcbnew BOARD and returns an audit dict.
It never saves a board. Call after routing, then review audit['unplaced'].
All decorative silk graphics/text and values are removed/hidden. Reference
properties are the only visible silkscreen text. Unplaceable references remain
visible at their original position and are explicitly reported, not silently
hidden. A clean audit is required before release.
"""
import json
import math
import pcbnew


def rect(item):
    b = item.GetBoundingBox()
    return tuple(pcbnew.ToMM(v) for v in (b.GetX(), b.GetY(), b.GetRight(), b.GetBottom()))


def expand(b, d):
    return (b[0]-d, b[1]-d, b[2]+d, b[3]+d)


def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def inside(a, b):
    return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]


class SpatialBoxes:
    """Small uniform grid keeps dense matrix search local."""
    def __init__(self, cell=4.0):
        self.cell = cell
        self.cells = {}

    def keys(self, box):
        for x in range(math.floor(box[0]/self.cell), math.floor(box[2]/self.cell)+1):
            for y in range(math.floor(box[1]/self.cell), math.floor(box[3]/self.cell)+1):
                yield x,y

    def add(self, box):
        for key in self.keys(box):
            self.cells.setdefault(key,[]).append(box)

    def overlaps(self, box):
        return any(intersects(box, candidate) for key in self.keys(box)
                   for candidate in self.cells.get(key,()))


def side(fp):
    return pcbnew.B_SilkS if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_SilkS


def side_pads(board):
    result = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            for copper, silk in ((pcbnew.F_Cu, pcbnew.F_SilkS), (pcbnew.B_Cu, pcbnew.B_SilkS)):
                if p.IsOnLayer(copper):
                    result[silk].append((fp.GetReference(), rect(p)))
    return result


def configure(ref, layer, height, angle, x, y):
    ref.SetVisible(True)
    ref.SetLayer(layer)
    ref.SetMirrored(layer == pcbnew.B_SilkS)
    ref.SetKeepUpright(False)
    ref.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(height), pcbnew.FromMM(height)))
    ref.SetTextThickness(pcbnew.FromMM(0.12))
    ref.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    ref.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    ref.ClearBoundingBoxCache()


def candidates(fp, ref, layer, height):
    """Nearby candidates, cardinal placements first, then a <=6 mm local grid."""
    x, y = (pcbnew.ToMM(v) for v in (fp.GetPosition().x, fp.GetPosition().y))
    pads = [rect(p) for p in fp.Pads()]
    if pads:
        body = (min(a[0] for a in pads), min(a[1] for a in pads), max(a[2] for a in pads), max(a[3] for a in pads))
    else:
        body = (x-.5, y-.5, x+.5, y+.5)
    for angle in (90, 0) if len(fp.GetReference()) >= 6 else (0, 90):
        configure(ref, layer, height, angle, x, y)
        rb = rect(ref)
        # bbox need not be centered on the text anchor in KiCad.
        cx, cy = (rb[0]+rb[2])/2-x, (rb[1]+rb[3])/2-y
        w, h = rb[2]-rb[0], rb[3]-rb[1]
        points = [(body[2]+.22+w/2-cx, y-cy), (body[0]-.22-w/2-cx, y-cy),
                  (x-cx, body[1]-.22-h/2-cy), (x-cx, body[3]+.22+h/2-cy)]
        for px, py in points:
            yield angle, px, py
    offsets = [(dx*.25, dy*.25) for dx in range(-24,25) for dy in range(-24,25)
               if dx*dx+dy*dy <= 24*24]
    offsets.sort(key=lambda q: q[0]*q[0]+q[1]*q[1])
    for dx, dy in offsets:
        for angle in (90,0) if len(fp.GetReference()) >= 6 else (0,90):
            yield angle, x+dx, y+dy


def board_drawings(board):
    """KiCad 10 builds differ in GetDrawings() SWIG typemap coverage."""
    try:
        return list(board.GetDrawings())
    except TypeError:
        # The legacy DRAWINGS wrapper has its own iterator typemap.
        return list(board.Drawings())


def apply_silk(board):
    """Place actual reference fields on component-side silk and return audit.

    Minimum text height 0.8 mm, stroke 0.12 mm, pad bbox clearance 0.20 mm,
    reference bbox clearance 0.15 mm, board-edge clearance 0.25 mm. Conservative
    axis-aligned bboxes intentionally overestimate rotated/rounded pad shapes.
    Dense long refs are placed first to avoid short refs consuming matrix gaps.
    """
    silks = (pcbnew.F_SilkS, pcbnew.B_SilkS)
    removed = 0
    for drawing in board_drawings(board):
        if drawing.GetLayer() in silks:
            board.Delete(drawing)
            removed += 1
    fps = list(board.GetFootprints())
    for fp in fps:
        fp.Value().SetVisible(False)
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() in silks:
                fp.Delete(item)
                removed += 1
    edge = board.GetBoardEdgesBoundingBox()
    bounds = (pcbnew.ToMM(edge.GetX())+.25, pcbnew.ToMM(edge.GetY())+.25,
              pcbnew.ToMM(edge.GetRight())-.25, pcbnew.ToMM(edge.GetBottom())-.25)
    pads = side_pads(board)
    occupied = {s: [] for s in silks}
    obstacles = {s: SpatialBoxes() for s in silks}
    for s in silks:
        for _, p in pads[s]:
            obstacles[s].add(expand(p,.20))
    placed, unplaced = [], []
    fps.sort(key=lambda fp: (-len(fp.GetReference()), fp.GetReference()))
    for fp in fps:
        ref = fp.Reference()
        layer = side(fp)
        original = ref.GetPosition()
        found = False
        # Dense matrices need consistent .8 mm labels; mixing 1 mm first
        # consumes neighboring cells and causes avoidable packing failures.
        heights = (.8,) if len(fp.GetReference()) >= 6 else (1.0, .8)
        for height in heights:
            for angle, x, y in candidates(fp, ref, layer, height):
                configure(ref, layer, height, angle, x, y)
                r = rect(ref)
                if not inside(r, bounds):
                    continue
                if obstacles[layer].overlaps(r):
                    continue
                occupied[layer].append((fp.GetReference(),r))
                obstacles[layer].add(expand(r,.15))
                placed.append({'reference':fp.GetReference(),'height_mm':height,'angle_deg':angle,
                               'layer':board.GetLayerName(layer),'bbox_mm':r,
                               'distance_mm':math.hypot(x-pcbnew.ToMM(fp.GetPosition().x),y-pcbnew.ToMM(fp.GetPosition().y))})
                found = True
                break
            if found:
                break
        if not found:
            configure(ref, layer, .8, 90 if len(fp.GetReference())>=6 else 0,
                      pcbnew.ToMM(original.x),pcbnew.ToMM(original.y))
            occupied[layer].append((fp.GetReference(), rect(ref)))
            obstacles[layer].add(expand(rect(ref),.15))
            unplaced.append(fp.GetReference())
    audit = audit_silk(board)
    audit.update({'removed_silk_items':removed,'placed':placed,'unplaced':unplaced,
                  'release_ready':not unplaced and audit['clean']})
    return audit


def audit_silk(board):
    pads = side_pads(board)
    refs = []
    bad = []
    edge = board.GetBoardEdgesBoundingBox()
    bounds = (pcbnew.ToMM(edge.GetX())+.25,pcbnew.ToMM(edge.GetY())+.25,
              pcbnew.ToMM(edge.GetRight())-.25,pcbnew.ToMM(edge.GetBottom())-.25)
    for fp in board.GetFootprints():
        r = fp.Reference()
        name = fp.GetReference()
        layer = side(fp)
        box = rect(r)
        if not r.IsVisible() or r.GetLayer()!=layer:
            bad.append([name,'hidden_or_wrong_side'])
        if r.IsMirrored() != (layer == pcbnew.B_SilkS):
            bad.append([name,'wrong_mirroring'])
        for item in fp.GraphicalItems():
            if item.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                bad.append([name,'remaining_footprint_silk_art'])
        if pcbnew.ToMM(r.GetTextHeight()) < .799 or pcbnew.ToMM(r.GetTextThickness()) < .119:
            bad.append([name,'text_too_small'])
        if fp.Value().IsVisible():
            bad.append([name,'visible_value'])
        if not inside(box,bounds):
            bad.append([name,'edge_clearance'])
        for owner,p in pads[layer]:
            if intersects(box,expand(p,.20)):
                bad.append([name,'pad_clearance',owner])
        for other,other_layer,other_box in refs:
            if layer==other_layer and intersects(box,expand(other_box,.15)):
                bad.append([name,'reference_clearance',other])
        refs.append((name,layer,box))
    for item in board_drawings(board):
        if item.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            bad.append(['board','remaining_board_silk_art'])
    return {'reference_count':len(refs),'clean':not bad,'violations':bad,
            'method':'Conservative text/pad axis-aligned bounding boxes, not a rendered glyph or solder-mask DRC.',
            'limits_mm':{'pad_clearance':.20,'reference_clearance':.15,'edge_clearance':.25,'minimum_height':.8,'stroke':.12}}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output',help='Explicit output path. Must differ from input.')
    parser.add_argument('--report',required=True)
    args = parser.parse_args()
    from pathlib import Path
    if Path(args.input).resolve()==Path(args.output).resolve():
        parser.error('input and output must differ')
    board = pcbnew.LoadBoard(args.input)
    report = apply_silk(board)
    pcbnew.SaveBoard(args.output,board)
    # Round-trip audit catches any serialization changes.
    report['roundtrip_audit'] = audit_silk(pcbnew.LoadBoard(args.output))
    report['release_ready'] = report['release_ready'] and report['roundtrip_audit']['clean']
    Path(args.report).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('reference_count','clean','unplaced','release_ready')}))
