FIXED CIRCUIT DELIVERABLE IS NOW APPROVED. Latest direct instruction supersedes prior preserve-electrical restriction. Preserve original root PCBs as evidence; repaired outputs isolated in two_layer.

Training/model engineer owns fixed_model/ ONLY, worker d7a92737. Forge owns generator/layout/routing/README and integrated emulator. Silkscreen helper engineer46b9b12c owns silk_* only.

LATEST DEFINITIVE update user explicitly requests physical signed-weight INVERTERS, not only balanced differential topology. Prefer local two-summer per neuron: negative-weight group inverts first, then final summer combines positive inputs and inverted negative-group output; L1 desired SUM negativepreactivation, existingDC2 inverts to positiveReLU. L2 desired positiveSCORE requires opposite signed group partition. Twoampsperneuron with single groupfeedback/equalunitybranch, no80globalinverters ornewbackplanenets. Need balanceoffsetbias and loading. Alternatively perinputinversion80amps if demonstrablybetter but hugeparts. CUDAmandatory train AND vectorized 5%resistorsets torchGPU4070SUPER12GB. FreeRoutingCPU. GPUchunksets conservativememoryandusephysical resistorrealizations. Sendearly topology decision for CAD.

Initial electrical inventory from frozen actual PCB manifests:
L1 each DC1x has one TL074, four summers OUT V_SUM_n / minus INV_Nn / plus GND. ReLU DC2 U1..4 has inverted stage (SUM -> R_IN10k -> INV_RELU; RF10k INV_RELU -> ACT; actual OP output OP_OUT and diode). It is not simply positive max(SUM,0). Must audit diode orientations, inactive ACT loading/backdrive, add output buffers if needed.
L2 U1 channelsn0,1,7,6; U2n2,3,9,8; U3n4,5,remaining two outputs/inputstiedGND(!). Do not leave unused outputs shorted.
Motherboard inputs are raw 74HC595 outputs, no 64 PWM RC filters visible. Emulator currently treats continuous voltages idealistically. Need RC filtering buffered/finite-source nodal solution OR explicitly implement bit-plane time-multiplex MCU protocol and retrain binary inputs. No hidden ideal PWM assumption; model source current/loading and provide realizable input drive. ADC3.3Vrail absent actualrootpinout; add dedicated3.3V reference header and deterministic net.

Constraints max100x100mm F/B copper only trace>=.2(.25preferred), clearance>=.2, vias>=.6/.3, readable component-side refdes-only silk. Correct physical76pin connector mating/cardpinmaps.

Resource request user wants kat-box utilized. Available52GB/32threads/GPU4070SUPER. Training vectorized GPU/big batches and 5%MC chunks acrosscores. Routing6-8jobs Xmx6g only when budget permits training coexistence; reserve>=4GB actualheadroom, nativeJava/OSalso counts, don't blindly48GBheaps+training. Coordinate stages so routing andtraining peaksmemorydon'tcollide. Remote/work/pcbai paths.

Authoritative model output must be explicit component resistor/pad-net manifest and nonlinear stage semantics plus tolerance assignments. No signmetadata substitute for actualsigncircuit. Need exact differentiallegbalance with ground conductance to handlepositive/negative channels if selected. Realaccuracy officialMNISTpreprocessingoriginalpreferred, otherwisedigitslabelsseparate.

Stockdiodes100x1N4148W SOD123 only,noSchottky. ADCmap +/-15rail conservativecorners into3.3V withheadroom offsetdividerand1kseries+siliconclamps; prove normalpoweredrange+quantifyfaultinjection/poweroffbackfeed+sequencewarning, notabsolutevoltageguarantee.

Status awaiting architecture manifest before generating repaired boards; unchanged routing trial terminated because it is no longer the deliverable. Oldarchive289d240provenanceonly. RootREADMEupdateatarchitecturemilestone, pushgitmilestonesapproved.
