#!/usr/bin/python3
"""Persistent bounded router of the isolated restored and renamed motherboard."""
from pathlib import Path
import collections,hashlib,json,os,re,signal,subprocess,time
import pcbnew as p
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
import silk_refs as s
ROOT=Path(__file__).resolve().parent
RUN=ROOT/'route_run_v2'
SOURCE=ROOT/'restored_shortrefs_v2.kicad_pcb'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def frozen(b):
 def pt(v):return [v.x,v.y]
 return {'physical':refs.physical(b),'fields':{str(f.m_Uuid.AsString()):[(q.GetText(),pt(q.GetPosition()),pt(q.GetTextSize()),q.GetTextThickness(),q.GetTextAngle().AsDegrees(),q.GetLayer(),q.IsVisible(),q.IsMirrored()) for q in f.GetFields()] for f in b.GetFootprints()},'drawings':sorted((str(q.GetClass()),q.GetLayer(),pt(q.GetStart()),pt(q.GetEnd()),q.GetWidth()) for q in s.board_drawings(b)),'layers':b.GetCopperLayerCount(),'zones':b.GetAreaCount()}
def drc(path):
 out=path.with_name(path.stem+'_drc.json');q=subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(out),str(path)],capture_output=True,text=True)
 path.with_name(path.stem+'_drc.log').write_text(q.stdout+q.stderr);d=json.loads(out.read_text())
 return d,{'errors':sum(v.get('severity')=='error' for v in d['violations']),'unconnected':len(d.get('unconnected_items',[])),'warnings':sum(v.get('severity')=='warning' for v in d['violations']),'categories':dict(collections.Counter(v['type'] for v in d['violations']))}
def main():
 signal.signal(signal.SIGHUP,signal.SIG_IGN);RUN.mkdir(exist_ok=False)
 audit=json.loads((ROOT/'prepared_audit_v2.json').read_text());assert sha(SOURCE)==audit['candidate_sha256'] and audit['errors']==0 and audit['silk']['clean']
 b=p.LoadBoard(str(SOURCE));identity=frozen(b);assert not list(b.GetTracks())
 dsn=RUN/'fresh_restored_shortrefs_v2.dsn';ses=dsn.with_suffix('.ses');candidate=RUN/'routed_shortrefs_v2.kicad_pcb'
 assert p.ExportSpecctraDSN(b,str(dsn));text=dsn.read_text();w=text[text.rfind('(wiring'):];assert '(wire ' not in w and '(via ' not in w
 text=re.sub(r'(\(rule\s*\(width\s+)[\d.]+',r'\g<1>250',text);text=re.sub(r'(\(clearance\s+)[\d.]+',r'\g<1>200',text);dsn.write_text(text)
 jar=Path('/tmp/freerouting_actual48.jar');assert sha(jar)=='19d06499ff6424368d4861c2ede43849944d9cb62bf673cae7f5039ee6620c6d'
 result={'source_sha256':sha(SOURCE),'dsn_sha256':sha(dsn),'router_sha256':sha(jar),'actual_pass_limit':48,'pid':os.getpid(),'release_authorized':False,'source_copper_segments':0,'source_vias':0};start=time.time();(RUN/'started_v2.json').write_text(json.dumps(result,indent=2)+'\n')
 try:
  subprocess.run(['java','-Xmx12g','-jar',str(jar),'-de',str(dsn),'-do',str(ses),'--gui.enabled=false','-mt','1'],timeout=21600,check=True)
  assert ses.exists() and ses.stat().st_size>100 and p.ImportSpecctraSES(b,str(ses));assert frozen(b)==identity
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):assert t.GetWidth(p.F_Cu)>=p.FromMM(.6) and t.GetDrillValue()>=p.FromMM(.3)
   else:assert t.GetWidth()>=p.FromMM(.2) and t.GetLayer() in (p.F_Cu,p.B_Cu)
  p.SaveBoard(str(candidate),b);candidate.with_suffix('.kicad_pro').write_text(SOURCE.with_suffix('.kicad_pro').read_text());d,stats=drc(candidate);loaded=p.LoadBoard(str(candidate));assert frozen(loaded)==identity and silk.audit(loaded)['clean']
  result.update(stats,candidate_sha256=sha(candidate),frozen_identity_verified=True,silk=silk.audit(loaded),pipeline_completed=True)
 except Exception as e:result.update(error=repr(e),pipeline_completed=False);raise
 finally:
  result['seconds']=time.time()-start;(RUN/'result_v2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
