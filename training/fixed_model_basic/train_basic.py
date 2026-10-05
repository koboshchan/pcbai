"""Value-only Basic resistor QAT. Existing component presence and pad nets stay fixed."""
import copy,json,time,sys
from pathlib import Path
import numpy as np
import torch
H=Path(__file__).resolve().parent; OLD=H.parent/'fixed_model'
torch.set_num_threads(6);torch.manual_seed(42064)
D='cuda';assert torch.cuda.is_available()
catalog=json.loads((H/'basic_catalog.json').read_text())['parts']
# Exclude short links and very small values from neural weights for realistic loading.
vs=np.array([p['ohms'] for p in catalog if p['ohms']>=1000]);lv=torch.tensor(np.log(vs),device=D,dtype=torch.float32)
base=json.loads((OLD/'circuit.json').read_text())
def snap(r):return float(vs[np.abs(np.log(vs)-np.log(r)).argmin()])
def project(c):
 c=copy.deepcopy(c)
 for key in ['layer1','layer2']:
  for row in c[key]:
   row['rf_ohms']=snap(row['rf_ohms'])
   if row['balance']:row['balance']['ohms']=snap(row['balance']['ohms'])
   for e in row['inputs']:e['ohms']=snap(e['ohms'])
 return c
rounded=project(base);(H/'rounded_circuit.json').write_text(json.dumps(rounded,indent=2))
class Layer(torch.nn.Module):
 def __init__(self,rows,n,rs):
  super().__init__();self.rows=rows;self.n=n;self.rs=rs
  r=np.full((len(rows),n+1),1e6);mask=np.zeros_like(r);sign=np.zeros_like(r)
  for j,row in enumerate(rows):
   for e in row['inputs']:r[j,e['index']]=e['ohms'];mask[j,e['index']]=1;sign[j,e['index']]=1 if e['leg']=='positive' else -1
  self.logr=torch.nn.Parameter(torch.tensor(np.log(np.minimum(r,1e6)),device=D,dtype=torch.float32))
  self.logbal=torch.nn.Parameter(torch.tensor(np.log([min(row['balance']['ohms'],1e6) for row in rows]),device=D,dtype=torch.float32))
  self.register_buffer('mask',torch.tensor(mask,device=D,dtype=torch.float32));self.register_buffer('sign',torch.tensor(sign,device=D,dtype=torch.float32));self.register_buffer('bpos',torch.tensor([row['balance']['leg']=='positive' for row in rows],device=D));self.noise=False;self.qat=True
 def quant(self,x):
  x=x.clamp(lv.min(),lv.max())
  if not self.qat:return x
  q=lv[(x[...,None]-lv).abs().argmin(-1)];return x+(q-x).detach()
 def forward(self,x):
  g=(-self.quant(self.logr)).exp()*self.mask;gb=(-self.quant(self.logbal)).exp();gf=torch.full_like(gb,1e-5)
  if self.noise:
   g=g/(1+torch.empty_like(g).uniform_(-.05,.05));gb=gb/(1+torch.empty_like(gb).uniform_(-.01,.01));gf=gf/(1+torch.empty_like(gf).uniform_(-.01,.01))
  gp=g*(self.sign>0);gn=g*(self.sign<0);totp=gp.sum(1)+gb*self.bpos
  P=gp/totp[:,None];k=(gf+gn.sum(1)+gb*(~self.bpos))/gf/totp
  coeff=gp*k[:,None]-gn/gf[:,None];G=g[:,:-1];C=torch.diag(G.sum(0))-G.T@P[:,:-1]
  sr=torch.full((self.n,),self.rs,device=D)
  if self.noise and self.rs>1000:sr=10000*(1+torch.empty_like(sr).uniform_(-.05,.05))+50
  T=torch.linalg.solve(torch.eye(self.n,device=D)+sr[:,None]*C,torch.eye(self.n,device=D))
  q=T@(sr*(G.T@P[:,-1])*5)
  return (x@T.T+q)@coeff[:,:-1].T+coeff[:,-1]*5
 def export(self):
  rows=copy.deepcopy(self.rows);r=self.quant(self.logr).detach().exp().cpu().numpy();bal=self.quant(self.logbal).detach().exp().cpu().numpy()
  for j,row in enumerate(rows):
   for e in row['inputs']:e['ohms']=snap(float(r[j,e['index']]))
   row['balance']['ohms']=snap(float(bal[j]));row['rf_ohms']=100000.
  return rows
class Net(torch.nn.Module):
 def __init__(self):
  super().__init__();self.l1=Layer(base['layer1'],64,10050.);self.l2=Layer(base['layer2'],16,1.);self.noise=False
 def forward(self,x):
  self.l1.noise=self.l2.noise=self.noise
  h=(-self.l1(x).clamp(-13.5,13.5)).relu()
  if self.noise:h=h*(1+torch.empty(16,device=D).uniform_(-.01,.01))/(1+torch.empty(16,device=D).uniform_(-.01,.01))
  return self.l2(h.clamp(max=12.7)).clamp(-13.5,13.5)
 def export(self):
  c=copy.deepcopy(base);c['layer1']=self.l1.export();c['layer2']=self.l2.export();c['status']='Basic0805 value-only constrained physical QAT, fixed original pad connectivity';c['balance']='one individually verified Basic0805 resistor, fixed leg; mismatch modeled';return c
if __name__=='__main__':
 data=np.load(OLD/'data/train.npz');X=np.round(data['X']/5*63)/63*5;y=data['y'];perm=np.random.default_rng(42064).permutation(len(X));vi=perm[:5000];ti=perm[5000:]
 x=torch.tensor(X[ti],device=D);yy=torch.tensor(y[ti],device=D);xv=torch.tensor(X[vi],device=D);yv=torch.tensor(y[vi],device=D)
 net=Net();best=-1;history=[];start=time.time();opt=torch.optim.Adam(net.parameters(),lr=.006)
 for epoch in range(320):
  # Brief continuous physical warmup, then actual Basic quantization on every pass.
  net.l1.qat=net.l2.qat=epoch>=12;net.noise=epoch>=45
  lr=.006 if epoch<120 else .003 if epoch<240 else .001
  for g in opt.param_groups:g['lr']=lr
  order=torch.randperm(len(x),device=D)
  for ids in order.split(1024):
   opt.zero_grad();scores=net(x[ids]);loss=torch.nn.functional.cross_entropy(scores,yy[ids]);loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),3);opt.step()
   with torch.no_grad():
    for p in net.parameters():p.clamp_(lv.min().item(),lv.max().item())
  net.noise=False
  with torch.no_grad():acc=float((net(xv).argmax(1)==yv).float().mean())
  history.append({'epoch':epoch,'validation_accuracy':acc,'qat':net.l1.qat})
  if net.l1.qat and acc>best:
   best=acc;torch.save(net.state_dict(),H/'best.pt');(H/'circuit.json').write_text(json.dumps(net.export(),indent=2));print('BEST',epoch,best,flush=True)
  if epoch%10==0:print('epoch',epoch,'accuracy',acc,'seconds',time.time()-start,flush=True)
 net.load_state_dict(torch.load(H/'best.pt',weights_only=True));net.l1.qat=net.l2.qat=True
 (H/'circuit.json').write_text(json.dumps(net.export(),indent=2));(H/'training_history.json').write_text(json.dumps({'seed':42064,'training_count':55000,'validation_count':5000,'test_used_for_selection':False,'best_validation':best,'epochs':320,'history':history,'seconds':time.time()-start},indent=2));print('DONE',best,time.time()-start,flush=True)
