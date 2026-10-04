#!/usr/bin/env python3
"""Conservative ADC divider corner audit, not proof of silicon clamp voltage."""
import itertools,json
from pathlib import Path

def voltage(score,reference,r_score,r_ref,r_ground):
    return (score/r_score+reference/r_ref)/(1/r_score+1/r_ref+1/r_ground)

def main():
    cases=[]
    for score,reference,ts,tr,tg in itertools.product([-15,15],[3.3*.95,3.3*1.05],[-.05,.05],[-.05,.05],[-.05,.05]):
        rs,rr,rg=220000*(1+ts),22000*(1+tr),22000*(1+tg)
        v=voltage(score,reference,rs,rr,rg)
        cases.append({'score':score,'reference':reference,'resistors':[rs,rr,rg],'voltage':v})
    low=min(cases,key=lambda x:x['voltage']);high=max(cases,key=lambda x:x['voltage'])
    # Powered upper bound compared with same individual reference, not fixed3.3.
    margin=min(c['reference']-c['voltage'] for c in cases)
    # Unpowered reference=0, conservatively pretend clamp conducts at0V.
    # Divider shunts represented by exact Thevenin series plus1k at5%low.
    injection=[]
    for ts,tr,tg in itertools.product([-.05,.05],repeat=3):
        rs,rr,rg=220000*(1+ts),22000*(1+tr),22000*(1+tg)
        eq=1/(1/rs+1/rr+1/rg)
        injection.append(abs(voltage(15,0,rs,rr,rg))/(eq+950))
    result={'normal_score_bound_V':[-15,15],'reference_tolerance_percent':5,'divider_tolerance_percent':5,'minimum_case':low,'maximum_case':high,'min_upper_reference_margin_V':margin,'powered_range_pass':low['voltage']>0 and margin>0,'poweroff_zero_drop_injection_bound_A_per_channel':max(injection),'poweroff_total_A_10channels':10*max(injection),'nominal_endpoints_15V':[voltage(-15,3.3,220000,22000,22000),voltage(15,3.3,220000,22000,22000)],'limits':'External1N4148WsiliconclampsNOTguaranteedtoengagebeforeMCUinternalESDandNOTpoweroffbackfeedproof. GPIOreferenceandMCUpoweredfirst,analograilsenabledlast/offfirst. NoADCsamplingtimingguaranteeuntiltargetMCUacquisitionimpedance/timingchecked. Noopenresistorfaultproof.'}
    assert result['powered_range_pass']
    Path(__file__).with_name('adc_corner_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
