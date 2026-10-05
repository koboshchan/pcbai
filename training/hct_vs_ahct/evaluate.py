"""Averaged asymmetric PWM driver comparison, isolated from CAD and routing.
Run on kat-box with python3 training/hct_vs_ahct/evaluate.py.
The historical exact physical draws are retained; no retraining or test selection.
"""
import argparse, copy, hashlib, json, sys, time
from pathlib import Path
import numpy as np
import torch
H = Path(__file__).resolve().parent
OLD = H.parent / 'fixed_model'
BASIC = H.parent / 'fixed_model_basic'
sys.path.insert(0, str(OLD))
import cuda_mc as mc
from model import coefficients
CASES = {
 'ideal': (0., 0.),
 'historical_50ohm': (50., 50.),
 'AHCT_typ_estimate': (50., 17.),
 'AHCT_worst_secant': (87.5, 55.),
 'HCT_typ_graph': (28., 29.),
 'HCT_worst_secant': (110., 55.),
 'Diodes_AHCT_worst_secant': (100., 68.75),
}

def pack_scale(pack, rail):
 W,B,P,PB,G = pack
 return W, B*rail/5., P, PB*rail/5., G

@torch.no_grad()
def evaluate_batch(duty, draws, high_r, low_r, rail=5., currents=False):
 # Reference KCL matrix uses low-state filter+driver resistance.
 # Averaged PWM g=d/(Rf+Rh)+(1-d)/(Rf+Rl), rhs=d*rail/(Rf+Rh).
 # Three small fixed-point corrections solve the image-dependent diagonal
 # without allocating 10000 separate 64x64 inverses for every physical board.
 p1=[pack_scale(d[0],rail) for d in draws]
 W,B,P,PB,G=[mc.tensor(np.stack([p[k] for p in p1])) for k in range(5)]
 filt=mc.tensor(np.stack([d[4]-50. for d in draws]))
 rs=filt+low_r; gh=1/(filt+high_r); gl=1/rs
 C=torch.diag_embed(G.sum(1))-G.transpose(1,2)@P
 T=torch.linalg.solve(torch.eye(64,device='cuda',dtype=torch.float64)[None]+rs[:,:,None]*C,
                      torch.eye(64,device='cuda',dtype=torch.float64)[None].expand(len(draws),64,64))
 q=(T@(rs*(G.transpose(1,2)@PB[:,:,None]).squeeze(-1))[:,:,None]).squeeze(-1)
 rhs=duty[None]*rail*(gh/gl)[:,None,:]
 delta=duty[None]*(gh/gl-1)[:,None,:]
 nodes=rhs@T.transpose(1,2)+q[:,None,:]
 for _ in range(3):
  nodes=(rhs-delta*nodes)@T.transpose(1,2)+q[:,None,:]
 residual=(nodes+rs[:,None,:]*(nodes@C.transpose(1,2)-(G.transpose(1,2)@PB[:,:,None]).squeeze(-1)[:,None,:]) - (rhs-delta*nodes)).abs().max()
 assert float(residual)<1e-7, float(residual)
 sums=(nodes@W.transpose(1,2)+B[:,None,:]).clamp(-13.5,13.5)
 hidden=(-sums*mc.tensor([d[1] for d in draws])[:,None,:]).clamp(0,12.7)
 A,b=mc.layer([pack_scale(d[2],rail) for d in draws],16,1.)
 scores=(hidden@A+b[:,None,:]).clamp(-13.5,13.5)
 r=mc.tensor([d[3] for d in draws]);rt,ru,rd=[r[:,k,None,:] for k in range(3)]
 adc=((scores/rt+3.3/ru)/(1/rt+1/ru+1/rd)/3.3*4095).round()/4095*3.3
 extra={'max_kcl_residual_V':float(residual)}
 if currents:
  ih=(rail-nodes)*gh[:,None,:];il=nodes*gl[:,None,:]
  average=duty[None]*ih-(1-duty[None])*il
  # U_SR1..8 drive consecutive eight pixels. These are output-load currents,
  # not whole-chip supply consumption from input cross-conduction or switching.
  extra.update(pin_average_abs_peak_mA=float(average.abs().max()*1000),
   pin_high_phase_peak_mA=float(ih.abs().max()*1000),pin_low_phase_peak_mA=float(il.abs().max()*1000),
   per_pin_average_abs_peak_mA=(average.abs().amax((0,1))*1000).cpu().tolist(),
   chip_average_source_peak_mA=(duty[None]*ih).reshape(len(draws),-1,8,8).sum(-1).amax((0,1)).mul(1000).cpu().tolist(),
   chip_average_sink_peak_mA=((1-duty[None])*il).reshape(len(draws),-1,8,8).sum(-1).amax((0,1)).mul(1000).cpu().tolist())
 return adc,scores,hidden,extra,nodes

def draws_for(c,tolerance,count):
 ct=copy.deepcopy(c)
 for key in ['layer1','layer2']:
  for row in ct[key]:
   for e in row['inputs']:e['tolerance']=tolerance
 rng=np.random.default_rng(51005)
 out=[]
 for _ in range(count):
  a=coefficients(ct['layer1'],64,rng)
  ratio=(1+rng.uniform(-.01,.01,16))/(1+rng.uniform(-.01,.01,16))
  b=coefficients(ct['layer2'],16,rng)
  r=np.array([[220000.]*10,[22000.]*10,[22000.]*10])
  for k in range(3):r[k]*=1+rng.uniform(-.01,.01,10)
  source=10000*(1+rng.uniform(-tolerance,tolerance,64))+50
  out.append((a,ratio,b,r,source))
 return out

def validate(duty,c,nominal):
 got=evaluate_batch(duty,[nominal],50.,50.)
 ref=mc.run(duty*5,[nominal],c)
 errs=[float((a-b).abs().max()) for a,b in zip(got[:3],ref)]
 assert errs[0]<1e-12 and max(errs)<1e-9,errs
 checks=[]
 for name in ['AHCT_typ_estimate','HCT_worst_secant']:
  rh,rl=CASES[name];result=evaluate_batch(duty[:32],[nominal],rh,rl)
  W,B,P,PB,G=nominal[0];C=np.diag(G.sum(0))-G.T@P
  errs=[]
  for i,d in enumerate(duty[:32].cpu().numpy()):
   gh=1/(10000+rh);gl=1/(10000+rl);g=d*gh+(1-d)*gl
   node=np.linalg.solve(C+np.diag(g),d*5*gh+G.T@PB)
   errs.append(float(np.max(abs(node-result[4][0,i].cpu().numpy()))))
  assert max(errs)<1e-7,max(errs)
  checks.append({'case':name,'numpy_direct_solve_node_max_error_V':max(errs)})
 return {'historical_adc_score_hidden_max_errors_V':[float((a-b).abs().max()) for a,b in zip(got[:3],ref)],'asymmetric_direct_solve':checks}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--boards',type=int,default=1000);ap.add_argument('--batch',type=int,default=10);args=ap.parse_args()
 start=time.time();torch.set_num_threads(4)
 c=json.loads((BASIC/'circuit.json').read_text());dataset=np.load(OLD/'data/test.npz')
 duty=mc.tensor(np.round(dataset['X'].astype(float)/5*63)/63)
 Y=torch.tensor(dataset['y'],device='cuda');nominal=mc.draw(c,None)
 net=json.loads((BASIC/'desired_netlist.json').read_text());count=np.zeros(64,dtype=int)
 for entries in net.values():
  for e in entries:
   if e.get('ref','').startswith('R1_'):
    for n in e['pads'].values():
     if n.startswith('IN_'):count[int(n.split('_')[1])]+=1
 out={'circuit_sha256':hashlib.sha256((BASIC/'circuit.json').read_bytes()).hexdigest(),
      'dataset_sha256':hashlib.sha256((OLD/'data/test.npz').read_bytes()).hexdigest(),
      'test_examples':len(Y),'boards_each':args.boards,'seed':51005,'device':torch.cuda.get_device_name(),
      'validation':validate(duty,c,nominal),'load_counts_per_input':count.tolist(),'cases':{}}
 assert len(Y)==10000
 for name,(rh,rl) in CASES.items():
  adc,s,h,extra,_=evaluate_batch(duty,[nominal],rh,rl,currents=True)
  correct=int((adc.argmax(2)==Y).sum())
  row={'Rh_ohms':rh,'Rl_ohms':rl,'correct':correct,'accuracy':correct/len(Y),'loading':extra,'rail_sensitivity':[]}
  for rail in [4.5,4.75,5.,5.25,5.5]:
   a,*_=evaluate_batch(duty,[nominal],rh,rl,rail)
   row['rail_sensitivity'].append({'rail_V':rail,'accuracy':float((a.argmax(2)==Y).double().mean())})
  out['cases'][name]=row
  print('nominal',name,correct,flush=True)
 assert out['cases']['historical_50ohm']['correct']==9454
 for tol in [.05,.01]:
  draws=draws_for(c,tol,args.boards)
  for name in ['ideal','AHCT_typ_estimate','AHCT_worst_secant','HCT_typ_graph','HCT_worst_secant','historical_50ohm']:
   rh,rl=CASES[name];samples=[];maxres=0.
   for i in range(0,args.boards,args.batch):
    a,s,h,extra,_=evaluate_batch(duty,draws[i:i+args.batch],rh,rl)
    samples.extend((a.argmax(2)==Y[None]).double().mean(1).cpu().tolist());maxres=max(maxres,extra['max_kcl_residual_V'])
   out['cases'][name]['mc_'+str(tol)]={'board_realizations':args.boards,'mean':float(np.mean(samples)),
    'worst':min(samples),'best':max(samples),'p05':float(np.quantile(samples,.05)),
    'std':float(np.std(samples,ddof=1)),'accuracy_samples':samples,'max_kcl_residual_V':maxres}
   print('MC',tol,name,np.mean(samples),min(samples),'seconds',time.time()-start,flush=True)
   (H/'metrics.json').write_text(json.dumps(out,indent=2)+'\n')
 out['seconds']=time.time()-start
 out['limitations']='Averaged PWM/DC ideal-opamp physical model, not transient RC ripple or measured I/V bounds. Worst secants are conservative sensitivity estimates derived at stated high current, NOT guaranteed resistances at sub-mA loads. AHCT high typical not published here;50ohm retains historical assumption;low17ohm read from TI graph. HCT typical28/29ohm read from TI graph. No part authenticity, simultaneous switching, opamp saturation commonmode failure, supply noise, propagation-delay or tolerance of driver strength across chips/pins. Common rail scales both layer bias terms and driver high, ADC3V3 fixed. Rail sweeps nominal only; MC uses5V to match existing1000-board setup. Static opamp13.5V and ReLU12.7V clips retained.'
 (H/'metrics.json').write_text(json.dumps(out,indent=2)+'\n')
 print('DONE',out['seconds'],flush=True)

if __name__=='__main__':main()
