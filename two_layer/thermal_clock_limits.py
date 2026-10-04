#!/usr/bin/python3
"""Conservative parametric L7805CV estimate, no coin cooling credit."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
p=ROOT/'power_audit.json';audit=json.loads(p.read_text())
bias=audit['thermal']['continuous_clock']['bias_bound_A']
v=5.25
static=.0375+64*v/9500+v/(820*.95)+8*80e-6+bias
slope=8*190e-12*v*1.5+8*50e-12*v/2
p0=11*static+15.75*.0093
pslope=11*slope
rows=[]
for theta in [50,40,30,20,10]:
 for ambient in [25,40,50]:
  def limit(t):return max(0,((t-ambient)/theta-p0)/pslope)
  rows.append({'assumed_effective_thetaJA_C_per_W':theta,'ambient_C':ambient,'design110_max_continuous_Hz':limit(110),'absolute125_diagnostic_Hz':limit(125),'coin_credit_authorized':False})
report={'input_V':15.75,'output_dissipation_corner_V':4.75,'load_current_corner_V':v,'TTL_A':.0375,'filter_A':64*v/9500,'minimum_load_A':v/(820*.95),'ICC_A':.00064,'bias_A':bias,'ground_A':.0093,'CPD_pF_typical':190,'CPD_engineering_multiplier':1.5,'serial_load_pF_assumed':50,'serial_toggle_frequency':'clock/2','static_load_A':static,'P0_W':p0,'P_slope_W_per_Hz':pslope,'power_equation':'P=P0+P_slope*f_continuous','bare_thetaJA_assumed':50,'coin_thetaJA':'UNKNOWN; historical coin superseded by aluminum TO-220 heatsink, assembled heatsink thetaJA unverified','clock_limit_rows':rows,'accuracy_at_reduced_clock':'UNQUALIFIED; fresh PWM/RC ripple and coupled-network simulation required','guaranteed_limit':False,'mechanical_cooling_optional':True}
(ROOT/'thermal_clock_limits.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['Conservative clock estimates for the vertical ST L7805CV. Lucas will hand-install a small aluminum TO-220 clip/screw heatsink instead of a coin. It stays out of JLC assembly and is not a routing gate. Its actual effective assembled thermal resistance is unknown. These are engineering estimates, not guaranteed operating ratings. Bare-package calculations use 50C/W with local ambient, design junction 110C and absolute diagnostic 125C. Do not operate at the absolute diagnostic limit.','',f'Python includes TTL37.5mA, filters{64*v/9500*1000:.3f}mA, minimum load{v/(820*.95)*1000:.3f}mA, ICC0.640mA, actual bias{bias*1000:.3f}mA and ground9.3mA. CPD190pF is typical, multiplied by1.5 as an engineering margin, not a guaranteed maximum. Dynamic current is 8*190pF*5.25V*f*1.5; serial current is 8*50pF*5.25V*f/2. Dissipation combines +15.75V and4.75V with those current bounds.', '',f'P(f)={p0:.6f}W+{pslope:.9g}W/Hz*f. Estimate f_max=max(0,((110-Tambient)/thetaJA-P0)/P_slope). Measured assembled thetaJA=(Tjunction-Tambient)/P, with junction inferred from a qualified thermal method; a coin surface temperature alone is not junction temperature. Validate at worst supply, actual local ambient, mounting and airflow, with margin. Do not claim measured cooling from coin dimensions.', '', 'Bare50C/W continuous limits follow.']
for r in rows[:3]:lines.append(f"At {r['ambient_C']}C local ambient, design110C estimates {r['design110_max_continuous_Hz']/1e6:.3f}MHz; absolute125C diagnostic {r['absolute125_diagnostic_Hz']/1e6:.3f}MHz.")
lines+=['','An initial conservative test ceiling is 1MHz continuous, bare-package estimate only, with junction/ambient monitoring. This is a thermal test recommendation, NOT an accuracy or unrestricted operation claim. At50C the1MHz CPD-margin estimate is '+f'{50+50*(p0+pslope*1e6):.2f}C junction.','', 'Assumed effective thetaJA values below50C/W in the JSON are diagnostic scenarios only, never claimed coin performance. Thermal overload protection is not a normal operating strategy.','', 'Normal20MHz burst BCM uses6/63 clock duty for the previous4960.317Hz frame schedule and estimates1.230W without CPD margin. Lowering serial clock changes allowable frame scheduling and RC ripple; the previous20MHz accuracy simulation does not establish performance at1MHz. A fresh full PWM/RC coupled-network accuracy simulation is required before accepting lower-clock operation. No changes to trained resistors, filters, reference nets or daughtercards are authorized by this report.','', 'Cooling is not a mechanical routing blocker. Thermal qualification, repaired schematic, signal integrity, part availability and strict final PCB audits remain fabrication-release gates.']
(ROOT/'THERMAL_CLOCK_LIMITS.md').write_text('\n'.join(lines)+'\n')
audit['thermal_note']=lines[0]+' See THERMAL_CLOCK_LIMITS.md; reduced-clock accuracy unqualified.'
audit['cooling_optional']=True;audit['coin_thermal_resistance']='UNKNOWN';audit['thermal_clock_limits']=report
for entry in audit['thermal'].values():entry.pop('Tj_with_10C_W_sink_and_2C_W_interface_C',None)
if (ROOT/'coin_clearance_audit.json').exists():
 coin=json.loads((ROOT/'coin_clearance_audit.json').read_text());audit['coin_clearance']=coin
 audit['power_parts']['U_REG5']['xy']=[round(x*1e6) for x in coin['regulator_anchor_mm']]
 audit['power_parts']['U_REG5']['angle']=coin['rotation_deg']
audit['mechanical_routing_blocked']=False;audit['thermal_release_passed']=False;audit['fabrication_ready']=False
p.write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(report,indent=2))
