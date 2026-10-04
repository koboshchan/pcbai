import itertools,json
from pathlib import Path
import numpy as np
from model import coefficients,loaded,infer
HERE=Path(__file__).resolve().parent
# Ideal matched differential resistor test, positive and negative coefficients recover exactly.
rows=[{'rf_ohms':100000,'balance':{'leg':'positive','ohms':100000/.8,'tolerance':.01},'inputs':[{'index':0,'leg':'positive','ohms':100000/0.7,'tolerance':.05},{'index':1,'leg':'negative','ohms':100000/0.5,'tolerance':.05}]}]
W,b,*_=coefficients(rows,2)
assert np.allclose(W,[[.7,-.5]])
# Ground balance on negative leg supports large positive coefficients without negative resistance.
rows=[{'rf_ohms':100000,'balance':{'leg':'negative','ohms':100000/1.2,'tolerance':.01},'inputs':[{'index':0,'leg':'positive','ohms':100000/2.7,'tolerance':.05},{'index':1,'leg':'negative','ohms':100000/.5,'tolerance':.05}]}]
W,b,*_=coefficients(rows,2);assert np.allclose(W,[[2.7,-.5]])
# Explicit KCL test with nonzero source impedance, both virtual nodes participate.
A,b,T,q,P,PB,G=loaded(rows,2,50);command=np.array([5.,0.]);actual=T@command+q;vp=P@actual+PB
assert np.allclose((command-actual)/50,G.sum(0)*actual-G.T@vp,atol=1e-12)
assert np.allclose(command@A+b,actual@W.T)
# 1% resistor corner, 3.3V +/-5% and SCORE anywhere within +/-15V.
vals=[];inj=[]
for t,u,d,sr,series in itertools.product([.99,1.01],repeat=5):
 rt=220000*t;ru=22000*u;rd=22000*d;rs=1000*series;g=1/rt+1/ru+1/rd;rth=1/g
 for score,vref in itertools.product([-15,15],[3.3*.95,3.3*1.05]):
  v=(score/rt+vref/ru)/g;vals.append(v)
  # Zero-drop conservative clamp currents, not assertion of which diode conducts first.
  inj.append(max(0,-v,v-vref)/(rth+rs))
# MCU supply off, both upper divider bias and clamp rail at 0, still driven bipolar15V.
off=[]
for t,u,d,series in itertools.product([.99,1.01],repeat=4):
 rt=220000*t;ru=22000*u;rd=22000*d;rs=1000*series;g=1/rt+1/ru+1/rd
 off.append((15/rt/g)/(1/g+rs))
out={'tests_passed':4,'powered_corner_min_V':min(vals),'powered_corner_max_V':max(vals),'powered_zero_drop_external_clamp_max_A':max(inj),'poweroff_max_per_pin_A':max(off),'poweroff_max_ten_pins_A':10*max(off),'note':'Silicon external clamps do not guarantee ADC absolute-voltage limit or prevent MCU rail backfeed. MCU3V3/GND first, analog last, analog off first. Powered voltage corners safe under stated steady-state +/-15V bound, transient model not included.'}
(HERE/'checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
