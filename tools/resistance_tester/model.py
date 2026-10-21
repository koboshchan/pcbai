#!/usr/bin/env python3
"""Full coupled RC fingerprints, NOT pairwise R=t/C.
Requires numpy+scipy. Model every tester C and finite 4.7k sink, plus DUT nets.
Nonlinear omitted devices require a known-good populated-board baseline.
"""
import argparse,csv,json,itertools
from pathlib import Path
import numpy as np
from scipy.linalg import eigh,solve

def stamp(m,a,b,value):
 if a is not None:m[a,a]+=value
 if b is not None:m[b,b]+=value
 if a is not None and b is not None:m[a,b]-=value;m[b,a]-=value

class Network:
 def __init__(self,dut,port_nets,series=4700.,cap=1e-7,parasitic=1e-12):
  if len(port_nets)!=20 or len(set(port_nets))!=20:raise ValueError("20 distinct test nets")
  self.names=sorted(set(port_nets)|{e[k] for kind in ['resistors','capacitors'] for e in dut.get(kind,[]) for k in ['a','b'] if e[k]})
  self.idx={s:i for i,s in enumerate(self.names)};self.ports=[self.idx[n] for n in port_nets];self.rs=series
  n=len(self.names);self.g=np.eye(n)*1e-14;self.c=np.eye(n)*parasitic
  for i in self.ports:self.c[i,i]+=cap
  for kind,m in [('resistors',self.g),('capacitors',self.c)]:
   for e in dut.get(kind,[]):
    # DUT net called GND is floating unless wired to an explicit test port.
    a=self.idx.get(e['a']);b=self.idx.get(e['b'])
    if a is not None and b is not None:
     stamp(m,a,b,1/e['value'] if kind=='resistors' else e['value'])
 def response(self,g,v0,force=None):
  force=np.zeros(len(g)) if force is None else force
  vss=solve(g,force,assume_a='pos')
  w,q=eigh(g,self.c);w=np.maximum(w,0)
  coeff=q.T@self.c@(v0-vss)
  return lambda t:vss+q@(np.exp(-w*t)*coeff)
 def precharge(self,voltage=3.3,seconds=.05):
  g=self.g.copy();force=np.zeros(len(g))
  for p in self.ports:g[p,p]+=1/self.rs;force[p]+=voltage/self.rs
  return self.response(g,np.zeros(len(g)),force)(seconds)
 def sink_response(self,sink,v0):
  g=self.g.copy();g[self.ports[sink],self.ports[sink]]+=1/self.rs
  return self.response(g,v0)
 def crossing(self,sense,sink,threshold=1.3,timeout=5.,v0=None):
  v0=self.precharge() if v0 is None else v0
  f=self.sink_response(sink,v0);i=self.ports[sense]
  if v0[i]<=threshold:return 0.,'precharge_failed'
  # Non-monotone passive networks can have multiple crossings. Locate FIRST.
  times=np.r_[0,np.geomspace(1e-8,timeout,500)]
  previous=0.
  for t in times[1:]:
   if f(t)[i]<=threshold:
    lo,hi=previous,t
    for _ in range(40):
     mid=(lo+hi)/2
     if f(mid)[i]>threshold:lo=mid
     else:hi=mid
    return (lo+hi)/2,'ok'
   previous=t
  return None,'timeout'
 def fingerprints(self,threshold=1.3,timeout=5.):
  v0=self.precharge()
  # Same sink drives 19 sense nodes, so diagonalization is reused.
  responses=[self.sink_response(s,v0) for s in range(20)]
  times=np.r_[0,np.geomspace(1e-8,timeout,500)]
  waves=[np.array([f(t) for t in times]) for f in responses]
  for a,b in itertools.combinations(range(20),2):
   for sense,sink in [(a,b),(b,a)]:
    p=self.ports[sense];w=waves[sink][:,p]
    hits=np.flatnonzero(w<=threshold)
    if not len(hits):yield [a+1,b+1,sense+1,sink+1,0,'','timeout'];continue
    k=int(hits[0])
    if k==0:yield [a+1,b+1,sense+1,sink+1,0,0,'precharge_failed'];continue
    lo,hi=times[k-1],times[k]
    for _ in range(35):
     mid=(lo+hi)/2
     if responses[sink](mid)[p]>threshold:lo=mid
     else:hi=mid
    yield [a+1,b+1,sense+1,sink+1,0,(lo+hi)*.5e6,'ok']

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('netlist');ap.add_argument('ports');ap.add_argument('output');ap.add_argument('--threshold',type=float,default=1.3);ap.add_argument('--timeout',type=float,default=5.);args=ap.parse_args()
 dut=json.loads(Path(args.netlist).read_text());ports=json.loads(Path(args.ports).read_text())['port_nets']
 n=Network(dut,ports)
 with open(args.output,'w') as f:
  w=csv.writer(f);w.writerow(['pair_a','pair_b','sense','sink','repeat','fall_us','status']);w.writerows(n.fingerprints(args.threshold,args.timeout))
 print('380 directed fingerprints, resistor-only/nonlinear-omitted model; calibrate threshold and use golden board')
