#!/usr/bin/python3
"""Read-only canonical footprint/pin invariance audit. Uses KiCad's parser.
Run with system Python. Net codes/geometry are intentionally not fingerprints.
"""
import argparse, collections, hashlib, json
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parent.parent
NAMES=['motherboard','daughtercard1a_weights_l1','daughtercard1b_weights_l1','daughtercard1c_weights_l1','daughtercard1d_weights_l1','daughtercard2_relu_l1','daughtercard3_weights_l2_wta']
def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def manifest(path):
    b=pcbnew.LoadBoard(str(path))
    fs=[]
    for f in b.GetFootprints():
        pads=sorted([{'number':p.GetNumber(),'net':p.GetNetname()} for p in f.Pads()],key=lambda p:(p['number'],p['net']))
        fs.append({'reference':f.GetReference(),'value':f.GetValue(),'footprint':str(f.GetFPID().GetLibItemName()),'description':f.GetFieldText('Description'),'lib_description':f.GetLibDescription(),'pads':pads})
    fs.sort(key=lambda f:(f['reference'],f['value']))
    pins=[(f['reference'],p['number'],p['net']) for f in fs for p in f['pads']]
    identity=[(f['reference'],f['value'],f['footprint'],f['description']) for f in fs]
    return {'source':str(path),'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'footprint_count':len(fs),'pad_count':len(pins),'copper_layers':b.GetCopperLayerCount(),'pin_net_sha256':digest(pins),'component_identity_sha256':digest(identity),'footprints':fs}
def compare(old,new):
    fields=['pin_net_sha256','component_identity_sha256']
    match=all(old[k]==new[k] for k in fields)
    a={f['reference']:f for f in old['footprints']};b={f['reference']:f for f in new['footprints']}
    diffs=[]
    for r in sorted(a.keys()|b.keys()):
        if a.get(r)!=b.get(r):diffs.append({'reference':r,'original':a.get(r),'converted':b.get(r)})
    return {'invariant_pass':match,'two_copper_layers':new['copper_layers']==2,'differences':diffs}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--converted',type=Path,default=ROOT/'two_layer');args=ap.parse_args()
    originals={n:manifest(ROOT/(n+'.kicad_pcb')) for n in NAMES}
    out=ROOT/'two_layer';out.mkdir(exist_ok=True)
    (out/'audit_original_manifest.json').write_text(json.dumps(originals,indent=2)+'\n')
    results={}
    for n,original in originals.items():
        p=args.converted/(n+'.kicad_pcb')
        if p.exists():
            m=manifest(p);(out/('audit_'+n+'_converted.json')).write_text(json.dumps(m,indent=2)+'\n')
            results[n]=compare(original,m)
        else:results[n]={'status':'not present'}
    (out/'audit_comparison.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({n:{'footprints':m['footprint_count'],'pads':m['pad_count'],'layers':m['copper_layers'],'pin_net_sha256':m['pin_net_sha256']} for n,m in originals.items()},indent=2))
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
