#!/usr/bin/python3
"""Read-only saved-footprint Economic PCBA side audit; never saves a board."""
import hashlib,json
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    paths=sorted(H.glob('daughtercard*_repaired.kicad_pcb'))
    assert len(paths)==6, paths
    protected=paths+sorted(H.parent.glob('*.kicad_pcb'))
    before={str(x.relative_to(H.parent)):sha(x) for x in protected}
    boards=[]
    for path in paths:
        b=p.LoadBoard(str(path)); items=[]; counts={'F.Cu':0,'B.Cu':0}; padcounts={'F.Cu':0,'B.Cu':0}
        for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
            pads=list(f.Pads()); smd=[q for q in pads if q.GetAttribute()==p.PAD_ATTRIB_SMD]
            tht=[q for q in pads if q.GetAttribute()==p.PAD_ATTRIB_PTH]
            ref=f.GetReference(); fp=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()); side=b.GetLayerName(f.GetLayer())
            row=dict(reference=ref,value=f.GetValue(),footprint=fp,footprint_side=side,smd_pad_count=len(smd),pth_pad_count=len(tht),smd_pad_layer_counts={layer:sum(q.IsOnLayer(num) for q in smd) for layer,num in [('F.Cu',p.F_Cu),('B.Cu',p.B_Cu)]})
            if ref.startswith('H'):
                row['category']='mechanical'
            elif tht or ref.startswith(('J_STRADDLE','J_SLOT')):
                row['category']='manual_tht_or_straddle'
            elif smd:
                assert side in counts,(path,ref,side)
                row['category']='smd'; counts[side]+=1
                for layer in counts: padcounts[layer]+=row['smd_pad_layer_counts'][layer]
                assert row['smd_pad_layer_counts'][side]==len(smd),(path,ref,'SMD pad/footprint mismatch')
            else: row['category']='mechanical'
            items.append(row)
        selected=max(counts,key=counts.get)
        manual=[]
        for row in items:
            if row['category']=='smd':
                row['assembly']='JLC_SMD' if row['footprint_side']==selected else 'manual_minority_smd'
                if row['assembly']=='manual_minority_smd':
                    fp=row['footprint']; easy=any(x in fp for x in ('0805','1206','1210','SOD-123','SOD123'))
                    row['hand_solder_assessment']='0805-or-larger passive / SOD123, ordinary hand-solderable package' if easy else 'package requires specific hand-solder review before geometry decision'
                    row['hand_solder_review_required']=not easy; manual.append(row)
            elif row['category']=='manual_tht_or_straddle': row['assembly']='manual_tht_or_straddle'
            else: row['assembly']='mechanical_excluded'
        boards.append(dict(board=path.name,sha256=sha(path),selected_jlc_side=selected,smd_footprint_counts=counts,smd_pad_counts=padcounts,minority_manual_smd=manual,manual_tht_or_straddle=[r for r in items if r['category']=='manual_tht_or_straddle'],items=items))
    assert before=={str(x.relative_to(H.parent)):sha(x) for x in protected},'Protected board bytes changed during audit'
    result=dict(board_geometry_modified=False,inventory_modified=False,fabrication_ready=False,scope='Six saved final daughtercards only. Routing/DRC not rerun by this side audit. Motherboard excluded because owned by active routing worker.',policy='JLC assembles majority SMD side only. Opposite-side SMD and all THT/straddle parts must be excluded from JLC BOM and CPL and hand assembled. Mechanical features excluded.',protected_source_sha256=before,boards=boards,hand_solder_review_blockers=[dict(board=b['board'],reference=r['reference'],footprint=r['footprint']) for b in boards for r in b['minority_manual_smd'] if r['hand_solder_review_required']])
    (H/'ECONOMIC_DAUGHTERCARDS_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['Economic daughtercard assembly audit','',result['policy'],'','This is a read-only side audit, not fabrication release or a fresh DRC certification. No board or inventory was rewritten. Full exact references, values, footprint names and pad-layer counts are recorded in ECONOMIC_DAUGHTERCARDS_AUDIT.json.','']
    for board in boards:
        lines += [board['board'],f"Selected JLC side {board['selected_jlc_side']}. SMD footprints F.Cu {board['smd_footprint_counts']['F.Cu']}, B.Cu {board['smd_footprint_counts']['B.Cu']}. SMD pads F.Cu {board['smd_pad_counts']['F.Cu']}, B.Cu {board['smd_pad_counts']['B.Cu']}."]
        for row in board['minority_manual_smd']:
            lines.append(f"Manual minority SMD {row['reference']} | {row['value']} | {row['footprint']} | {row['footprint_side']} | {row['hand_solder_assessment']}.")
        if not board['minority_manual_smd']:lines.append('No minority-side SMD.')
        for row in board['manual_tht_or_straddle']:lines.append(f"Manual THT/straddle {row['reference']} | {row['value']} | {row['footprint']} | {row['footprint_side']}.")
        lines += [f"Source SHA256 {board['sha256']}",'']
    lines += ['No difficult minority-SMD package blockers found.' if not result['hand_solder_review_blockers'] else 'Review blockers are enumerated in the JSON.','Assembly-export owner must implement these exclusions in the Economic BOM/CPL; this helper deliberately does not change existing assembly files.','']
    (H/'ECONOMIC_DAUGHTERCARDS_AUDIT.md').write_text('\n'.join(lines))
    print(json.dumps({b['board']:dict(side=b['selected_jlc_side'],counts=b['smd_footprint_counts'],manual=[r['reference'] for r in b['minority_manual_smd']]) for b in boards},indent=2))
if __name__=='__main__':main()
