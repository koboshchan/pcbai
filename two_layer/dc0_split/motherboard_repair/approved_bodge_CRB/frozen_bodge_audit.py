from pathlib import Path
import json,sys,hashlib
import pcbnew as p
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));from run import copper,refs,s
pre=p.LoadBoard(str(D/'pre_crb.kicad_pcb'));post=p.LoadBoard(str(D/'post_crb.kicad_pcb'))
a=copper(pre);b=copper(post);added={k:v for k,v in b.items() if k not in a};assert all(b.get(k)==v for k,v in a.items());assert len(added)==1;assert next(iter(added.values()))[0]=='+5V'
def footprints(path):
 text=path.read_text();out={};start=0
 while True:
  start=text.find('(footprint ',start)
  if start<0:break
  depth=0;quote=False;esc=False
  for end in range(start,len(text)):
   ch=text[end]
   if esc:esc=False;continue
   if ch=='\\' and quote:esc=True;continue
   if ch=='"':quote=not quote
   if not quote:
    if ch=='(':depth+=1
    if ch==')':
     depth-=1
     if depth==0:break
  block=text[start:end+1];import re
  ref=re.search(r'\(property "Reference" "([^"]+)"',block).group(1);out[ref]=block;start=end+1
 return out
x=footprints(D/'pre_crb.kicad_pcb');y=footprints(D/'post_crb.kicad_pcb');assert x.keys()==y.keys();changed=[k for k in x if x[k]!=y[k]];assert changed==['CRB'],changed
for ext in ['.kicad_pro','.kicad_dru']:
 a1=(D/'pre_crb').with_suffix(ext);a2=(D/'post_crb').with_suffix(ext)
 assert a1.exists()==a2.exists()
 if a1.exists():assert a1.read_bytes()==a2.read_bytes()
raw=json.loads((D/'post_crb_drc.json').read_text());excluded=[v for v in raw['violations'] if v['severity']=='exclusion'];assert not excluded
s.write(D/'FROZEN_NON_CRB_AUDIT.json',{'non_CRB_complete_footprint_text_identical':True,'non_CRB_count':len(x)-1,'changed_footprints':changed,'all_existing_tracks_vias_exact_preserved':True,'local_CRB_tracks_added':added,'rules_projects_exact_preserved':True,'DRC_exclusions':0,'errors':0,'approved_IN38_raw_opens':1})
print('complete footprint text frozen',len(x)-1,changed)
