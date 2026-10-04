#!/usr/bin/python3
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parent;P=R.parent
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
files=sorted(P.glob('*.kicad_pcb'))+sorted(P.glob('*.kicad_pro'))+[P/'restore_v2/restored_shortrefs_v2.kicad_pcb',P/'restore_v2/restored_shortrefs_v2.kicad_pro']
now={str(f.relative_to(P)):sha(f) for f in files}
if sys.argv[1]=='before':
 assert now['restore_v2/restored_shortrefs_v2.kicad_pcb']==json.loads((R/'source_sha256.json').read_text())['restore_v2/restored_shortrefs_v2.kicad_pcb'];(R/'remote_original_sha256.json').write_text(json.dumps(now,indent=2))
else:
 old=json.loads((R/'remote_original_sha256.json').read_text());assert now==old,{k:(old.get(k),v) for k,v in now.items() if old.get(k)!=v};(R/'remote_originals_unchanged.json').write_text(json.dumps({'verified':True,'files':len(now),'hashes':now},indent=2))
