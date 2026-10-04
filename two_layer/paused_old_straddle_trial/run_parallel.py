#!/usr/bin/python3
"""Run independent two-layer CAD jobs in parallel on kat-box only."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess, json
ROOT=Path(__file__).resolve().parent
BOARDS=['motherboard']+[f'daughtercard1{c}_weights_l1' for c in 'abcd']+['daughtercard2_relu_l1','daughtercard3_weights_l2_wta']
def run(name):
 with (ROOT/(name+'_pipeline.log')).open('w') as log:
  subprocess.run(['/usr/bin/python3',str(ROOT/'convert.py'),'prep',name],stdout=log,stderr=subprocess.STDOUT,check=True)
  subprocess.run(['java','-Xmx5g','-jar',str(ROOT/'freerouting_bounded.jar'),'-de',str(ROOT/(name+'.dsn')),'-do',str(ROOT/(name+'.ses')),'--gui.enabled=false','-mp','24','-mt','1'],stdout=log,stderr=subprocess.STDOUT,timeout=1800,check=True)
  subprocess.run(['/usr/bin/python3',str(ROOT/'convert.py'),'finish',name],stdout=log,stderr=subprocess.STDOUT,check=True)
 return name
if __name__=='__main__':
 import sys
 with ThreadPoolExecutor(max_workers=7) as pool:
  futures={pool.submit(run,n):n for n in sys.argv[1:] or BOARDS}
  for f,n in futures.items():
   try: print('completed',f.result(),flush=True)
   except Exception as e: print('failed',n,str(e),flush=True)
