#!/usr/bin/python3
"""Held-out nominal class margins and bounded ADC-error sensitivity, not hardware ENOB."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import torch
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'fixed_model'))
from cuda_mc import tensor,draw,run,noisegain

@torch.no_grad()
def main():
 c=json.loads((H/'fixed_model/circuit.json').read_text())
 data=np.load(H/'fixed_model/data/test.npz')
 X=tensor(np.round(data['X'].astype(float)/5*63)/63*5)
 Y=torch.as_tensor(data['y'],device='cuda')
 adc,scores,hidden=run(X,[draw(c,None)],c)
 adc=adc[0];scores=scores[0]
 values,indices=scores.topk(2,dim=1)
 gap=values[:,0]-values[:,1]
 nominal=(adc.argmax(1)==Y)
 # True-class gap is positive only if the true class strictly beats every alternative.
 rivals=adc.clone();rivals[torch.arange(len(Y),device='cuda'),Y]=-torch.inf
 true_gap=adc[torch.arange(len(Y),device='cuda'),Y]-rivals.max(1).values
 out={'model_sha256':hashlib.sha256((H/'fixed_model/circuit.json').read_bytes()).hexdigest(),
      'dataset':'official held-out MNIST10000, six-bit quantized grayscale',
      'device':torch.cuda.get_device_name(), 'nominal_correct':int(nominal.sum()),
      'score_top_two_gap_V_quantiles':dict(zip(['min','p01','p05','median','p95','max'],torch.quantile(gap,tensor([0,.01,.05,.5,.95,1])).cpu().tolist())),
      'ADC_LSB_V':3.3/4095,'nominal_score_to_ADC_gain':1/21,
      'neural_noise_gain':{'layer1':noisegain(c['layer1']).tolist(),'layer2':noisegain(c['layer2']).tolist()},
      'bounded_independent_ADC_error':[],
      'fabrication_ready':False,
      'limitations':'Nominal resistor-only static model, optimistic loaded swing, ideal12bit ADC. Each deterministic bound allows independent adversarial per-channel error after ideal conversion, not measured noise, ENOB, DNL or an error distribution. Classification stability is a sufficient condition only; zero gaps/ties cannot be certified. No automatic oversampling/averaging claim.'}
 for lsb in [0,1,2,4,8,16,32]:
  bound=lsb*3.3/4095
  # Each pairwise gap may shrink by twice the channel error bound.
  guaranteed=true_gap>2*bound
  stable=(values[:,0]-values[:,1])/21>2*bound+2*3.3/4095
  out['bounded_independent_ADC_error'].append({'per_channel_bound_LSB':lsb,'per_channel_bound_V':bound,
    'guaranteed_correct_under_bound':int(guaranteed.sum()),
    'guaranteed_correct_fraction':float(guaranteed.double().mean()),
    'prediction_stability_sufficient_count_including_quantization_guard':int(stable.sum())})
 (H/'adc_class_margin_audit.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__': main()
