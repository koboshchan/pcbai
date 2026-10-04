"""Independent unchanged ADC corners and constrained-QAT/export agreement."""
import itertools,json,sys
from pathlib import Path
import numpy as np
import torch
H=Path(__file__).resolve().parent;OLD=H.parent/'fixed_model';sys.path.insert(0,str(OLD))
from model import loaded
import cuda_mc as mc
from train_basic import Net
c=json.loads((H/'circuit.json').read_text());d=np.load(OLD/'data/test.npz');xn=np.round(d['X'].astype(float)/5*63)/63*5;X=mc.tensor(xn)
net=Net();net.load_state_dict(torch.load(H/'best.pt',weights_only=True));net.l1.qat=net.l2.qat=True;net.noise=False
with torch.no_grad():ss=net(X.float()).cpu().numpy()
a,s,h=mc.run(X,[mc.draw(c,None)],c);error=float(np.max(abs(ss-s[0].cpu().numpy())));assert error<.002,error
values=[];off=[]
for t,u,d,rs in itertools.product([.99,1.01],repeat=4):
 rt=220000*t;ru=22000*u;rd=22000*d;g=1/rt+1/ru+1/rd
 for score,vref in itertools.product([-15,15],[3.3*.95,3.3*1.05]):values.append((score/rt+vref/ru)/g)
 off.append((15/rt/g)/(1/g+1000*rs))
loads={}
for key,n,source,command,output in [('layer1',64,10050,X,None),('layer2',16,1,h[0],s[0])]:
 A,b,T,q,P,PB,G=loaded(c[key],n,source);actual=command@mc.tensor(T).T+mc.tensor(q);vp=actual@mc.tensor(P).T+mc.tensor(PB)
 loads[key]={'driver_max_abs_mA':float(((command-actual)/source).abs().max()*1000),'positive_node_min_V':float(vp.min()),'positive_node_max_V':float(vp.max())}
 if output is None:output=(command@mc.tensor(A)+mc.tensor(b)).clamp(-13.5,13.5)
 loads[key]['feedback_max_abs_mA']=float(((output-vp)/100000).abs().max()*1000)
out={'qat_float32_export_float64_score_max_error_V':error,'adc_powered_corner_min_V':min(values),'adc_powered_corner_max_V':max(values),'poweroff_per_pin_max_A':max(off),'nominal_test_set_loading':loads,'constraints_preserved':{'summer_clip_V':13.5,'ReLU_clip_V':12.7,'source_ohms':10050,'ADC_bits':12,'PWM_bits':6,'rails':'+/-15V','rf_ohms':100000},'caveat':'Static ideal nodal model. Not loaded TL074 swing/commonmode/current guarantees or hardware qualification. ADC divider unchanged. Silicon clamps do not guarantee absolute voltage nor prevent MCU rail backfeed; MCU3V3/GND first, analog last. PWM ripple/settling must be rerun for changed conductances before hardware signoff.'}
(H/'checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
