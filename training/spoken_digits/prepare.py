"""Stream official Speech Commands v2, retaining digits and official split lists only."""
import tarfile,urllib.request,hashlib,json,wave
from pathlib import Path
import numpy as np
import torch
H=Path(__file__).resolve().parent
D=H/'data'; D.mkdir(exist_ok=True)
CLASSES=['zero','one','two','three','four','five','six','seven','eight','nine']
URL='https://storage.googleapis.com/download.tensorflow.org/data/speech_commands_v0.02.tar.gz'
def download():
 if (D/'download_complete.json').exists() and (D/'validation_list.txt').exists() and (D/'testing_list.txt').exists():return
 req=urllib.request.urlopen(URL,timeout=120)
 sha=hashlib.sha256()
 class Reader:
  def read(self,n=-1):
   b=req.read(n);sha.update(b);return b
 count=0
 with tarfile.open(fileobj=Reader(),mode='r|gz') as tar:
  for m in tar:
   p=Path(m.name)
   if m.isfile() and (p.as_posix() in ['validation_list.txt','testing_list.txt','LICENSE','README.md'] or (len(p.parts)==2 and p.parts[0] in CLASSES and p.suffix=='.wav')):
    dest=D/p;dest.parent.mkdir(exist_ok=True)
    dest.write_bytes(tar.extractfile(m).read());count+=1
    if count%5000==0:print('download retained',count,flush=True)
 # Drain response so checksum covers complete compressed archive.
 while True:
  chunk=req.read(1024*1024)
  if not chunk:break
  sha.update(chunk)
 assert sha.hexdigest()=='af14739ee7dc311471de98f5f9d2c9191b18aedfe957f4a6ff791c709868ff58'
 (D/'download_complete.json').write_text(json.dumps({'url':URL,'compressed_stream_sha256':sha.hexdigest(),'retained_files':count}))
def features(bands,slices):
 out=D/f'features_{bands}x{slices}.npz'
 if out.exists():return
 torch.set_num_threads(8)
 val=set((D/'validation_list.txt').read_text().splitlines());test=set((D/'testing_list.txt').read_text().splitlines())
 # Fixed 20Hz..8kHz triangular mel bank, 25ms windows / 10ms hop.
 hz=lambda m:700*(10**(m/2595)-1)
 mel=lambda h:2595*np.log10(1+h/700)
 edges=hz(np.linspace(mel(20),mel(8000),bands+2))
 f=np.linspace(0,8000,257); bank=np.maximum(0,np.minimum((f[None]-edges[:-2,None])/(edges[1:-1,None]-edges[:-2,None]),(edges[2:,None]-f[None])/(edges[2:,None]-edges[1:-1,None])))
 bank=torch.tensor(bank,dtype=torch.float32)
 xs=[];ys=[];splits=[];names=[]
 for yi,c in enumerate(CLASSES):
  files=sorted((D/c).glob('*.wav'))
  for start in range(0,len(files),256):
   batch=files[start:start+256];audio=[]
   for p in batch:
    with wave.open(str(p)) as w:
     assert w.getframerate()==16000 and w.getnchannels()==1 and w.getsampwidth()==2
     a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768
    audio.append(np.pad(a[:16000],(0,max(0,16000-len(a)))))
   a=torch.tensor(np.array(audio))
   spec=torch.stft(a,512,160,400,torch.hann_window(400),return_complex=True).abs().square()
   log=torch.log10((bank@spec).clamp(min=1e-10))
   feat=torch.stack([x.mean(-1) for x in torch.tensor_split(log,slices,dim=-1)],-1).reshape(len(batch),64).numpy()
   xs.extend(feat);ys.extend([yi]*len(batch))
   for p in batch:
    rel=p.relative_to(D).as_posix();names.append(rel);splits.append(2 if rel in test else 1 if rel in val else 0)
  print('features',bands,slices,c,len(xs),flush=True)
 X=np.array(xs);s=np.array(splits);train=X[s==0]
 # Train-only per-feature robust scaling. Clip validation/test without fitting them.
 lo=np.quantile(train,.01,axis=0);hi=np.quantile(train,.99,axis=0)
 speaker_sets=[{Path(names[i]).stem.split('_nohash_')[0] for i in np.where(s==k)[0]} for k in range(3)]
 assert all(not speaker_sets[i]&speaker_sets[j] for i in range(3) for j in range(i))
 (H/f'preprocess_{bands}x{slices}.json').write_text(json.dumps({'bands':bands,'slices':slices,'lo':lo.tolist(),'hi':hi.tolist(),'scaling_fit':'training only','speaker_sets_disjoint':True},indent=2))
 X=np.clip((X-lo)/np.maximum(hi-lo,1e-6),0,1).astype('float32')
 np.savez_compressed(out,X=np.round(X*63)/63*5,y=np.array(ys),split=s,names=np.array(names),lo=lo,hi=hi)
if __name__=='__main__':
 download()
 for b,s in [(8,8),(16,4)]:features(b,s)
