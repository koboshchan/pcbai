"""Nominal test-set static loading demands, GPU evaluation, not datasheet guarantees."""
import json,numpy as np,torch
from cuda_mc import H,tensor,draw,run
from model import loaded
c=json.loads((H/'circuit.json').read_text());d=np.load(H/'data/test.npz');X=tensor(np.round(d['X']/5*63)/63*5);adc,s,h=run(X,[draw(c,None)],c);h=h[0];s=s[0]
def demand(rows,n,rs,x,out):
 _,_,T,q,P,PB,G=loaded(rows,n,rs)
 actual=x@tensor(T).T+tensor(q);vp=actual@tensor(P).T+tensor(PB)
 input_i=(x-actual)/rs
 feedback=(out-vp)/tensor([r['rf_ohms'] for r in rows])
 return {'driver_max_abs_mA_per_channel':(input_i.abs().max(0).values*1000).cpu().tolist(),'feedback_max_abs_mA_per_amplifier':(feedback.abs().max(0).values*1000).cpu().tolist(),'positive_input_node_min_V':vp.min(0).values.cpu().tolist(),'positive_input_node_max_V':vp.max(0).values.cpu().tolist()}
A,b,*_=loaded(c['layer1'],64,10050);sums=(X@tensor(A)+tensor(b)).clamp(-13.5,13.5)
l1=demand(c['layer1'],64,10050,X,sums);l2=demand(c['layer2'],16,1,h,s)
mid=(s/220000+3.3/22000)/(1/220000+2/22000)
adci=(s-mid)/220000
# Sum signed feedback and ADC currents at score outputs.
_,_,T,q,P,PB,G=loaded(c['layer2'],16,1);actual=h@tensor(T).T+tensor(q);vp=actual@tensor(P).T+tensor(PB)
score_current=(s-vp)/100000+adci
out={'layer1':l1,'layer2':l2,'score_total_feedback_plus_ADC_max_abs_mA':(score_current.abs().max(0).values*1000).cpu().tolist(),'rectifier_output_load_conservative_mA':1.35,'limitations':'Nominal official10k test set only; not hypercube bound, tolerance bound, current limit qualification, or commonmode validation. L1 output drives10k active rectifier input, <=1.35mA for modeled13.5V swing, in addition to feedback. Inactive rectifier ideal model does not establish current/recovery. ACT followers drive complete L2 resistor network through modeled1ohm source. Score LEDs/WTA removed. TL074 load/swing/commonmode and HCT595 bank total current require datasheet/hardware qualification.'}
(H/'loading_cuda.json').write_text(json.dumps(out,indent=2));print('loading complete')
