"""Reproduce trimmed WAV features and verify the delivered selected checkpoints."""
import json
import wave
from pathlib import Path
import numpy as np
import torch
from scipy.signal import sosfilt
from prepare import BAND_SETS, envelope_filters
from temporal import alignment_bounds, pool_interval, ALIGNMENT_LABELS

H=Path(__file__).resolve().parent

def main():
    base=np.load(H/"data/features_8x8.npz")
    torch.set_num_threads(8)
    for label in ALIGNMENT_LABELS:
        d=np.load(H/f"data/features_{label}.npz")
        p=json.loads((H/f"preprocess_{label}.json").read_text())
        for key in ["names","y","split"]:
            np.testing.assert_array_equal(d[key],base[key])
        assert d["X"].shape==(38908,64) and np.isfinite(d["X"]).all()
        assert d["X"].min()>=0 and d["X"].max()<=5
        np.testing.assert_allclose(d["X"]/5*63,np.round(d["X"]/5*63),atol=1e-5)
        np.testing.assert_array_equal(d["lo"],p["lo"])
        np.testing.assert_array_equal(d["hi"],p["hi"])
        assert p["scaling_fit"]=="training only" and p["speaker_sets_disjoint"]
        ids=[i for y in range(10) for s in range(3)
             for i in np.flatnonzero((d["y"]==y)&(d["split"]==s))[:2]]
        audio=[]
        for i in ids:
            with wave.open(str(H/"data"/str(d["names"][i]))) as w:
                a=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float32)/32768
            audio.append(np.pad(a[:16000],(0,max(0,16000-len(a)))))
        bounds=[alignment_bounds(x,label) for x in audio]
        if "-onset" in label:
            audio=[np.pad(x,(0,16000)) for x in audio]
        a=np.array(audio)
        if label.startswith("4"):
            filters=envelope_filters(BAND_SETS["4x16-alt"])
            power=np.stack([sosfilt(sos,a,axis=-1)**2 for sos in filters],axis=1)
            raw=np.array([np.log10(np.maximum(pool_interval(v,lo,hi,16),1e-10)).reshape(64)
                          for v,(lo,hi) in zip(power,bounds)])
        else:
            hz=lambda m:700*(10**(m/2595)-1)
            mel=lambda h:2595*np.log10(1+h/700)
            edges=hz(np.linspace(mel(20),mel(8000),10));f=np.linspace(0,8000,257)
            bank=np.maximum(0,np.minimum((f[None]-edges[:-2,None])/(edges[1:-1,None]-edges[:-2,None]),
                                         (edges[2:,None]-f[None])/(edges[2:,None]-edges[1:-1,None])))
            spec=torch.stft(torch.tensor(a),512,160,400,torch.hann_window(400),return_complex=True).abs().square()
            log=torch.log10((torch.tensor(bank,dtype=torch.float32)@spec).clamp(min=1e-10)).numpy()
            raw=np.array([pool_interval(v,lo/160,min(hi/160,v.shape[-1]),8).reshape(64)
                          for v,(lo,hi) in zip(log,bounds)])
        x=np.clip((raw-d["lo"])/np.maximum(d["hi"]-d["lo"],1e-6),0,1).astype("float32")
        np.testing.assert_array_equal(np.round(x*63)/63*5,d["X"][ids])
        print(label,"38908 IDs/splits and 60 exact WAV features PASS",flush=True)

    from train import Net, device
    from model import synthesize
    from train import e96
    for label in ALIGNMENT_LABELS:
        d=np.load(H/f"data/features_{label}.npz")
        m=json.loads((H/label/"metrics.json").read_text())
        xv=torch.tensor(d["X"][d["split"]==1],device=device)
        yv=torch.tensor(d["y"][d["split"]==1],device=device)
        f=torch.nn.Sequential(torch.nn.Linear(64,16),torch.nn.ReLU(),torch.nn.Linear(16,10)).to(device)
        f.load_state_dict(torch.load(H/label/"float.pt",weights_only=True,map_location=device))
        n=Net().to(device)
        n.load_state_dict(torch.load(H/label/"hardware.pt",weights_only=True,map_location=device))
        n.qat=True;n.noise=False
        with torch.no_grad():
            assert (f(xv).argmax(1)==yv).float().mean().item()==m["float_validation"]
            assert (n(xv).argmax(1)==yv).float().mean().item()==m["hardware_validation"]
        w=np.load(H/label/"trained_float.npz")
        for key,v in [("w1",n.fc1.weight),("b1",n.fc1.bias),("w2",n.fc2.weight),("b2",n.fc2.bias)]:
            np.testing.assert_array_equal(w[key],v.detach().cpu().numpy())
        c=json.loads((H/label/"circuit.json").read_text())
        assert c["layer1"]==synthesize(-w["w1"],-w["b1"],e96)
        assert c["layer2"]==synthesize(w["w2"],w["b2"],e96)
        print(label,"selected checkpoints and exact resistor exports PASS",flush=True)
if __name__=="__main__":main()
