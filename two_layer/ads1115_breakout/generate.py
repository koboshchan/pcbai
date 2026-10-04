#!/usr/bin/env python3
"""Generate the isolated F.Cu-only ADS1115 carrier with KiCad 10 pcbnew."""
from pathlib import Path
import json, subprocess, random, math
import pcbnew as p
import numpy as np
from scipy.ndimage import distance_transform_edt
from skimage.graph import MCP_Geometric
OUT=Path(__file__).resolve().parent
LIB=Path('/usr/share/kicad/footprints')
S=.2; NX=251; NY=351
v=lambda x,y:p.VECTOR2I(p.FromMM(float(x)),p.FromMM(float(y)))
b=p.BOARD(); b.SetCopperLayerCount(2)
names=['3V3','GND','SCL','SDA']+[f'ADC_{i}' for i in range(10)]
nets={}
for n in names:
    z=p.NETINFO_ITEM(b,n); b.Add(z); nets[n]=z
pads=[]; holes=[]
def text(s,x,y,size=.9,layer=p.F_SilkS):
    t=p.PCB_TEXT(b); t.SetText(s); t.SetPosition(v(x,y)); t.SetTextSize(v(size,size)); t.SetTextThickness(p.FromMM(.15)); t.SetLayer(layer); b.Add(t)
def fp(lib,name,ref,x,y,ang,mapping):
    f=p.FootprintLoad(str(LIB/(lib+'.pretty')),name); b.Add(f); f.SetReference(ref); f.SetPosition(v(x,y)); f.SetOrientationDegrees(ang); f.Reference().SetVisible(False); f.Value().SetVisible(False)
    for a in f.Pads():
        if a.GetAttribute()==p.PAD_ATTRIB_PTH:
            a.SetSize(v(1.8,1.8)); a.SetDrillSize(v(1,1)); a.SetShape(p.PAD_SHAPE_CIRCLE if a.GetNumber()!='1' else p.PAD_SHAPE_RECT)
            ls=p.LSET(); ls.AddLayer(p.F_Cu); ls.AddLayer(p.B_Mask); ls.AddLayer(p.F_Mask); a.SetLayerSet(ls)
            n=mapping.get(int(a.GetNumber()))
            if n: a.SetNet(nets[n])
            q=a.GetPosition(); pads.append((p.ToMM(q.x),p.ToMM(q.y),n,a.GetShape()==p.PAD_SHAPE_RECT,ref,a.GetNumber()))
    return f
# Right-angle socket opening points toward the left edge. Carrier stands perpendicular to motherboard.
fp('Connector_PinSocket_2.54mm','PinSocket_1x12_P2.54mm_Horizontal','JAD',10.5,18,0,{i+1:f'ADC_{i}' for i in range(10)}|{11:'GND',12:'GND'})
for k,y in enumerate([7,27,47]):
    mapping={1:'3V3',2:'GND',3:'SCL',4:'SDA',5:['GND','3V3','SDA'][k]}
    for j in range(4): mapping[7+j]=f'ADC_{4*k+j}' if 4*k+j<10 else 'GND'
    fp('Connector_PinSocket_2.54mm','PinSocket_1x10_P2.54mm_Vertical',f'JM{k+1}',40,y,270,mapping)
    text(f'ADS1115 0x{0x48+k:02X}',28.5,y+12,1.1)
    # Module body envelope is assembly guidance, not a fabricated outline.
    for a,c in [((15.5,y-1.3),(41.5,y-1.3)),((41.5,y-1.3),(41.5,y+16)),((41.5,y+16),(15.5,y+16)),((15.5,y+16),(15.5,y-1.3))]:
        d=p.PCB_SHAPE(); d.SetShape(p.SHAPE_T_SEGMENT); d.SetStart(v(*a)); d.SetEnd(v(*c)); d.SetWidth(p.FromMM(.15)); d.SetLayer(p.Dwgs_User); b.Add(d)
    for j,s in enumerate(['VDD','GND','SCL','SDA','ADDR','ALRT','A0','A1','A2','A3']):
        # Rotate names to fit the 2.54 mm pitch.
        t=p.PCB_TEXT(b); t.SetText(s); t.SetPosition(v(40-2.54*j,y+3.4)); t.SetTextSize(v(.8,.8)); t.SetTextThickness(p.FromMM(.12)); t.SetTextAngle(p.EDA_ANGLE(90,p.DEGREES_T)); t.SetLayer(p.F_SilkS); b.Add(t)
fp('Connector_PinHeader_2.54mm','PinHeader_1x04_P2.54mm_Vertical','JI2C',46,26,0,{1:'3V3',2:'GND',3:'SDA',4:'SCL'})
fp('Connector_PinHeader_2.54mm','PinHeader_1x02_P2.54mm_Vertical','JAR',46,39,0,{1:'3V3',2:'GND'})
fp('Capacitor_THT','C_Disc_D3.0mm_W1.6mm_P2.50mm','C1',46,50, -90,{1:'3V3',2:'GND'})
text('I2C',46,23.5); text('TO JAR',45,36.5,.85); text('C1 100n DNP',44,55,.75)
for j,s in enumerate(['3V3','GND','SDA','SCL']):text(s,42.5,26+j*2.54,.8)
text('3V3',42.5,39,.8);text('GND',42.5,41.54,.8)
text('JAD',5,14,1.2);text('< MOTHER',5.4,16,.75)
for j in range(12): text(str(j+1),12.8,18+j*2.54,.7)
text('ADS1115 x3 / 3V3 ONLY',25,3.5,1.1); text('50 x 70 / F.Cu only',25,67.2,.9)
for i,(x,y) in enumerate([(3.5,3.5),(46.5,3.5),(3.5,66.5),(46.5,66.5)]):
    f=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_3.2mm_M3');b.Add(f);f.SetReference(f'H{i+1}');f.SetPosition(v(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False); holes.append((x,y))
for a,c in [((0,0),(50,0)),((50,0),(50,70)),((50,70),(0,70)),((0,70),(0,0))]:
    d=p.PCB_SHAPE(); d.SetShape(p.SHAPE_T_SEGMENT);d.SetStart(v(*a));d.SetEnd(v(*c));d.SetWidth(p.FromMM(.05));d.SetLayer(p.Edge_Cuts);b.Add(d)
# Single-layer grid maze router. No top copper and no vias. Trials differ only net order.
xx=np.arange(NX)[:,None]*S; yy=np.arange(NY)[None,:]*S
padmasks=[]
for x,y,n,sq,ref,num in pads:
    padmasks.append(((np.abs(xx-x)<=.9)&(np.abs(yy-y)<=.9)) if sq else ((xx-x)**2+(yy-y)**2<=.9**2))
paddist=[distance_transform_edt(~pm)*S for pm in padmasks]
base=np.zeros((NX,NY),bool)
base[:8]=True;base[-8:]=True;base[:,:8]=True;base[:,-8:]=True
for x,y in holes:base|=(xx-x)**2+(yy-y)**2<=1.8**2
netpoints={n:[(round(x/S),round(y/S)) for x,y,nn,*_ in pads if nn==n] for n in names}
best=None
for trial in range(30):
    rng=random.Random(7700+trial)
    order=[n for n in names if n.startswith('ADC_')];rng.shuffle(order)
    bus=['3V3','GND','SCL','SDA'];rng.shuffle(bus)
    order=(bus+order) if trial%3==0 else (order+bus)
    occupied={}; routes={};failed=[]
    for n in order:
        width=.8 if n in ['3V3','GND'] else .5
        mask=base.copy()
        for pd,(_,_,nn,*_) in zip(paddist,pads):
            if nn!=n: mask |= pd < width/2+.65
        for other,(trace,ow) in occupied.items():mask |= distance_transform_edt(~trace)*S < (width+ow)/2+.65
        costs=np.ones((NX,NY));costs[mask]=np.inf
        points=netpoints[n]; tree=np.zeros((NX,NY),bool);tree[points[0]]=True; paths=[]
        for dest in points[1:]:
            if tree[dest]:continue
            m=MCP_Geometric(costs,fully_connected=True);dist,_=m.find_costs(np.argwhere(tree).tolist(),[dest],find_all_ends=False)
            if not np.isfinite(dist[dest]):failed.append((n,dest));continue
            path=m.traceback(dest);paths.append(path)
            for a in path:tree[a]=True
        occupied[n]=(tree,width);routes[n]=(paths,width)
    score=len(failed)
    if best is None or score<best[0]:
        best=(score,routes,failed,trial,{n:(a.copy(),w) for n,(a,w) in occupied.items()});print('trial',trial,'unrouted',score,failed,flush=True)
    if score==0:break
score,routes,failed,trial,occupied=best
jumpers=[]
# Assembly wire links reuse existing connector holes. Coincident SMD landing markers
# add no drill or hidden track; same-number jumper pads model the required wire only.
for n,dest in failed:
    actual=[(x,y,sq,ref,num) for x,y,nn,sq,ref,num in pads if nn==n]
    end=next(a for a in actual if (round(a[0]/S),round(a[1]/S))==dest)
    start=min((a for a in actual if a!=end and occupied[n][0][round(a[0]/S),round(a[1]/S)]),key=lambda a:math.dist(a[:2],end[:2]))
    a=(start[0]/S,start[1]/S);c=(end[0]/S,end[1]/S)
    jumpers.append((n,a,c))
    f=p.FOOTPRINT(b);b.Add(f);f.SetReference(f'W{len(jumpers)}');f.SetValue(f'{n} insulated wire');f.SetDuplicatePadNumbersAreJumpers(True);f.Reference().SetVisible(False);f.Value().SetVisible(False)
    for landing in [start,end]:
        x,y,sq,ref,num=landing
        pad=p.PAD(f);pad.SetNumber('1');pad.SetNet(nets[n]);pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetSize(v(1.8,1.8));pad.SetShape(p.PAD_SHAPE_RECT if sq else p.PAD_SHAPE_CIRCLE);ls=p.LSET();ls.AddLayer(p.F_Cu);pad.SetLayerSet(ls);pad.SetPosition(v(x,y));f.Add(pad)
    line=p.PCB_SHAPE(f);line.SetShape(p.SHAPE_T_SEGMENT);line.SetStart(v(a[0]*S,a[1]*S));line.SetEnd(v(c[0]*S,c[1]*S));line.SetWidth(p.FromMM(.15));line.SetLayer(p.Dwgs_User);f.Add(line)
    text(f'W{len(jumpers)}',a[0]*S,a[1]*S-1.7,.75)
print('Wire links',len(jumpers),flush=True)
for n,(paths,width) in routes.items():
    for path in paths:
        # Compress consecutive collinear grid steps.
        pts=[path[0]]
        for i in range(1,len(path)-1):
            if (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1]) != (path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]):pts.append(path[i])
        pts.append(path[-1])
        for a,c in zip(pts,pts[1:]):
            t=p.PCB_TRACK(b);t.SetStart(v(a[0]*S,a[1]*S));t.SetEnd(v(c[0]*S,c[1]*S));t.SetWidth(p.FromMM(width));t.SetLayer(p.F_Cu);t.SetNet(nets[n]);b.Add(t)
from finish_board import finish
finish(b)
p.SaveBoard(str(OUT/'ads1115_breakout.kicad_pcb'),b)
(OUT/'connectivity.json').write_text(json.dumps({'size_mm':[50,70],'copper_layers_used':['F.Cu'],'jumpers':[{'reference':f'W{i+1}','net':n,'start_mm':[a[0]*S,a[1]*S],'end_mm':[c[0]*S,c[1]*S],'pad_distance_mm':math.dist(a,c)*S} for i,(n,a,c) in enumerate(jumpers)],'router_trial':trial,'pads':[dict(x=x,y=y,net=n,reference=ref,pin=num) for x,y,n,_,ref,num in pads]},indent=2)+'\n')
print('Saved',OUT,flush=True)
