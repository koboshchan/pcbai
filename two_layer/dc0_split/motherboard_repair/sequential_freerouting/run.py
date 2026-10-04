#!/usr/bin/python3
from pathlib import Path
import sys,json,shutil,re,subprocess,hashlib,collections
import pcbnew as p
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R));import successor100 as s;import motherboard_refs as refs;import shortrefs_motherboard_silk as silk
src=D.parent/'motherboard.kicad_pcb';dc=R/'successor100/DC0_routed.kicad_pcb'
def write(n,x):s.write(D/n,x)
def copper(b):
 return {t.m_Uuid.AsString():[t.GetNetname(),t.GetLayer(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth(), isinstance(t,p.PCB_VIA),t.GetDrillValue() if isinstance(t,p.PCB_VIA) else None] for t in b.GetTracks()}
def protected():
 return {str(f):s.sha(f) for f in R.parent.rglob('*') if f.is_file() and f.suffix in ['.kicad_pcb','.kicad_pro','.kicad_dru'] and D not in f.parents}
def prepare():
 assert s.sha(src)=='a749ddb28801bfe1e609fdd965f86a186c0d8dd8e2f8850e9b1753c224348d0c';assert s.sha(dc)=='1196b0d47c1c553b22a4061d3ac7e1c41cbf3d4a35dd5b7f1d4cda102bfdb34a'
 write('protected_before.json',protected());b=p.LoadBoard(str(src));write('baseline_copper.json',copper(b));write('baseline_identity.json',s.identity(b));write('baseline_physical.json',refs.physical(b))
 for ext in ['.kicad_pro','.kicad_dru']:
  project=R/'successor100/motherboard_routed';f=project.with_suffix(ext)
  if f.exists():shutil.copyfile(f,D/('pre_crb'+ext))
 zones=list(b.Zones())
 for z in zones:b.Remove(z)
 dsn=D/'locked.dsn';assert p.ExportSpecctraDSN(b,str(dsn));text=dsn.read_text();idx=text.rfind('(wiring');assert idx>0;head,tail=text[:idx],text[idx:];count=len(b.GetTracks());tail,n=re.subn(r'\(type\s+\w+\)', '(type fix)',tail);assert n==len(re.findall(r'\((?:wire|via)\s',tail)),(n,count);assert n>0
 guards=''
 for i,(x1,y1,x2,y2) in enumerate([(-10000,-110000,600,10000),(99400,-110000,110000,10000),(-10000,-600,110000,10000),(-10000,-110000,110000,-99400)]):
  for layer in ['F.Cu','B.Cu']:guards+=f'    (keepout edge_guard_{i}_{layer} (rect {layer} {x1} {y1} {x2} {y2}))\n'
 head=head.replace('    (via ',guards+'    (via ',1);dsn.write_text(head+tail)
 write('DSN_FIXED_AUDIT.json',{'tracks_and_vias':count,'type_fix_count':n,'all_existing_fixed':True,'source_reference':'https://github.com/freerouting/freerouting/blob/master/src_v19/main/java/app/freerouting/designforms/specctra/Wiring.java','encoding':'type fix maps SYSTEM_FIXED','zones_omitted_for_signal_router_only':len(zones),'source_opens':['ADC_2','IN_58']})
 with (D/'locked_router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual48.jar','-de',str(dsn),'-do',str(D/'locked.ses'),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True)
 write('ROUTER_FINISHED.json',{'session_exists':(D/'locked.ses').exists()})
if __name__=='__main__':prepare()
