"""Exact coupled linear RC state propagation for explicit bit-plane schedule."""
import json,time
from pathlib import Path
import numpy as np
import torch
from scipy.linalg import expm
from model import coefficients,loaded
from cuda_mc import tensor,draw,run
H=Path(__file__).resolve().parent
c=json.loads((H/'circuit.json').read_text());d=np.load(H/'data/test.npz');raw=d['X'].astype(float);y=d['y'];X=tensor(raw)
W,B,P,PB,G=coefficients(c['layer1'],64)
C=np.diag(G.sum(0))-G.T@P
rs=10050.;K=np.eye(64)/rs+C
out=[]
for bits in [6,8]:
 commands=np.round(raw/5*(2**bits-1)).astype(int)
 for cap in [.8e-6,1e-6,1.2e-6]:
  # LSB first, minimum dwell equals one64bit SPI shift at20MHz.
  times=np.array([64/20e6*2**k for k in range(bits)])
  eq=[tensor(np.linalg.solve(K,((commands>>k)&1).T*5/rs+(G.T@PB)[:,None]).T) for k in range(bits)]
  Es=[tensor(expm(-K*t/cap)) for t in times]
  F=torch.eye(64,device='cuda',dtype=torch.float64);v=torch.zeros_like(X)
  for E,e in zip(Es,eq):v=v@E.T+e@(torch.eye(64,device='cuda',dtype=torch.float64)-E).T;F=E@F
  v=torch.linalg.solve(torch.eye(64,device='cuda',dtype=torch.float64)-F,v.T).T
  vals=[];acc=[];ripplemax=0.;mean=tensor(np.round(raw/5*(2**bits-1))/(2**bits-1)*5)
  T=np.linalg.solve(np.eye(64)+rs*C,np.eye(64));q=T@(rs*G.T@PB)
  average=mean@tensor(T).T+tensor(q)
  for k in range(bits):
   E=tensor(expm(-K*times[k]/cap/4))
   for sample in range(4):
    v=(v-eq[k])@E.T+eq[k]
    ripplemax=max(ripplemax,float((v-average).abs().max()))
    # Re-express nodevoltages as static commands solely to reuse exact nonlinear chain.
    source=(v-tensor(q))@tensor(np.linalg.inv(T)).T
    adc,s,h=run(source,[draw(c,None)],c)
    acc.append(float((adc[0].argmax(1).cpu().numpy()==y).mean()))
  out.append({'bits':bits,'capacitance_F':cap,'period_s':float(times.sum()),'frequency_Hz':float(1/times.sum()),'samples_per_plane':4,'max_abs_input_deviation_V':ripplemax,'phase_accuracy_min':min(acc),'phase_accuracy_mean':float(np.mean(acc)),'phase_accuracy_max':max(acc),'phase_accuracies':acc})
  print(out[-1],flush=True)
(H/'pwm_ripple.json').write_text(json.dumps({'slowest_nominal_timeconstant_s':float(1e-6/np.linalg.eigvals(K).real.min()),'schedule':'LSBfirst BCM,64bits20MHzSPI,minimumdwell3.2us,shift next plane while previous outputs latched; no extra latch/firmware overhead assumed','capacitor_stress':'0.8/1/1.2uF assumed20percent sensitivity, not part-specific certified tolerance','model':'Exact64coupled RC linear states at periodic steady state, ideal static nonlinearopamps at4samplesperplane; no opamp bandwidth/recovery model','results':out},indent=2))
