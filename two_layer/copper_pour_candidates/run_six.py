#!/usr/bin/python3
from pathlib import Path
import json,shutil,sys
from pour_ground import apply,drc,sha
R=Path(__file__).resolve().parent; ROOT=R.parent.parent; TL=R.parent
names=['daughtercard1'+x+'_weights_l1_differential' for x in 'abcd']+['daughtercard2_relu_l1_buffered','daughtercard3_weights_l2_wta_differential']
results=[]
for name in names:
    src=TL/(name+'_repaired.kicad_pcb'); d=R/name; d.mkdir(exist_ok=True)
    source=d/'source.kicad_pcb';shutil.copy2(src,source)
    project=R/(name+'_repaired.kicad_pro')
    authority='actual repaired sibling project copied read-only from kat-box /work/pcbai/two_layer'
    if not project.exists():
        base=name.replace('_differential','').replace('_buffered','')
        project=ROOT/(base+'.kicad_pro');authority='reconstructed effective repaired rules from route_repaired.prepare because repaired sibling project absent locally'
    j=json.loads(project.read_text()); assert not j['board']['design_settings'].get('drc_exclusions')
    shutil.copy2(project,source.with_suffix('.kicad_pro'))
    source_counts=drc(source,d/'source_drc.json')
    result=apply(src,d/'ground_candidate.kicad_pcb',source.with_suffix('.kicad_pro'),True)
    result.update(board=name,source_counts=source_counts,project_authority=authority,project_source=str(project),original_sha256=sha(src))
    results.append(result); (R/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n');print(name,json.dumps(result),flush=True)
