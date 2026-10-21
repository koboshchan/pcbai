#!/usr/bin/env python3
"""Reproducible linear RC reset bound; no nonlinear/hidden-cap guarantee."""
import json,math
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from model import Network

def report(port_count=26):
 rmax=4700*1.01;cmax=100e-9*1.10;hold=.1
 # Every port capacitor has its OWN low GPIO path through Rs.
 # With passive nonnegative inter-port R, at the maximum-voltage node,
 # inter-port current cannot raise it. Therefore max V <= V0 exp(-t/RmaxCmax).
 tau=rmax*cmax
 g=np.eye(port_count)/rmax
 for a in range(port_count-1):
  b=a+1;conductance=1/1000.
  g[a,a]+=conductance;g[b,b]+=conductance
  g[a,b]-=conductance;g[b,a]-=conductance
 eigen=eigh(g,np.eye(port_count)*cmax,eigvals_only=True)
 data=dict(port_count=port_count,hold_seconds=hold,initial_volts=3.3,series_max_ohms=rmax,
           fixture_cap_max_farads=cmax,fixture_max_tau_seconds=tau,
           fixture_max_residual_volts=3.3*math.exp(-hold/tau),
           fixture_chain_1k_chain_min_decay_per_second=float(eigen[0]),
           fixture_chain_1k_chain_tau_seconds=float(1/eigen[0]),
           applies_only_to='26 directly shunted fixture caps, ideal low GPIOs, linear passive inter-port resistors',
           excludes='GPIO VOL/ground offset, X7R absorption, added DUT capacitors, hidden/nonlinear/isolated rail charge')
 root=Path(__file__).resolve().parent
 dut=json.loads((root/'dc3-passive.json').read_text())
 ports=json.loads((root/'dc3-ports.json').read_text())['port_nets']
 n=Network(dut,ports,series=rmax,cap=cmax)
 g=n.g.copy()-np.eye(len(n.g))*1e-14  # remove artificial gmin for physical reset bound
 for port in n.ports:g[port,port]+=1/rmax
 decay=eigh(g,n.c,eigvals_only=True)
 data['extracted_dc3_linear_model_min_decay_per_second']=float(decay[0])
 data['extracted_dc3_full_network_reset_qualified']=bool(decay[0]>1e-6)
 if decay[0]>1e-6:
  # Energy norm bound, not max-node-voltage bound for arbitrary internal C.
  data['extracted_dc3_energy_norm_amplitude_ratio_bound']=float(math.exp(-decay[0]*hold))
 else:
  data['extracted_dc3_note']='Floating resistor islands/capacitor-only rails prevent a full-network reset guarantee; gmin must not fake one.'
 return data

if __name__=='__main__':
 print(json.dumps(report(),indent=2))
