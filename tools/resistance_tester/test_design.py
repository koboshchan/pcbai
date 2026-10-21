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

def emulate(code,limit,crossing,no_sink=False):
 """Instruction-level check of actual upstream-assembled program, 2MHz cycles.
 crossing is cycles after sink output-enable, None means open.
 """
 pc=x=osr=isr=0;cycle=0;t0=0 if no_sink else None;remaining=None;released=no_sink
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
 def test_reference_pio_never_drives(self):
  fw=load_firmware();code=fw.self_falling[0]
  self.assertFalse(any(w>>13==7 for w in code))
  remain,_,_=emulate(code,100,None,no_sink=True)
  self.assertEqual(remain,0xffffffff)
  remain,_,_=emulate(code,100,14,no_sink=True)
  self.assertEqual(100-remain,6)  # 2 setup cycles then 2 cycles/count
 def test_reference_measure_uses_no_sink_program_and_releases(self):
  fw=load_firmware();inits=[];holds=[];calls=[]
  class Pin:
   IN=0;OUT=1
   def __init__(self,*a,**kw):calls.append((a,kw))
   def value(self):return 1
  class SM:
   def active(self,x):pass
   def init(self,*a,**kw):inits.append((a,kw))
   def put(self,x):pass
   def rx_fifo(self):return 1
   def get(self):return 0xffffffff
  fw.Pin=Pin;fw.rp2.StateMachine=lambda _:SM()
  fw.time=types.SimpleNamespace(sleep_ms=holds.append,ticks_ms=lambda:0)
  self.assertEqual(fw.measure(1,0,100,250),(None,'timeout'))
  self.assertEqual(inits[0][0],(fw.self_falling,))
  self.assertNotIn('set_base',inits[0][1])
  self.assertEqual(holds,[250,50])
  self.assertEqual([kw for _,kw in calls[-20:]],[dict(pull=None)]*20)
 def test_reference_quality(self):
  from compare import reference_quality
  for t in [10000.,100000.]:
   d={(1,0):[('timeout',None)]*8,(1,2):[('ok',t)]*8}
   self.assertEqual(reference_quality(d,5000000)[0]['classification'],'sink_resolved')
  d={(1,0):[('ok',120000.)]*8,(1,2):[('ok',100000.)]*8}
  self.assertEqual(reference_quality(d,5000000)[0]['classification'],'leakage_limited')
  d={(1,0):[('timeout',None)]*8,(1,2):[('timeout',None)]*8}
  self.assertEqual(reference_quality(d,5000000)[0]['classification'],'open_compatible_unquantified')
  self.assertFalse(reference_quality(d,5000000)[0]['open_proven'])
 def test_reference_missing_or_failed(self):
  from compare import reference_quality
  for refs in [[],[('precharge_failed',None)],[('ok',10000),('timeout',None)]]:
   d={(1,0):refs,(1,2):[('ok',100)]}
   self.assertEqual(reference_quality(d,5000000)[0]['classification'],'unqualified')
 def test_reference_scan_cleanup(self):
  fw=load_firmware();calls=[];released=[]
  fw.release=lambda:released.append(True)
  def fail(*a):
   calls.append(a);raise KeyboardInterrupt()
  fw.measure=fail
  import contextlib,io
  with contextlib.redirect_stdout(io.StringIO()):
   with self.assertRaises(KeyboardInterrupt):fw.scan(1)
  self.assertEqual(calls,[(1,0,5000000,100)])
  self.assertTrue(released)
 def test_reference_csv_window(self):
  from compare import capture_window
  import tempfile
  with tempfile.NamedTemporaryFile(mode='w+') as f:
   f.write('window_us\n5000000\n5000000\n');f.flush()
   self.assertEqual(capture_window(f.name),5000000)
 def test_discharge_disables_pulls(self):
  fw=load_firmware();calls=[];holds=[]
  class Recorder:
   OUT=1
   def __init__(self,*a,**kw):calls.append((a,kw))
  fw.Pin=Recorder
  fw.time=types.SimpleNamespace(sleep_ms=holds.append)
  fw.discharge()
  self.assertEqual(holds,[100])
  self.assertEqual([a[0] for a,_ in calls],list(fw.GPIO))
  self.assertTrue(all(k==dict(pull=None,value=0) for _,k in calls))
 def test_gpio_consistency(self):
  fw=load_firmware();manifest=json.loads((R/'manifest.json').read_text())
  self.assertEqual(list(fw.GPIO),[p['gpio'] for p in manifest['gpio_map']])
  self.assertEqual(len(set(fw.GPIO)),20)
 def test_pair_coverage(self):
  fw=load_firmware();rows=[]
  fw.measure=lambda a,b,t,d:(123,'ok')
  import builtins
  old=builtins.print;builtins.print=lambda *a,**kw:rows.append(a)
  try:fw.scan(1)
  finally:builtins.print=old
  self.assertEqual(len(rows),401)
  self.assertEqual(len({(r[0],r[1]) for r in rows[21:]}),190)
  self.assertEqual(len({(r[2],r[3]) for r in rows[21:]}),380)
 def test_model_coupled_caps_and_value_separation(self):
  from model import Network
  import numpy as np
  ports=['N'+str(i) for i in range(20)]
  times=[]
  for resistance in [100.,1000.,10000.,100000.,1e6]:
   n=Network({'resistors':[{'a':'N0','b':'N1','value':resistance}]},ports)
   t,s=n.crossing(0,1,timeout=10.)
   self.assertEqual(s,'ok');times.append(t)
   self.assertGreater(t,0)
  self.assertTrue(all(a<b for a,b in zip(times,times[1:])),times)
  self.assertGreater(times[4]/times[3],8)
  # Sink node has finite Rs and its own timing cap. Shorted pair is TWO caps.
  expected=2*1e-7*4700*np.log(3.3/1.3)
  self.assertLess(abs(times[0]/expected-1),.03)
  n=Network({},ports);self.assertEqual(n.crossing(0,1,timeout=10.)[1],'timeout')
  report=dict(isolated_test_resistors_ohms=[100,1000,10000,100000,1000000],modeled_fall_seconds=times,not_hardware_accuracy=True)
  (R/'evidence/isolated-model.json').write_text(json.dumps(report,indent=2)+'\n')
 def test_reset_bound(self):
  from reset_bound import report
  d=report()
  self.assertAlmostEqual(d['fixture_max_tau_seconds'],.00052217)
  self.assertAlmostEqual(d['twenty_port_1k_chain_tau_seconds'],d['fixture_max_tau_seconds'])
  self.assertLess(d['fixture_max_residual_volts'],1e-80)
  self.assertFalse(d['extracted_dc3_full_network_reset_qualified'])
 def test_100k_1m_open_reference_classification_model(self):
  from model import Network
  from compare import reference_quality
  ports=['N'+str(i) for i in range(20)]
  records=[]
  for resistance in [100000.,1000000.,None]:
   dut={} if resistance is None else {'resistors':[{'a':'N0','b':'N1','value':resistance}]}
   n=Network(dut,ports)
   t,status=n.crossing(0,1,timeout=5.)
   ref,ref_status=n.crossing(0,None,timeout=5.)
   d={(1,0):[(ref_status,None if ref is None else ref*1e6)]*8,
      (1,2):[(status,None if t is None else t*1e6)]*8}
   q=reference_quality(d,5000000)[0]
   self.assertEqual(q['classification'],'open_compatible_unquantified' if resistance is None else 'sink_resolved')
   records.append(dict(nominal_ohms=resistance,pair_seconds=t,pair_status=status,
                       reference_seconds=ref,reference_status=ref_status,quality=q))
  self.assertGreater(records[1]['pair_seconds']/records[0]['pair_seconds'],8)
  (R/'evidence/reference-classification-model.json').write_text(json.dumps(dict(
   simulated_only=True,hardware_discrimination_not_verified=True,cases=records),indent=2)+'\n')
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
