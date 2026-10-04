#!/usr/bin/python3
from pathlib import Path
import pcbnew as p,json,shutil,subprocess
R=Path(__file__).resolve().parent
T=R/'exception_tests'
def main():
 T.mkdir(exist_ok=True);result={}
 for kind in ['track','via','ordinary_pad','unlisted_J0_pad']:
  b=p.LoadBoard(str(R/'DC0.kicad_pcb'))
  if kind=='track':
   q=p.PCB_TRACK(b);q.SetStart(p.VECTOR2I(p.FromMM(.9),p.FromMM(39.475)));q.SetEnd(p.VECTOR2I(p.FromMM(1.1),p.FromMM(39.475)));q.SetWidth(p.FromMM(.25));q.SetLayer(p.F_Cu);b.Add(q)
  elif kind=='via':
   q=p.PCB_VIA(b);q.SetPosition(p.VECTOR2I(p.FromMM(1),p.FromMM(39.3)));q.SetWidth(p.FromMM(.6));q.SetDrill(p.FromMM(.3));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(q)
  else:
   if kind=='unlisted_J0_pad':f=next(f for f in b.GetFootprints() if f.GetReference()=='J0')
   else:f=p.FOOTPRINT(b);f.SetReference('TEST_ONLY');b.Add(f)
   q=p.PAD(f);q.SetNumber('999');q.SetAttribute(p.PAD_ATTRIB_SMD);q.SetShape(p.PAD_SHAPE_RECT);q.SetSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)));q.SetPosition(p.VECTOR2I(p.FromMM(1),p.FromMM(39.2)));ls=p.LSET();ls.AddLayer(p.F_Cu);q.SetLayerSet(ls);f.Add(q)
  uuid=q.m_Uuid.AsString();target=T/(kind+'.kicad_pcb');p.SaveBoard(str(target),b)
  for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(R/('DC0'+ext),target.with_suffix(ext))
  out=target.with_suffix('.json');subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(out),str(target)],capture_output=True,check=True);d=json.loads(out.read_text());matches=[v for v in d['violations'] if v['type']=='copper_edge_clearance' and any(i['uuid']==uuid for i in v['items'])];assert matches,(kind,d['violations']);result[kind]={'nonexempt_edge_violation_detected':True,'test_object_uuid':uuid,'violations':matches}
 (R/'edge_exception_precedence_test.json').write_text(json.dumps({'KiCad':p.Version(),'all_negative_controls_passed':True,'controls':result},indent=2))
if __name__=='__main__':main()
