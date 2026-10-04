#!/usr/bin/env python3
"""Deterministic placement-only repair; run with KiCad's system Python."""
import argparse,hashlib,json,pathlib,re,subprocess
import pcbnew

def mm(v): return round(pcbnew.ToMM(v),6)
def identity(b):
    parts=[]
    for f in b.GetFootprints():
        pads=[]
        for p in f.Pads():
            pos=p.GetFPRelativePosition()
            pads.append((p.GetNumber(),p.GetNetname(),mm(pos.x),mm(pos.y),mm(p.GetSize().x),mm(p.GetSize().y),mm(p.GetDrillSize().x),mm(p.GetDrillSize().y),int(p.GetShape()),int(p.GetAttribute()),str(p.GetLayerSet().FmtBin())))
        parts.append((f.GetReference(),f.GetValue(),int(f.GetLayer()),sorted(pads)))
    return {'copper_layers':b.GetCopperLayerCount(),'parts':sorted(parts)}
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def move(f,x,y,angle=None):
    if angle is not None:f.SetOrientationDegrees(angle)
    f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)))
    f.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y-2)))
def apply(b,name):
    for f in b.GetFootprints():
        r=f.GetReference()
        if name.startswith('motherboard'):
            m=re.fullmatch(r'(R_TOP|R_BOT|R_REF|R_ADC|D_HI|D_LO)_(\d+)',r)
            if m:
                typ,j=m.group(1),int(m.group(2)); k=['R_TOP','R_BOT','R_REF','R_ADC','D_HI','D_LO'].index(typ)
                move(f,7+(j%2)*49+[0,6,12,18,26,34][k],37.5+11*(j//2),0)
        elif name.startswith('daughtercard2'):
            m=re.fullmatch(r'U_BUF([1-4])',r)
            if m: move(f,15,15+20*(int(m.group(1))-1))
            m=re.fullmatch(r'C_U_BUF([1-4])([PN])',r)
            if m:move(f,8 if m.group(2)=='P' else 22,15+20*(int(m.group(1))-1))
        elif name.startswith('daughtercard3'):
            if r.startswith('Rf_L2_'):
                j=int(r.rsplit('_',1)[1]);move(f,52.32 if j<6 else 74.32,21.19+25*(j//2) if j<6 else 21.19+25*((j-6)//2),0)
                # Odd neurons are the second amplifier in each vertical group.
                if j%2:move(f,52.32 if j<6 else 74.32,28.81+25*(j//2) if j<6 else 28.81+25*((j-6)//2),0)
            if r.startswith('R_BAL_2_'):
                j=int(r.rsplit('_',1)[1]);move(f,7+9*j,90,0)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('boards',nargs='+');a=ap.parse_args();reports=[]
    for arg in a.boards:
        p=pathlib.Path(arg)
        assert p.name.endswith('_repaired_unrouted.kicad_pcb') and p.parent.name=='two_layer','Only repaired candidates in two_layer are accepted'
        b=pcbnew.LoadBoard(str(p));assert b.GetCopperLayerCount()==2
        assert not list(b.GetTracks()),'Placement must precede routing'
        before=identity(b)
        fixed={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees()) for f in b.GetFootprints() if f.GetReference().startswith(('J_','H'))}
        edges=[str(d.GetStart())+str(d.GetEnd()) for d in b.GetDrawings() if d.GetLayer()==pcbnew.Edge_Cuts]
        apply(b,p.name);assert before==identity(b),'electrical identity changed'
        assert fixed=={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees()) for f in b.GetFootprints() if f.GetReference().startswith(('J_','H'))}
        assert edges==[str(d.GetStart())+str(d.GetEnd()) for d in b.GetDrawings() if d.GetLayer()==pcbnew.Edge_Cuts]
        pcbnew.SaveBoard(str(p),b);after=identity(pcbnew.LoadBoard(str(p)));assert before==after,'roundtrip identity changed'
        out=p.with_name(p.stem+'_placement_drc.json')
        subprocess.run(['kicad-cli','pcb','drc','--format','json','--all-track-errors','-o',str(out),str(p)],check=True)
        drc=json.loads(out.read_text());counts={}
        for v in drc['violations']:counts[v['type']]=counts.get(v['type'],0)+1
        report={'board':str(p),'before_identity_sha256':digest(before),'after_identity_sha256':digest(after),'identity_preserved':True,'headers_mounts_edges_preserved':True,'counts':counts,'placement_clean':not any(counts.get(k,0) for k in ['shorting_items','clearance','courtyards_overlap','solder_mask_bridge'])}
        reports.append(report);print(json.dumps(report))
    pathlib.Path('two_layer/placement_audit.json').write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
