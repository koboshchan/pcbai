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

def reference_quality(capture, window_us, minimum_ratio=2.):
 """Conservative leakage guard, NOT resistance estimation/open proof.
 window_us must match the capture metadata; old CSV without window needs
 an explicit known observation window. Mixed failures are never qualified.
 """
 reports=[]
 for (sense,sink),rows in sorted(capture.items()):
  if sink == 0:
   continue
  refs=capture.get((sense,0),[])
  values=[v for status,v in rows if status=='ok' and v is not None]
  ref_values=[v for status,v in refs if status=='ok' and v is not None]
  status='unqualified'
  if refs and len(values)==len(rows) and values:
   # Require the slowest pair repeat to be at least 2x faster than the
   # earliest reference fall, or the entire no-fall reference window.
   if all(s=='timeout' for s,_ in refs):
    limit=window_us
   elif len(ref_values)==len(refs):
    limit=min(ref_values)
   else:
    limit=None
   if limit is not None:
    status='sink_resolved' if max(values)*minimum_ratio < limit else 'leakage_limited'
  elif refs and rows and all(s=='timeout' for s,_ in rows):
   status='open_compatible_unquantified' if all(s=='timeout' for s,_ in refs) else 'leakage_limited'
  reports.append(dict(pair=(sense,sink),classification=status,
                      resistance_ohms=None,open_proven=False))
 return reports

def capture_window(path):
 """Reject mixed/absent observation windows instead of assuming 5 seconds."""
 with open(path,newline='') as f:
  windows={int(r['window_us']) for r in csv.DictReader(f)}
 if len(windows)!=1 or next(iter(windows))<=0:
  raise ValueError('one positive window_us required')
 return next(iter(windows))

if __name__=='__main__':
 golden,measured=read(sys.argv[1]),read(sys.argv[2])
 print(json.dumps(dict(comparison=compare(golden,measured),
                       golden_quality=reference_quality(golden,capture_window(sys.argv[1])),
                       measured_quality=reference_quality(measured,capture_window(sys.argv[2]))),indent=2))
