#!/usr/bin/env python3
import unittest,sys,types,importlib.util,ast,json,csv
from pathlib import Path
R=Path(__file__).resolve().parent

class PIO:
 SHIFT_LEFT=0
 SHIFT_RIGHT=1
 JOIN_NONE=0
 IN_LOW=0
 IN_HIGH=1
 OUT_LOW=2
 OUT_HIGH=3

def load_firmware():
 low=types.ModuleType('_rp2');low.PIO=PIO;sys.modules['_rp2']=low
 micro=types.ModuleType('micropython');micro.const=lambda x:x;sys.modules['micropython']=micro
 spec=importlib.util.spec_from_file_location('rp2',R/'vendor/rp2_assembler.py');rp2=importlib.util.module_from_spec(spec);sys.modules['rp2']=rp2;spec.loader.exec_module(rp2)
 machine=types.ModuleType('machine')
 class Pin:
  IN=0;OUT=1
  def __init__(self,*a,**kw):pass
 machine.Pin=Pin;sys.modules['machine']=machine
 spec=importlib.util.spec_from_file_location('firmware',R/'firmware/main.py');fw=importlib.util.module_from_spec(spec);spec.loader.exec_module(fw)
 return fw

def emulate(code,limit,crossing):
 """Instruction-level check of actual upstream-assembled program, 2MHz cycles.
 crossing is cycles after sink output-enable, None means open.
 """
 pc=x=osr=isr=0;cycle=0;t0=None;remaining=None;released=False
 for _ in range(limit*3+100):
  w=code[pc];op=w>>13;arg=w&31;dest=(w>>5)&7;pc+=1
  if op==0:
   cond=(w>>5)&7;take=False
   if cond==0:take=True
   elif cond==2:
    take=x!=0;x=(x-1)&0xffffffff
   elif cond==6:take=crossing is None or t0 is None or cycle-t0<crossing
   else:raise AssertionError(('jmp',cond))
   if take:pc=arg
  elif op==4:
   if w&0x80:osr=limit
   else:remaining=isr
  elif op==5:
   src=w&7;value={1:x,6:isr,7:osr}[src]
   if dest==1:x=value
   elif dest==6:isr=value
   else:raise AssertionError(('mov',dest))
  elif op==7:
   if dest==4:
    if arg==1:t0=cycle+1
    else:released=True
  else:raise AssertionError(('op',op))
  cycle+=1
  if remaining is not None and released:return remaining,t0,cycle
 raise AssertionError("did not finish")

class Tests(unittest.TestCase):
 def test_pio_assembles_and_terminates(self):
  fw=load_firmware();code=fw.falling[0];self.assertLessEqual(len(code),32)
  for counts in [0,1,5,99]:
   remain,_,_=emulate(code,100,counts*2)
   self.assertEqual(100-remain,counts)
  remain,_,_=emulate(code,100,None);self.assertEqual(remain,0xffffffff)
 def test_gpio_consistency(self):
  fw=load_firmware();manifest=json.loads((R/'manifest.json').read_text())
  self.assertEqual(list(fw.GPIO),[p['gpio'] for p in manifest['gpio_map']])
  self.assertEqual(len(set(fw.GPIO)),20)
 def test_pair_coverage(self):
  fw=load_firmware();rows=[]
  fw.measure=lambda a,b,t:(123,'ok')
  import builtins
  old=builtins.print;builtins.print=lambda *a,**kw:rows.append(a)
  try:fw.scan(1)
  finally:builtins.print=old
  self.assertEqual(len(rows),381)
  self.assertEqual(len({(r[0],r[1]) for r in rows[1:]}),190)
  self.assertEqual(len({(r[2],r[3]) for r in rows[1:]}),380)
 def test_model_coupled_caps_and_value_separation(self):
  from model import Network
  import numpy as np
  ports=['N'+str(i) for i in range(20)]
  times=[]
  for resistance in [100.,1000.,10000.,100000.,1e6,30e6]:
   n=Network({'resistors':[{'a':'N0','b':'N1','value':resistance}]},ports)
   t,s=n.crossing(0,1,timeout=10.)
   self.assertEqual(s,'ok');times.append(t)
   self.assertGreater(t,0)
  self.assertTrue(all(a<b for a,b in zip(times,times[1:])),times)
  self.assertGreater(times[4]/times[3],8)
  self.assertGreater(times[5]/times[4],25)
  # Sink node has finite Rs and its own timing cap. Shorted pair is TWO caps.
  expected=2*1e-7*4700*np.log(3.3/1.3)
  self.assertLess(abs(times[0]/expected-1),.03)
  n=Network({},ports);self.assertEqual(n.crossing(0,1,timeout=10.)[1],'timeout')
  report=dict(isolated_test_resistors_ohms=[100,1000,10000,100000,1000000,30000000],modeled_fall_seconds=times,not_hardware_accuracy=True)
  (R/'evidence/isolated-model.json').write_text(json.dumps(report,indent=2)+'\n')
 def test_model_finite_precharge(self):
  from model import Network
  ports=['N'+str(i) for i in range(20)]
  n=Network({'resistors':[{'a':'N0','b':'N1','value':1e6},{'a':'N1','b':'MID','value':30e6}]},ports)
  v=n.precharge();self.assertGreater(v[n.idx['N0']],3.2)
  self.assertLess(v[n.idx['MID']],3.3)
 def test_compare_raw_fingerprints(self):
  from compare import compare
  d=compare({(1,2):[('ok',100.)]*3},{(1,2):[('ok',150.)]*3})
  self.assertEqual(d[0]['status'],'changed')
  d=compare({(1,2):[('timeout',None)]},{(1,2):[('timeout',None)]})
  self.assertEqual(d[0]['status'],'same_status_unquantified')
 def test_value_parser(self):
  # Extractor import is normally KiCad, use a stub just for value parsing.
  sys.modules.setdefault('pcbnew',types.ModuleType('pcbnew'))
  from extract_dut import value
  for text,want in [('100k',100000),('1M',1e6),('4k7',4700),('0.1uF',1e-7)]:
   self.assertAlmostEqual(value(text),want)
 def test_sources_parse(self):
  for p in R.glob('*.py'):ast.parse(p.read_text())
  ast.parse((R/'firmware/main.py').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
