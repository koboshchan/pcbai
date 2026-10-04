#!/usr/bin/python3
"""Read-only CAD inventory, provisional purchasing overlay. Never exports a CPL."""
import json,hashlib,re,csv
from pathlib import Path
import pcbnew as p
import motherboard_refs
H=Path(__file__).resolve().parent
NAMES=['motherboard_adc_repaired.kicad_pcb']+[x.name for x in sorted(H.glob('daughtercard*_repaired.kicad_pcb'))]
def main():
 # Assembly overlays must describe the authoritative routed hybrid, not stale Economic geometry.
 drc=json.loads((H/'motherboard_adc_repaired_drc.json').read_text())
 status=json.loads((H/'restored_hybrid_shortrefs_run/final_audit.json').read_text())
 assert not any(v.get('severity')=='error' for v in drc['violations']) and not drc.get('unconnected_items',[])
 assert status['errors']==0 and status['unconnected']==0 and status['frozen_identity_verified']
 assert status['candidate_sha256']==hashlib.sha256((H/NAMES[0]).read_bytes()).hexdigest()
 rows=[];hashes={}
 for name in NAMES:
  path=H/name;hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest();b=p.LoadBoard(str(path))
  def is_manual(f):
   return f.GetReference().startswith(('J_SLOT','J_STRADDLE')) or any(q.GetAttribute()==p.PAD_ATTRIB_PTH for q in f.Pads())
  smd_counts={layer:sum(f.GetLayer()==layer and bool(list(f.Pads())) and not f.GetReference().startswith('H') and not is_manual(f) for f in b.GetFootprints()) for layer in (p.F_Cu,p.B_Cu)}
  assembly_layer=p.B_Cu if name.startswith('motherboard') else max(smd_counts,key=smd_counts.get)
  for f in b.GetFootprints():
   ref=f.GetReference();role=motherboard_refs.role(f) if name.startswith('motherboard') else ref;value=f.GetValue();fp=str(f.GetFPID().GetLibItemName());desc=f.GetLibDescription();codes=re.findall(r'\bC\d{4,}\b',desc)
   mechanical=ref.startswith('H');manual=ref.startswith(('J_SLOT','J_STRADDLE')) or any(q.GetAttribute()==p.PAD_ATTRIB_PTH for q in f.Pads())
   if role in [f'U_SR{i}' for i in range(1,9)]:
    assert fp=='SOIC-16_3.9x9.9mm_P1.27mm';value='74AHCT595S16-13';codes=['C126402'];manual=name.startswith('motherboard')
    if name.startswith('motherboard'):assert f.GetLayer()==p.F_Cu,'Approved motherboard AHCTs must remain on top'
   if role=='C_REG_IN' and name.startswith('motherboard'):
    assert fp=='C_0805_2012Metric';value='1uF';codes=['C28323'];manual=False
   side='Top' if f.GetLayer()==p.F_Cu else 'Bottom' if f.GetLayer()==p.B_Cu else 'Other'
   assembly_side='Top' if assembly_layer==p.F_Cu else 'Bottom'
   minority_smd=not mechanical and not manual and f.GetLayer()!=assembly_layer
   reason='mechanical_feature' if mechanical else 'approved_C126402_top_AHCT_manually_sourced_and_soldered_by_Lucas' if name.startswith('motherboard') and role in [f'U_SR{i}' for i in range(1,9)] else 'through_hole_or_edge_header' if manual else 'minority_side_smd_hand_solder' if minority_smd else ''
   manual=manual or minority_smd
   rows.append(dict(board=name,reference=ref,historical_reference=role,component_uuid=str(f.m_Uuid.AsString()),value=value,footprint=fp,description=desc,lcsc=codes[0] if len(set(codes))==1 else '',side=side,jlc_assembly_side=assembly_side,assembly_exclusion_reason=reason,assembly='mechanical' if mechanical else 'manual' if manual else 'JLC_SMD',stock_status='verified_C126402' if role.startswith('U_SR') else 'verified_C28323_2026-10-04T07:49:15Z' if role=='C_REG_IN' and name.startswith('motherboard') else 'unverified'))
 for name,sha in hashes.items():assert hashlib.sha256((H/name).read_bytes()).hexdigest()==sha
 for name in NAMES:
  assembled=[r for r in rows if r['board']==name and r['assembly']=='JLC_SMD']
  assert len({r['side'] for r in assembled})<=1,'Economic assembly must be single sided'
  if name.startswith('motherboard'):
   assert all(r['side']=='Bottom' for r in assembled)
 out=dict(provisional=True,fabrication_ready=False,CPL_generated=False,assembly_policy='Economic single-sided SMT; minority-side SMD and all THT/edge headers hand-soldered',source_board_sha256=hashes,items=rows,note='Purchasing overlay only, not final assembly or placement files. CPL withheld pending final routing audits. All unassigned catalog codes remain blockers; historical root BOMs are obsolete.')
 (H/'sourcing_inventory_provisional.json').write_text(json.dumps(out,indent=2)+'\n')
 folder=H/'assembly_provisional';folder.mkdir(exist_ok=True)
 for name in NAMES:
  with (folder/(name.replace('.kicad_pcb','')+'_full_bom.csv')).open('w',newline='') as fh:
   w=csv.writer(fh);w.writerow(['Comment','Designator','Footprint','LCSC Part #'])
   for r in rows:
    if r['board']==name and r['assembly']!='mechanical':w.writerow([r['value'],r['reference'],r['footprint'],r['lcsc']])
  for suffix,assembly in [('economic_smd_bom','JLC_SMD'),('manual_bom','manual')]:
   with (folder/(name.replace('.kicad_pcb','')+'_'+suffix+'.csv')).open('w',newline='') as fh:
    w=csv.writer(fh);w.writerow(['Comment','Designator','Footprint','LCSC Part #'])
    for r in rows:
     if r['board']==name and r['assembly']==assembly:w.writerow([r['value'],r['reference'],r['footprint'],r['lcsc']])
 (folder/'manifest.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(dict(boards=len(hashes),items=len(rows),unknown_codes=sum(not r['lcsc'] and r['assembly']!='mechanical' for r in rows),smd=sum(r['assembly']=='JLC_SMD' for r in rows)),indent=2))
if __name__=='__main__':main()
