import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import sys,gzip,json,time,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
PCB_EMU_DIR=Path(os.environ.get('PCB_EMU_DIR',str(ROOT.parent/'pcb-emu')))
sys.path.insert(0,str(PCB_EMU_DIR/'examples'))
from mnist_stack import area_downsample,drive_averaged_pwm
from pcb_emu import Board,Emulator
R=Path(os.environ.get('EMU_OUT',str(ROOT/'out/v2_emu_100')));E=None

def build(x,bodge):
 e=Emulator(ideal_copper=True)
 for b in x['boards']:e.add_board(Board(b['path'],b['board'],extracted=b))
 mb=e.boards['MB']
 for name,socket in [('DC0','JD0'),('DC1a','JS0'),('DC1b','JS1'),('DC1c','JS2'),('DC1d','JS3'),('DC2','JS4'),('DC3','JS5')]:e.plug(e.boards[name],'J0' if name=='DC0' else 'J_STRADDLE_EDGE',mb,socket)
 if bodge:e.add_jumper(mb.pin('JS1','B7'),mb.pin('JS2','B7'))
 for ref,pad,value in [('JP','1',15),('JP','2',0),('JP','3',-15),('JAR','1',3.3),('JSPI','3',0),('JSPI','4',0),('JSPI','5',0),('JSPI','6',0)]:e.drive(mb.pin(ref,pad),value)
 return e

def one(arg):
 i,image,label,ref,base=arg
 row={'index':i,'label':int(label),'float_prediction':int(ref),'matched_baseline_prediction':int(base)}
 try:
  drive_averaged_pwm(E,area_downsample(image));E.dc();mb=E.boards['MB']
  scores=np.array([E.read(mb.pin('JS5',f'B{j+1}')) for j in range(10)])
  adc=np.array([E.read(mb.pin('JAD',str(j+1))) for j in range(10)])
  row.update(prediction=int(adc.argmax()),scores=scores.tolist(),adc=adc.tolist())
 except Exception as exc:row['error']=f'{type(exc).__name__}: {exc}'
 print(i,row.get('prediction'),row.get('error',''),flush=True)
 return row

def main():
 global E
 x=json.loads((R/'extracted.json').read_text())
 raw=gzip.decompress((PCB_EMU_DIR/'data/t10k-images-idx3-ubyte.gz').read_bytes());lab=gzip.decompress((PCB_EMU_DIR/'data/t10k-labels-idx1-ubyte.gz').read_bytes())
 images=np.frombuffer(raw[16:],np.uint8).reshape(-1,28,28)[:100];labels=np.frombuffer(lab[8:],np.uint8)[:100]
 pixels=np.stack([area_downsample(im) for im in images]).astype(np.float32)/np.float32(63)*np.float32(5)
 file=(ROOT/'training/fixed_model/trained_float.npz');z=np.load(file)
 assert hashlib.sha256(file.read_bytes()).hexdigest()=='8b027bb984d25831fcc3bde7c4260406ca3abc54d458502665f1b3b9d4c40959'
 hidden=np.clip(pixels@z['w1'].T+z['b1'],0,12.7);scores=np.clip(hidden@z['w2'].T+z['b2'],-13.5,13.5);ref=scores.argmax(1)
 baseline=json.loads((PCB_EMU_DIR/'runs/matched_adaptive.json').read_text());assert baseline['correct']==958 and baseline['solver_failures']==0
 base=[r['prediction'] for r in sorted(baseline['samples'],key=lambda r:r['index'])[:100]]
 result={'count':100,'selection':'FIRST 100 official MNIST test images, indices 0..99','preprocessing':'crop intensity>20, padding2, square-expand, PIL BOX8x8, float32 six-bit PWM, averaged IC output drive','float_reference_correct':int((ref==labels).sum()),'float_reference_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'float_reference_formula':'clip(ReLU(X@w1.T+b1),0,12.7); clip(h@w2.T+b2,-13.5,13.5), matching non-QAT training forward','matched_baseline_correct':int((np.array(base)==labels).sum()),'physical_connectivity_from_copper_geometry':True,'ideal_intra_board_copper':True,'contact_resistance_ohms':0.02,'bodge_resistance_ohms':0.012,'source_audit':json.loads((R/'audit.json').read_text())}
 for bodge in [True,False]:
  mode='with_bodge' if bodge else 'without_bodge';t=time.perf_counter();E=build(x,bodge);E._compile();print('COMPILED',mode,len(E.nodes),len(E.edges),flush=True)
  with ProcessPoolExecutor(max_workers=32) as pool:rows=list(pool.map(one,[(i,images[i],labels[i],ref[i],base[i]) for i in range(100)]))
  solved=[r for r in rows if 'error' not in r]
  report={'correct':sum(r.get('prediction',-1)==r['label'] for r in rows),'solver_failures':100-len(solved),'disagreements_vs_float':sum(r['prediction']!=r['float_prediction'] for r in solved),'disagreements_vs_matched_baseline':sum(r['prediction']!=r['matched_baseline_prediction'] for r in solved),'seconds':time.perf_counter()-t,'samples':rows}
  (R/(mode+'.json')).write_text(json.dumps(report,indent=2));result[mode]=report
  (R/'result.json').write_text(json.dumps(result,indent=2));print(mode,json.dumps({k:v for k,v in report.items() if k!='samples'}),flush=True)
if __name__=='__main__':main()
