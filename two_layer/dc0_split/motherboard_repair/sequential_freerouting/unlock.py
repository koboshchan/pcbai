#!/usr/bin/python3
from run import *
from import_locked import copper

def main():
 rows=json.loads((D/'SCOPED_PATHS.json').read_text());ids=set(q for r in rows for q in r['blocking_items']);b=p.LoadBoard(str(src));orig=copper(b);phys=refs.physical(b);ident=s.identity(b);removed={k:v for k,v in orig.items() if k in ids};assert len(removed)<=12;write('SCOPED_UNLOCK_MANIFEST.json',{'precise_removed_geometry':removed,'count':len(removed),'reason':'Weighted 0.08mm raster path for ADC_2 and IN_58 intersects only these track segments; all other source tracks/vias remain system-fixed. Seven IN_58 blockers, five ADC_2 blockers. No net-wide rip-up.','candidate_paths':'SCOPED_PATHS.json'})
 tracks=list(b.GetTracks())
 for t in tracks:
  if t.m_Uuid.AsString() in ids:b.Remove(t)
 zones=list(b.Zones())
 for z in zones:b.Remove(z)
 dsn=D/'scoped.dsn';assert p.ExportSpecctraDSN(b,str(dsn));text=dsn.read_text();idx=text.rfind('(wiring');head,tail=text[:idx],text[idx:];tail,n=re.subn(r'\(type\s+\w+\)', '(type fix)',tail);assert n==len(re.findall(r'\((?:wire|via)\s',tail));head=re.sub(r'(\(width\s+)250(?=\))',r'\g<1>200',head)
 guards=''
 for i,(x1,y1,x2,y2) in enumerate([(-10000,-110000,600,10000),(99400,-110000,110000,10000),(-10000,-600,110000,10000),(-10000,-110000,110000,-99400)]):
  for layer in ['F.Cu','B.Cu']:guards+=f'    (keepout edge_guard_{i}_{layer} (rect {layer} {x1} {y1} {x2} {y2}))\n'
 dsn.write_text(head.replace('    (via ',guards+'    (via ',1)+tail)
 write('SCOPED_FIXED_AUDIT.json',{'fixed_export_scopes':n,'baseline_remaining_items':len(b.GetTracks()),'removed':len(ids),'all_nonselected_fixed':True,'new_trace_width_mm':.2})
 with (D/'scoped_router.log').open('w') as log:subprocess.run(['java','-Xmx4g','-jar','/tmp/freerouting_actual48.jar','-de',str(dsn),'-do',str(D/'scoped.ses'),'--gui.enabled=false','-mt','2'],stdout=log,stderr=subprocess.STDOUT,check=True)
 raw=p.LoadBoard(str(src));assert p.ImportSpecctraSES(raw,str(D/'scoped.ses'));p.SaveBoard(str(D/'scoped_raw.kicad_pcb'),raw)
 for t in raw.GetTracks():new=t.Duplicate();new.SetUuid(p.KIID());b.Add(new)
 for z in zones:b.Add(z.Duplicate(False))
 # Export only removes zones on this private in-memory baseline. Footprints never imported.
 out=D/'scoped_candidate.kicad_pcb';p.SaveBoard(str(out),b)
 for ext in ['.kicad_pro','.kicad_dru']:
  if (D/'pre_crb').with_suffix(ext).exists():shutil.copyfile((D/'pre_crb').with_suffix(ext),out.with_suffix(ext))
 stats=s.drc(out,True);loaded=p.LoadBoard(str(out));c=copper(loaded);stats.update(candidate=str(out),sha=s.sha(out),identity=s.identity(loaded)==ident,physical_identity=refs.physical(loaded)==phys,silk_clean=silk.audit(loaded)['clean'],all_nonselected_copper_preserved=all(c.get(k)==v for k,v in orig.items() if k not in ids),protected_unchanged=all(s.sha(Path(f))==h for f,h in json.loads((D/'protected_before.json').read_text()).items()),removed_item_count=len(ids),dc0_sha=s.sha(dc));stats['strict_pass']=stats['errors']==stats['opens']==0 and all(stats[k] for k in ['identity','physical_identity','silk_clean','all_nonselected_copper_preserved','protected_unchanged']);write('SCOPED_AUDIT.json',stats);print(json.dumps(stats),flush=True)
 if stats['strict_pass']:
  shutil.copyfile(out,D/'pre_crb.kicad_pcb');stats['candidate']=str(D/'pre_crb.kicad_pcb');write('PRE_CRB_AUDIT.json',stats)
if __name__=='__main__':main()
