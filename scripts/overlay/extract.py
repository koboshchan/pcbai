import pcbnew, json, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("OVERLAY_DIR", str(ROOT / "out/overlay")))
OUT.mkdir(parents=True, exist_ok=True)
SRC = {
 'DC0_v2': str(ROOT / 'boards/dc0/DC0_verified.kicad_pcb'),
 'DC1': str(ROOT / 'boards/dc1/board.kicad_pcb'),
 'DC2': str(ROOT / 'boards/dc2/daughtercard2_relu_l1_buffered_repaired.kicad_pcb'),
 'DC3_v2': str(ROOT / 'boards/dc3/dc3_universal.kicad_pcb'),
 'motherboard_v2': str(ROOT / 'boards/motherboard/post_crb.kicad_pcb'),
}
mm = pcbnew.ToMM
out = {}
for name, p in SRC.items():
    b = pcbnew.LoadBoard(p)
    bb = b.GetBoardEdgesBoundingBox()
    edges = []
    for d in b.GetDrawings():
        if d.GetLayerName() == 'Edge.Cuts':
            s, e = d.GetStart(), d.GetEnd()
            edges.append([mm(s.x), mm(s.y), mm(e.x), mm(e.y)])
    tracks = []
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            tracks.append(['via', mm(t.GetPosition().x), mm(t.GetPosition().y), mm(t.GetWidth(pcbnew.F_Cu) if hasattr(t,'GetWidth') else 0.6)])
        else:
            s, e = t.GetStart(), t.GetEnd()
            tracks.append(['seg', t.GetLayerName(), mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(t.GetWidth())])
    fps = []
    for f in b.GetFootprints():
        pads = []
        for pd in f.Pads():
            sz = pd.GetSize(pcbnew.F_Cu) if pd.GetClass() else pd.GetSize()
            try: shape = pd.GetShape(pcbnew.F_Cu)
            except Exception: shape = pd.GetShape()
            pads.append(dict(x=mm(pd.GetPosition().x), y=mm(pd.GetPosition().y), w=mm(sz.x), h=mm(sz.y),
                             rot=pd.GetOrientation().AsDegrees(), shape=int(shape),
                             th=pd.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH),
                             num=pd.GetNumber(), front=pd.IsOnLayer(pcbnew.F_Cu), back=pd.IsOnLayer(pcbnew.B_Cu)))
        fb = f.GetBoundingBox(False, False) if True else None
        fps.append(dict(ref=f.GetReference(), value=f.GetValue(), side='B' if f.IsFlipped() else 'F',
                        x=mm(f.GetPosition().x), y=mm(f.GetPosition().y), rot=f.GetOrientation().AsDegrees(),
                        fp=str(f.GetFPID().GetLibItemName()),
                        bbox=[mm(fb.GetLeft()), mm(fb.GetTop()), mm(fb.GetRight()), mm(fb.GetBottom())], pads=pads))
    out[name] = dict(bbox=[mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())], edges=edges, tracks=tracks, fps=fps)
    print(name, len(fps), file=sys.stderr)
json.dump(out, open(OUT / 'geom.json', 'w'))
