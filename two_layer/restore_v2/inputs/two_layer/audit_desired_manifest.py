#!/usr/bin/python3
"""Check the published component manifest against saved weighted-board pad nets."""
from pathlib import Path
import argparse, json, math
import pcbnew as p
from audit_final_model import resistance
H=Path(__file__).resolve().parent

def audit(routed=False):
    desired=json.loads((H/'fixed_model/desired_netlist.json').read_text())
    result={}
    for name,items in desired.items():
        suffix='_differential_repaired.kicad_pcb' if routed else '_differential_repaired_unrouted.kicad_pcb'
        board=p.LoadBoard(str(H/(name+suffix)))
        footprints={f.GetReference():f for f in board.GetFootprints()}
        errors=[]
        for row in items:
            ref=row['ref']
            if ref not in footprints:
                errors.append(f'missing {ref}');continue
            fp=footprints[ref]
            actual={pad.GetNumber():pad.GetNetname() for pad in fp.Pads()}
            if 'pads' in row:
                if actual!=row['pads']:errors.append(f'{ref} terminals differ')
                if not math.isclose(resistance(fp.GetValue()),row['ohms'],rel_tol=1e-9):errors.append(f'{ref} value differs')
            else:
                for num,net in row['patch_pads'].items():
                    if actual.get(num)!=net:errors.append(f'{ref} pad {num} differs')
        result[name]={'entries':len(items),'errors':errors}
    report={'routed':routed,'all_manifest_entries_match':all(not v['errors'] for v in result.values()),'boards':result,'fabrication_ready':False}
    target=H/('desired_manifest_routed_audit.json' if routed else 'desired_manifest_unrouted_audit.json')
    target.write_text(json.dumps(report,indent=2)+'\n')
    assert report['all_manifest_entries_match'],report
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('--routed',action='store_true')
    audit(args.parse_args().routed)
