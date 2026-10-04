from pathlib import Path
import pcbnew as p,json
import motherboard_refs as refs
R=Path(__file__).resolve().parent;b=p.LoadBoard(str(R/'DC0.kicad_pcb'));before=refs.physical(b);ok=p.ImportSpecctraSES(b,str(R/'route_DC0/DC0_named_header.ses'));after=refs.physical(b);diff={k:{q:[before[k][q],after[k][q]] for q in before[k] if before[k][q]!=after[k][q]} for k in before if before[k]!=after[k]};(R/'import_diff.json').write_text(json.dumps({'import_success':ok,'diff':diff},indent=2));print(json.dumps({'import_success':ok,'diff':diff})[:15000])
