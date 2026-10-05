"""Static AHCT/common-regulator diagnostics. No retraining or CAD changes."""
import json, copy, hashlib
import numpy as np
import torch
from cuda_mc import H, tensor, draw, layer, run
from model import coefficients

def packs(c, rail):
    out=[]
    for rows,n in [(c['layer1'],64),(c['layer2'],16)]:
        W,B,P,PB,G=coefficients(rows,n)
        out.append((W,B*(rail/5),P,PB*(rail/5),G))
    return out

def numpy_layer(pack, rs):
    W,B,P,PB,G=pack
    C=np.diag(G.sum(0))-G.T@P
    T=np.linalg.solve(np.eye(W.shape[1])+rs*C,np.eye(W.shape[1]))
    q=T@(rs*(G.T@PB))
    return T.T@W.T,q@W.T+B,T,q

def numpy_run(duty,c,case):
    p1,p2=packs(c,case['rail_V'])
    rs=10000+case['driver_ohms']
    command=case['low_V']+duty*(case['high_V']-case['low_V'])
    A,b,T,q=numpy_layer(p1,rs)
    sums=np.clip(command@A+b,-13.5,13.5)
    hidden=np.clip(-sums,0,12.7)
    A,b,_,_=numpy_layer(p2,1.)
    scores=np.clip(hidden@A+b,-13.5,13.5)
    adc=np.round(((scores/220000+3.3/22000)/(1/220000+2/22000))/3.3*4095)/4095*3.3
    return adc,scores,hidden

@torch.no_grad()
def gpu_run(duty,c,case):
    p1,p2=packs(c,case['rail_V'])
    rs=10000+case['driver_ohms']
    command=case['low_V']+duty*(case['high_V']-case['low_V'])
    A,b=layer([p1],64,np.full((1,64),rs))
    sums=(command[None]@A+b[:,None]).clamp(-13.5,13.5)
    hidden=(-sums).clamp(0,12.7)
    A,b=layer([p2],16,1.)
    scores=(hidden@A+b[:,None]).clamp(-13.5,13.5)
    adc=(((scores/220000+3.3/22000)/(1/220000+2/22000))/3.3*4095).round()/4095*3.3
    return adc,scores,hidden

def main():
    c=json.loads((H/'circuit.json').read_text());d=np.load(H/'data/test.npz')
    duty=np.round(d['X'].astype(float)/5*63)/63
    X=tensor(duty);Y=torch.tensor(d['y'],device='cuda')
    cases=[]
    for rail in np.linspace(4.75,5.25,11):
        cases.append(dict(kind='common_rail_only',rail_V=float(rail),high_V=float(rail),low_V=0.,driver_ohms=50.))
    # Exact published VCC=4.5V loaded endpoints, not a transfer curve or bound.
    for temp,high,low in [('25C',3.94,.36),('-40..85C',3.80,.44),('-40..125C',3.70,.55)]:
        cases.append(dict(kind='published_loaded_endpoint_diagnostic',temperature=temp,rail_V=4.5,high_V=high,low_V=low,driver_ohms=0.))
    # Secant resistance derived from (4.5-VOH)/8mA. This is NOT guaranteed resistance.
    for r in [0.,50.,70.,87.5,100.,200.]:
        for rail in [4.75,5.,5.25]:
            cases.append(dict(kind='impedance_sensitivity_not_guarantee',rail_V=rail,high_V=rail,low_V=0.,driver_ohms=r))
    for rail in [4.75,5.,5.25]:
        cases.append(dict(kind='extrapolated_loaded_level_stress_not_guarantee',rail_V=rail,high_V=rail-.8,low_V=.55,driver_ohms=50.))
    results=[]
    for case in cases:
        got=gpu_run(X,c,case);ref=numpy_run(duty,c,case)
        errors=[float(np.max(np.abs(t[0].cpu().numpy()-n))) for t,n in zip(got,ref)]
        assert errors[0]<1e-12 and max(errors[1:])<1e-9,errors
        correct=int((got[0][0].argmax(1)==Y).sum())
        p1,_=packs(c,case['rail_V']);rs=10000+case['driver_ohms'];_,_,T,q=numpy_layer(p1,rs)
        command=case['low_V']+duty*(case['high_V']-case['low_V'])
        actual=command@T.T+q
        dc_mA=float(np.max(abs(command-actual))/rs*1000)
        # At switching instant capacitor voltage is continuous. This is a sampled DC-node estimate, not transient certification.
        switched_mA=float(np.max(np.maximum(abs(case['high_V']-actual),abs(case['low_V']-actual)))/rs*1000)
        results.append(dict(**case,correct=correct,accuracy=correct/len(duty),numpy_cuda_max_errors=errors,max_average_driver_current_mA=dc_mA,max_switching_current_from_static_nodes_mA=switched_mA))
        print(case['kind'],case['rail_V'],correct,flush=True)
    baseline=run(tensor(duty*5),[draw(c,None)],c)
    nominal=next(r for r in results if r['kind']=='common_rail_only' and r['rail_V']==5.)
    assert nominal['correct']==9501
    assert torch.equal(baseline[0],gpu_run(X,c,nominal)[0])
    out=dict(device=torch.cuda.get_device_name(),dtype='float64',examples=10000,dataset='official held-out MNIST, unchanged crop/BOX8x8 and 6bit quantization',circuit_sha256=hashlib.sha256((H/'circuit.json').read_bytes()).hexdigest(),co_variation='Both layers B and PB scale by rail/5 before coupled KCL solve. Input commanded high uses same rail. C/T unchanged except source impedance; q recalculated from scaled PB. ADC reference remains 3.3V.',datasheet=dict(url='https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT595.pdf',revision='9, 9 May 2025',part='Nexperia 74AHCT595D SO16/SOT109-1, C554704',recommended_VCC=[4.5,5.5],VIH_min_V=2.,VIL_max_V=.8,loaded_test='VCC=4.5V, VI=VIH or VIL, VOH at -8mA and VOL at +8mA',VOH_min_V=[3.94,3.8,3.7],VOL_max_V=[.36,.44,.55],temperature_ranges=['25C','-40..85C','-40..125C'],light_load_test='VCC=4.5V, +/-50uA, VOH>=4.4V, VOL<=0.1V all specified temperatures',absolute_limits_not_operating_targets=dict(output_mA=25,supply_mA=75,ground_mA=75)),limitations='Nominal resistors only; historical 1000-board MC preserved separately and not rerun at rail/driver corners. Loaded endpoints are specifications at a stated current, not measured current-voltage curves; 50ohm and derived secants are assumptions, not certified bounds. Extrapolated rail-relative level corners are diagnostic only. Published endpoint cases set added driver impedance zero to avoid double-counting load drop. Fixed 13.5V/12.7V opamp clips remain optimistic. No offset, commonmode, bandwidth, capacitor dynamics, inter-channel driver mismatch, package simultaneous-switching, ground bounce, regulator noise, thermal, timing or hardware certification.',cases=results)
    (H/'commonrail_sensitivity.json').write_text(json.dumps(out,indent=2)+'\n')
    print('DONE',flush=True)

if __name__=='__main__':main()
