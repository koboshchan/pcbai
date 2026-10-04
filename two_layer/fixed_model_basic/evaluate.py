"""Official held-out evaluation after validation selection; same shared physical CUDA MC."""
import copy,hashlib,json,sys,time
from pathlib import Path
import numpy as np
import torch
H=Path(__file__).resolve().parent;OLD=H.parent/'fixed_model';sys.path.insert(0,str(OLD))
import cuda_mc as mc
from model import infer

def evaluate(c,name,X,Y,xn,y):
 start=time.time();out={'name':name,'circuit_sha256':hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()};dr=mc.draw(c,None);adc,s,h=mc.run(X,[dr],c)
 out['nominal']={'correct':int((adc.argmax(2)==Y).sum()),'accuracy':float((adc.argmax(2)==Y).double().mean()),'adc_min_V':float(adc.min()),'adc_max_V':float(adc.max()),'hidden_max_V':float(h.max()),'score_absmax_V':float(s.abs().max())}
 regression=[]
 for seed in [None,51005,51006,51007]:
  r=None if seed is None else np.random.default_rng(seed);d=mc.draw(c,r)
  r=None if seed is None else np.random.default_rng(seed);ref=infer(xn,c,r,source_ohms=d[4]);got=mc.run(X,[d],c)
  err=[float(np.max(abs(t[0].cpu().numpy()-v))) for t,v in zip(got,ref)];assert err[0]<1e-12 and max(err[1:])<1e-9;regression.append({'seed':seed,'adc_score_hidden_max_error':err})
 out['regression']=regression
 for tolerance in [.05,.01]:
  ct=copy.deepcopy(c)
  for key in ['layer1','layer2']:
   for row in ct[key]:
    for e in row['inputs']:e['tolerance']=tolerance
  rng=np.random.default_rng(51005);accuracies=[]
  for i in range(0,1000,20):
   draws=[]
   for _ in range(20):
    a=mc.coefficients(ct['layer1'],64,rng);ratio=(1+rng.uniform(-.01,.01,16))/(1+rng.uniform(-.01,.01,16));b=mc.coefficients(ct['layer2'],16,rng)
    r=np.array([[220000.]*10,[22000.]*10,[22000.]*10])
    for k in range(3):r[k]*=1+rng.uniform(-.01,.01,10)
    source=10000*(1+rng.uniform(-tolerance,tolerance,64))+50;draws.append((a,ratio,b,r,source))
   a,s,h=mc.run(X,draws,ct);accuracies.extend((a.argmax(2)==Y[None]).double().mean(1).cpu().tolist())
  out['mc_'+str(tolerance)]={'board_realizations':1000,'test_images_each':10000,'seed':51005,'mean':float(np.mean(accuracies)),'worst':min(accuracies),'best':max(accuracies),'p05':float(np.quantile(accuracies,.05)),'std':float(np.std(accuracies,ddof=1)),'accuracy_samples':accuracies,'distribution':'Uniform independent per physical component, fixed per board across all images. Weight/bias and64input filters use stated tolerance; feedback/balance/rectifier/ADC remain1%. Assumed50ohm driver,6bitgrayscale,12bitADC,13.5V clip and12.7V ReLU. No opamp offset or PWM dynamics.'}
  (H/(name+'_metrics.json')).write_text(json.dumps(out,indent=2));print(name,tolerance,'nominal',out['nominal']['accuracy'],'mean',out['mc_'+str(tolerance)]['mean'],'worst',out['mc_'+str(tolerance)]['worst'],flush=True)
 a,s,h=mc.run(X,[dr],c,swing=10.);out['conservative_10V_accuracy']=float((a.argmax(2)==Y).double().mean());out['seconds']=time.time()-start
 (H/(name+'_metrics.json')).write_text(json.dumps(out,indent=2));return out
if __name__=='__main__':
 d=np.load(OLD/'data/test.npz');xn=np.round(d['X'].astype(float)/5*63)/63*5;y=d['y'];X=mc.tensor(xn);Y=torch.tensor(y,device='cuda');out={}
 for name,file in [('rounded',H/'rounded_circuit.json'),('trained',H/'circuit.json')]:out[name]=evaluate(json.loads(file.read_text()),name,X,Y,xn,y)
 out['baseline']={'nominal':json.loads((OLD/'metrics.json').read_text()),'mc_5percent':json.loads((OLD/'cuda_mc.json').read_text())}
 out['device']=torch.cuda.get_device_name();out['selection']='Only 5000 validation samples select checkpoint; official10000test first read after training completes.'
 (H/'metrics.json').write_text(json.dumps(out,indent=2));print('EVALUATION DONE',flush=True)
