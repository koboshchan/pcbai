#!/usr/bin/python3
"""Adjacent motherboard silk using shortened actual references and exact glyphs."""
import math
import pcbnew as p
import silk_refs as s
import manual_motherboard_silk as base
import motherboard_refs as refs

def local_candidates(f,ref):
    x=p.ToMM(f.GetPosition().x);y=p.ToMM(f.GetPosition().y)
    role=refs.role(f)
    if f.GetReference().startswith(('RP','CP')):
        yield 0,x,y-2.7
        yield 0,x,y+2.7
    if False:
        # Keep the same own-component facing lanes as the approved full-ref helper.
        resistor=role.startswith('R_')
        s.configure(ref,s.side(f),.8,90,x,y);bb=base.bbox(base.glyph(ref))
        tx=x+1.652-bb[0] if resistor else x-1.652-bb[2]
        ty=2*y+(.7 if resistor else -1.5)-(bb[1]+bb[3])/2
        offsets=sorted(((i*.01,j*.025) for i in range(-5,6) for j in range(-6,7)),key=lambda q:math.hypot(*q))
        for dx,dy in offsets:yield 90,x+tx+dx,ty+dy
    # Only candidates adjacent to the footprint/pad body, never remote banks.
    for angle,px,py in s.candidates(f,ref,s.side(f),.8):
        if math.hypot(px-x,py-y)<=6.01 or role.startswith('J_'):
            yield angle,px,py

def adjacency(board):
    bad=[];rows=[]
    for f in board.GetFootprints():
        b=base.bbox(base.glyph(f.Reference()));pads=[s.rect(q) for q in f.Pads()]
        if pads:
            body=(min(q[0] for q in pads),min(q[1] for q in pads),max(q[2] for q in pads),max(q[3] for q in pads))
        else:
            x,y=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y);body=(x-.5,y-.5,x+.5,y+.5)
        dx=max(body[0]-b[2],b[0]-body[2],0);dy=max(body[1]-b[3],b[1]-body[3],0);gap=math.hypot(dx,dy)
        # Long connectors may label at either end but must still be beside own body.
        limit=3.0 if refs.role(f).startswith('J_') else 4.01
        rows.append({'reference':f.GetReference(),'legacy_role':refs.role(f),'label_to_own_pad_body_gap_mm':gap,'maximum_mm':limit})
        if gap>limit:bad.append([f.GetReference(),'nonadjacent_reference',gap])
    return {'clean':not bad,'violations':bad,'references':rows}

def audit(board):
    out=base.audit(board);adj=adjacency(board);out['adjacency']=adj
    out['violations']+=adj['violations'];out['clean']=not out['violations'];return out

def apply(board):
    for g in s.board_drawings(board):
        if g.GetLayer() in (p.F_SilkS,p.B_SilkS):board.Delete(g)
    fps=list(board.GetFootprints())
    for f in fps:
        for field in f.GetFields():
            if not field.IsReference():field.SetVisible(False)
        for g in list(f.GraphicalItems()):
            if g.GetLayer() in (p.F_SilkS,p.B_SilkS):f.Delete(g)
    edge=board.GetBoardEdgesBoundingBox();bounds=(p.ToMM(edge.GetX())+.25,p.ToMM(edge.GetY())+.25,p.ToMM(edge.GetRight())-.25,p.ToMM(edge.GetBottom())-.25)
    pads=s.side_pads(board);occupied={p.F_SilkS:[],p.B_SilkS:[]};placed=[];unplaced=[]
    fps.sort(key=lambda f:(not refs.role(f).startswith(('R_PWM_','C_PWM_')),-len(f.GetReference()),f.GetReference()))
    for f in fps:
        ref=f.Reference();layer=s.side(f);name=f.GetReference();found=False
        for angle,x,y in local_candidates(f,ref):
            s.configure(ref,layer,.8,angle,x,y);shape=base.glyph(ref);box=base.bbox(shape)
            if not s.inside(box,bounds):continue
            if any(s.intersects(box,s.expand(pad,.2)) for _,pad in pads[layer]):continue
            if any(s.intersects(box,s.expand(ob,.15)) and shape.Collide(os,p.FromMM(.15)) for os,ob in occupied[layer]):continue
            occupied[layer].append((shape,box));placed.append({'reference':name,'angle_deg':angle,'bbox_mm':box,'anchor_mm':[x,y],'distance_mm':math.hypot(x-p.ToMM(f.GetPosition().x),y-p.ToMM(f.GetPosition().y))});found=True;break
        if not found:unplaced.append(name)
    result=audit(board);result.update(placed=placed,unplaced=unplaced);return result
