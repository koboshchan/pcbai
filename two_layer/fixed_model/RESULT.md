Signed 64-16-10 analog repair

Complete component-level static model and binary MNIST training. This does not claim fabricated-board validation, SPICE validation, or original92.15% accuracy reproduction.

Authoritative artifacts are circuit.json, desired_netlist.json, trained_float.npz, best.pt, metrics.json, dataset_provenance.json. desired_netlist.json contains full new synaptic, bias, feedback, balance resistor pad nets plus existing TL074 input-pad patches. Board CAD is owned by parent, not written here.

Architecture

Keep64IN,16V_SUM,16ACT,10SCORE buses and76-pin slot mapping. Local differential weighted summer per neuron, existing amplifier count unchanged on weight cards. Synapse sign is encoded by physical attachment to POS or INV input, not metadata. L1 implements negative learned preactivation, DC2 inverting rectifier turns this into positive hidden activation. L2 directly implements scores. One E96 ground resistor balances conductances on whichever leg needs it; rounded mismatch included in model. Realized gain equation is out=(1+Rf*(Gn+Gbn))*Vplus-Rf*sum(gn*x), Vplus=sum(gp*x)/(Gp+Gbp). Rf100k1%; weight and bias resistors E24 5%; balance E96 1%.1041 neural resistors including weights,biases,feedbacks,balances across both layers.

DC2 requires16unity followers,4TL074additional, because inactive raw rectifier10k output impedance is coupled/backdriven by L2 positive leg. Rename rectified diode/R_FB output RECT_k and keep ACT_k as follower output. Rectifiers remain R_IN=R_FB10k1%,2silicon1N4148W per channel. Followers inputs RECT_k, output ACT_k, feedback ACT_k to negative input, positive input RECT_k. Their output drive current and transient recovery remain a qualification requirement.

Delete/disable old score diode max bus and direct1kLED loads or independently buffer them. Algorithm chooses largest ADC sample, no claim of unique legal analog winner or one-hot LED circuitry. Ground unused TL074 positive inputs and configure unity feedback from output to negative input, do not short outputs to ground as original board did.

Input and dataset

Motherboard74HC595 outputs are binary, not analog grayscale. Officialylecun/mnist parquet train60000/test10000 downloaded and SHA256recorded. Preprocess exactly original crop intensity>20 with2pxpadding, square-expanded bbox, PIL BOX8x8, then threshold2.5V into0/5V. Training55000/validation5000split seed42064. Validation selected best quantization-aware epoch; test never selects epoch. Training60epochs initialized originalfloatcheckpoint, final45conductanceQATepochs with physical tolerance injection last35epochs. GPU4070SUPER.

Accuracy

Nominal predicted10k-test accuracy83.60%,8360correct,50ohm input source model. Source0ohm83.55%,100ohm83.61%. ADC12bitquantization included, no perchannel tolerance calibration.200independent board realizations, each same10000examples. MC seed51005, independent uniform5%actualweight/bias resistors,1%feedback/balance/rectifier/ADC resistors. Shared neuron feedback/balance creates coefficient correlation; all resistors shared across that board's examples. MC mean83.4051%,sampleSD0.1701percentagepoints,minimum82.78%,maximum83.75%,5thpercentile83.089%. These are simulated tolerance distributions, not worstcase guarantees or confidence limits on manufactured yield. No opamp offset/noise distribution is modeled. Originalgrayscale92.15%claimed figure not reproduced and not comparable.

Physical loading

Input source impedance50ohm assumed,0/50/100ohm sensitivity reported. Full KCL solves shared input loading through all positive/negative legs and positive node common voltages.16follower output modeled1ohmsource resistance, no independent matrix Gaussian fiction. Conservative static amplifier output clip±10V, raw rectifier ACT limit9.2V for diode headroom. ±15Vrails assumed; original netlabels±12V require parent supply decision. Output clip is a modeling envelope, not full TL074 common-mode/load/temperature or recovery guarantee. TL074 offset,current limits,noise,finitegain,settling,PWM not included. https://www.st.com/resource/en/datasheet/tl074.pdf

ADC

Perchannel220kSCORE->MID,22k3V3->MID,22kGND->MID,1kMID->ADC, all1%divider components. Upper clamp anodeADC/cathode3V3, lower clamp anodeGND/cathodeADC,1N4148W SOD123. Add3V3 supply to motherboard MCUscore/header. Full±15Vsteady score bound, resistor1%corners,3V3±5% gives0.75614..2.38679V. Zero-drop powered clamp injection0. Poweroff bound62.9728uA/pin,629.7284uAfor10pins, includes series1%corner and both bias rails0. Silicon diodes cannot guarantee external conduction before internal ESD, absolute3.6V protection, or prevent3V3backfeed. MCUground/3V3first, analograils last; reverse shutdown. No transient protection guarantee.

Tests

checks.py passes4structural/nodal/corner checks. Both ground-balance leg cases recover exact desired ideal coefficients with constructed resistors; full input shared-node KCL equality independently checked; voltage and injection corners enumerated. Positive-value component check passes1041resistors. Compilation passes. Source boards/rootREADME/rootemulator untouched.
