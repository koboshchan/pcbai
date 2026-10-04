from pathlib import Path
import pcbnew as p,json,shutil
import motherboard_refs as refs
import shortrefs_motherboard_silk as silk
from route_split import drc
from pour_ground import apply
R=Path(__file__).resolve().parent
b=p.LoadBoard(str(R/'motherboard.kicad_pcb'));frozen=refs.physical(b);ses=R/'route_motherboard/motherboard.ses';fixed=ses.with_name('motherboard_named_header.ses');fixed.write_text(ses.read_text().replace('(component \n','(component DC0_Isolated:Socket2x38\n'));assert p.ImportSpecctraSES(b,str(fixed))
for f in b.GetFootprints():
 old=frozen[f.m_Uuid.AsString()];new=f.GetPosition();assert abs(new.x-old['position'][0])<=1 and abs(new.y-old['position'][1])<=1;f.SetPosition(p.VECTOR2I(*old['position']))
assert refs.physical(b)==frozen
target=R/'route_motherboard/motherboard_routed.kicad_pcb';p.SaveBoard(str(target),b);shutil.copyfile(R/'motherboard.kicad_pro',target.with_suffix('.kicad_pro'));target=apply(target);stats=drc(target);stats.update(candidate=str(target),silk_clean=silk.audit(p.LoadBoard(str(target)))['clean'],physical_identity=True);(R/'MOTHER_RESULT.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats),flush=True)
