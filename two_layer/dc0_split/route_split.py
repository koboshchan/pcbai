#!/usr/bin/python3
from pathlib import Path
import pcbnew as p,json,hashlib,subprocess,time,re,collections,os
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
R=Path(__file__).resolve().parent

def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def drc(f):
 out=f.with_name(f.stem+'_drc.json');q=subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(out),str(f)],capture_output=True,text=True);f.with_name(f.stem+'_drc.log').write_text(q.stdout+q.stderr);d=json.loads(out.read_text());return {'errors':sum(v['severity']=='error' for v in d['violations']),'unconnected':len(d['unconnected_items']),'warnings':sum(v['severity']=='warning' for v in d['violations']),'categories':dict(collections.Counter(v['type'] for v in d['violations']))}
def main():
 result={'release_authorized':False,'pid':os.getpid(),'boards':{}};start=time.time()
 try:
  for n in ['DC0','motherboard']:
   src=R/(n+'.kicad_pcb');b=p.LoadBoard(str(src));frozen=refs.physical(b);assert silk.audit(b)['clean'];pre=drc(src);assert pre['errors']==0,pre
   run=R/('route_'+n);run.mkdir(exist_ok=False);dsn=run/(n+'.dsn');ses=dsn.with_suffix('.ses');assert p.ExportSpecctraDSN(b,str(dsn))
   text=dsn.read_text();text=re.sub(r'(\(rule\s*\(width\s+)[\d.]+',r'\g<1>250',text);text=re.sub(r'(\(clearance\s+)[\d.]+',r'\g<1>200',text);dsn.write_text(text)
   jar=Path('/tmp/freerouting_actual48.jar');assert sha(jar)=='19d06499ff6424368d4861c2ede43849944d9cb62bf673cae7f5039ee6620c6d'
   record={'source_sha256':sha(src),'dsn_sha256':sha(dsn),'actual_pass_limit':48,'placement':pre};result['boards'][n]=record;(R/'ROUTING_STATUS.json').write_text(json.dumps(result,indent=2))
   with (run/'router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar',str(jar),'-de',str(dsn),'-do',str(ses),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,timeout=21600,check=True)
   assert ses.exists() and p.ImportSpecctraSES(b,str(ses));assert refs.physical(b)==frozen
   target=run/(n+'_routed.kicad_pcb');p.SaveBoard(str(target),b);target.with_suffix('.kicad_pro').write_bytes(src.with_suffix('.kicad_pro').read_bytes())
   if src.with_suffix('.kicad_dru').exists():target.with_suffix('.kicad_dru').write_bytes(src.with_suffix('.kicad_dru').read_bytes())
   from pour_ground import apply
   target=apply(target);stats=drc(target);record.update(stats,candidate_sha256=sha(target),physical_identity=True,silk_clean=silk.audit(p.LoadBoard(str(target)))['clean'],candidate=str(target));record['strict_pass']=stats['errors']==0 and stats['unconnected']==0 and record['silk_clean'];(R/'ROUTING_STATUS.json').write_text(json.dumps(result,indent=2))
  result['strict_pass']=all(v['strict_pass'] for v in result['boards'].values());result['pipeline_completed']=True
 except Exception as e:result.update(error=repr(e),pipeline_completed=False)
 finally:
  subprocess.run(['/usr/bin/python3',str(R/'snapshot_remote.py'),'after'],check=True)
  result['elapsed_seconds']=time.time()-start;(R/'FINAL.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
