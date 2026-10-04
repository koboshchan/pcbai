#!/usr/bin/python3
from pathlib import Path
import sys,json
import pcbnew as p
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import successor100 as s;import motherboard_refs as refs;import shortrefs_motherboard_silk as silk
D=R/'motherboard_repair';out=D/'motherboard.kicad_pcb';src=R/'successor100/motherboard_routed.kicad_pcb';dc=R/'successor100/DC0_routed.kicad_pcb'
assert s.sha(src)=='cb85e3b510f840965050c5aa1c9874f7896faf1ece7ef54abdf6eca3011cf12e'
assert s.sha(dc)=='1196b0d47c1c553b22a4061d3ac7e1c41cbf3d4a35dd5b7f1d4cda102bfdb34a'
stats=s.drc(out,True);b=p.LoadBoard(str(out));orig=p.LoadBoard(str(src));protected=json.loads((D/'protected_before.json').read_text());audit=silk.audit(b)
stats.update(candidate=str(out),sha=s.sha(out),identity=s.identity(b)==s.identity(orig),physical_identity=refs.physical(b)==refs.physical(orig),placement_unchanged=refs.physical(b)==refs.physical(orig),footprint_count=len(list(b.GetFootprints())),silk_clean=audit['clean'],protected_unchanged=all(s.sha(Path(f))==h for f,h in protected.items()),dc0_sha=s.sha(dc),source_sha=s.sha(src),release_authorized=False)
stats['strict_pass']=stats['errors']==stats['opens']==0 and stats['footprint_count']==85 and all(stats[k] for k in ['identity','physical_identity','silk_clean','protected_unchanged'])
s.write(D/'FINAL_AUDIT.json',stats);s.write(D/'FINAL_SILK.json',audit);print(json.dumps(stats),flush=True)
