"""Independent artifacts, split identity, feature reproduction and checkpoint checks."""
import json
import numpy as np
import torch
import train as tr
from window400 import *
from train400 import evaluate_scores
def check(label):
 d=np.load(D/f"features_{label}.npz");s=d["split"];ids=d["ids"];y=d["y"]
 original=np.load(D/"features_8x8.npz")
 for k in ["names","y","split"]:np.testing.assert_array_equal(d[k],original[k])
 speakers=[{Path(n).stem.split("_nohash_")[0] for n in d["names"][s==i]} for i in range(3)]
 assert all(not speakers[i]&speakers[j] for i in range(3) for j in range(i))
 assert np.array_equal(np.unique(ids),np.arange(len(s)))
 # Reproduce sixty original WAV identities, twenty per split, all windows + onset.
 selected=np.concatenate([np.random.default_rng(400+i).choice(np.flatnonzero(s==i),20,replace=False) for i in range(3)])
 for i in selected:
  a=read_audio(str(d["names"][i]));ss,on=windows(a);ix=np.flatnonzero(ids==i)
  np.testing.assert_array_equal(d["starts"][ix],ss);assert d["onset_starts"][i]==on
  f=scale(raw_features(a,ss+[on],label),d["lo"],d["hi"])
  np.testing.assert_array_equal(d["X"][ix],f[:-1]);np.testing.assert_array_equal(d["onset"][i],f[-1])
 # Recompute scaler from ALL expanded training windows, without reading heldout audio.
 raw=[]
 for i in np.flatnonzero(s==0):
  a=read_audio(str(d["names"][i]));ss,_=windows(a);raw.extend(raw_features(a,ss,label))
 raw=np.array(raw)
 np.testing.assert_array_equal(np.quantile(raw,.01,axis=0),d["lo"])
 np.testing.assert_array_equal(np.quantile(raw,.99,axis=0),d["hi"])
 out=H/label;m=json.loads((out/"metrics.json").read_text())
 assert m["float_validation"]==max(v["float_validation"] for v in m["logs"])
 assert m["hardware_validation"]==max(v["hardware_validation"] for v in m["logs"][15:])
 xv=torch.tensor(d["onset"][s==1],device=tr.device);yv=torch.tensor(y[s==1],device=tr.device)
 fn=torch.nn.Sequential(torch.nn.Linear(64,16),torch.nn.ReLU(),torch.nn.Linear(16,10)).to(tr.device)
 fn.load_state_dict(torch.load(out/"float.pt",weights_only=True))
 net=tr.Net().to(tr.device);net.load_state_dict(torch.load(out/"hardware.pt",weights_only=True));net.qat=True;net.noise=False
 with torch.no_grad():
  assert (fn(xv).argmax(1)==yv).float().mean().item()==m["float_validation"]
  assert (net(xv).argmax(1)==yv).float().mean().item()==m["hardware_validation"]
 w=np.load(out/"trained_float.npz")
 for k,v in dict(w1=net.fc1.weight,b1=net.fc1.bias,w2=net.fc2.weight,b2=net.fc2.bias).items():np.testing.assert_array_equal(w[k],v.detach().cpu().numpy())
 c=json.loads((out/"circuit.json").read_text())
 assert c["layer1"]==tr.synthesize(-w["w1"],-w["b1"],tr.e96)
 assert c["layer2"]==tr.synthesize(w["w2"],w["b2"],tr.e96)
 n=int((s==2).sum())
 assert m["counts"]=={k:int((s==i).sum()) for i,k in enumerate(["train","validation","test"])}
 for k,r in m["modes"].items():
  for ck,ak in [("float_confusion","float_test_accuracy"),("hardware_confusion","hardware_nominal_accuracy")]:
   cm=np.array(r[ck]);assert cm.sum()==n;assert np.trace(cm)/n==r[ak]
  samples=np.array(r["mc"]["accuracy_samples"]);assert len(samples)==1000
  assert samples.mean()==r["mc"]["mean"];np.testing.assert_allclose(samples*n,np.round(samples*n),atol=1e-9)
 assert m["same_board_draws_both_modes"] and not m["test_used_for_selection"]
 print("PASS",label,"60 original WAVs; full training-only scaler; split identities; checkpoints; exact export; counts/confusions/1000 board samples",flush=True)
if __name__=="__main__":
 torch.set_num_threads(1)
 for label in LABELS:check(label)
