from pathlib import Path
import pcbnew as p,json,shutil,subprocess,traceback
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
from route_split import drc,sha
from pour_ground import apply
R=Path(__file__).resolve().parent
try:
 for name,kind in [('DC0','Straddle2x38'),('motherboard','Socket2x38')]:
  path=R/(name+'.kicad_pcb');b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()==('J0' if name=='DC0' else 'JD0'));fid=p.LIB_ID();fid.SetLibNickname(p.UTF8('DC0_Isolated'));fid.SetLibItemName(p.UTF8(kind));f.SetFPID(fid);p.SaveBoard(str(path),b)
 b=p.LoadBoard(str(R/'DC0.kicad_pcb'));frozen=refs.physical(b);ses=R/'route_DC0/DC0.ses';fixed=ses.with_name('DC0_named_header.ses');fixed.write_text(ses.read_text().replace('(component \n','(component DC0_Isolated:Straddle2x38\n'));assert p.ImportSpecctraSES(b,str(fixed)),'import still failed';assert refs.physical(b)==frozen
 target=R/'route_DC0/DC0_routed.kicad_pcb';p.SaveBoard(str(target),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(R/('DC0'+ext),target.with_suffix(ext))
 target=apply(target);stats=drc(target);stats.update(candidate=str(target),silk_clean=silk.audit(p.LoadBoard(str(target)))['clean'],physical_identity=True);(R/'DC0_RESULT.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats),flush=True)
except Exception:
 traceback.print_exc();raise
