"""Fixed 400ms augmentation. Original sample identities remain the evaluation unit."""
import json, wave
from pathlib import Path
import numpy as np
import torch
from scipy.signal import sosfilt
from prepare import H,D,envelope_filters,BAND_SETS
from temporal import detected_region,pool_interval,VAD_CONFIG
N=6400
LABELS=["4x16-alt-aug400","8x8-aug400"]

def starts_for_region(region):
    lo,hi=(0,16000) if region is None else region
    if not 0<=lo<hi<=16000: raise ValueError("invalid region")
    if hi-lo>=N:
        starts=list(range(lo,hi-N+1,1600))
        if starts[-1]!=hi-N: starts.append(hi-N)
        return starts
    # End-aligned, start-aligned, centered. Never clamp to clip and shift the word.
    return [hi-N,lo,(lo+hi-N)//2]

def windows(audio):
    region=detected_region(audio)
    return starts_for_region(region),0 if region is None else region[0]

def padded_window(audio,start):
    out=np.zeros(N,dtype=np.asarray(audio).dtype)
    lo=max(0,start);hi=min(len(audio),start+N)
    if hi>lo:out[lo-start:hi-start]=audio[lo:hi]
    return out

def raw_features(audio,starts,label):
    """Filter the full original clip before pooling, including original pre-window history.
    Zero padding extends the original recording, not the detected word. No time resizing.
    STFT uses 25ms Hann, 10ms hop, 512 FFT, triangular mel, then exact fractional
    frame-cell pooling of log power over 50ms bins. Four-band uses 25ms means
    of causal SOS power then log10. All 64 features are band-major.
    """
    a=np.asarray(audio,dtype=np.float32)
    if a.shape!=(16000,):raise ValueError("expected 1s")
    padded=np.pad(a,(N,N))
    if label.startswith("4x16"):
        power=np.stack([sosfilt(sos,padded)**2 for sos in envelope_filters(BAND_SETS["4x16-alt"])])
        return np.array([np.log10(np.maximum(pool_interval(power,s+N,s+N+N,16),1e-10)).reshape(64) for s in starts])
    hz=lambda m:700*(10**(m/2595)-1)
    mel=lambda f:2595*np.log10(1+f/700)
    edges=hz(np.linspace(mel(20),mel(8000),10));f=np.linspace(0,8000,257)
    bank=np.maximum(0,np.minimum((f[None]-edges[:-2,None])/(edges[1:-1,None]-edges[:-2,None]),(edges[2:,None]-f[None])/(edges[2:,None]-edges[1:-1,None])))
    spec=torch.stft(torch.tensor(padded),512,160,400,torch.hann_window(400),return_complex=True).abs().square()
    log=torch.log10((torch.tensor(bank,dtype=torch.float32)@spec).clamp(min=1e-10)).numpy()
    return np.array([pool_interval(log,(s+N)/160,(s+N+N)/160,8).reshape(64) for s in starts])

def read_audio(name):
    with wave.open(str(D/name)) as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(16000,1,2)
        a=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float32)/32768
    return np.pad(a[:16000],(0,max(0,16000-len(a))))

def scale(raw,lo,hi):
    return (np.round(np.clip((raw-lo)/np.maximum(hi-lo,1e-6),0,1)*63)/63*5).astype("float32")

def prepare(label):
    out=D/f"features_{label}.npz"
    if out.exists():return
    torch.set_num_threads(1)
    source=np.load(D/"features_8x8.npz")
    names,y,split=source["names"],source["y"],source["split"]
    raw=[];onset=[];ids=[];starts=[];onsets=[]
    for i,name in enumerate(names):
        a=read_audio(str(name));ss,oo=windows(a)
        both=raw_features(a,ss+[oo],label)
        raw.extend(both[:-1]);onset.append(both[-1]);ids.extend([i]*len(ss));starts.extend(ss);onsets.append(oo)
        if i%5000==0:print(label,"features",i,flush=True)
    raw=np.array(raw);onset=np.array(onset);ids=np.array(ids);starts=np.array(starts)
    lo=np.quantile(raw[split[ids]==0],.01,axis=0);hi=np.quantile(raw[split[ids]==0],.99,axis=0)
    meta={"layout":label,"duration_samples":N,"duration_ms":400,"sample_rate":16000,
      "slice_ms":25 if label.startswith("4") else 50,
      "vad":{**VAD_CONFIG,"margin_samples":0,"minimum_samples":None},
      "augmentation":"raw detected bounds; >400ms slide 100ms plus final end-aligned; exactly400 one; short end/start/center",
      "fallback":"whole original one-second clip, seven windows at 0..600ms",
      "padding":"original surrounding audio, may contain background; zeros only outside original 1s; never shift or truncate word",
      "filter_history":"full original clip plus 400ms zeros either side before filtering; causal SOS preserves original history; STFT noncausal centered context preserved",
      "pooling":"fixed400ms, no variable-time resizing, band-major; 4band power means then log; 8band log-mel fractional frame-cell means",
      "optimization":"expanded training windows only; no expanded validation/test independent identities",
      "scaling_fit":"1st/99th percentiles expanded TRAIN windows only; quantized6bit 0..5V",
      "checkpoint_selection":"realtime single-onset400 validation accuracy, first best; hardware only QAT epochs15..59",
      "evaluation":"per original clip; expanded mode averages output scores then argmax, realtime uses one onset400 window",
      "lo":lo.tolist(),"hi":hi.tolist()}
    (H/f"preprocess_{label}.json").write_text(json.dumps(meta,indent=2))
    np.savez_compressed(out,X=scale(raw,lo,hi),onset=scale(onset,lo,hi),y=y,split=split,names=names,ids=ids,starts=starts,onset_starts=np.array(onsets),lo=lo,hi=hi)
    print(label,"prepared",len(names),len(ids),flush=True)
