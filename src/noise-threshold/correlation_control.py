"""Explicitly separate stress control: stationary Gaussian AR(1) noise.

The interactive bench remains IID. This checks the cost of incorrectly using an
IID null calibration on correlated noise of the same per-sample variance.
"""
import math,json,time
from pathlib import Path
from model import RNG,phase_grid,measure,family_seed,wilson,simulate
OUT=Path(__file__).resolve().parent/'data'

def ar_record(a,rho,seed,n=256,keep=False):
    rng=RNG(seed);z=rng.normal();wave=phase_grid(n);errors=[]
    for i in range(n):
        if i:z=rho*z+math.sqrt(1-rho*rho)*rng.normal()
        errors.append(.8*z)
    noisy=[a*w+e for w,e in zip(wave,errors)]
    r=measure([int(x>1) for x in noisy],wave,errors)
    if keep:r['errors']=errors
    return r

def main():
    start=time.perf_counter();base=20261025;rows=[];iidcut=json.loads((OUT/'controls.json').read_text())['frozen_cutoff']
    assert ar_record(.25,0,base)==simulate(.25,1,.8,base,256)
    for rho in (0,.5,.9,.98):
        calibration=sorted(ar_record(0,rho,family_seed(base,3,i))['projection'] for i in range(512))
        cutoff=calibration[math.ceil(.95*512)-1]
        nil=[ar_record(0,rho,family_seed(base,4,i),keep=True) for i in range(512)]
        sig=[ar_record(.25,rho,family_seed(base,5,i)) for i in range(512)]
        variance=sum(r['mse'] for r in nil)/len(nil)
        autocov=sum(sum(e1*e2 for e1,e2 in zip(r['errors'],r['errors'][1:]))/255 for r in nil)/len(nil)
        rows.append({'rho':rho,'expected_marginal_variance':.64,'observed_null_mean_squared_noise':variance,'lag1_correlation_from_second_moments':autocov/variance,
                     'iid_cutoff':iidcut,'correctly_calibrated_cutoff':cutoff,
                     'using_iid_null_calibration':{'power':wilson(sum(r['projection']>iidcut for r in sig),512),'false_alarm':wilson(sum(r['projection']>iidcut for r in nil),512)},
                     'using_matched_correlated_null':{'power':wilson(sum(r['projection']>cutoff for r in sig),512),'false_alarm':wilson(sum(r['projection']>cutoff for r in nil),512)}})
    assert all(abs(r['observed_null_mean_squared_noise']-.64)<.06 for r in rows)
    assert all(abs(r['lag1_correlation_from_second_moments']-r['rho'])<.025 for r in rows)
    data={'parameters':{'a':.25,'threshold':1,'noise_sd':.8,'n':256,'base_seed':base,'calibration_batches':512,'test_batches_per_class':512},'rows':rows,'seconds':time.perf_counter()-start,'scope':'Additional model stress test only; IID comparator results are unchanged. Stationary initialization preserves variance; correlated samples are not extra independent observations.'}
    (OUT/'correlation-control.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'seconds':data['seconds'],'rows':[{'rho':r['rho'],'iid_pfa':r['using_iid_null_calibration']['false_alarm']['rate'],'matched_pfa':r['using_matched_correlated_null']['false_alarm']['rate'],'matched_power':r['using_matched_correlated_null']['power']['rate']} for r in rows]},indent=2))
if __name__=='__main__':main()
