"""Batched CUDA physical resistor Monte Carlo; NumPy RNG order matches model.infer."""
import json,time
from pathlib import Path
import numpy as np
import torch
from model import coefficients,infer
H=Path(__file__).resolve().parent
D='cuda';dtype=torch.float64
torch.set_num_threads(8)
assert torch.cuda.is_available()
def tensor(x):return torch.as_tensor(np.asarray(x),device=D,dtype=dtype)
def draw(c,rng):
 a=coefficients(c['layer1'],64,rng)
 ratio=np.ones(16) if rng is None else (1+rng.uniform(-.01,.01,16))/(1+rng.uniform(-.01,.01,16))
 b=coefficients(c['layer2'],16,rng)
 r=np.array([[220000.]*10,[22000.]*10,[22000.]*10])
 if rng is not None:
  for k in range(3):r[k]*=1+rng.uniform(-.01,.01,10)
 return a,ratio,b,r,(np.full(64,10050.) if rng is None else 10000*(1+rng.uniform(-.05,.05,64))+50)
# Noise gain derives from actual shared feedback, not independent coefficient noise.
def noisegain(rows,rng=None):
 out=[]
 for row in rows:
  rf=row['rf_ohms'];gn=sum(1/e['ohms'] for e in row['inputs'] if e['leg']=='negative')
  bal=row['balance']
  if bal and bal['leg']=='negative':gn+=1/bal['ohms']
  out.append(1+rf*gn)
 return np.array(out)
def layer(pack,n,rs,vos=None,ng=None):
 W,B,P,PB,G=[tensor(np.stack([p[k] for p in pack])) for k in range(5)]
 C=torch.diag_embed(G.sum(1))-G.transpose(1,2)@P
 source=tensor(rs) if not np.isscalar(rs) else rs
 if not np.isscalar(rs):source=source[:,:,None]
 T=torch.linalg.solve(torch.eye(n,device=D,dtype=dtype)[None]+source*C,torch.eye(n,device=D,dtype=dtype)[None].expand(len(pack),n,n))
 virtual=PB if vos is None else PB+tensor(vos)
 q=(T@(source*(G.transpose(1,2)@virtual[:,:,None]))).squeeze(-1)
 A=T.transpose(1,2)@W.transpose(1,2)
 b=(q[:,None,:]@W.transpose(1,2)).squeeze(1)+B
 if vos is not None:b+=tensor(vos)*tensor(ng)
 return A,b
@torch.no_grad()
def run(X,draws,c,high=5.,offset=0.,swing=13.5):
 A,b=layer([d[0] for d in draws],64,np.stack([d[4] for d in draws]),np.full((len(draws),16),offset) if offset else None,noisegain(c['layer1']))
 sums=(X[None]*(high/5)@A+b[:,None,:]).clamp(-swing,swing)
 h=(-sums*tensor([d[1] for d in draws])[:,None,:]+2*offset).clamp(0,swing-.8)
 # Diagnostic fixed signed input offset on each unity ACT follower.
 h=h+offset
 A,b=layer([d[2] for d in draws],16,1.,np.full((len(draws),10),offset) if offset else None,noisegain(c['layer2']))
 s=(h@A+b[:,None,:]).clamp(-swing,swing)
 r=tensor([d[3] for d in draws]);rt,ru,rd=[r[:,k,None,:] for k in range(3)]
 adc=((s/rt+3.3/ru)/(1/rt+1/ru+1/rd)/3.3*4095).round()/4095*3.3
 return adc,s,h
if __name__=='__main__':
 start=time.time();c=json.loads((H/'circuit.json').read_text());d=np.load(H/'data/test.npz');xn=np.round(d['X'].astype(float)/5*63)/63*5;y=d['y'];X=tensor(xn);Y=torch.tensor(y,device=D)
 regress=[]
 for seed in [None,51005,51006,51007]:
  r=None if seed is None else np.random.default_rng(seed);dr=draw(c,r)
  r=None if seed is None else np.random.default_rng(seed);ref=infer(xn,c,r,source_ohms=dr[4],swing=13.5)
  got=run(X,[dr],c)
  err=[float(np.max(abs(t[0].cpu().numpy()-v))) for t,v in zip(got,ref)]
  assert err[0]<1e-12 and max(err[1:])<1e-9,err
  regress.append({'seed':seed,'adc_score_hidden_max_error':err})
 print('regression passed',regress,flush=True)
 rng=np.random.default_rng(51005);acc=[]
 for i in range(0,1000,20):
  draws=[draw(c,rng) for _ in range(20)]
  adc,s,h=run(X,draws,c);acc.extend((adc.argmax(2)==Y[None]).double().mean(1).cpu().tolist())
  if i%100==0:print('boards',i+20,'seconds',time.time()-start,flush=True)
 nominal=draw(c,None);diagnostics=[]
 for high in [4.5,4.75,5.]:
  for offset in [-.01,0.,.01]:
   a,s,h=run(X,[nominal],c,high,offset);diagnostics.append({'driver_high_V':high,'all_amplifier_input_offset_V':offset,'correct':int((a.argmax(2)==Y).sum()),'accuracy':float((a.argmax(2)==Y).double().mean())})
 a,s,h=run(X,[nominal],c,swing=10.);diagnostics.append({'conservative_swing_V':10,'correct':int((a.argmax(2)==Y).sum()),'accuracy':float((a.argmax(2)==Y).double().mean())})
 out={'device':torch.cuda.get_device_name(),'dtype':'float64','gpu_batched_boards':20,'board_realizations':1000,'examples_each':10000,'seed':51005,'distribution':'Shared10kfilter +/-5% perinput plus fixed50ohmdriver; actual weight/bias resistors +/-5%; feedback/balance/rectifier/ADC +/-1%. Shared components per board, shared input KCL, ADC12bit,6bitgrayscale,13.5Vswing. No random opamp offset in tolerance MC.','min':min(acc),'mean':float(np.mean(acc)),'max':max(acc),'std':float(np.std(acc,ddof=1)),'p05':float(np.quantile(acc,.05)),'accuracy_samples':acc,'regression':regress,'diagnostic_assumptions':'Driver high is commanded source level with 10050ohm impedance; +5V bias reference remains5V. Coherent +/-10mV input offsets applied to both weighted summers and16 unity followers. Active rectifier offset modeled with ideal noisegain2 before zero/output clipping; off-state leakage/recovery not modeled. Not measured offsets, not worst-case independent-sign search or random distribution.','sensitivity':diagnostics,'noise_gain':{'layer1':noisegain(c['layer1']).tolist(),'layer2':noisegain(c['layer2']).tolist(),'followers':1,'active_rectifiers':2},'seconds':time.time()-start}
 (H/'cuda_mc.json').write_text(json.dumps(out,indent=2));print('DONE',out['min'],out['mean'],out['max'],out['seconds'],flush=True)
