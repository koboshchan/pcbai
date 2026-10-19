"""Small real-WAV check only. Never downloads, fits a model or writes feature caches."""
import json
import wave
import numpy as np
import torch
from prepare import D, H, CLASSES, extract_batch, envelope_features, envelope_filters, BAND_SETS
from temporal import ALIGNMENT_LABELS, alignment_bounds, alignment_config

def main():
    torch.set_num_threads(2)
    val=set((D/"validation_list.txt").read_text().splitlines())
    test=set((D/"testing_list.txt").read_text().splitlines())
    files=[next(p for p in sorted((D/c).glob("*.wav"))
                if p.relative_to(D).as_posix() not in val|test) for c in CLASSES[:6]]
    audio=[]
    for p in files:
        with wave.open(str(p)) as w:
            assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(16000,1,2)
            a=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float32)/32768
        audio.append(np.pad(a[:16000],(0,max(0,16000-len(a)))))
    for label in ALIGNMENT_LABELS:
        x=extract_batch(audio,label)
        assert x.shape==(6,64) and np.isfinite(x).all()
        single=np.concatenate([extract_batch([a],label) for a in audio])
        np.testing.assert_allclose(x,single,rtol=1e-6,atol=1e-6)
        for a in audio:
            lo,hi=alignment_bounds(a,label)
            assert 0<=lo<hi<=32000
            if "-onset" in label:
                assert hi-lo==int(label.rsplit("onset",1)[1])*16
                assert alignment_config(label)["margin_samples"]==0
        print(label,"6 training WAVs, 64 finite features, batch parity and bounds PASS")
    # Confirm extracting controls still reproduces the committed quantized cache.
    for label in ["4x16-alt","8x8"]:
        d=np.load(D/f"features_{label}.npz")
        names=d["names"].tolist()
        indexes=[names.index(p.relative_to(D).as_posix()) for p in files]
        x=extract_batch(audio,label)
        scaled=np.clip((x-d["lo"])/np.maximum(d["hi"]-d["lo"],1e-6),0,1).astype("float32")
        np.testing.assert_array_equal(np.round(scaled*63)/63*5,d["X"][indexes])
        print(label,"6 unchanged control feature vectors match cache exactly")
    # Late onsets must retain exact duration even past the original capture.
    late=np.zeros(16000,dtype=np.float32)
    late[12800:]=.2*np.sin(np.arange(3200))
    for label in ALIGNMENT_LABELS:
        x=extract_batch([late,np.zeros(16000,dtype=np.float32)],label)
        assert x.shape==(2,64) and np.isfinite(x).all()
    print("late onset zero-padding and silent fallback feature extraction PASS")

if __name__=="__main__":main()
