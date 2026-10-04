#!/usr/bin/python3
from pathlib import Path
import pcbnew as p,json,csv
R=Path(__file__).resolve().parent

def main():
 final=json.loads((R/'FINAL.json').read_text());assert final['strict_pass'],'No final CPL until both strict DRC checks pass'
 for name,entry in final['boards'].items():
  b=p.LoadBoard(entry['candidate']);rows=[];cpl=[]
  for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
   ref=f.GetReference();manual=ref in ['J0','JD0'] or any(q.GetAttribute()==p.PAD_ATTRIB_PTH for q in f.Pads());part='C126402' if name=='DC0' and ref in ['U'+str(i) for i in range(1,9)] else '';side=b.GetLayerName(f.GetLayer());rows.append([ref,f.GetValue(),f.GetFPID().GetUniStringLibId(),part,'manual TH' if manual else ('JLC top Economic' if name=='DC0' else ('JLC bottom Economic' if f.GetLayer()==p.B_Cu else 'manual top'))])
   if not manual and (name=='DC0' or f.GetLayer()==p.B_Cu):cpl.append([ref,p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y),'top' if f.GetLayer()==p.F_Cu else 'bottom',f.GetOrientationDegrees()])
  with (R/(name+'_BOM.csv')).open('w') as out:w=csv.writer(out);w.writerow(['Reference','Value','Footprint','LCSC','Assembly']);w.writerows(rows)
  with (R/(name+'_CPL.csv')).open('w') as out:w=csv.writer(out);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation']);w.writerows(cpl)
 (R/'ASSEMBLY_NOT_RELEASED.txt').write_text('Strict DRC-gated engineering exports only. No fabrication release or orders authorized. Validate JLC rotation against exact library orientation before ordering. Generic 2-row header is manually bent and soldered as a straddle connector.\n')
if __name__=='__main__':main()
