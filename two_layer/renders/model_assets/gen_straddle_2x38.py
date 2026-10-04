#!/usr/bin/env python3
"""Corrected 2x38 straddle header render model (render-only).
KiCad VRML units: 1 unit = 2.54 mm. Model frame: x along edge, +y = board inward
(KiCad -y), z=0 board top copper side, board bottom z=-1.6.
Nominal generic 2-row header: row spacing 2.54, 0.64 sq post (Samtec TSW, FCI BergStik).
Header centered on board midplane -> rows at -0.8 +/- 1.27; NOT shrunk to fake contact."""
import sys
N,P,ROW,PW,T=38,2.54,2.54,0.635,1.6
mid=-T/2; zt=mid+ROW/2; zb=mid-ROW/2
TAIL_IN=3.0      # inboard pin end y (mm from edge); pads span 0.4..4.5
BAR_GAP=0.1      # plastic starts 0.1 mm outside edge
BAR_D=2.54; POST=6.0
S=1/2.54
def box(x0,x1,y0,y1,z0,z1,mat):
    v=[(x,y,z) for x in(x0,x1) for y in(y0,y1) for z in(z0,z1)]
    pts=",".join(f"{a*S:.5f} {b*S:.5f} {c*S:.5f}" for a,b,c in v)
    f="0,1,3,2,-1,4,6,7,5,-1,0,4,5,1,-1,2,3,7,6,-1,0,2,6,4,-1,1,5,7,3,-1"
    return f"Shape{{appearance Appearance{{material USE {mat}}} geometry IndexedFaceSet{{solid FALSE coord Coordinate{{point[{pts}]}} coordIndex[{f}]}}}}\n"
o=["#VRML V2.0 utf8\n",
 "Shape{appearance Appearance{material DEF GOLD Material{diffuseColor 0.85 0.68 0.25 specularColor 1 0.9 0.6 shininess 0.6 ambientIntensity 0.3}} geometry Box{size 0.0001 0.0001 0.0001}}\n",
 "Shape{appearance Appearance{material DEF BLK Material{diffuseColor 0.04 0.04 0.045 specularColor 0.2 0.2 0.2 shininess 0.2}} geometry Box{size 0.0001 0.0001 0.0001}}\n"]
x0=-(N-1)/2*P
o.append(box(x0-P/2,-x0+P/2,-BAR_GAP-BAR_D,-BAR_GAP,mid-ROW,mid+ROW,"BLK"))
for i in range(N):
    x=x0+i*P
    for zc in(zt,zb):
        o.append(box(x-PW/2,x+PW/2,-BAR_GAP-BAR_D-POST,TAIL_IN,zc-PW/2,zc+PW/2,"GOLD"))
open(sys.argv[1],"w").write("".join(o))
print(dict(top_pin_bottom_z=zt-PW/2,bottom_pin_top_z=zb+PW/2,gap_each_side=round(zt-PW/2,4)))
