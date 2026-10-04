import pcbnew as p
from pathlib import Path
b=p.LoadBoard('/work/pcbai/two_layer/motherboard_adc_repaired_unrouted.kicad_pcb')
for f in b.GetFootprints():
 x,y=f.GetPosition().x/1e6,f.GetPosition().y/1e6
 if 45<x<83 and y>75:print(f.GetReference(),x,y,f.GetLayer(),f.GetBoundingBox().GetX()/1e6,f.GetBoundingBox().GetY()/1e6,f.GetBoundingBox().GetWidth()/1e6,f.GetBoundingBox().GetHeight()/1e6)
