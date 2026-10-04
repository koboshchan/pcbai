#!/usr/bin/python3
"""Onboard +15 -> +5 linear power. KiCad10 system Python only.
Run after repair_motherboard_final.py. Thermal release requires heatsink testing.
"""
from pathlib import Path
import json,subprocess,math
import pcbnew as p
ROOT=Path(__file__).resolve().parent
PCB=ROOT/'motherboard_adc_repaired_unrouted.kicad_pcb'
def net(b,n):
 if n not in b.GetNetsByName():b.Add(p.NETINFO_ITEM(b,n))
 return b.GetNetsByName()[n]
def snapshot(b):
 return {f.GetReference(): {'pads':{q.GetNumber():q.GetNetname() for q in f.Pads()},'value':f.GetValue(),'xy':[f.GetPosition().x,f.GetPosition().y],'angle':f.GetOrientationDegrees()} for f in b.GetFootprints()}
def ahct_drive_audit():
 # Nexperia Rev9 pp6-10. Current ratings are not an output-voltage guarantee.
 channel=5.25/9500
 return {'datasheet_revision':'9, 9 May 2025','VIH_min_V':2.0,'VIL_max_V':0.8,
 'VCC_operating_V':[4.5,5.5],'input_transition_max_ns_per_V':20,
 'output_test_VCC_V':4.5,'output_test_current_mA':8,
 'VOH_min_85C_V':3.80,'VOL_max_85C_V':0.44,
 'VOH_min_125C_V':3.70,'VOL_max_125C_V':0.55,
 'filter_channel_bound_A':channel,'filter_bank_8_bound_A':8*channel,
 'continuous_serial_50pF_10MHz_average_A':50e-12*5.25*10e6,
 'bank_outputs_plus_serial_average_A':8*channel+50e-12*5.25*10e6,
 'absolute_output_mA_not_design_rating':25,'absolute_bank_supply_mA':75,
 'serial_next_input_max_pF':10,'serial_assumed_total_pF':50,
 'serial_DC_leakage_125C_uA':2,'CPD_typical_pF':190,
 'guaranteed_rail_tracking':False,
 'qualification':'8mA test rows are characterization conditions, not 25mA design permission. 0.553mA/channel and 4.421mA/filter bank are below test current. 50pF serial load is an assumption requiring routed capacitance and edge/peak-current verification; average current does not bound transient peaks. No guaranteed intermediate-load rail droop or linear output resistance; model must cover VOH/VOL and common rail separately. 1.5mA TTL allowance is specified at VI=VCC-2.1V, not a guarantee for all input voltages.'}

def main():
 b=p.LoadBoard(str(PCB));assert b.GetCopperLayerCount()==2 and not list(b.GetTracks())
 before=snapshot(b)
 owned={'J_REF_IN','U_REG5','C_REG_IN','C_REG_OUT','C_REG_BULK','R_REF_LINK','R_REG_MINLOAD'}
 for f in list(b.GetFootprints()):
  if f.GetReference() in owned:b.Delete(f)
 def add(lib,item,ref,value,x,y,nets,bottom=True,desc=''):
  f=p.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty',item);assert f
  f.SetUuid(p.KIID());f.SetReference(ref);f.SetValue(value);f.Value().SetVisible(False)
  f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));b.Add(f)
  if bottom:f.Flip(f.GetPosition(),False)
  f.SetLibDescription(f.GetLibDescription()+'; '+desc)
  for q in f.Pads():q.SetNet(net(b,nets[q.GetNumber()]))
  return f
 add('Package_TO_SOT_THT','TO-220-3_Vertical','U_REG5','L7805CV',61,96,{'1':'+15V','2':'GND','3':'+5V'},False,'LCSC C111887; ST; pin1 IN pin2 GND tab GND pin3 OUT; mandatory external heatsink thetaSA<=10C/W in actual ambient, interface<=2C/W; mechanical fit and bench qualification pending')
 add('Capacitor_SMD','C_0805_2012Metric','C_REG_IN','0.33uF',60,94,{'1':'+15V','2':'GND'},True,'50V X7R; >=0.33uF effective capacitance required')
 add('Capacitor_SMD','C_0805_2012Metric','C_REG_OUT','0.1uF',66,94,{'1':'+5V','2':'GND'},True,'50V X7R')
 add('Capacitor_SMD','CP_Elec_5x5.8','C_REG_BULK','10uF',83,94,{'1':'+5V','2':'GND'},True,'>=16V polarized; burst local reservoir; qualification pending')
 add('Resistor_SMD','R_0805_2012Metric','R_REF_LINK','0R',52,92,{'1':'+5V','2':'+5V_REF'},True,'Shared regulator source for PWM high and bias; 0ohm, do not omit')
 add('Resistor_SMD','R_0805_2012Metric','R_REG_MINLOAD','820',52,94.5,{'1':'+5V','2':'GND'},True,'5%; >=0.125W; ensures >=5mA regulator load even with MCU absent and all outputs low')
 for f in b.GetFootprints():
  if f.GetReference().startswith('U_SR'):
   assert f.GetValue() in ('74HCT595D','74AHCT595D');f.SetValue('74AHCT595D');f.SetLibDescription('Nexperia 74AHCT595D,112 SO16 LCSC C554704; supply4.5..5.5V TTL inputs')
  if f.GetReference()=='J_MCU_SPI':
   f.SetValue('MCU_3V3_SPI_PIN1_NC');
   for q in f.Pads():
    if q.GetNumber()=='1':q.SetNet(net(b,'NC_MCU_PIN1'))
 p.SaveBoard(str(PCB),b);b=p.LoadBoard(str(PCB));after=snapshot(b)
 exceptions=owned|{'J_MCU_SPI'}|{r for r in before if r.startswith('U_SR')}
 assert all(after[r]==v for r,v in before.items() if r not in exceptions)
 for r in before:
  if r.startswith('U_SR'):assert after[r]['pads']==before[r]['pads'] and after[r]['xy']==before[r]['xy']
 assert after['J_MCU_SPI']['pads']['1']=='NC_MCU_PIN1'
 assert all(after['J_MCU_SPI']['pads'][str(i)]==before['J_MCU_SPI']['pads'][str(i)] for i in range(2,7))
 assert 'J_REF_IN' not in after
 assert after['C_BULK_P']['pads']=={'1':'+15V','2':'GND'} and after['C_BULK_N']['pads']=={'1':'GND','2':'-15V'}
 # Conservative bias current bound: count all connections to +5V_REF across actual repaired daughters.
 bias=0.;bias_paths=[]
 for fn in sorted(ROOT.glob('daughter*repaired_unrouted.kicad_pcb')):
  bb=p.LoadBoard(str(fn))
  for f in bb.GetFootprints():
   if f.GetReference().startswith('R') and any(q.GetNetname()=='+5V_REF' for q in f.Pads()):
    v=f.GetValue().lower().replace('ohm','').strip()
    try:r=float(v[:-1])*{'k':1000,'m':1e6}[v[-1]] if v[-1] in 'km' else float(v)
    except (ValueError,KeyError):raise AssertionError(('unknown bias resistor',fn.name,f.GetReference(),v))
    # Bound other terminal anywhere inside +/-15.75 rails, 5% resistance.
    current=(5.25+15.75)/(r*.95);bias+=current;bias_paths.append([fn.name,f.GetReference(),r,current])
 def budget(duty,mult):
  voltage=5.25;dyn=8*190e-12*voltage*20e6*duty*mult
  ttl=25*1.5e-3;icc=8*80e-6;filters=64*voltage/9500
  serial=8*50e-12*voltage*10e6*duty
  minimum=voltage/(820*.95)
  load=dyn+ttl+icc+filters+serial+minimum+bias
  # Conservative independently combined current and voltage corners.
  diss=(15.75-4.75)*load+15.75*.0093
  return {'clock_duty':duty,'cpd_multiplier':mult,'dynamic_A':dyn,'TTL_extra_A':ttl,'static_A':icc,'filters_A':filters,'serial_capacitance_A':serial,'minimum_load_A':minimum,'bias_bound_A':bias,'Iout_A':load,'P_reg_W':diss,'Tj_bare_TO220_C':50+50*diss,'Tj_bare_D2PAK_C':50+62.5*diss,'Tj_with_10C_W_sink_and_2C_W_interface_C':50+17*diss}
 # 6-bit BCM, base quantum3.2us, total63 quanta, 64-bit shifts at20MHz.
 frame_hz=1/(63*3.2e-6)
 duty=6*64/20e6*frame_hz
 thermal={'normal_BCM':budget(duty,1),'continuous_clock':budget(1,1),'continuous_clock_CPD_50pct_margin':budget(1,1.5)}
 drc=ROOT/'motherboard_power_placement_drc.json'
 subprocess.run(['kicad-cli','pcb','drc','--format','json','--all-track-errors','-o',str(drc),str(PCB)],check=True)
 d=json.loads(drc.read_text());errors=[v for v in d['violations'] if v.get('severity')=='error']
 report={'board':PCB.name,'regulator':'ST L7805CV','LCSC':'C111887','regulator_output_V':[4.75,5.25],'required_model':'PWM high and +5V_REF co-vary with common regulator output; driver load droop separate','sources':['https://www.st.com/resource/en/datasheet/l78.pdf','https://www.lcsc.com/product-detail/C111887.html','https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT595.pdf','https://www.lcsc.com/product-detail/shift-registers_nexperia-74ahct595d-112_C554704.html'],'input':'+15V,GND,-15V only; MCU separately provides3V3_ADC and SPI','MCU_pin1':'NC, never attach5V','negative_reference':'unsourced preserved unused bus','thermal':thermal,'BCM_frame_hz':frame_hz,'AHCT_driver':ahct_drive_audit(),'repaired_schematic_final_gate':'Missing current repaired schematic; root HC/HCT sheets obsolete and untouched','bias_paths':bias_paths,'thermal_release_passed':False,'thermal_note':'Heatsink <=10C/W at actual50C local ambient with interface<=2C/W is REQUIRED; physical fitting and thermal bench test pending. CPD is typical, not guaranteed maximum. 50pct multiplier is engineering margin, not datasheet guarantee. No bare-package operation authorization. Minimum normal junction0C for C version. Current budget25 TTL inputs =3 shared MCU lines*8+DS first; MR tied5V. Includes bounded rail-to-bias resistor current.','preserved_filters':64,'preserved_ADC_and_slot_pad_nets':True,'power_parts':{r:after[r] for r in owned if r in after},'drc_error_count':len(errors),'unconnected_count':len(d.get('unconnected_items',[])),'fabrication_ready':False}
 (ROOT/'power_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not errors
if __name__=='__main__':main()
