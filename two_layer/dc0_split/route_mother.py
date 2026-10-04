from pathlib import Path
import pcbnew as p,subprocess,re,json,traceback
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
from route_split import drc
from pour_ground import apply
R=Path(__file__).resolve().parent
try:
 b=p.LoadBoard(str(R/'motherboard.kicad_pcb'));frozen=refs.physical(b);assert drc(R/'motherboard.kicad_pcb')['errors']==0
 run=R/'route_motherboard';run.mkdir(exist_ok=False);dsn=run/'motherboard.dsn';ses=dsn.with_suffix('.ses');assert p.ExportSpecctraDSN(b,str(dsn));text=dsn.read_text();text=re.sub(r'(\(rule\s*\(width\s+)[\d.]+',r'\g<1>250',text);text=re.sub(r'(\(clearance\s+)[\d.]+',r'\g<1>200',text);dsn.write_text(text)
 with (run/'router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual48.jar','-de',str(dsn),'-do',str(ses),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,timeout=21600,check=True)
 assert p.ImportSpecctraSES(b,str(ses));assert refs.physical(b)==frozen;target=run/'motherboard_routed.kicad_pcb';p.SaveBoard(str(target),b);target.with_suffix('.kicad_pro').write_bytes((R/'motherboard.kicad_pro').read_bytes());target=apply(target);stats=drc(target);stats.update(candidate=str(target),silk_clean=silk.audit(p.LoadBoard(str(target)))['clean'],physical_identity=True);(R/'MOTHER_RESULT.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats),flush=True)
except Exception:traceback.print_exc();raise
finally:subprocess.run(['/usr/bin/python3',str(R/'snapshot_remote.py'),'after'],check=True)
