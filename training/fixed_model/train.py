"""Official MNIST binary retraining with physical conductance QAT. Outputs isolated."""
import os,sys,json,io,time,urllib.request,hashlib,ast
from pathlib import Path
import numpy as np
import torch
from PIL import Image
import pyarrow.parquet as pq
from model import VALUES,RF,synthesize,infer
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
torch.set_num_threads(8); torch.manual_seed(42064);np.random.seed(42064)
device='cuda' if torch.cuda.is_available() else 'cpu'
def data():
 cache=HERE/'data';cache.mkdir(exist_ok=True)
 arrays=[]; provenance={}
 for split in ['train','test']:
  file=cache/(split+'.parquet');url=f'https://huggingface.co/datasets/ylecun/mnist/resolve/main/mnist/{split}-00000-of-00001.parquet'
  if not file.exists():urllib.request.urlretrieve(url,file)
  provenance[split]={'url':url,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
  npz=cache/(split+'.npz')
  if not npz.exists():
   table=pq.read_table(file).to_pydict();X=[]
   for item in table['image']:
    im=Image.open(io.BytesIO(item['bytes']));a=np.array(im);r=np.where(a.max(axis=1)>20)[0];c=np.where(a.max(axis=0)>20)[0]
    if len(r) and len(c):
     r0,r1=max(0,r[0]-2),min(a.shape[0],r[-1]+3);c0,c1=max(0,c[0]-2),min(a.shape[1],c[-1]+3);h,w=r1-r0,c1-c0;diff=abs(h-w)
     if h>w:c0=max(0,c0-diff//2);c1=min(a.shape[1],c1+diff-diff//2)
     elif w>h:r0=max(0,r0-diff//2);r1=min(a.shape[0],r1+diff-diff//2)
     im=im.crop((c0,r0,c1,r1))
    x=np.array(im.resize((8,8),Image.Resampling.BOX),dtype=np.float32).flatten()/255*5
    X.append(x)
   np.savez_compressed(npz,X=np.array(X),y=np.array(table['label'],dtype=np.int64))
  d=np.load(npz);arrays.extend([d['X'],d['y']])
 provenance['preprocess']='Original pipeline crop intensity>20 with2pxpadding, square-expanded bounding box, PIL BOX8x8; grayscale voltage0..5,6bit PWM quantization'
 (HERE/'dataset_provenance.json').write_text(json.dumps(provenance,indent=2))
 return arrays
source=ast.parse((ROOT/'train_mnist_hardware.py').read_text())
for node in source.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='E96_BASE_VALUES' for t in node.targets):base=ast.literal_eval(node.value.args[0])
e96=np.concatenate([np.array(base)*10**d for d in range(0,8)])
values=torch.tensor(VALUES,dtype=torch.float32,device=device);balvalues=torch.tensor(e96,dtype=torch.float32,device=device)
def ste_snap(r,vs):
 index=(torch.log(r.clamp(min=1)).unsqueeze(-1)-torch.log(vs)).abs().argmin(-1);q=vs[index]
 return r+(q-r).detach()
class Net(torch.nn.Module):
 def __init__(self):
  super().__init__();self.fc1=torch.nn.Linear(64,16);self.fc2=torch.nn.Linear(16,10);self.qat=False;self.noise=False
 def layer(self,x,w,b,rs,inverted=False):
  a=torch.cat([w,b[:,None]/5],1)
  if inverted:a=-a
  if not self.qat:return x@a[:,:-1].T+a[:,-1]*5
  sign=a.detach().sign();r=RF/a.abs().clamp(min=.01);r=ste_snap(r,values);g=1/r
  active=(a.detach().abs()>=.01);g=g*active
  gp=g*(sign>0);gn=g*(sign<0)
  # A real fixed balance resistor selected from the current nominal quantized weights.
  diff=(1/RF+gn.sum(1)-gp.sum(1)).detach();bal=ste_snap(1/diff.abs().clamp(min=1e-14),balvalues).detach()
  gb=1/bal;positive=diff>=0
  if self.noise:
   g=g/(1+torch.empty_like(g).uniform_(-.05,.05));gp=g*(sign>0);gn=g*(sign<0)
   gf=(1/RF)/(1+torch.empty(len(b),device=device).uniform_(-.01,.01));gb=gb/(1+torch.empty_like(gb).uniform_(-.01,.01))
  else:gf=torch.full_like(b,1/RF)
  gbp=gb*positive;gbn=gb*(~positive);totp=gp.sum(1)+gbp
  P=gp/totp[:,None];k=(gf+gn.sum(1)+gbn)/gf/totp
  coeff=gp*k[:,None]-gn/gf[:,None]
  G=g[:,:-1];C=torch.diag(G.sum(0))-G.T@P[:,:-1]
  source_r=torch.full((x.shape[1],),float(rs),device=device)
  if self.noise and rs>1000:source_r=10000*(1+torch.empty_like(source_r).uniform_(-.05,.05))+50
  T=torch.linalg.inv(torch.eye(x.shape[1],device=device)+source_r[:,None]*C)
  q=T@(source_r*(G.T@P[:,-1])*5)
  actual=x@T.T+q
  return actual@coeff[:,:-1].T+coeff[:,-1]*5
 def forward(self,x):
  sums=self.layer(x,self.fc1.weight,self.fc1.bias,10050,True).clamp(-13.5,13.5)
  h=(-sums).relu().clamp(max=12.7)
  if self.noise:h=h*((1+torch.empty(16,device=device).uniform_(-.01,.01))/(1+torch.empty(16,device=device).uniform_(-.01,.01)))
  return self.layer(h,self.fc2.weight,self.fc2.bias,1).clamp(-13.5,13.5)
X,y,Xt,yt=data();X=X.astype('float32');Xt=Xt.astype('float32')
# Grayscale source duty quantized to six bits, never thresholded.
X=np.round(X/5*63)/63*5;Xt=np.round(Xt/5*63)/63*5
# 5000 validation samples are separated from training; test never selects epochs.
perm=np.random.default_rng(42064).permutation(len(X));vi=perm[:5000];ti=perm[5000:]
x=torch.tensor(X[ti],device=device);yy=torch.tensor(y[ti],device=device);xv=torch.tensor(X[vi],device=device);yv=torch.tensor(y[vi],device=device)
net=Net().to(device);net.load_state_dict(torch.load(ROOT/'mnist_analog_model.pt',map_location=device,weights_only=True))
opt=torch.optim.Adam(net.parameters(),lr=.0015);best=-1;start=time.time()
for epoch in range(60):
 net.qat=epoch>=15;net.noise=epoch>=25;order=torch.randperm(len(x),device=device)
 for ids in order.split(512):
  opt.zero_grad();scores=net(x[ids]);loss=torch.nn.functional.cross_entropy(scores,yy[ids]);loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),5);opt.step()
 net.noise=False
 with torch.no_grad():acc=(net(xv).argmax(1)==yv).float().mean().item()
 print(epoch,round(acc,5),'qat',net.qat,'seconds',round(time.time()-start),flush=True)
 if net.qat and acc>best:
  best=acc;torch.save(net.state_dict(),HERE/'best.pt')
net.load_state_dict(torch.load(HERE/'best.pt',map_location=device,weights_only=True));net.qat=True;net.noise=False
circ=json.loads((HERE/'circuit.json').read_text());circ['status']='trained binary official MNIST, selected validation epoch only'
w1=net.fc1.weight.detach().cpu().numpy();b1=net.fc1.bias.detach().cpu().numpy();w2=net.fc2.weight.detach().cpu().numpy();b2=net.fc2.bias.detach().cpu().numpy()
circ['layer1']=synthesize(-w1,-b1,e96);circ['layer2']=synthesize(w2,b2,e96)
(HERE/'trained_circuit.json').write_text(json.dumps(circ,indent=2));np.savez(HERE/'trained_float.npz',w1=w1,b1=b1,w2=w2,b2=b2)
metrics={'dataset':'official MNIST test10000, binary2.5V threshold after original preprocessing','train_count':55000,'validation_count':5000,'test_count':10000,'seed':42064,'best_validation':best,'device':device,'test_used_for_selection':False}
for rs in [10050]:
 adc,s,h=infer(Xt,circ,source_ohms=rs,swing=13.5);pred=adc.argmax(1);metrics['nominal_source_'+str(rs)]={'correct':int((pred==yt).sum()),'accuracy':float((pred==yt).mean()),'adc_min':float(adc.min()),'adc_max':float(adc.max()),'hidden_max':float(h.max()),'score_absmax':float(abs(s).max()),'per_digit':[float((pred[yt==i]==i).mean()) for i in range(10)]}
mc=[];rng=np.random.default_rng(51005)
for trial in range(0):
 adc,s,h=infer(Xt,circ,rng);mc.append(float((adc.argmax(1)==yt).mean()))
 if trial%20==0:print('MC',trial,mc[-1],flush=True)
metrics['mc']={'status':'pending CUDA1000, no CPU board loop'}
metrics['dataset']='official MNIST grayscale6bit PWM, same crop BOX8x8, test10000'
circ['status']='grayscale6bit PWM physical10050ohm source, validation-selected'
circ['input_conditioning']={'series_ohms':10000,'series_tolerance':.05,'driver_ohms':50,'capacitance_F':1e-6,'pwm_bits':6,'source_high_V':5,'swing_V':13.5,'rectifier_max_V':12.7,'architecture':'differential summers with16 ACT followers'}
(HERE/'trained_circuit.json').write_text(json.dumps(circ,indent=2))
(HERE/'circuit.json').write_text(json.dumps(circ,indent=2))
(HERE/'metrics.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics),flush=True)
