#!/usr/bin/python3
"""Exact KiCad stroked-glyph clearance for dense restored PWM lanes.
Bounding boxes are a broad phase only, not a substitute for actual glyphs.
No relaxed clearance, text size, or stroke rules.
"""
import pcbnew as p
import silk_refs as s
_BASE_AUDIT=s.audit_silk

def shape_box(shape):
    b=shape.BBox()
    return tuple(p.ToMM(v) for v in (b.GetX(),b.GetY(),b.GetRight(),b.GetBottom()))

def collides(shape,other,clearance):
    return s.intersects(shape_box(shape),s.expand(shape_box(other),clearance)) and shape.Collide(other,p.FromMM(clearance))

def pads(board):
    result={p.F_SilkS:[],p.B_SilkS:[]}
    for f in board.GetFootprints():
        for pad in f.Pads():
            for copper,silk in ((p.F_Cu,p.F_SilkS),(p.B_Cu,p.B_SilkS)):
                if pad.IsOnLayer(copper):result[silk].append((f.GetReference(),pad.GetEffectiveShape(copper)))
    return result

def audit_silk(board):
    report=_BASE_AUDIT(board)
    bad=[v for v in report['violations'] if v[1] not in ('pad_clearance','reference_clearance')]
    ps=pads(board);refs=[]
    for f in board.GetFootprints():
        name=f.GetReference();layer=s.side(f);sh=f.Reference().GetEffectiveTextShape()
        for owner,pad in ps[layer]:
            if collides(sh,pad,.2):bad.append([name,'pad_clearance',owner])
        for other,other_layer,other_shape in refs:
            if layer==other_layer and collides(sh,other_shape,.15):bad.append([name,'reference_clearance',other])
        refs.append((name,layer,sh))
    report.update(clean=not bad,violations=bad,method='KiCad exact stroked glyph SHAPE_COMPOUND versus actual pad/text shapes; conservative bounding-box broad phase. Unchanged .20 mm pad/.15 mm text clearance and .8/.12 mm typography.')
    return report

def finish_local_search(board,report):
    """Refine only failed PWM references, leaving every placed field fixed."""
    fs={f.GetReference():f for f in board.GetFootprints()};remaining=set(report['unplaced']);ps=pads(board)
    fixed=[(name,s.side(f),f.Reference().GetEffectiveTextShape()) for name,f in fs.items() if name not in remaining]
    for name in report['unplaced']:
        assert name.startswith(('R_PWM_','C_PWM_')),name
        f=fs[name];r=f.Reference();layer=s.side(f);x=p.ToMM(f.GetPosition().x);y=p.ToMM(f.GetPosition().y);found=False
        for angle,px,py in s.candidates(f,r,layer,.8):
            if (px-x)**2+(py-y)**2>4.01**2:continue
            s.configure(r,layer,.8,angle,px,py);sh=r.GetEffectiveTextShape()
            edge=board.GetBoardEdgesBoundingBox();bounds=(p.ToMM(edge.GetX())+.25,p.ToMM(edge.GetY())+.25,p.ToMM(edge.GetRight())-.25,p.ToMM(edge.GetBottom())-.25)
            if not s.inside(shape_box(sh),bounds):continue
            if any(collides(sh,q,.2) for _,q in ps[layer]):continue
            if any(side==layer and collides(sh,q,.15) for _,side,q in fixed):continue
            fixed.append((name,layer,sh));remaining.remove(name);found=True
            report['placed'].append(dict(reference=name,height_mm=.8,angle_deg=angle,layer=board.GetLayerName(layer),bbox_mm=shape_box(sh),distance_mm=((px-x)**2+(py-y)**2)**.5,exact_glyph_refinement=True))
            break
        if not found:break
    report.update(audit_silk(board));report['unplaced']=sorted(remaining);report['release_ready']=report['clean'] and not remaining
    return report
