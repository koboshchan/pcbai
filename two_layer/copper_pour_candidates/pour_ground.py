#!/usr/bin/python3
"""Isolated GND pour helper. Does not modify its source or promote outputs.
Usage: pour_ground.py SOURCE OUTPUT PROJECT [--stitch]
Requires system pcbnew and kicad-cli. Input project must be the actual effective
project rules; limits are only strengthened. All old zones are preserved.
"""
import argparse,collections,hashlib,json,subprocess,shutil,tempfile,re
from pathlib import Path
import pcbnew as p

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def identity(b):
    # Whole serialized footprints preserve UUIDs, pads, fields, silk, positions.
    with tempfile.TemporaryDirectory() as td:
        f=Path(td)/'identity.kicad_pcb'; p.SaveBoard(str(f),b); text=f.read_text()
    chunks=[]
    for m in re.finditer(r'\n\t\(footprint ',text):
        start=m.start()+2; depth=0; quoted=False; escaped=False
        for end in range(start,len(text)):
            c=text[end]
            if escaped: escaped=False; continue
            if c=='\\' and quoted: escaped=True; continue
            if c=='"': quoted=not quoted
            if not quoted:
                if c=='(': depth+=1
                elif c==')':
                    depth-=1
                    if depth==0: chunks.append(text[start:end+1]); break
    assert len(chunks)==len(list(b.GetFootprints())), 'Footprint extraction failed'
    return hashlib.sha256('\n'.join(sorted(chunks)).encode()).hexdigest()
def drc(path,report):
    r=subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','--output',str(report),str(path)],capture_output=True,text=True)
    report.with_suffix('.log').write_text(r.stdout+r.stderr)
    if not report.exists(): raise RuntimeError(r.stdout+r.stderr)
    j=json.loads(report.read_text()); return {'errors':sum(v['severity']=='error' for v in j['violations']),'opens':len(j['unconnected_items']),'warnings':sum(v['severity']=='warning' for v in j['violations']),'categories':dict(collections.Counter(v['type'] for v in j['violations']))}
def strengthen(project):
    j=json.loads(Path(project).read_text()); d=j['board']['design_settings']
    if d.get('drc_exclusions'): raise ValueError('Input contains DRC exclusions')
    r=d['rules']
    for key,val in {'min_clearance':.2,'min_copper_edge_clearance':.5,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_via_annular_width':.15,'min_text_height':.8,'min_text_thickness':.12}.items(): r[key]=max(r.get(key,0),val)
    for c in j['net_settings']['classes']:
        for k,v in {'clearance':.2,'via_diameter':.6,'via_drill':.3}.items(): c[k]=max(c.get(k,0),v)
    return j

def apply(source,out,project,stitch=False):
    source=Path(source).resolve(); out=Path(out).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    assert source!=out
    original=sha(source); b=p.LoadBoard(str(source)); before=identity(b)
    out.with_suffix('.kicad_pro').write_text(json.dumps(strengthen(project),indent=2)+'\n')
    rules=source.with_suffix('.kicad_dru')
    if rules.exists(): shutil.copy2(rules,out.with_suffix('.kicad_dru'))
    outline=p.SHAPE_POLY_SET()
    if not b.GetBoardPolygonOutlines(outline,False) or outline.OutlineCount()==0: raise ValueError('No valid exact board outline')
    net=b.FindNet('GND')
    if not net or net.GetNetCode()==0: raise ValueError('No GND net')
    old_zone_count=len(list(b.Zones()))
    for layer in (p.F_Cu,p.B_Cu):
        z=p.ZONE(b); z.SetLayer(layer); z.SetNetCode(net.GetNetCode()); z.SetLocalClearance(p.FromMM(.2)); z.SetPadConnection(p.ZONE_CONNECTION_THT_THERMAL); z.SetThermalReliefGap(p.FromMM(.25)); z.SetThermalReliefSpokeWidth(p.FromMM(.3)); z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS); z.SetMinThickness(p.FromMM(.2)); z.SetAssignedPriority(0)
        for i in range(outline.OutlineCount()):
            chain=outline.Outline(i); oi=z.Outline().NewOutline()
            for k in range(chain.PointCount()): q=chain.CPoint(k); z.Outline().Append(q.x,q.y,oi)
            for h in range(outline.HoleCount(i)):
                hi=z.Outline().NewHole(oi); hole=outline.Hole(i,h)
                for k in range(hole.PointCount()): q=hole.CPoint(k); z.Outline().Append(q.x,q.y,oi,hi)
        b.Add(z)
    p.SaveBoard(str(out),b); result=drc(out,out.with_name(out.stem+'_poured_drc.json'))
    accepted_vias=[]
    # Only try sparse stitches inside existing filled GND on both sides. Full
    # DRC gating rejects the entire via if it adds any error or an open.
    if stitch and result['errors']==0 and result['opens']==0:
        b=p.LoadBoard(str(out)); box=b.GetBoardEdgesBoundingBox(); zones=list(b.Zones())[-2:]
        for fx,fy in ((.25,.25),(.75,.25),(.25,.75),(.75,.75)):
            pos=p.VECTOR2I(int(box.GetX()+box.GetWidth()*fx),int(box.GetY()+box.GetHeight()*fy))
            if not all(z.HitTestFilledArea(z.GetLayer(),pos) for z in zones): continue
            checkpoint=out.read_bytes(); via=p.PCB_VIA(b); via.SetPosition(pos); via.SetWidth(p.FromMM(.6)); via.SetDrill(p.FromMM(.3)); via.SetViaType(p.VIATYPE_THROUGH); via.SetLayerPair(p.F_Cu,p.B_Cu); via.SetNetCode(net.GetNetCode()); b.Add(via); p.SaveBoard(str(out),b)
            tested=drc(out,out.with_name(out.stem+'_stitch_trial_drc.json'))
            if tested['errors']==0 and tested['opens']==0: accepted_vias.append([p.ToMM(pos.x),p.ToMM(pos.y)])
            else: out.write_bytes(checkpoint)
            b=p.LoadBoard(str(out)); zones=list(b.Zones())[-2:]
    result=drc(out,out.with_name(out.stem+'_final_drc.json')); final=p.LoadBoard(str(out))
    result.update(source_sha256=original,final_sha256=sha(out),source_unchanged=sha(source)==original,footprint_identity_sha256=before,footprint_identity_unchanged=identity(final)==before,old_zone_count=old_zone_count,final_zone_count=len(list(final.Zones())),accepted_stitch_positions_mm=accepted_vias,release_authorized=False)
    assert result['source_unchanged'] and result['footprint_identity_unchanged']
    out.with_name(out.stem+'_audit.json').write_text(json.dumps(result,indent=2)+'\n'); return result
if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('source');a.add_argument('output');a.add_argument('project');a.add_argument('--stitch',action='store_true');v=a.parse_args();print(json.dumps(apply(v.source,v.output,v.project,v.stitch),indent=2))
