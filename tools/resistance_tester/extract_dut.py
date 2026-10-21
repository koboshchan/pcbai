#!/usr/bin/python3
"""Run with KiCad 10 pcbnew. Never infer connections from pad positions.
Extracts actual board pin nets, resistor edges and capacitor edges; opamp/dio
devices are retained as explicit omissions, not modeled as resistors.
"""
import pcbnew,hashlib,json,re,sys
from pathlib import Path
def value(s):
 s=s.strip().replace("Ω","").replace("ohm","").split()[0]
 if s.endswith(('F','f')):s=s[:-1]
 m=re.fullmatch(r"(\d+(?:\.\d+)?)([RrKkMmGgNnUuPp]?)(\d*)",s)
 if not m:raise ValueError(s)
 scales={'':1,'r':1,'R':1,'k':1e3,'K':1e3,'M':1e6,'m':1e-3,'G':1e9,'g':1e9,'n':1e-9,'N':1e-9,'u':1e-6,'U':1e-6,'p':1e-12,'P':1e-12}
 a,suffix,digits=m.groups()
 return float(a+('.'+digits if digits and '.' not in a else ''))*scales[suffix]
def extract(path):
 b=pcbnew.LoadBoard(str(path));res=[];caps=[];headers={};omitted=[];pads={}
 for f in b.GetFootprints():
  ref=f.GetReference();ps={a.GetNumber():a.GetNetname() for a in f.Pads()};pads[ref]=ps
  if ref.startswith('J'):headers[ref]={'value':f.GetValue(),'pins':ps}
  elif ref.startswith(('R','C')) and len(ps)==2:
   try:val=value(f.GetValue())
   except ValueError:
    omitted.append({'ref':ref,'value':f.GetValue(),'pins':ps,'reason':'unparsed passive value'});continue
   edge={'ref':ref,'value':val,'a':ps.get('1',''),'b':ps.get('2','')}
   (res if ref.startswith('R') else caps).append(edge)
  else:omitted.append({'ref':ref,'value':f.GetValue(),'pins':ps,'reason':'nonlinear or unsupported'})
 return dict(source=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),resistors=res,capacitors=caps,headers=headers,omitted_devices=omitted,pads=pads)
if __name__=='__main__':
 d=extract(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(d,indent=2)+'\n')
 print(len(d['resistors']),'resistors',len(d['capacitors']),'capacitors',len(d['omitted_devices']),'omissions')
