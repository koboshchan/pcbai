import copy,csv,hashlib,json,sys,os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from pcb_emu.extract import extract_board
ROOT=Path(__file__).resolve().parents[2]
R=Path(os.environ.get('EMU_OUT',str(ROOT/'out/v2_emu_100')));R.mkdir(parents=True,exist_ok=True)
paths={'MB':str(ROOT/'boards/motherboard/post_crb.kicad_pcb'),'DC0':str(ROOT/'boards/dc0/DC0_verified.kicad_pcb'),'DC1a':str(ROOT/'boards/dc1/board.kicad_pcb'),'DC2':str(ROOT/'boards/dc2/daughtercard2_relu_l1_buffered_repaired.kicad_pcb'),'DC3':str(ROOT/'boards/dc3/dc3_universal.kicad_pcb')}
expected={'MB':'4932b44c','DC0':'899da15d','DC1a':'b5d0b202','DC2':'04167d23','DC3':'d7c2393f'}
def extract(pair):
 name,path=pair
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest().startswith(expected[name])
 b=extract_board(name,path)
 (R/(name+'_raw.json')).write_text(json.dumps(b))
 print('extracted',name,b['sha256'],list(b['report']['split_declared_nets']),len(b['report']['shorts']),flush=True)
 return b
if __name__=='__main__':
 with ProcessPoolExecutor(max_workers=5) as pool: boards=list(pool.map(extract,paths.items()))
 base=next(b for b in boards if b['board']=='DC1a');boards.remove(base)
 for name in ['DC1a','DC1b','DC1c','DC1d']:
  b=copy.deepcopy(base);b['board']=name
  for n in b['nets']:n['node']=n['node'].replace('DC1a_',name+'_')
  for c in b['components']:
   for p in c['pads'].values():p['node']=p['node'].replace('DC1a_',name+'_')
  byref={c['ref']:c for c in b['components']};file=(ROOT/'boards/dc1')/(name+'.csv')
  for row in csv.DictReader(file.open()):
   if not row['Reference'].startswith('R'):continue
   c=byref[row['Reference']]
   assert c['pads']['1']['label']==row['Pad1'] and c['pads']['2']['label']==row['Pad2']
   c['value']=row['Value'];c['dnp']=row['Value']=='DNP'
  b['population_csv']=str(file);b['population_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();boards.append(b)
 order=['MB','DC0','DC1a','DC1b','DC1c','DC1d','DC2','DC3'];boards.sort(key=lambda b:order.index(b['board']))
 x={'boards':boards};(R/'extracted.json').write_text(json.dumps(x))
 audit={b['board']:{'sha256':b['sha256'],'shorts':b['report']['shorts'],'split_declared_nets':b['report']['split_declared_nets'],'population_sha256':b.get('population_sha256')} for b in boards}
 (R/'audit.json').write_text(json.dumps(audit,indent=2));print('READY',flush=True)
