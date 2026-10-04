#!/usr/bin/python3
from pathlib import Path
import json,os,signal,subprocess
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
 assert not (ROOT/'router_launcher_v2.json').exists()
 signal.signal(signal.SIGHUP,signal.SIG_IGN)
 with (ROOT/'route_log_v2.txt').open('xb') as log:
  proc=subprocess.Popen(['/usr/bin/python3','-u',str(ROOT/'route_v2.py')],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 (ROOT/'router_launcher_v2.json').write_text(json.dumps({'pid':proc.pid,'host':'kat-box','detached':True})+'\n')
 print(proc.pid,flush=True)
