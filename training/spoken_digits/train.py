"""Reuse fixed_model physical QAT and CUDA board solver without modifying MNIST."""
import ast,json,sys,time
from pathlib import Path
import numpy as np
import torch
H=Path(__file__).resolve().parent;F=H.parent/'fixed_model'
sys.path.insert(0,str(F))
from model import synthesize,infer
import cuda_mc as mc
# Execute only the existing training definitions, not MNIST downloads/training.
text=(F/'train.py').read_text().split('X,y,Xt,yt=data();')[0]
ns={'__file__':str(F/'train.py'),'__name__':'fixed_definitions'}
exec(compile(text,str(F/'train.py'),'exec'),ns)
Net=ns['Net'];e96=ns['e96'];device=ns['device']
torch.set_num_threads(8)
def confusion(y,p):
 return np.bincount(y*10+p,minlength=100).reshape(10,10).tolist()
def train_layout(bands,slices):
 torch.manual_seed(42064);np.random.seed(42064)
 label=f'{bands}x{slices}';out=H/label;out.mkdir(exist_ok=True)
 d=np.load(H/'data'/f'features_{label}.npz')
 X=d['X'];y=d['y'];split=d['split']
 sets=[(torch.tensor(X[split==i],device=device),torch.tensor(y[split==i],device=device)) for i in range(3)]
 x,yy=sets[0];xv,yv=sets[1];xt,yt=sets[2]
 floatnet=torch.nn.Sequential(torch.nn.Linear(64,16),torch.nn.ReLU(),torch.nn.Linear(16,10)).to(device)
 opt=torch.optim.Adam(floatnet.parameters(),lr=.0015);best=-1;logs=[]
 for epoch in range(60):
  for ids in torch.randperm(len(x),device=device).split(512):
   opt.zero_grad();loss=torch.nn.functional.cross_entropy(floatnet(x[ids]),yy[ids]);loss.backward();opt.step()
  with torch.no_grad():acc=(floatnet(xv).argmax(1)==yv).float().mean().item()
  if acc>best:best=acc;torch.save(floatnet.state_dict(),out/'float.pt')
  logs.append({'epoch':epoch,'float_validation':acc})
 floatnet.load_state_dict(torch.load(out/'float.pt',weights_only=True))
 with torch.no_grad():fp=floatnet(xt).argmax(1).cpu().numpy()
 net=Net().to(device)
 net.fc1.load_state_dict(floatnet[0].state_dict());net.fc2.load_state_dict(floatnet[2].state_dict())
 opt=torch.optim.Adam(net.parameters(),lr=.0015);besthw=-1
 for epoch in range(60):
  net.qat=epoch>=15;net.noise=epoch>=25
  for ids in torch.randperm(len(x),device=device).split(512):
   opt.zero_grad();loss=torch.nn.functional.cross_entropy(net(x[ids]),yy[ids]);loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),5);opt.step()
  net.noise=False
  with torch.no_grad():acc=(net(xv).argmax(1)==yv).float().mean().item()
  print(label,'hardware epoch',epoch,'validation',acc,flush=True)
  logs[epoch]['hardware_validation']=acc
  if net.qat and acc>besthw:besthw=acc;torch.save(net.state_dict(),out/'hardware.pt')
 net.load_state_dict(torch.load(out/'hardware.pt',weights_only=True))
 w1=net.fc1.weight.detach().cpu().numpy();b1=net.fc1.bias.detach().cpu().numpy();w2=net.fc2.weight.detach().cpu().numpy();b2=net.fc2.bias.detach().cpu().numpy()
 c=json.loads((F/'circuit.json').read_text())
 c['layer1']=synthesize(-w1,-b1,e96);c['layer2']=synthesize(w2,b2,e96)
 c['status']='Speech Commands v2 digits, official splits, validation-selected, not fabricated-board weights'
 (out/'circuit.json').write_text(json.dumps(c,indent=2));np.savez(out/'trained_float.npz',w1=w1,b1=b1,w2=w2,b2=b2)
 xn=X[split==2].astype(float);yn=y[split==2];gpu=mc.tensor(xn);Y=torch.tensor(yn,device=device)
 regress=[]
 for seed in [None,51005,51006,51007]:
  dr=mc.draw(c,None if seed is None else np.random.default_rng(seed))
  ref=infer(xn,c,None if seed is None else np.random.default_rng(seed),source_ohms=dr[4])
  got=mc.run(gpu,[dr],c)
  errors=[float(np.max(abs(t[0].cpu().numpy()-v))) for t,v in zip(got,ref)]
  assert errors[0]<1e-12 and max(errors[1:])<1e-9,errors
  regress.append({'seed':seed,'errors':errors})
 nominal=mc.run(gpu,[mc.draw(c,None)],c)[0][0].argmax(1).cpu().numpy()
 rng=np.random.default_rng(51005);accs=[]
 for i in range(0,1000,20):
  a,_,_=mc.run(gpu,[mc.draw(c,rng) for _ in range(20)],c)
  accs.extend((a.argmax(2)==Y[None]).double().mean(1).cpu().tolist())
  if i%200==0:print(label,'MC',i+20,flush=True)
 metrics={'layout':label,'seed':42064,'classes':['zero','one','two','three','four','five','six','seven','eight','nine'],'counts':{k:int((split==i).sum()) for i,k in enumerate(['train','validation','test'])},'float_validation':best,'hardware_validation':besthw,'float_test_accuracy':float((fp==yn).mean()),'hardware_nominal_accuracy':float((nominal==yn).mean()),'float_confusion':confusion(yn,fp),'hardware_confusion':confusion(yn,nominal),'mc':{'boards':1000,'mean':float(np.mean(accs)),'min':min(accs),'max':max(accs),'p05':float(np.quantile(accs,.05)),'std':float(np.std(accs)),'accuracy_samples':accs,'seed':51005},'solver_regression':regress,'epochs':60,'logs':logs,'device':torch.cuda.get_device_name(),'test_used_for_selection':False}
 (out/'metrics.json').write_text(json.dumps(metrics,indent=2))
 print('RESULT',label,metrics['float_test_accuracy'],metrics['hardware_nominal_accuracy'],metrics['mc']['mean'],metrics['mc']['min'],flush=True)
 return metrics
if __name__=='__main__':
 results=[train_layout(8,8),train_layout(16,4)]
 # Layout decision uses validation, never test results.
 winner=max(results,key=lambda m:m['hardware_validation'])
 (H/'summary.json').write_text(json.dumps({'chosen_by_hardware_validation':winner['layout'],'results':[{k:v for k,v in m.items() if k not in ['logs','float_confusion','hardware_confusion']} for m in results]},indent=2))
