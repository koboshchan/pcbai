#!/usr/bin/python3
from run import *
import csv

def main():
 pre=json.loads((D/'PRE_CRB_AUDIT.json').read_text());assert pre['strict_pass'];source=D/'pre_crb.kicad_pcb';assert s.sha(source)==pre['sha'];b=p.LoadBoard(str(source));before=refs.physical(b);ids=s.identity(b);old=next(f for f in b.GetFootprints() if f.GetReference()=='CRB');uid=old.m_Uuid.AsString();center=old.GetPosition();ang=old.GetOrientationDegrees();nets={q.GetNumber():q.GetNetname() for q in old.Pads()};pos={q.GetNumber():q.GetPosition() for q in old.Pads()};reftext=old.Reference();valuetext=old.Value();new=p.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty','C_0805_2012Metric');assert new;new.SetFPID(p.LIB_ID('Capacitor_SMD','C_0805_2012Metric'));new.m_Uuid=old.m_Uuid;new.SetReference('CRB');new.SetValue('10uF');new.SetPosition(center)
 if old.GetLayer()==p.B_Cu:new.Flip(center,False)
 new.SetOrientationDegrees(ang)
 for a,c in [(new.Reference(),reftext),(new.Value(),valuetext)]:
  a.SetPosition(c.GetPosition());a.SetTextSize(c.GetTextSize());a.SetTextThickness(c.GetTextThickness());a.SetTextAngle(c.GetTextAngle());a.SetLayer(c.GetLayer());a.SetVisible(c.IsVisible())
 for q in new.Pads():q.SetNet(b.FindNet(nets[q.GetNumber()]))
 b.Remove(old);b.Add(new);routes=[]
 for q in new.Pads():
  if q.GetNetname()=='GND':continue
  t=p.PCB_TRACK(b);t.SetStart(pos[q.GetNumber()]);t.SetEnd(q.GetPosition());t.SetWidth(p.FromMM(.25));t.SetLayer(new.GetLayer());t.SetNet(q.GetNet());b.Add(t);routes.append(t.m_Uuid.AsString())
 out=D/'post_crb.kicad_pcb';p.SaveBoard(str(out),b)
 for ext in ['.kicad_pro','.kicad_dru']:
  if source.with_suffix(ext).exists():shutil.copyfile(source.with_suffix(ext),out.with_suffix(ext))
 stats=s.drc(out,True);b=p.LoadBoard(str(out));after=refs.physical(b);new=next(f for f in b.GetFootprints() if f.GetReference()=='CRB');netafter={q.GetNumber():q.GetNetname() for q in new.Pads()}
 unchanged=all(after[k]==v for k,v in before.items() if k!=uid);identity=all(s.identity(b)[k]==v for k,v in ids.items() if k!=uid)
 audit={'reference':'CRB','uuid':uid,'old_footprint':ids[uid]['fpid'],'new_footprint':new.GetFPID().GetUniStringLibId(),'value':new.GetValue(),'specification':'10uF 25V X7R nonpolar ceramic','center_before':[center.x,center.y],'center_after':[new.GetPosition().x,new.GetPosition().y],'orientation_before':ang,'orientation_after':new.GetOrientationDegrees(),'pad_net_before':nets,'pad_net_after':netafter,'center_preserved':new.GetPosition()==center,'net_map_preserved':nets==netafter,'other_physical_unchanged':unchanged,'other_identity_unchanged':identity,'local_copper_added':routes,'source_pre_sha':pre['sha'],'LCSC':None,'sourcing_status':'pending exact compatible part selection; obsolete electrolytic sourcing cleared'};write('CRB_CHANGE_AUDIT.json',audit)
 fields=['reference','value','footprint','specification','LCSC','sourcing_status']
 with (D/'candidate_BOM.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for fp in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
   row={'reference':fp.GetReference(),'value':fp.GetValue(),'footprint':fp.GetFPID().GetUniStringLibId(),'LCSC':'','sourcing_status':'candidate identity inventory only; shared authoritative sourcing not promoted'}
   if fp.GetReference()=='CRB':row.update(specification=audit['specification'],sourcing_status=audit['sourcing_status'])
   w.writerow(row)
 write('candidate_manifest.json',{'candidate':str(out),'sha':s.sha(out),'pre_crb_sha':pre['sha'],'CRB':audit,'shared_BOM_pending_promotion':True,'release_authorized':False})
 stats.update(candidate=str(out),sha=s.sha(out),non_CRB_physical_unchanged=unchanged,non_CRB_identity_unchanged=identity,CRB_center_preserved=audit['center_preserved'],CRB_netmap_preserved=audit['net_map_preserved'],silk_clean=silk.audit(b)['clean'],protected_unchanged=all(s.sha(Path(f))==h for f,h in json.loads((D/'protected_before.json').read_text()).items()),dc0_sha=s.sha(dc),release_authorized=False)
 stats['strict_pass']=stats['errors']==stats['opens']==0 and all(stats[k] for k in ['non_CRB_physical_unchanged','non_CRB_identity_unchanged','CRB_center_preserved','CRB_netmap_preserved','silk_clean','protected_unchanged']);write('POST_CRB_AUDIT.json',stats);write('POST_CRB_SILK.json',silk.audit(b));print(json.dumps(stats))
if __name__=='__main__':main()
