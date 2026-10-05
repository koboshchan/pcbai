"""Render scoped results from metrics; does not modify any other project file."""
import json
from pathlib import Path
H=Path(__file__).resolve().parent
m=json.loads((H/'metrics.json').read_text())
assert m['boards_each']==1000 and 'seconds' in m
rows=[]
for n,d in m['cases'].items():
 mc=d.get('mc_0.05');one=d.get('mc_0.01')
 rows.append(f"| {n} | {d['Rh_ohms']:g}/{d['Rl_ohms']:g} | {d['accuracy']*100:.2f}% | "+(f"{mc['mean']*100:.5f}% | {mc['worst']*100:.2f}% | {one['mean']*100:.5f}% | {one['worst']*100:.2f}% |" if mc else 'not run | not run | not run | not run |'))
load=m['cases']['HCT_worst_secant']['loading']
pin=5.5/9500*1000;chip=pin*8
text=f'''Genuine 74HCT595 is acceptable for this candidate's analog input drive. There is no meaningful modeled accuracy penalty versus AHCT. This is conditional engineering approval of the logic family, not authentication of the cheap AliExpress chips or a complete board qualification. Ordinary 74HC595 is not an equivalent 3.3V-input substitute at 5V.

The official 10000-example test is unchanged. Every Monte Carlo entry uses 1000 physical boards and the same 10000 examples, seed51005, with paired physical resistor draws between driver cases. Weight/bias and input-filter resistors vary uniformly by the listed tolerance. Feedback, balancing, rectifier and ADC resistors remain1%. No network retraining, CAD, routing, BOM or cart modifications occurred. Historical50ohm simulation is reproduced and checked against the existing evaluator.

| Driver | High/low resistance ohms | Official | 5% MC mean | 5% MC worst | 1% MC mean | 1% MC worst |
| --- | --- | --- | --- | --- | --- | --- |
'''+ '\n'.join(rows)+f'''

The model solves the shared 64-input KCL, including coupling through positive summer legs, rather than attenuating pixels independently. Each pin drives one 10k series resistor, then one1uF capacitor to ground and the post-filter L1 fanout. There are {min(m['load_counts_per_input'])} to {max(m['load_counts_per_input'])} L1 resistor branches per filtered input. Those branches do not multiply the output load by their count because the same10k input filter is in series with the whole network. The1uF is not directly connected to the595 output. Source output load is set primarily by10k, so even100ohm driver impedance only changes it by about1%.

For duty d, the averaged output term is g=d/(Rf+Rh)+(1-d)/(Rf+Rl), and its forcing term is d*VCC/(Rf+Rh). High/low asymmetry therefore changes both effective source voltage and impedance. The implementation uses three small fixed-point corrections against a low-state KCL solve, checks residuals below1e-7V, and verifies asymmetric nodes against direct NumPy solves. Driver values are fixed and coherent across64 pins for each case; they are not additional random per-pin draws.

TI HCT at4.5V and6mA specifies minimum VOH3.98V and maximum VOL0.26V at25C, and3.84V/0.33V over-40..125C. Full-temperature secants are110ohm high and55ohm low. Figure6-2/6-3 around4mA gives approximately28ohm high and29ohm low at25C, used for the typical HCT run. TI's current HCT datasheet lists a TSSOP package, not the anonymous cheap SOP16 product, so use this as a family comparison until the actual vendor is known.

TI AHCT at4.5V and8mA specifies minimum VOH3.94V and maximum VOL0.36V at25C, and3.80V/0.44V over-40..125C. Full-temperature secants are87.5ohm high and55ohm low. TI's5V typical low-state graph suggests about17ohm. Its high-state typical curve is not supplied here, so the AHCT typical case is explicitly an estimate retaining the existing conservative50ohm high assumption, not a measured manufacturer typical50ohm value. It is intentionally not a claim that AHCT has weaker typical high drive than HCT.

Diodes74AHCT595 has the same25C3.94V/0.36V points but over-40..125C specifies3.70V/0.55V at8mA, yielding100ohm/68.75ohm secants. This additional nominal case is included because that manufacturer was originally approved. The secant-derived worst cases are sensitivity models, NOT guaranteed sub-mA output resistance or rigorous worst-case accuracy bounds. Extrapolation is stated explicitly; real nonlinear I/V and pin variation require bench measurement.

At5.5V with10k-5%=9.5k, a capacitor initially at the opposite rail gives at most{pin:.4f}mA per pin, and{chip:.4f}mA for all8 pins on one chip. This conservative charging/discharging bound assumes the RC node remains between ground and VCC during normal powered operation. It does not bound power sequencing, faults, switching shoot-through, or an unpowered opamp feeding the RC node. The source branch current bypasses the uncertainty about detailed fanout and remains far below6mA HCT characterization current and8mA AHCT recommended current.

TI HCT absolute maximum is35mA per output and70mA through VCC/GND. The above analog load uses{pin/35*100:.2f}% of the per-pin maximum and{chip/70*100:.2f}% of the rail maximum, leaving{35-pin:.3f}mA and{70-chip:.3f}mA respectively before the IC's own consumption. TI/Diodes AHCT limits are25mA and75mA, leaving{25-pin:.3f}mA per pin and{75-chip:.3f}mA on the supply rail. These absolute maximum margins are stress comparisons, not operating targets.

Across the official test, HCT worst-secant nominal averaged branch peak is{load['pin_average_abs_peak_mA']:.4f}mA. Hypothetical high-phase and low-phase peaks using the averaged RC node are{load['pin_high_phase_peak_mA']:.4f}mA and{load['pin_low_phase_peak_mA']:.4f}mA. Per-eight-input-group average source peaks in mA are{load['chip_average_source_peak_mA']}; sink peaks are{load['chip_average_sink_peak_mA']}. The generator maps U_SR1..8 to group starts0,8,16,24,56,48,40,32, so the last four current groups correspond to U_SR8,7,6,5, not U_SR5,6,7,8. QH' only drives the next SER logic input, not another analog channel.

IC supply consumption is additional to output load. TI HCT lists80uA rail-input quiescent ICC plus up to2.9mA per input under its unfavorable0.5V/2.4V test condition. With SER,SRCLK,RCLK,OE conservatively treated as four MCU-level inputs, this illustrative static budget is{chip+0.08+4*2.9:.3f}mA, still below70mA. This2.9mA point is not a guaranteed3.3V supply-current bound. TI AHCT gives40uA ICC and1.5mA per input at3.4V, Diodes gives80uA and1.5mA atVCC-2.1V. Actual clock-frequency-dependent dynamic current must also be allowed for. The tiny analog load is not the reason to select AHCT, and a complete all-condition supply-current guarantee cannot be extracted for anonymous chips from these specs alone.

Both families have2.0V VIH and0.8V VIL at their stated5V operating conditions, so3.3V Pico logic is compatible. HCT is slower. The TI HCT datasheet gives25MHz full-temperature clock characterization at4.5V plus20ns minimum clock/latch pulse widths. Do not silently reuse an AHCT-rate firmware clock above the actual HCT vendor's guaranteed chained-register timing. Capacitor settling, actual PWM frequency, startup, simultaneous switching, PCB supply noise and TL074 nonidealities remain outside this static family comparison.

Rail sensitivity uses common595 VCC and BOTH layers'5V-referenced bias terms together, while retaining3.3V ADC reference. It covers4.5,4.75,5.0,5.25,5.5V on nominal resistors rather than incorrectly moving only the pixels while holding the bias reference fixed. The full results are in metrics.json. This is a sensitivity sweep, not an assertion that the regulator has10% tolerance.

Sources are https://www.ti.com/lit/gpn/SN74HCT595 pages4,5,8; https://www.ti.com/lit/gpn/SN74AHCT595 pages4,5,7; and https://www.diodes.com/datasheet/download/74AHCT595.pdf page4. Manufacturer documents were retrieved and read directly.

Reproduce on a CUDA machine with NumPy and PyTorch using OPENBLAS_NUM_THREADS=1 python3 training/hct_vs_ahct/evaluate.py --boards 1000. Run python3 training/hct_vs_ahct/report.py after evaluation. The project candidate and official dataset must be present. The recorded circuit SHA256 is{m['circuit_sha256']} and test archive SHA256 is{m['dataset_sha256']}.

The plain decision is to use genuine HCT if the cheap listing really contains HCT in the correct footprint and the firmware clock respects its timing. AHCT's higher price is not justified by modeled accuracy or analog current headroom on this10k-filtered design. No cart change or fabrication approval is made by this report.
'''
(H/'RESULT.md').write_text(text)
print(text[:250]);print('report written')
