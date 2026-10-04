#!/usr/bin/python3
"""Sole-owner isolated 100x100 successor; no promotion."""
from pathlib import Path
import sys,json,hashlib,shutil,re,subprocess,traceback,time,collections
import pcbnew as p
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R))
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
S=R/'successor100'; S.mkdir(exist_ok=True)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def identity(b):
 rows={}
 for f in b.GetFootprints():
  rows[f.m_Uuid.AsString()]={'ref':f.GetReference(),'value':f.GetValue(),'fpid':f.GetFPID().GetUniStringLibId(),'pads':sorted((q.m_Uuid.AsString(),q.GetNumber(),q.GetNetname(),q.GetSize().x,q.GetSize().y,q.GetDrillSize().x,q.GetDrillSize().y,q.GetShape(),q.GetAttribute(),q.GetLayerSet().FmtHex()) for q in f.Pads())}
 return json.loads(json.dumps(rows))
def protected():
 files=list(R.parent.glob('*.kicad_pcb'))+list(R.parent.glob('*.kicad_pro'))+[R/'DC0.kicad_pcb',R/'motherboard.kicad_pcb']
 return {str(f):sha(f) for f in files}
def write(f,data): f.write_text(json.dumps(data,indent=2))
def drc(f,refill=False):
 out=f.with_name(f.stem+'_drc.json');cmd=['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(out)]
 if refill:cmd+=['--refill-zones','--save-board']
 q=subprocess.run(cmd+[str(f)],capture_output=True,text=True);f.with_name(f.stem+'_drc.log').write_text(q.stdout+q.stderr);d=json.loads(out.read_text())
 return {'errors':sum(v['severity']=='error' for v in d['violations']),'opens':len(d['unconnected_items']),'categories':dict(collections.Counter(v['type'] for v in d['violations'] if v['severity']=='error'))}
def prepare():
 write(S/'protected_before.json',protected());record={}
 for name in ['DC0','motherboard']:
  src=R/(name+'.kicad_pcb');b=p.LoadBoard(str(src));before=identity(b);physical=refs.physical(b)
  if name=='DC0':
   retained_shapes=list(b.GetDrawings());retained_footprints=list(b.GetFootprints());new_shapes=[]
   for g in retained_shapes:
    if g.GetLayer()==p.Edge_Cuts:b.Remove(g)
   for a,c in [((0,0),(100,0)),((100,0),(100,100)),((100,100),(0,100)),((0,100),(0,0))]:
    g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(xy(*a));g.SetEnd(xy(*c));g.SetLayer(p.Edge_Cuts);g.SetWidth(p.FromMM(.05));b.Add(g);new_shapes.append(g)
   for f in retained_footprints:
    r=f.GetReference()
    if r=='J0':f.SetPosition(f.GetPosition()+xy(0,60));continue
    if r.startswith(('RP','CP')):
     n=int(r[2:]);bank=n//8;k=n%8;f.SetPosition(xy(8.7+11.8*bank+(-2.7 if r.startswith('RP') else 2.7),40+6*k));f.SetOrientationDegrees(90)
    elif r.startswith('U'):f.SetPosition(xy(8.7+11.8*(int(r[1:])-1),22))
    elif r.startswith('C'):f.SetPosition(xy(8.7+11.8*(int(r[1:])-1),29))
    else:raise AssertionError(r)
   assert identity(b)==before
   si=silk.apply(b);assert si['clean'],si;write(S/'DC0_silk.json',si)
  else:assert refs.physical(b)==physical
  dest=S/(name+'.kicad_pcb');p.SaveBoard(str(dest),b)
  for ext in ['.kicad_pro','.kicad_dru']:
   if src.with_suffix(ext).exists():shutil.copyfile(src.with_suffix(ext),dest.with_suffix(ext))
  record[name]={'source':str(src),'source_sha':sha(src),'prepared_sha':sha(dest),'electrical_identity':identity(b)==before,'physical':refs.physical(b),'silk_clean':silk.audit(b)['clean'],'dimensions':[100,100]}
  write(S/(name+'_identity.json'),before)
  write(S/(name+'_placement_drc_summary.json'),drc(dest))
 write(S/'PLACEMENT.json',record)
def export(name):
 src=S/(name+'.kicad_pcb');b=p.LoadBoard(str(src));dsn=S/(name+'.dsn');assert p.ExportSpecctraDSN(b,str(dsn));text=dsn.read_text()
 text=re.sub(r'(\(rule\s*\(width\s+)[\d.]+',r'\g<1>250',text);text=re.sub(r'(\(clearance\s+)[\d.]+',r'\g<1>200',text)
 guards=''
 for n,(x1,y1,x2,y2) in enumerate([(-10000,-110000,500,10000),(99500,-110000,110000,10000),(-10000,-500,110000,10000),(-10000,-110000,110000,-99500)]):
  for layer in ['F.Cu','B.Cu']:guards+=f'    (keepout edge_guard_{n}_{layer} (rect {layer} {x1} {y1} {x2} {y2}))\n'
 text=text.replace('    (via ',guards+'    (via ',1);dsn.write_text(text);return dsn

def pour(f):
 b=p.LoadBoard(str(f));frozen=refs.physical(b)
 for z in list(b.Zones()):b.Delete(z)
 for layer in [p.F_Cu,p.B_Cu]:
  z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('GND'));z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.25));z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS);o=z.Outline();o.NewOutline()
  for x,y in [(.55,.55),(99.45,.55),(99.45,99.45),(.55,99.45)]:o.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
 p.SaveBoard(str(f),b);stats=drc(f,True);assert refs.physical(p.LoadBoard(str(f)))==frozen;return stats

def route(name):
 src=S/(name+'.kicad_pcb');b=p.LoadBoard(str(src));frozen=refs.physical(b);dsn=export(name);ses=dsn.with_suffix('.ses');jar=Path('/tmp/freerouting_actual48.jar');assert sha(jar)=='19d06499ff6424368d4861c2ede43849944d9cb62bf673cae7f5039ee6620c6d'
 with (S/(name+'_router.log')).open('w') as log: subprocess.run(['java','-Xmx4g','-jar',str(jar),'-de',str(dsn),'-do',str(ses),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=21600)
 assert ses.exists();assert p.ImportSpecctraSES(b,str(ses))
 for f in b.GetFootprints():
  old=frozen[f.m_Uuid.AsString()];new=f.GetPosition();assert abs(new.x-old['position'][0])<=1 and abs(new.y-old['position'][1])<=1;f.SetPosition(p.VECTOR2I(*old['position']))
 assert refs.physical(b)==frozen
 out=S/(name+'_routed.kicad_pcb');p.SaveBoard(str(out),b)
 for ext in ['.kicad_pro','.kicad_dru']:
  if src.with_suffix(ext).exists():shutil.copyfile(src.with_suffix(ext),out.with_suffix(ext))
 stats=pour(out);loaded=p.LoadBoard(str(out));stats.update(candidate=str(out),sha=sha(out),identity=identity(loaded)==json.loads((S/(name+'_identity.json')).read_text()),placement_unchanged=refs.physical(loaded)==frozen,silk_clean=silk.audit(loaded)['clean']);stats['strict_pass']=stats['errors']==0 and stats['opens']==0 and stats['identity'] and stats['placement_unchanged'] and stats['silk_clean'];write(S/(name+'_RESULT.json'),stats);return stats

def main():
 result={'release_authorized':False,'boards':{}}
 (S/'FINAL.json').unlink(missing_ok=True)
 try:
  prepare()
  for name in ['DC0','motherboard']:
   result['boards'][name]=route(name);write(S/'STATUS.json',result)
  result['strict_pass']=all(v['strict_pass'] for v in result['boards'].values())
 except Exception:result['error']=traceback.format_exc();print(result['error'],flush=True)
 finally:
  before=json.loads((S/'protected_before.json').read_text());after=protected();write(S/'protected_after.json',after);result['protected_unchanged']=before==after;write(S/'FINAL.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
