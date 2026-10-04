Grayscale6bit BCM-PWM is authoritative, binary results preserved in binary_archive.
Nominal official10000 MNIST95.01%, validation-selected94.84%, training55000 validation5000.
Physical source perinput10kfilter plus50ohm driver, full shared64input coupled KCL. Analog differentialL1/L2 plus16 ACT followers unchanged. ±15Vrails, ideal13.5Vswing/12.7Vrectifier maximum; not a TL074 loaded-output guarantee.
CUDA1000sets x10000 mean94.90848%, minimum94.47%, maximum95.33%. Each10kfilter/weight/bias independently uniform5%; feedback/balance/rectifier/ADC1%; component draws shared across all images. Offsets not in MC.
Conservative10Vswing nominal94.82%. Driver4.5..5V/coherent10mVoffset diagnostic94.60..95.01%, not certified worstcase.
PWM periodic transient/ripple simulation completed6/8bit cap0.8/1/1.2uF. Selected6bit4.960kHz nominal deviation12.537mV andworst sampledphase94.97%. SlowestRCmode8.7226ms;40.169ms for1% linearsettling. Static idealopamp dynamicqualification only, no hardwarecertification. Parent has trained desired_netlist.json for CAD; all further files stay underfixed_model only.
