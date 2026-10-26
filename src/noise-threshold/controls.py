"""Controls: raw-data LRT, frozen cutoffs, retuning, finite calibration."""
import json,math,time
from pathlib import Path
from statistics import NormalDist
from model import *
OUT=Path(__file__).resolve().parent/'data'
NORMAL=NormalDist(); Z95=NORMAL.inv_cdf(.95)

def raw_power(a,sigma,n=256,measurement_sd=0):
    validate(a,1,sigma,n)
    sd=math.hypot(measurement_sd,sigma)
    if sd==0:return 1.0 if a>0 else 0.0
    return NORMAL.cdf(a*math.sqrt(n/2)/sd-Z95)

def fixed_cutoff(a,t,sigma,cutoff,base=20261025,n=256,test=512):
    nil=[simulate(0,t,sigma,family_seed(base,4,i),n)['projection'] for i in range(test)]
    sig=[simulate(a,t,sigma,family_seed(base,5,i),n)['projection'] for i in range(test)]
    return {'cutoff':cutoff,'false_alarm':wilson(sum(x>cutoff for x in nil),test),'power':wilson(sum(x>cutoff for x in sig),test)}

def main():
    start=time.perf_counter();rows=[];base=20261025
    reference=detection(.25,1,.8,base,256,512,512)
    for j in range(41):
        s=j/10;q0=exceedance(0,1,s)
        # One or more active samples; not the phase statistic.
        any_null=-math.expm1(256*math.log1p(-q0)) if q0<1 else 1
        log_miss=sum(math.log1p(-exceedance(.25*w,1,s)) for w in phase_grid(256))
        any_signal=-math.expm1(log_miss)
        rows.append({'sigma':s,'any_active':{'power':any_signal,'false_alarm':any_null},'frozen_projection':fixed_cutoff(.25,1,s,reference['cutoff']), 'calibrated_projection':detection(.25,1,s,base,256,512,512),'raw_lrt':{'false_alarm':.05 if s>0 else 0,'power':raw_power(.25,s)}})
    # Strict Gaussian negative control: existing measurement noise has SD 1.
    gaussian=[{'added_sd':j/10,'original_sd':1,'raw_lrt_power':raw_power(.25,j/10,256,1),'false_alarm':.05} for j in range(41)]
    # Calibration variability at selected fixed conditions, no optimization.
    calibrations=[]
    for offset in range(12):
        for s in (.4,.8,2):
            d=detection(.25,1,s,(base+offset*10000019)&0xffffffff,256,512,512)
            calibrations.append({'replicate':offset,'sigma':s,**d})
    # Average over randomly permuted phase labels: MI plugin bias and BA chance.
    import random
    r=simulate(.25,1,.8,base,256,True);gen=random.Random(98123)
    shuffles=[]
    for _ in range(512):
        labels=r['wave'][:];gen.shuffle(labels)
        h=2*sum(y for y,w in zip(r['outputs'],labels) if w>0)/256
        f=2*sum(y for y,w in zip(r['outputs'],labels) if w<0)/256
        shuffles.append({'ba':(1+h-f)/2,'mi':phase_information(h,f)})
    data={'reference_calibration_sigma':.8,'frozen_cutoff':reference['cutoff'],'n':256,'base_seed':base,'calibration_batches':512,'test_batches':512,'rows':rows,'gaussian_negative_control':gaussian,'calibration_replicates':calibrations,'label_shuffle':{k:summarize([r[k] for r in shuffles]) for k in ('ba','mi')},'seconds':time.perf_counter()-start}
    assert all(gaussian[i+1]['raw_lrt_power']<=gaussian[i]['raw_lrt_power'] for i in range(40))
    (OUT/'controls.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'seconds':data['seconds'],'frozen_cutoff':data['frozen_cutoff'],'gaussian_power_start_end':[gaussian[0]['raw_lrt_power'],gaussian[-1]['raw_lrt_power']],'label_shuffle':data['label_shuffle']},indent=2))
if __name__=='__main__':main()
