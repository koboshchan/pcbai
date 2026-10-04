#!/usr/bin/python3
"""Read-only CAD inventory, provisional purchasing overlay. Never exports a CPL."""
import json,hashlib,re,csv
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent
NAMES=['motherboard_adc_repaired_unrouted.kicad_pcb']+[x.name for x in sorted(H.glob('daughtercard*_repaired.kicad_pcb'))]
def main():
 rows=[];hashes={}
 for name in NAMES:
  path=H/name;hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest();b=p.LoadBoard(str(path))
  for f in b.GetFootprints():
   ref=f.GetReference();value=f.GetValue();fp=str(f.GetFPID().GetLibItemName());desc=f.GetLibDescription();codes=re.findall(r'\bC\d{4,}\b',desc)
   mechanical=ref.startswith('H');manual=ref.startswith(('J_SLOT','J_STRADDLE')) or any(q.GetAttribute()==p.PAD_ATTRIB_PTH for q in f.Pads())
   if ref in [f'U_SR{i}' for i in range(1,9)]:
    assert fp=='SOIC-16_3.9x9.9mm_P1.27mm';value='74AHCT595S16-13';codes=['C126402'];manual=False
   if ref=='C_REG_IN' and name.startswith('motherboard'):
    assert fp=='C_0805_2012Metric';value='1uF';codes=['C28323'];manual=False
   rows.append(dict(board=name,reference=ref,value=value,footprint=fp,description=desc,lcsc=codes[0] if len(set(codes))==1 else '',assembly='mechanical' if mechanical else 'manual' if manual else 'JLC_SMD',stock_status='verified_C126402' if ref.startswith('U_SR') else 'verified_C28323_2026-10-04T07:49:15Z' if ref=='C_REG_IN' and name.startswith('motherboard') else 'unverified'))
 for name,sha in hashes.items():assert hashlib.sha256((H/name).read_bytes()).hexdigest()==sha
 out=dict(provisional=True,fabrication_ready=False,CPL_generated=False,source_board_sha256=hashes,items=rows,note='Motherboard is unrouted. Purchasing overlay only, not final assembly or placement files. All unassigned catalog codes remain blockers; historical root BOMs are obsolete.')
 (H/'sourcing_inventory_provisional.json').write_text(json.dumps(out,indent=2)+'\n')
 folder=H/'assembly_provisional';folder.mkdir(exist_ok=True)
 for name in NAMES:
  with (folder/(name.replace('.kicad_pcb','')+'_full_bom.csv')).open('w',newline='') as fh:
   w=csv.writer(fh);w.writerow(['Comment','Designator','Footprint','LCSC Part #'])
   for r in rows:
    if r['board']==name and r['assembly']!='mechanical':w.writerow([r['value'],r['reference'],r['footprint'],r['lcsc']])
 (folder/'manifest.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(dict(boards=len(hashes),items=len(rows),unknown_codes=sum(not r['lcsc'] and r['assembly']!='mechanical' for r in rows),smd=sum(r['assembly']=='JLC_SMD' for r in rows)),indent=2))
if __name__=='__main__':main()
