#!/usr/bin/python3
"""Run explicit repaired CPU routing candidates on kat-box.
No root originals or unchanged-netlist pipeline. No Gerber release here.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import argparse,json,subprocess,time
ROOT=Path(__file__).resolve().parent

def run(path):
    path=Path(path).resolve();stem=path.name.replace('_repaired_unrouted.kicad_pcb','')
    log=ROOT/(stem+'_route.log');ses=ROOT/(stem+'_repaired.ses')
    start=time.time();result={'candidate':str(path),'release_ready':False,'started':start}
    try:
        with log.open('w') as output:
            subprocess.run(['/usr/bin/python3',str(ROOT/'route_repaired.py'),'prepare',str(path)],stdout=output,stderr=subprocess.STDOUT,check=True)
            dsn=ROOT/(stem+'_repaired.dsn')
            subprocess.run(['java','-Xmx6g','-jar',str(ROOT/'freerouting_bounded.jar'),'-de',str(dsn),'-do',str(ses),'--gui.enabled=false','-mp','12','-mt','1'],stdout=output,stderr=subprocess.STDOUT,timeout=3600,check=True)
            assert ses.exists() and ses.stat().st_size>100,'No usable session'
            subprocess.run(['/usr/bin/python3',str(ROOT/'route_repaired.py'),'finish',str(path),'--ses',str(ses)],stdout=output,stderr=subprocess.STDOUT,check=True)
        result['pipeline_completed']=True
    except Exception as exc:result.update(pipeline_completed=False,error=str(exc))
    result['seconds']=time.time()-start
    (ROOT/(stem+'_route_run.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);parser.add_argument('boards',nargs='+');args=parser.parse_args()
    assert 1<=args.workers<=6,'Reserve RAM for native Java and GPU model host buffers'
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs=[pool.submit(run,path) for path in args.boards]
        for future in as_completed(jobs):print(json.dumps(future.result()),flush=True)
