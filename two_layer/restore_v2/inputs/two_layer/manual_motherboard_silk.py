#!/usr/bin/python3
"""Motherboard-only local full-reference silk using actual KiCad stroke geometry."""
import math
import pcbnew as p
import silk_refs as s

def bbox(shape):
 b=shape.BBox();return tuple(p.ToMM(v) for v in (b.GetX(),b.GetY(),b.GetRight(),b.GetBottom()))
def glyph(ref):return ref.GetEffectiveTextShape().Clone()
def pwm_candidates(f,ref):
 name=f.GetReference();x,y=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y);resistor=name.startswith('R_')
 s.configure(ref,s.side(f),.8,90,x,y);r=bbox(glyph(ref))
 # Facing lanes. Anchor corrected for the actual asymmetric stroke extents.
 tx=(x+1.652-r[0]) if resistor else (x-1.652-r[2])
 ty=2*y+(.7 if resistor else -1.5)-(r[1]+r[3])/2
 offsets=sorted(((i*.01,j*.025) for i in range(-5,6) for j in range(-6,7)),key=lambda q:math.hypot(*q))
 for dx,dy in offsets:yield 90,x+tx+dx,ty+dy

def audit(board):
 pads=s.side_pads(board);refs=[];bad=[];edge=board.GetBoardEdgesBoundingBox();bounds=(p.ToMM(edge.GetX())+.25,p.ToMM(edge.GetY())+.25,p.ToMM(edge.GetRight())-.25,p.ToMM(edge.GetBottom())-.25)
 for f in board.GetFootprints():
  ref=f.Reference();name=f.GetReference();layer=s.side(f);shape=glyph(ref);box=bbox(shape)
  if not ref.IsVisible() or ref.GetLayer()!=layer or ref.IsMirrored()!=(layer==p.B_SilkS):bad.append([name,'visibility_side_mirroring'])
  if p.ToMM(ref.GetTextHeight())<.799 or p.ToMM(ref.GetTextThickness())<.119:bad.append([name,'undersize'])
  if not s.inside(box,bounds):bad.append([name,'edge_clearance'])
  for owner,pad in pads[layer]:
   if s.intersects(box,s.expand(pad,.2)):bad.append([name,'pad_clearance',owner])
  for owner,other_layer,other_shape,other_box in refs:
   if layer==other_layer and s.intersects(box,s.expand(other_box,.15)) and shape.Collide(other_shape,p.FromMM(.15)):bad.append([name,'glyph_clearance',owner])
  if any(field.IsVisible() and not field.IsReference() for field in f.GetFields()):bad.append([name,'nonreference_visible'])
  if any(g.GetLayer() in (p.F_SilkS,p.B_SilkS) for g in f.GraphicalItems()):bad.append([name,'remaining_silk_art'])
  refs.append((name,layer,shape,box))
 if any(g.GetLayer() in (p.F_SilkS,p.B_SilkS) for g in s.board_drawings(board)):bad.append(['board','remaining_silk_art'])
 return {'reference_count':len(refs),'clean':not bad,'violations':bad,'method':'Actual KiCad stroked glyph shapes, conservative pad bounding boxes; no font or clearance reduction. Text bounding boxes may overlap when the actual strokes do not.','limits_mm':{'height':.8,'stroke':.12,'pad_clearance':.2,'glyph_clearance':.15,'edge_clearance':.25}}

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
 fps.sort(key=lambda f:(not f.GetReference().startswith(('R_PWM_','C_PWM_')),-len(f.GetReference()),f.GetReference()))
 for f in fps:
  ref=f.Reference();layer=s.side(f);name=f.GetReference();found=False
  candidates=pwm_candidates(f,ref) if name.startswith(('R_PWM_','C_PWM_')) else s.candidates(f,ref,layer,.8)
  for angle,x,y in candidates:
   s.configure(ref,layer,.8,angle,x,y);shape=glyph(ref);box=bbox(shape)
   if not s.inside(box,bounds):continue
   if any(s.intersects(box,s.expand(pad,.2)) for _,pad in pads[layer]):continue
   if any(s.intersects(box,s.expand(ob,.15)) and shape.Collide(os,p.FromMM(.15)) for os,ob in occupied[layer]):continue
   occupied[layer].append((shape,box));placed.append({'reference':name,'angle_deg':angle,'bbox_mm':box,'anchor_mm':[x,y],'distance_mm':math.hypot(x-p.ToMM(f.GetPosition().x),y-p.ToMM(f.GetPosition().y))});found=True;break
  if not found:unplaced.append(name)
 result=audit(board);result.update(placed=placed,unplaced=unplaced)
 return result
