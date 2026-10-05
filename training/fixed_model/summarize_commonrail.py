"""Append audited completed diagnostic results to RESULT.md."""
import json
from pathlib import Path
H=Path(__file__).resolve().parent
d=json.loads((H/'commonrail_sensitivity.json').read_text());cases=d['cases']
def span(kind):
 v=[r['correct']/100 for r in cases if r['kind']==kind]
 return f'{min(v):.2f}..{max(v):.2f}%'
rail=[r for r in cases if r['kind']=='common_rail_only']
endpoints=[r for r in rail if r['rail_V'] in [4.75,5.,5.25]]
text='\n\nShared onboard regulator / AHCT recheck\n\n'
text+='Selected part is Nexperia74AHCT595D SO16 C554704, powered by onboard L7805CV TO220 C111887 from+15V. All PWM high commands and BOTH layers +5V_REF biases co-vary together. The11-point4.75..5.25V sweep scales both B and positive-node PB before KCL solves, recalculating q; this is not an input-only scale shortcut. Fixed13.5V summer and12.7V rectifier clips and3.3V ADC reference are unchanged.\n\n'
text+='Official held-out10000 images, no retraining/resistor changes. Shared-rail accuracy '+span('common_rail_only')+'. '+', '.join(f"{r['rail_V']:.2f}V gives{r['correct']/100:.2f}%" for r in endpoints)+'. Historical nominal95.01% and1000-boardMC remain unchanged; no MC at rail/driver corners performed.\n\n'
text+='Manufacturer Rev9 dated9May2025 page8 atVCC4.5V, VI=VIH/VIL, IO=-8mA/+8mA gives VOHmin/VOLmax3.94/.36V at25C,3.80/.44V at-40..85C,3.70/.55V at-40..125C. Applying these as fixed endpoints withzero extra driver impedance gives diagnostic accuracy '+span('published_loaded_endpoint_diagnostic')+'. This is NOT an output I-V curve, operating-current guarantee or accuracy bound. Datasheet https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT595.pdf . AHCT operatingVCC4.5..5.5V, VIHmin2V/VILmax0.8V. Absolute25mA/output and75mA supply/ground limits are not design targets or guaranteed VOH/VOL operating points.\n\n'
text+='Independent assumed driver0/50/70/87.5/100/200ohm sweeps at4.75/5/5.25V span '+span('impedance_sensitivity_not_guarantee')+'.70/87.5/100ohm are high-output secants from published8mA endpoints, not guaranteed differential/source resistances. Separately extrapolated high=rail-0.8V,low=0.55V with50ohm driver atthose rails span '+span('extrapolated_loaded_level_stress_not_guarantee')+'. Extrapolation and double-effect level/impedance stress are deliberately diagnostic, not manufacturer qualification.\n\n'
text+='All35 cases evaluated CUDAfloat64 on'+d['device']+'; independent NumPy full10000-image KCL calculations crosscheck ADC/score/hidden for every case to numerical precision. The5V nominal ADC tensor exactly matches thehistoricalCUDAimplementation. Static-node switching-current estimates and average currents are in commonrail_sensitivity.json; they do not certify dynamic bank currents, rail noise, timing, thermals, ground bounce, mismatched channels, opamp offset/commonmode/bandwidth/recovery or fullPWMtransients. No PCB files changed. desired_netlist.json contains only resistor connectivity, no HCT metadata, so it is intentionally not metadata-edited.\n'
p=H/'RESULT.md';p.write_text(p.read_text()+text)
print(text)
