#!/usr/bin/env python3
"""Render-only generic 2x38 2.54mm vertical female socket (KiCad VRML unit = 2.54mm).
Origin = footprint centre (pads x -46.99..46.99, y +/-1.27). Body 5.08 wide x 8.5 tall on top,
76 discrete 0.64 sq solder tails to z=-3.0 (through 1.6 board), dark entry holes on top."""
import sys
N,P=38,2.54;S=1/2.54
def box(x0,x1,y0,y1,z0,z1,mat):
    v=[(x,y,z) for x in(x0,x1) for y in(y0,y1) for z in(z0,z1)]
    pts=",".join(f"{a*S:.5f} {b*S:.5f} {c*S:.5f}" for a,b,c in v)
    f="0,1,3,2,-1,4,6,7,5,-1,0,4,5,1,-1,2,3,7,6,-1,0,2,6,4,-1,1,5,7,3,-1"
    return f"Shape{{appearance Appearance{{material USE {mat}}} geometry IndexedFaceSet{{solid FALSE coord Coordinate{{point[{pts}]}} coordIndex[{f}]}}}}\n"
o=["#VRML V2.0 utf8\n",
"Shape{appearance Appearance{material DEF BLK Material{diffuseColor 0.09 0.09 0.1 specularColor 0.3 0.3 0.3 shininess 0.4}} geometry Box{size 0.0001 0.0001 0.0001}}\n",
"Shape{appearance Appearance{material DEF HOLE Material{diffuseColor 0.01 0.01 0.01}} geometry Box{size 0.0001 0.0001 0.0001}}\n",
"Shape{appearance Appearance{material DEF TIN Material{diffuseColor 0.8 0.8 0.78 specularColor 1 1 1 shininess 0.7}} geometry Box{size 0.0001 0.0001 0.0001}}\n"]
x0=-(N-1)/2*P
o.append(box(x0-P/2,-x0+P/2,-P,P,0,8.5,"BLK"))
for i in range(N):
    x=x0+i*P
    for y in(-1.27,1.27):
        o.append(box(x-0.5,x+0.5,y-0.5,y+0.5,8.5,8.52,"HOLE"))
        o.append(box(x-0.32,x+0.32,y-0.32,y+0.32,-3.0,0,"TIN"))
open(sys.argv[1],"w").write("".join(o))
