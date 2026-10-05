"""Physical differential conductance model. All resistances are actual components."""
import numpy as np
RF=100000.
E24=np.array([1,1.1,1.2,1.3,1.5,1.6,1.8,2,2.2,2.4,2.7,3,3.3,3.6,3.9,4.3,4.7,5.1,5.6,6.2,6.8,7.5,8.2,9.1])
VALUES=np.concatenate([E24*10**d for d in range(4,8)])
VALUES=VALUES[VALUES<=1e7]
# 1% ground balancing, two resistors in series, E96 values synthesized as standard log lattice.
# Exact E96 table imported from original training script during export instead of approximate lattice.
def snap(v,values=VALUES):
 return values[np.argmin(abs(np.log(values)-np.log(np.maximum(v,1))))]

def synthesize(w,b,e96):
 rows=[]
 for j in range(len(b)):
  entries=[]
  for i,a in enumerate(np.r_[w[j],b[j]/5]):
   if abs(a)<.01: continue
   r=float(snap(RF/abs(a)))
   entries.append({'index':i,'source': 'input' if i<w.shape[1] else '+5V_REF','leg':'positive' if a>0 else 'negative','ohms':r,'tolerance':.05})
  gp=sum(1/e['ohms'] for e in entries if e['leg']=='positive')
  gn=sum(1/e['ohms'] for e in entries if e['leg']=='negative')
  diff=1/RF+gn-gp
  target=1/abs(diff) if abs(diff)>1e-14 else None
  balance=None
  if target:
   # One standard E96 part; rounding is included in nominal model, never claimed exact.
   balance={'leg':'positive' if diff>=0 else 'negative','ohms':float(snap(target,e96)),'tolerance':.01}
  rows.append({'neuron':j,'rf_ohms':RF,'rf_tolerance':.01,'balance':balance,'inputs':entries})
 return rows

def coefficients(rows,n,rng=None):
 W=np.zeros((len(rows),n));B=np.zeros(len(rows));P=np.zeros_like(W);PB=np.zeros(len(rows));G=np.zeros_like(W)
 for j,row in enumerate(rows):
  rf=row['rf_ohms']*(1+rng.uniform(-.01,.01) if rng is not None else 1)
  es=[]
  for e in row['inputs']:
   r=e['ohms']*(1+rng.uniform(-e['tolerance'],e['tolerance']) if rng is not None else 1);es.append((e,1/r))
  gp=sum(g for e,g in es if e['leg']=='positive');gn=sum(g for e,g in es if e['leg']=='negative')
  bal=row['balance'];gbp=gbn=0.
  if bal:
   g=1/(bal['ohms']*(1+rng.uniform(-.01,.01) if rng is not None else 1))
   if bal['leg']=='positive':gbp=g
   else:gbn=g
  totalp=gp+gbp
  k=(1+rf*(gn+gbn))/totalp if totalp else 0
  for e,g in es:
   a=g*k if e['leg']=='positive' else -rf*g
   if e['index']<n:
    W[j,e['index']]=a;G[j,e['index']]=g
    if e['leg']=='positive':P[j,e['index']]=g/totalp
   else:
    B[j]+=a*5
    if e['leg']=='positive':PB[j]+=g/totalp*5
 return W,B,P,PB,G

def loaded(rows,n,rs,rng=None):
 W,B,P,PB,G=coefficients(rows,n,rng)
 # Every input resistor terminates at that neuron's common virtual node v+=P*x+PB.
 # Input commands through Rs see complete shared load, not independent weight noise.
 C=np.diag(G.sum(axis=0))-G.T@P
 rv=np.asarray(rs);rowrs=rv[:,None] if rv.ndim else rv
 T=np.linalg.solve(np.eye(n)+rowrs*C,np.eye(n))
 q=T@(rv*(G.T@PB))
 return T.T@W.T, q@W.T+B, T,q,P,PB,G

def infer(X,circuit,rng=None,source_ohms=10050.,follower_ohms=1.,swing=13.5):
 A,b,*_=loaded(circuit['layer1'],64,source_ohms,rng)
 sums=np.clip(X@A+b,-swing,swing)
 ratio=np.ones(16)
 if rng is not None:ratio=(1+rng.uniform(-.01,.01,16))/(1+rng.uniform(-.01,.01,16))
 # L1 stored affine already inverted. Active rectifier then buffer.
 h=np.clip(-sums*ratio,0,swing-.8)
 A,b,*_=loaded(circuit['layer2'],16,follower_ohms,rng)
 scores=np.clip(h@A+b,-swing,swing)
 # Offset attenuator is independently sampled per channel, no nominal channel calibration.
 rt=np.full(10,220000.);ru=np.full(10,22000.);rd=np.full(10,22000.)
 if rng is not None:
  rt*=1+rng.uniform(-.01,.01,10);ru*=1+rng.uniform(-.01,.01,10);rd*=1+rng.uniform(-.01,.01,10)
 adc=(scores/rt+3.3/ru)/(1/rt+1/ru+1/rd)
 adc=np.round(adc/3.3*4095)/4095*3.3
 return adc,scores,h
