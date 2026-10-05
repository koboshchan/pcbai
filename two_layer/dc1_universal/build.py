#!/usr/bin/python3
"""Build isolated universal DC1 topology and population records from routed sources.
Zero coefficients are DNP. Separate P/N footprints implement sign changes.
"""
from pathlib import Path
import csv,hashlib,json,re,sys
import pcbnew as p
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def mm(x):return p.FromMM(x)
def xy(x,y):return p.VECTOR2I(mm(x),mm(y))
def normalized(n,offset):
 m=re.fullmatch(r'(POS_N|INV_N|V_SUM_)(\d+)',n)
 return m[1]+str(int(m[2])-offset) if m else n

def snapshot():
 cards={}; union={}
 manifest=json.loads((ROOT/'differential_repair_manifest.json').read_text())
 for offset,c in enumerate('abcd'):
  path=ROOT/f'daughtercard1{c}_weights_l1_differential_repaired.kicad_pcb'
  b=p.LoadBoard(str(path)); entries={}
  for f in b.GetFootprints():
   pads={q.GetNumber():normalized(q.GetNetname(),offset*4) for q in f.Pads()}
   if f.GetReference().startswith('R'):
    key=tuple(sorted(pads.values()));assert len(key)==2
    assert key not in entries
    source=manifest[f'daughtercard1{c}_weights_l1']['components'][f.GetReference()]
    units={'k':1000,'M':1000000};v=f.GetValue();ohms=float(v[:-1])*units[v[-1]] if v[-1] in units else float(v)
    assert abs(ohms-source['ohms'])<1e-6,(c,f.GetReference(),ohms,source['ohms'])
    assert {k:normalized(v,offset*4) for k,v in source['pads'].items()}==pads
    entries[key]={'ref':f.GetReference(),'value':f.GetValue(),'ohms':ohms,'tolerance':source['tolerance'],'pads':pads}
    union.setdefault(key,{})[c]=entries[key]
  cards[c]={'source':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'resistors':len(entries),'connector':{q.GetNumber():normalized(q.GetNetname(),offset*4) for f in b.GetFootprints() if f.GetReference()=='J_STRADDLE_EDGE' for q in f.Pads()}}
 assert all(c['connector']==cards['a']['connector'] for c in cards.values())
 return cards,union

def configure(f,ref,value,x,y):
 f.SetReference(ref);f.SetValue(value);f.SetUuid(p.KIID());f.SetPosition(xy(x,y));f.SetOrientationDegrees(0)
 f.Reference().SetVisible(True);f.Value().SetVisible(False)
 f.Reference().SetTextSize(xy(.8,.8));f.Reference().SetTextThickness(mm(.12));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));f.Reference().SetPosition(xy(x,y-1.23))
 for g in list(f.GraphicalItems()):
  if g.GetLayer()==p.F_SilkS:g.SetLayer(p.F_Fab)
 return f

def main():
 cards,union=snapshot(); b=p.LoadBoard(str(ROOT/'daughtercard1a_weights_l1_differential_repaired.kicad_pcb'))
 fixed={f.GetReference():f for f in b.GetFootprints() if not f.GetReference().startswith('R')}
 mechanical={ref:{q.GetNumber():[q.GetPosition().x,q.GetPosition().y,q.GetNetname()] for q in f.Pads()} for ref,f in fixed.items() if ref.startswith(('J','H'))}
 for t in list(b.GetTracks()):b.Delete(t)
 for z in list(b.Zones()):b.Delete(z)
 for f in list(b.GetFootprints()):
  if f.GetReference().startswith('R'):b.Delete(f)
 for d in list(b.GetDrawings()):
  if d.GetLayer()!=p.Edge_Cuts:b.Delete(d)
 b.SetCopperLayerCount(2)
 def net(n):
  if n not in b.GetNetsByName():b.Add(p.NETINFO_ITEM(b,n))
  return b.GetNetsByName()[n]
 def track(a,z,n,layer,width=.25):
  if a==z:return
  t=p.PCB_TRACK(b);t.SetStart(xy(*a));t.SetEnd(xy(*z));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(net(n));b.Add(t)
 def via(x,y,n):
  v=p.PCB_VIA(b);v.SetPosition(xy(x,y));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net(n));b.Add(v)
 template=p.FootprintLoad('/usr/share/kicad/footprints/Resistor_SMD.pretty','R_0805_2012Metric');assert template
 rows=[];buses={};inputs={}
 def sortkey(k):
  inp=next((n for n in k if n.startswith('IN_')),None)
  if inp:
   dst=next(n for n in k if n!=inp);return (0,int(inp[3:]),int(dst[-1]),0 if dst.startswith('POS') else 1)
  return (1,)+k
 for i,key in enumerate(sorted(union,key=sortkey),1):
  inp=next((n for n in key if n.startswith('IN_')),None)
  if inp:
   k=int(inp[3:]);dst=next(n for n in key if n!=inp);j=int(dst[-1]);leg=0 if dst.startswith('POS') else 1
   x=5.8+(j*2+leg)*5.2+(52 if k>=32 else 0);y=9.7+(k%32)*2.65
   pads={'1':inp,'2':dst}
  else:
   other_index=sum(not any(n.startswith('IN_') for n in r['nets']) for r in rows)
   x=47 if other_index%2==0 else 52.6;y=59+5*(other_index//2)
   pads={'1':key[0],'2':key[1]}
  ref=f'R{i:03d}';f=p.Cast_to_FOOTPRINT(template.Duplicate(False));configure(f,ref,'POPULATION',x,y)
  for q in f.Pads():q.SetNet(net(pads[q.GetNumber()]))
  b.Add(f)
  row={'reference':ref,'nets':list(key),'pads':pads,'x_mm':x,'y_mm':y,'cards':union[key]};rows.append(row)
  if inp:
   # Deliberate orthogonal matrix. Front vertical summing buses, rear input rows.
   pad={q.GetNumber():(p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)) for q in f.Pads()}
   v=(pad['1'][0],y+.95);track(pad['1'],v,inp,p.F_Cu);via(*v,inp);inputs.setdefault(inp,[]).append(v)
   busx=x+2.15;track(pad['2'],(busx,y),dst,p.F_Cu);buses.setdefault((dst,busx),[]).append(y)
 for (n,x),ys in buses.items():track((x,min(ys)),(x,max(ys)),n,p.F_Cu)
 for n,pts in inputs.items():track(min(pts),max(pts),n,p.B_Cu)
 # Reserve an uncomplicated central escape for IN_27 before other connector nets.
 # The first autoroute otherwise congested this corridor and left exactly this net open.
 n='IN_27';a=max(inputs[n]);y=94.3;x=71.59
 track(a,(49,a[1]),n,p.B_Cu);track((49,a[1]),(49,y),n,p.B_Cu);track((49,y),(x,y),n,p.B_Cu);via(x,y,n);track((x,y),(x,97.55),n,p.F_Cu)
 for ref,f in fixed.items():
  if ref=='U1':x,y=50,34
  elif ref=='C_U1P':x,y=47,23
  elif ref=='C_U1N':x,y=53,23
  else:continue
  configure(f,ref,f.GetValue(),x,y)
 # Pin-1 contact and mounting geometry are copied byte-for-byte in relative pose.
 assert mechanical=={ref:{q.GetNumber():[q.GetPosition().x,q.GetPosition().y,q.GetNetname()] for q in fixed[ref].Pads()} for ref in mechanical}
 for f in b.GetFootprints():
  for q in f.Pads():
   if q.GetNetname():q.SetNet(net(normalized(q.GetNetname(),0)))
 p.SaveBoard(str(HERE/'dc1_universal_unrouted.kicad_pcb'),b)
 project=json.loads((ROOT.parent/'daughtercard1a_weights_l1.kicad_pro').read_text());ds=project['board']['design_settings'];ds['drc_exclusions']=[]
 ds['rules'].update(min_clearance=.2,min_track_width=.2,min_via_diameter=.6,min_through_hole_diameter=.3,min_via_annular_width=.15,min_copper_edge_clearance=.3,min_silk_clearance=.15,min_text_height=.8,min_text_thickness=.12)
 project['net_settings']['classes'][0].update(clearance=.2,track_width=.25,via_diameter=.6,via_drill=.3)
 (HERE/'dc1_universal_unrouted.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
 assert p.ExportSpecctraDSN(b,str(HERE/'dc1_universal.dsn'))
 (HERE/'manifest.json').write_text(json.dumps({'cards':cards,'union_resistor_positions':len(rows),'input_positions':sum(any(n.startswith('IN_') for n in r['nets']) for r in rows),'rows':rows,'mechanical':mechanical},indent=2)+'\n')
 for c in cards:
  with (HERE/f'DC1{c}.csv').open('w',newline='') as out:
   w=csv.writer(out);w.writerow(['Reference','Value','Tolerance_percent','Original_reference','Pad1','Pad2','X_mm','Y_mm','Footprint'])
   for row in rows:
    rec=row['cards'].get(c);w.writerow([row['reference'],rec['value'] if rec else 'DNP',100*rec['tolerance'] if rec else '',rec['ref'] if rec else '',row['pads']['1'],row['pads']['2'],row['x_mm'],row['y_mm'],'0805'])
   for ref in ['U1','C_U1P','C_U1N','J_STRADDLE_EDGE']:
    f=fixed[ref];w.writerow([ref,f.GetValue(),'',ref,'','',p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y),str(f.GetFPID().GetLibItemName())])
 print(json.dumps({'union':len(rows),'cards':{c:d['resistors'] for c,d in cards.items()},'buses':len(buses),'vias':len([t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)])}))
if __name__=='__main__':main()
