# Grayscale PWM physical MNIST model

The final input is grayscale6-bit BCM-PWM from64 74AHCT595 outputs through individual10k series resistors and1uF shunt capacitors. Source model50ohm plus actual10k perinput, full coupled64input nodal solution including positive-leg loading. Supply±15V, ideal static output clip±13.5V, positive rectifier headroom12.7V. Differential summers and16 ACT followers retained. No DAC or ideal unloaded input assumption.

Official MNIST uses identical intensity>20 crop with2pixelpadding, square-expanded bounds andPIL BOX8x8. Training55000 andvalidation5000, seed42064, selected only byvalidation94.84%. Official held-out10000 test result9501 correct,95.01%. This is quantized actual resistor circuit accuracy, not an ideal float benchmark. Binary83.85% float/83.60% physical andits1000boardMC preserved separately inbinary_archive.

GPU1000 independently sampled boards each evaluated onall10000 test images. Uniform perinput10kfilters5%, weights/bias5%, feedback/balance/ReLUratios/ADC1%. Shared component realizations preserve correlations across images andcoupled inputs. Mean94.90848%, worst94.47%, best95.33%. MC excludes random opampoffsets and capacitor dynamics. NumPy/CUDA nominal andthree seeded tolerance cases agree to numerical precision, seecuda_mc.json.

Conservative10V clip gives94.82% nominal. Driverhigh4.5..5V andcoherent±10mV weighted-summer/rectifier/follower diagnostic span94.60..95.01%. Not a worstcase independent-offset search, measured production spread or manufacturer guarantee. TL07413.5V swing is an optimistic approximation, not the guaranteed loaded swing. TI TL074-EP specifiesminimum12V at10kload and10V at2kload overtemperature; actual purchasedvariant must bechecked. Source https://www.ti.com/lit/gpn/TL074-EP . Full current/commonmode/bandwidth qualification remains required.

PWM simulation uses explicitLSB-first BCM with64bitSPI20MHz andminimum dwell3.2us, shift nextplane whilecurrent outputs remain latched, no extra firmware/latch overhead. Exact64node matrixexponential propagation solves periodic steady state. Fourphase samples perbitplane thenstatic nonlinear circuit inference, acrossall10000images. Capacitors0.8/1/1.2uF represent assumed20% sensitivity, not a selectedpart guarantee.

Sixbit period201.6us,4960.31746Hz. Nominal1uF maximum deviation fromloaded steadyaverage12.537mV. Acrosscapacitorcases sampledphase minimum94.97%. See authoritativepwm_ripple.json for exactphase results. Eightbit period816us,1225.49020Hz, nominaldeviation50.762mV andworst sampledphase94.91%, no useful gain. Sixbit chosenforlower ripple andstablephase accuracy. Nominal sixbitphase mean95.012083%, cap0.8/1.2uFmeans95.005833%/95.01375%.

Slowestnominal RCmode8.722572ms. Roughly40ms afternewimage for1% linear residual; this is a model-derived engineering startingpoint, not guaranteed complete boardsettling. Finite phase samples cannotproveglobalinterior extrema. Opamp bandwidth, dioderecovery, saturation recovery, AHCT sourceimpedance/nonlinear outputvoltage, latchoverhead, firmware scheduling andrail/reference noise absent fromdynamic model. Capacitor tolerances do not affect steady DC MC; filter resistor tolerances do.

Authoritativecircuit.json anddesired_netlist.json useactual localDC1weight refsj%4 withglobal Rb_Nj/Rf_Nj andglobal netnames. They are CAD inputs, notfabrication orDRC signoff. No PCBfiles modified here. Loading report is a testset diagnostic only. Final hardware acceptance needs realwaveform tests andfreshCAD electrical audit.


Shared onboard regulator / AHCT recheck

Selected part is Nexperia74AHCT595D SO16 C554704, powered by onboard L7805CV TO220 C111887 from+15V. All PWM high commands and BOTH layers +5V_REF biases co-vary together. The11-point4.75..5.25V sweep scales both B and positive-node PB before KCL solves, recalculating q; this is not an input-only scale shortcut. Fixed13.5V summer and12.7V rectifier clips and3.3V ADC reference are unchanged.

Official held-out10000 images, no retraining/resistor changes. Shared-rail accuracy 95.01..95.03%. 4.75V gives95.01%, 5.00V gives95.01%, 5.25V gives95.03%. Historical nominal95.01% and1000-boardMC remain unchanged; no MC at rail/driver corners performed.

Manufacturer Rev9 dated9May2025 page8 atVCC4.5V, VI=VIH/VIL, IO=-8mA/+8mA gives VOHmin/VOLmax3.94/.36V at25C,3.80/.44V at-40..85C,3.70/.55V at-40..125C. Applying these as fixed endpoints withzero extra driver impedance gives diagnostic accuracy 54.88..69.98%. This is NOT an output I-V curve, operating-current guarantee or accuracy bound. Datasheet https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT595.pdf . AHCT operatingVCC4.5..5.5V, VIHmin2V/VILmax0.8V. Absolute25mA/output and75mA supply/ground limits are not design targets or guaranteed VOH/VOL operating points.

Independent assumed driver0/50/70/87.5/100/200ohm sweeps at4.75/5/5.25V span 95.00..95.03%.70/87.5/100ohm are high-output secants from published8mA endpoints, not guaranteed differential/source resistances. Separately extrapolated high=rail-0.8V,low=0.55V with50ohm driver atthose rails span 56.91..60.79%. Extrapolation and double-effect level/impedance stress are deliberately diagnostic, not manufacturer qualification.

All35 cases evaluated CUDAfloat64 onNVIDIA GeForce RTX 4070 SUPER; independent NumPy full10000-image KCL calculations crosscheck ADC/score/hidden for every case to numerical precision. The5V nominal ADC tensor exactly matches thehistoricalCUDAimplementation. Static-node switching-current estimates and average currents are in commonrail_sensitivity.json; they do not certify dynamic bank currents, rail noise, timing, thermals, ground bounce, mismatched channels, opamp offset/commonmode/bandwidth/recovery or fullPWMtransients. No PCB files changed. desired_netlist.json contains only resistor connectivity, no HCT metadata, so it is intentionally not metadata-edited.
