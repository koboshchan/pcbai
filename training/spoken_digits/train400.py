"""Two fixed-window experiments, separate summary so legacy baseline schema is unchanged."""
import json
import numpy as np
import torch
import train as tr
from window400 import H,D,LABELS,prepare
def evaluate_scores(scores,ids,n):
    # Scores may be float logits or physical ADC output voltages, never class votes.
    grouped=torch.zeros((scores.shape[0],n,10),dtype=scores.dtype,device=scores.device)
    grouped.index_add_(1,ids,scores)
    counts=torch.bincount(ids,minlength=n)
    assert torch.all(counts>0)
    return grouped/counts[None,:,None]

def run(label):
    torch.manual_seed(42064);np.random.seed(42064)
    out=H/label;out.mkdir(exist_ok=True)
    d=np.load(D/f"features_{label}.npz")
    X,y,split,ids=d["X"],d["y"],d["split"],d["ids"]
    x=torch.tensor(X[split[ids]==0],device=tr.device);yy=torch.tensor(y[ids[split[ids]==0]],device=tr.device)
    xv=torch.tensor(d["onset"][split==1],device=tr.device);yv=torch.tensor(y[split==1],device=tr.device)
    testids=np.flatnonzero(split==2);remap=np.full(len(y),-1);remap[testids]=np.arange(len(testids))
    mask=split[ids]==2;groupids=torch.tensor(remap[ids[mask]],device=tr.device)
    xn=X[mask].astype(float);realtime=d["onset"][split==2].astype(float);yn=y[split==2]
    # One combined tensor allows identical board draws for both inference modes.
    allx=np.concatenate([xn,realtime]);gpu=tr.mc.tensor(allx);n=len(yn);nw=len(xn)
    def predictions(scores):
        expanded=evaluate_scores(scores[:,:nw],groupids,n).argmax(2)
        return {"expanded_average":expanded,"realtime_onset":scores[:,nw:].argmax(2)}
    floatnet=torch.nn.Sequential(torch.nn.Linear(64,16),torch.nn.ReLU(),torch.nn.Linear(16,10)).to(tr.device)
    opt=torch.optim.Adam(floatnet.parameters(),lr=.0015);best=-1;logs=[]
    for epoch in range(60):
        for ix in torch.randperm(len(x),device=tr.device).split(512):
            opt.zero_grad();loss=torch.nn.functional.cross_entropy(floatnet(x[ix]),yy[ix]);loss.backward();opt.step()
        with torch.no_grad():acc=(floatnet(xv).argmax(1)==yv).float().mean().item()
        if acc>best:best=acc;torch.save(floatnet.state_dict(),out/"float.pt")
        logs.append({"epoch":epoch,"float_validation":acc})
    floatnet.load_state_dict(torch.load(out/"float.pt",weights_only=True))
    with torch.no_grad():fp={k:v[0].cpu().numpy() for k,v in predictions(floatnet(torch.tensor(allx,dtype=torch.float32,device=tr.device))[None]).items()}
    net=tr.Net().to(tr.device)
    net.fc1.load_state_dict(floatnet[0].state_dict());net.fc2.load_state_dict(floatnet[2].state_dict())
    opt=torch.optim.Adam(net.parameters(),lr=.0015);besthw=-1
    for epoch in range(60):
        net.qat=epoch>=15;net.noise=epoch>=25
        for ix in torch.randperm(len(x),device=tr.device).split(512):
            opt.zero_grad();loss=torch.nn.functional.cross_entropy(net(x[ix]),yy[ix]);loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),5);opt.step()
        net.noise=False
        with torch.no_grad():acc=(net(xv).argmax(1)==yv).float().mean().item()
        logs[epoch]["hardware_validation"]=acc
        print(label,"hardware",epoch,acc,flush=True)
        if net.qat and acc>besthw:besthw=acc;torch.save(net.state_dict(),out/"hardware.pt")
    net.load_state_dict(torch.load(out/"hardware.pt",weights_only=True))
    weights={k:v.detach().cpu().numpy() for k,v in dict(w1=net.fc1.weight,b1=net.fc1.bias,w2=net.fc2.weight,b2=net.fc2.bias).items()}
    c=json.loads((tr.F/"circuit.json").read_text());c.pop("shared_5V_rail",None)
    c.update(input="64 fixed400ms spoken-digit features,6bit PWM0..5V,10050ohm sources",preprocessing=f"../preprocess_{label}.json",status="validation-selected experiment, not fabricated-board weights")
    c["layer1"]=tr.synthesize(-weights["w1"],-weights["b1"],tr.e96);c["layer2"]=tr.synthesize(weights["w2"],weights["b2"],tr.e96)
    (out/"circuit.json").write_text(json.dumps(c,indent=2));np.savez(out/"trained_float.npz",**weights)
    regress=[]
    # Compare all inference windows, not just one mode.
    for seed in [None,51005,51006,51007]:
        draw=tr.mc.draw(c,None if seed is None else np.random.default_rng(seed))
        ref=tr.infer(allx,c,None if seed is None else np.random.default_rng(seed),source_ohms=draw[4])
        got=tr.mc.run(gpu,[draw],c)
        errors=[float(np.max(abs(t[0].cpu().numpy()-v))) for t,v in zip(got,ref)]
        assert errors[0]<1e-12 and max(errors[1:])<1e-9,errors
        regress.append({"seed":seed,"errors":errors})
    nominal={k:v[0].cpu().numpy() for k,v in predictions(tr.mc.run(gpu,[tr.mc.draw(c,None)],c)[0]).items()}
    rng=np.random.default_rng(51005);samples={k:[] for k in nominal};Y=torch.tensor(yn,device=tr.device)
    for i in range(0,1000,10):
        scores=tr.mc.run(gpu,[tr.mc.draw(c,rng) for _ in range(10)],c)[0]
        for k,p in predictions(scores).items():samples[k].extend((p==Y[None]).double().mean(1).cpu().tolist())
        if i%200==0:print(label,"MC",i+10,flush=True)
    modes={}
    for k,accs in samples.items():
        modes[k]={"float_test_accuracy":float((fp[k]==yn).mean()),"hardware_nominal_accuracy":float((nominal[k]==yn).mean()),
          "float_confusion":tr.confusion(yn,fp[k]),"hardware_confusion":tr.confusion(yn,nominal[k]),
          "mc":{"boards":1000,"seed":51005,"accuracy_samples":accs,"mean":float(np.mean(accs)),"min":min(accs),"max":max(accs),"std":float(np.std(accs)),"p05":float(np.quantile(accs,.05))}}
    metrics={"layout":label,"seed":42064,"epochs":60,"counts":{k:int((split==i).sum()) for i,k in enumerate(["train","validation","test"])},
      "window_counts":{k:int((split[ids]==i).sum()) for i,k in enumerate(["train","validation","test"])},
      "float_validation":best,"hardware_validation":besthw,"checkpoint_mode":"realtime_onset",
      "same_board_draws_both_modes":True,"test_used_for_selection":False,"modes":modes,"logs":logs,"solver_regression":regress}
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2));print("RESULT",label,json.dumps(modes),flush=True)
    return metrics
if __name__=="__main__":
    results=[]
    for label in LABELS:
        prepare(label);results.append(run(label))
    (H/"summary400.json").write_text(json.dumps({"chosen_by_hardware_validation":max(results,key=lambda x:x["hardware_validation"])["layout"],"results":[{k:v for k,v in m.items() if k not in ["logs"]} for m in results]},indent=2))
