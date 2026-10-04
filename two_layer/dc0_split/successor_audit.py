#!/usr/bin/python3
from pathlib import Path
import pcbnew as p,json,shutil,subprocess,sys
R=Path(__file__).resolve().parent;S=R/'successor100';T=S/'exception_tests';T.mkdir(exist_ok=True)
def mm(v):return p.ToMM(v)
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def main():
 b=p.LoadBoard(str(S/'DC0.kicad_pcb'));m=p.LoadBoard(str(S/'motherboard.kicad_pcb'));j=next(f for f in b.GetFootprints() if f.GetReference()=='J0');jd=next(f for f in m.GetFootprints() if f.GetReference()=='JD0');jp={q.GetNumber():q for q in j.Pads()};mp={q.GetNumber():q for q in jd.Pads()};mapping=json.loads((R/'split_identity.json').read_text())['pinmap'];rows=[]
 for n in range(1,77):
  q=jp[str(n)];r=mp[str(n)];assert q.GetNetname()==r.GetNetname()==mapping[str(n)];assert abs(q.GetPosition().x-r.GetPosition().x)<=1;assert q.GetLayer()==(p.F_Cu if n%2 else p.B_Cu);assert r.GetAttribute()==p.PAD_ATTRIB_PTH
  setback=100-mm(q.GetPosition().y)-mm(q.GetSize().y)/2;assert abs(setback-.4)<1e-6;rows.append({'pin':n,'uuid':q.m_Uuid.AsString(),'net':q.GetNetname(),'edge_setback_mm':setback,'x_mm':mm(q.GetPosition().x),'layer':b.GetLayerName(q.GetLayer())})
 assert abs(mm(jp['75'].GetPosition().x-jp['1'].GetPosition().x)-93.98)<1e-6
 controls={}
 for kind in ['track','via','ordinary_pad','unlisted_J0_pad']:
  b=p.LoadBoard(str(S/'DC0.kicad_pcb'))
  if kind=='track':
   q=p.PCB_TRACK(b);q.SetStart(xy(.9,99.475));q.SetEnd(xy(1.1,99.475));q.SetWidth(p.FromMM(.25));q.SetLayer(p.F_Cu);b.Add(q)
  elif kind=='via':
   q=p.PCB_VIA(b);q.SetPosition(xy(1,99.3));q.SetWidth(p.FromMM(.6));q.SetDrill(p.FromMM(.3));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(q)
  else:
   if kind=='unlisted_J0_pad':f=next(f for f in b.GetFootprints() if f.GetReference()=='J0')
   else:f=p.FOOTPRINT(b);f.SetReference('TEST_ONLY');b.Add(f)
   q=p.PAD(f);q.SetNumber('999');q.SetAttribute(p.PAD_ATTRIB_SMD);q.SetShape(p.PAD_SHAPE_RECT);q.SetSize(xy(.8,.8));q.SetPosition(xy(1,99.2));ls=p.LSET();ls.AddLayer(p.F_Cu);q.SetLayerSet(ls);f.Add(q)
  uid=q.m_Uuid.AsString();out=T/(kind+'.kicad_pcb');p.SaveBoard(str(out),b)
  for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(S/('DC0'+ext),out.with_suffix(ext))
  report=out.with_suffix('.json');subprocess.run(['kicad-cli','pcb','drc','--severity-all','--format','json','-o',str(report),str(out)],capture_output=True,check=True);d=json.loads(report.read_text());hits=[v for v in d['violations'] if v['type']=='copper_edge_clearance' and any(i['uuid']==uid for i in v['items'])];assert hits,kind;controls[kind]=True
 (S/'HEADER_AUDIT.json').write_text(json.dumps({'pinmap_exact':True,'same_column_direction':True,'pitch_mm':2.54,'span_mm':93.98,'straddle_pads':rows,'negative_controls':controls,'KiCad':p.Version()},indent=2))
if __name__=='__main__':main()
