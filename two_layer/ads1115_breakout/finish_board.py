"""Remove every unused B.Cu pad flash; retain unused ALRT pads on F.Cu."""
from pathlib import Path
import pcbnew as p

def finish(b):
    for f in b.GetFootprints():
        for a in f.Pads():
            if a.GetAttribute()!=p.PAD_ATTRIB_PTH:continue
            a.SetRemoveUnconnected(True);a.SetKeepTopBottom(False)
            if f.GetReference().startswith('JM') and a.GetNumber()=='6' and not a.GetNetname():
                n=p.NETINFO_ITEM(b,'NC_ALRT_'+f.GetReference());b.Add(n);a.SetNet(n)
                q=a.GetPosition();t=p.PCB_TRACK(b);t.SetStart(q);t.SetEnd(p.VECTOR2I(q.x+p.FromMM(.3),q.y));t.SetWidth(p.FromMM(.5));t.SetLayer(p.F_Cu);t.SetNet(n);b.Add(t)
    return b

if __name__=='__main__':
    path=Path(__file__).with_name('ads1115_breakout.kicad_pcb')
    p.SaveBoard(str(path),finish(p.LoadBoard(str(path))))
