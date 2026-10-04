#!/usr/bin/python3
"""Resume approved immutable motherboard copper with a verified real pass cap.
No promotion before complete strict audits. No placement or silkscreen mutation.
"""
from pathlib import Path
import collections, hashlib, json, re, signal, subprocess, time
import pcbnew as p
import route_repaired as route
import silk_refs
ROOT=Path(__file__).resolve().parent
RUN=ROOT/'economic_motherboard_long_run'
SOURCE=ROOT/'motherboard_adc_repaired.kicad_pcb'
FROZEN=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def point(q):return [q.x,q.y]
def freeze(b):
    fps=[]
    for f in b.GetFootprints():
        pads=sorted((q.GetNumber(),q.GetNetname(),point(q.GetPosition()),point(q.GetSize()),point(q.GetDrillSize()),q.GetShape(),q.GetAttribute(),q.GetOrientationDegrees(),q.GetLayerSet().FmtHex()) for q in f.Pads())
        fields=sorted((q.GetText(),point(q.GetPosition()),point(q.GetTextSize()),q.GetTextThickness(),q.GetTextAngle().AsDegrees(),q.GetLayer(),q.IsVisible()) for q in f.GetFields())
        fps.append((f.GetReference(),f.GetValue(),f.GetFPID().GetUniStringLibId(),point(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),pads,fields))
    drawings=sorted((str(q.GetClass()),q.GetLayer(),point(q.GetStart()),point(q.GetEnd()),q.GetWidth()) for q in b.GetDrawings())
    return {'footprints':sorted(fps),'drawings':drawings,'layers':b.GetCopperLayerCount(),'zones':b.GetAreaCount()}
def export_proof(b,dsn):
    assert p.ExportSpecctraDSN(b,str(dsn))
    s=dsn.read_text();w=s[s.rfind('(wiring'):]
    norm=lambda v:round(v,1)
    def xy(q):return (norm(p.ToMM(q.x)*1000),norm(-p.ToMM(q.y)*1000))
    def segment(layer,width,net,a,z):return (layer,norm(width),net,tuple(sorted((a,z))))
    expected=collections.Counter();ev=collections.Counter()
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):ev[(t.GetNetname(),xy(t.GetPosition()))]+=1
        else:expected[segment(b.GetLayerName(t.GetLayer()),p.ToMM(t.GetWidth())*1000,t.GetNetname(),xy(t.GetStart()),xy(t.GetEnd()))]+=1
    actual=collections.Counter()
    for layer,width,coords,net in re.findall(r'\(wire\s+\(path\s+(\S+)\s+([\d.]+)\s+([^)]*)\)\s*\(net\s+([^)]*)\)',w):
        nums=list(map(float,coords.split()));pts=list(zip(nums[::2],nums[1::2]));net=net.strip('"')
        for a,z in zip(pts,pts[1:]):actual[segment(layer,float(width),net,a,z)]+=1
    av=collections.Counter((net.strip('"'),(float(x),float(y))) for x,y,net in re.findall(r'\(via\s+"[^"]+"\s+([-\d.]+)\s+([-\d.]+)\s+\(net\s+([^)]*)\)',w))
    proof={'source_segments':sum(expected.values()),'dsn_segments':sum(actual.values()),'source_vias':sum(ev.values()),'dsn_vias':sum(av.values()),'missing_segments':len(expected-actual),'extra_segments':len(actual-expected),'missing_vias':len(ev-av),'extra_vias':len(av-ev),'export_coordinate_precision_um':.1}
    (RUN/'resume_export_proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    assert expected==actual and ev==av,proof
    s=re.sub(r'(\(rule\s*\(width\s+)[\d.]+',r'\g<1>250',s)
    s=re.sub(r'(\(clearance\s+)[\d.]+',r'\g<1>200',s)
    dsn.write_text(s)
    return proof

def main():
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    RUN.mkdir(exist_ok=True)
    assert sha(FROZEN)=='9f5510139d42ebc33c149f6d501c4caa0f98b091a723ec1e8a2e5959cfb14a77'
    b=p.LoadBoard(str(SOURCE));original=freeze(b);assert original==freeze(p.LoadBoard(str(FROZEN)))
    identity=route.checksum(b);dsn=RUN/'resume48.dsn';ses=RUN/'resume48.ses';candidate=RUN/'resume48.kicad_pcb'
    assert not ses.exists() and not candidate.exists(),'Distinct candidate paths required'
    proof=export_proof(b,dsn)
    jar=Path('/tmp/freerouting_actual48.jar');start=time.time()
    assert sha(jar)=='19d06499ff6424368d4861c2ede43849944d9cb62bf673cae7f5039ee6620c6d','Verified hard-bound jar required'
    result={'source_sha256':sha(SOURCE),'placement_sha256':sha(FROZEN),'resume_proof':proof,'router_sha256':sha(jar),'actual_pass_limit':48,'release_authorized':False}
    try:
        subprocess.run(['java','-Xmx10g','-jar',str(jar),'-de',str(dsn),'-do',str(ses),'--gui.enabled=false','-mt','1'],timeout=21600,check=True)
        assert ses.exists() and ses.stat().st_size>100
        assert p.ImportSpecctraSES(b,str(ses))
        assert identity==route.checksum(b) and original==freeze(b)
        for t in b.GetTracks():
            if isinstance(t,p.PCB_VIA):assert t.GetWidth(p.F_Cu)>=p.FromMM(.6) and t.GetDrillValue()>=p.FromMM(.3)
            else:assert t.GetWidth()>=p.FromMM(.2) and t.GetLayer() in (p.F_Cu,p.B_Cu)
        p.SaveBoard(str(candidate),b);candidate.with_suffix('.kicad_pro').write_text(SOURCE.with_suffix('.kicad_pro').read_text())
        drc=RUN/'resume48_drc.json'
        q=subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','-o',str(drc),str(candidate)],capture_output=True,text=True)
        (RUN/'resume48_drc.log').write_text(q.stdout+q.stderr)
        d=json.loads(drc.read_text());reloaded=p.LoadBoard(str(candidate));assert original==freeze(reloaded) and identity==route.checksum(reloaded)
        silk=silk_refs.audit_silk(reloaded);assert silk['clean']
        result.update(pipeline_completed=True,errors=sum(v.get('severity')=='error' for v in d['violations']),unconnected=len(d.get('unconnected_items',[])),warnings=sum(v.get('severity')=='warning' for v in d['violations']),categories=dict(collections.Counter(v['type'] for v in d['violations'])),silk=silk,candidate_sha256=sha(candidate),frozen_identity_verified=True)
    except Exception as e:
        result.update(pipeline_completed=False,error=repr(e));raise
    finally:
        result['seconds']=time.time()-start;(RUN/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
