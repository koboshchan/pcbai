#!/usr/bin/env python3
"""Compare repeated real captures to golden-board capture, report raw timings."""
import csv,statistics,json,sys
def read(path):
 d={}
 with open(path,newline='') as f:
  for r in csv.DictReader(f):
   key=(int(r['sense']),int(r['sink']))
   d.setdefault(key,[]).append((r['status'],float(r['fall_us']) if r['fall_us'] else None))
 return d
def compare(golden,measured,tolerance=.20):
 reports=[]
 for key in sorted(set(golden)|set(measured)):
  g=golden.get(key,[]);m=measured.get(key,[])
  if not g or not m:reports.append(dict(pair=key,status='missing'));continue
  gs={s for s,_ in g};ms={s for s,_ in m}
  if gs!={'ok'} or ms!={'ok'}:
   reports.append(dict(pair=key,status='same_status_unquantified' if gs==ms else 'status_changed',golden=list(gs),measured=list(ms)));continue
  gv=[x for _,x in g];mv=[x for _,x in m];base=statistics.median(gv);actual=statistics.median(mv)
  mad=statistics.median(abs(x-base) for x in gv);limit=max(5.,abs(base)*tolerance,6*mad)
  reports.append(dict(pair=key,status='changed' if abs(actual-base)>limit else 'within_band',golden_us=base,measured_us=actual,limit_us=limit))
 return reports
if __name__=='__main__':
 print(json.dumps(compare(read(sys.argv[1]),read(sys.argv[2])),indent=2))
