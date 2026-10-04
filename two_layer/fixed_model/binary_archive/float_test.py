"""Held-out unquantized float checkpoint test, no selection or retraining."""
from pathlib import Path
import json,numpy as np,torch
H=Path(__file__).resolve().parent
assert torch.cuda.is_available()
d=np.load(H/'data/test.npz');X=torch.tensor((d['X']>=2.5)*5,device='cuda',dtype=torch.float64);y=torch.tensor(d['y'],device='cuda')
w=np.load(H/'trained_float.npz');t={k:torch.tensor(w[k],device='cuda',dtype=torch.float64) for k in w.files}
with torch.no_grad():
 h=torch.relu(X@t['w1'].T+t['b1']);s=h@t['w2'].T+t['b2'];correct=int((s.argmax(1)==y).sum().item())
 # A second diagnostic isolates clipping from resistor quantization/loading.
 hc=h.clamp(max=9.2);sc=(hc@t['w2'].T+t['b2']).clamp(-10,10);clip_correct=int((sc.argmax(1)==y).sum().item())
result={'test_examples':len(y),'dataset':'official MNIST test split; frozen cached original8x8 crop/BOX preprocessing;binary threshold2.5V into0/5V','checkpoint':'trained_float.npz same validation-selected weights behind physical manifest','device':torch.cuda.get_device_name(),'dtype':'float64','float_unquantized_no_loading_no_clipping':{'correct':correct,'accuracy':correct/len(y)},'float_clipping_only_no_loading_no_quantization':{'correct':clip_correct,'accuracy':clip_correct/len(y)},'test_used_for_selection':False}
(H/'float_test.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
