#!/usr/bin/python3
from pathlib import Path
import json
import pcbnew as p
from pour_ground import sha
R=Path(__file__).resolve().parent
results=json.loads((R/'RESULTS.json').read_text())
lines=['All six GND pour candidates FAILED the new 0.5 mm edge acceptance gate. No promotion or release.', '', 'Each original source passes 0 errors / 0 opens with its actual repaired 0.3 mm copper-edge rule. Actual repaired sibling projects were copied read-only from kat-box /work/pcbai/two_layer into this isolated folder and used unchanged for source verification. RESULTS.json records the project source and provenance.', '', 'Each candidate has two refilled GND zones, 0.2 mm zone clearance, THT thermal reliefs, always-remove islands, and a strict 0.5 mm whole-board copper-edge rule. Each has exactly 76 copper_edge_clearance errors / 0 opens, all involving the unchanged 76 straddle pads at actual 0.4 mm edge clearance. Original pads cannot satisfy the new requirement without authorized placement or footprint geometry changes. No rules were relaxed to conceal this conflict. Sparse GND stitching is DRC-gated and was skipped on these already-failing candidates.', '', 'Full serialized footprint hashes remain identical, including UUIDs, pad geometry/nets, reference/value fields, position/orientation, and silk. Original board SHA256 values remain unchanged. Source and final DRC have no silk overlap/height/thickness findings; remaining warnings are footprint-library differences.', '', 'Reusable helper is pour_ground.py. Invocation with system Python is pour_ground.py SOURCE OUTPUT ACTUAL_PROJECT --stitch. It preserves existing zones, uses the actual board polygon and cutouts, and never writes to SOURCE. It only strengthens rules, copies sibling custom rules, rejects projects containing DRC exclusions, refills before all audits, and admits sparse stitching only following full strict 0 errors / 0 opens DRC. All helper outputs remain isolated.', '']
for r in results:
    b=p.LoadBoard(str(R/r['board']/'ground_candidate.kicad_pcb'))
    texts=[]
    for f in b.GetFootprints():
        for t in list(f.GetFields())+list(f.GraphicalItems()):
            if hasattr(t,'GetTextHeight') and t.GetLayer() in (p.F_SilkS,p.B_SilkS) and t.IsVisible() and t.GetText(): texts.append(t)
    for t in b.GetDrawings():
        if hasattr(t,'GetTextHeight') and t.GetLayer() in (p.F_SilkS,p.B_SilkS) and t.IsVisible() and t.GetText():texts.append(t)
    r['visible_silk_text_count']=len(texts)
    r['silk_min_height_mm']=min((p.ToMM(t.GetTextHeight()) for t in texts),default=None)
    r['silk_min_thickness_mm']=min((p.ToMM(t.GetTextThickness()) for t in texts),default=None)
    assert r['silk_min_height_mm']>=.8 and r['silk_min_thickness_mm']>=.12
    assert sha(R.parent/(r['board']+'_repaired.kicad_pcb'))==r['source_sha256']
    assert r['categories']['copper_edge_clearance']==r['errors']==76 and r['opens']==0
    r['accepted']=False
    lines.extend([r['board']+' has 76 errors / 0 opens.','Original SHA256 '+r['source_sha256'],'Candidate SHA256 '+r['final_sha256'],'Footprint identity SHA256 '+r['footprint_identity_sha256'],'Visible silk minimum '+str(r['silk_min_height_mm'])+' mm height / '+str(r['silk_min_thickness_mm'])+' mm thickness.',''])
(R/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
(R/'REPORT.txt').write_text('\n'.join(lines)+'\n')
