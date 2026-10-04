#!/usr/bin/python3
"""Bounded explicit Economic motherboard route, preserving audited silk."""
from pathlib import Path
import json,time,subprocess,hashlib,os
import route_repaired as route
import silk_refs
ROOT=Path(__file__).resolve().parent
PCB=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def main():
 placement=json.loads((ROOT/'economic_motherboard_placement.json').read_text())
 assert placement['placement_errors']==0 and placement['silk']['clean']
 assert hashlib.sha256(PCB.read_bytes()).hexdigest()==placement['pcb_sha256']
 start=time.time();dsn=route.prepare(PCB);ses=ROOT/'motherboard_adc_repaired.ses'
 if ses.exists():ses.rename(ROOT/'economic_motherboard_previous.ses')
 result={'release_authorized':False,'placement_sha256':placement['pcb_sha256']}
 try:
  subprocess.run(['java','-Xmx6g','-jar',os.environ.get('ECONOMIC_ROUTER_JAR',str(ROOT/'freerouting_bounded.jar')),'-de',str(dsn),'-do',str(ses),'--gui.enabled=false','-mp','4','-mt','1'],timeout=3600,check=True)
  assert ses.exists() and ses.stat().st_size>100
  silk_refs.apply_silk=lambda b:silk_refs.audit_silk(b)
  route.finish(PCB,ses)
  result['pipeline_completed']=True
 except Exception as exc:
  result.update(pipeline_completed=False,error=str(exc));raise
 finally:
  result['seconds']=time.time()-start
  (ROOT/'economic_motherboard_route_run.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
