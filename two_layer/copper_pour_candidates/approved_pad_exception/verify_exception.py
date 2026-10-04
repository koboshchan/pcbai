#!/usr/bin/python3
"""Isolated actual KiCad precedence/negative controls and filled copper geometry audit."""
import sys,json,shutil
from pathlib import Path
import pcbnew as p
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from pour_ground import drc,sha
sys.path.insert(0,'/tmp/approved-edge-shapely')
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
R=Path(__file__).resolve().parent

def chain(c):return [(p.ToMM(c.CPoint(i).x),p.ToMM(c.CPoint(i).y)) for i in range(c.PointCount())]
def outlines(s):
    return [Polygon(chain(s.Outline(i)),[chain(s.Hole(i,h)) for h in range(s.HoleCount(i))]) for i in range(s.OutlineCount())]
def geometry(folder):
    b=p.LoadBoard(str(folder/'ground_candidate.kicad_pcb')); outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline,False)
    polys=outlines(outline); boundary=unary_union([x.boundary for x in polys]); manifest=json.loads((folder/'pad_exception_manifest.json').read_text()); exempt={x['uuid'] for x in manifest['pads']}; records=[]
    for f in b.GetFootprints():
        for pad in f.Pads():
            for layer in (p.F_Cu,p.B_Cu):
                if not pad.IsOnLayer(layer):continue
                shape=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(shape,layer,0,100,p.ERROR_OUTSIDE)
                copper=unary_union(outlines(shape));dist=copper.distance(boundary)
                records.append({'type':'pad','uuid':pad.m_Uuid.AsString(),'reference':f.GetReference(),'number':pad.GetNumber(),'layer':p.LayerName(layer),'distance_mm':dist,'minimum_mm':.4 if pad.m_Uuid.AsString() in exempt else .5})
    for track in b.GetTracks():
        if isinstance(track,p.PCB_VIA):
            # Circular radial extent at exact center, no polygon approximation.
            q=track.GetPosition();dist=boundary.distance(LineString([(p.ToMM(q.x),p.ToMM(q.y)),(p.ToMM(q.x),p.ToMM(q.y))]))-p.ToMM(track.GetWidth(p.F_Cu))/2
        else:
            a=track.GetStart();z=track.GetEnd();dist=boundary.distance(LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))]))-p.ToMM(track.GetWidth())/2
        records.append({'type':'via' if isinstance(track,p.PCB_VIA) else 'track','uuid':track.m_Uuid.AsString(),'distance_mm':dist,'minimum_mm':.5})
    for zone in b.Zones():
        for layer in (p.F_Cu,p.B_Cu):
            if not zone.IsOnLayer(layer):continue
            filled=zone.GetFilledPolysList(layer);copper=unary_union(outlines(filled));dist=copper.distance(boundary) if not copper.is_empty else None
            records.append({'type':'zone','uuid':zone.m_Uuid.AsString(),'layer':p.LayerName(layer),'distance_mm':dist,'minimum_mm':.5,'local_clearance_mm':p.ToMM(zone.GetLocalClearance()),'thermal_mode':zone.GetPadConnection(),'island_removal':zone.GetIslandRemovalMode()})
    # 0.1um approximation/tolerance, DRC remains the authoritative exact gate.
    failures=[r for r in records if r['distance_mm'] is not None and r['distance_mm']+0.00011<r['minimum_mm']]
    result={'outline_count':outline.OutlineCount(),'cutout_counts':[outline.HoleCount(i) for i in range(outline.OutlineCount())],'approximation_tolerance_mm':.00011,'all_pass':not failures,'failures':failures,'records':records}
    (folder/'copper_distance_audit.json').write_text(json.dumps(result,indent=2)+'\n');assert not failures,failures[:3]
    return {'all_pass':True,'minimum_exempt_pad_mm':min(r['distance_mm'] for r in records if r['type']=='pad' and r['uuid'] in exempt),'minimum_nonexempt_mm':min(r['distance_mm'] for r in records if r['distance_mm'] is not None and not(r['type']=='pad' and r['uuid'] in exempt))}

def controls(folder):
    out=R/'negative_controls';out.mkdir(exist_ok=True);source=folder/'ground_candidate.kicad_pcb';original=sha(source);reports=[]
    for case in ('ordinary_pad_at_0p4','track_at_0p4','via_at_0p4','selected_pad_at_0p35','exception_disabled','exception_threshold_0p41'):
        path=out/(case+'.kicad_pcb');b=p.LoadBoard(str(source));uid=None
        if case.startswith('ordinary'):
            f=p.FOOTPRINT(b);f.SetReference('NEGATIVE_ORDINARY_HEADER');b.Add(f);item=p.PAD(f);item.SetNumber('A1');item.SetAttribute(p.PAD_ATTRIB_SMD);item.SetShape(p.PAD_SHAPE_RECT);item.SetSize(p.VECTOR2I(p.FromMM(.6),p.FromMM(.6)));layers=p.LSET();layers.AddLayer(p.F_Cu);item.SetLayerSet(layers);item.SetPosition(p.VECTOR2I(p.FromMM(.7),p.FromMM(10)));f.Add(item);uid=item.m_Uuid.AsString()
        elif case.startswith('track'):
            item=p.PCB_TRACK(b);item.SetStart(p.VECTOR2I(p.FromMM(.5),p.FromMM(10)));item.SetEnd(p.VECTOR2I(p.FromMM(.5),p.FromMM(11)));item.SetWidth(p.FromMM(.2));item.SetLayer(p.F_Cu);b.Add(item);uid=item.m_Uuid.AsString()
        elif case.startswith('via'):
            item=p.PCB_VIA(b);item.SetPosition(p.VECTOR2I(p.FromMM(.7),p.FromMM(10)));item.SetWidth(p.FromMM(.6));item.SetDrill(p.FromMM(.3));item.SetViaType(p.VIATYPE_THROUGH);item.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(item);uid=item.m_Uuid.AsString()
        elif case.startswith('selected'):
            f=next(f for f in b.GetFootprints() if f.GetReference()=='J_STRADDLE_EDGE');item=next(x for x in f.Pads() if x.GetNumber()=='A1');pos=item.GetPosition();item.SetPosition(p.VECTOR2I(pos.x,pos.y+p.FromMM(.05)));uid=item.m_Uuid.AsString()
        p.SaveBoard(str(path),b);shutil.copy2(source.with_suffix('.kicad_pro'),path.with_suffix('.kicad_pro'));text=source.with_suffix('.kicad_dru').read_text()
        if case=='exception_disabled':text='(version 1)\n(rule "Global all copper edge 0.5mm" (constraint edge_clearance (min 0.5mm)))\n'
        elif case=='exception_threshold_0p41':text=text.replace('(min 0.4mm)','(min 0.41mm)')
        path.with_suffix('.kicad_dru').write_text(text);counts=drc(path,path.with_suffix('.json'));data=json.loads(path.with_suffix('.json').read_text());edges=[v for v in data['violations'] if v['type']=='copper_edge_clearance'];target=[v for v in edges if uid and any(x.get('uuid')==uid for x in v.get('items',[]))]
        assert len(edges)==76 if case in ('exception_disabled','exception_threshold_0p41') else len(target)>=1,(case,edges[:2],uid)
        expected='.4' if case.startswith('selected') else '.5'
        if target:assert ('0.4000' if expected=='.4' else '0.5000') in target[0]['description'],target
        reports.append({'case':case,'counts':counts,'target_uuid':uid,'target_edge_violations':target,'edge_violation_count':len(edges),'passed':True})
    assert sha(source)==original
    (out/'RESULTS.json').write_text(json.dumps(reports,indent=2)+'\n');return reports
if __name__=='__main__':
    results=json.loads((R/'RESULTS.json').read_text());audits={}
    for r in results:
        audits[r['board']]=geometry(R/r['board']);print(r['board'],audits[r['board']],flush=True)
    controls(R/results[0]['board']);(R/'VERIFICATION.json').write_text(json.dumps({'kicad_version':'10.0.6','geometry':audits,'negative_controls_pass':True},indent=2)+'\n')
