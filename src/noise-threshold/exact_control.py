"""Exact 16-sample discrete output experiment: enumerate all 65,536 records.

This separately labelled smaller budget permits exact null probability matching.
The main 256-sample experiment remains unchanged. No Monte Carlo here.
"""
import math,json,time
from pathlib import Path
from statistics import NormalDist
from model import exceedance,entropy
N=16; ALPHA=.05
POSITIVE=[math.sin(2*math.pi*(i+.5)/N) for i in range(4)]
BIN=[0,1,2,3,3,2,1,0,0,1,2,3,3,2,1,0]
SIGN=[1]*8+[-1]*8
W=[SIGN[i]*POSITIVE[BIN[i]] for i in range(N)]
OUT=Path(__file__).resolve().parent/'data'

def softplus(x):return max(x,0)+math.log1p(math.exp(-abs(x)))

def raw_information(a,sigma,n=N,steps=4096):
    if sigma==0:return float(a>0)
    d=a*math.sqrt(n/2)/sigma
    # Symmetry of the two equiprobable Gaussian classes: average under H1 only.
    h=24/steps;total=0
    for i in range(steps+1):
        z=-12+i*h
        value=math.exp(-z*z/2)/math.sqrt(2*math.pi)*softplus(-d*z-d*d/2)/math.log(2)
        total+=(1 if i in (0,steps) else 4 if i%2 else 2)*value
    answer=1-total*h/3
    if not -1e-10<=answer<=1+1e-10:raise ValueError('quadrature outside information bounds')
    return max(0,min(1,answer))


def randomized_roc(states,score_index=0,decimals=12):
    # State tuple = (log likelihood ratio, projection, P0, P1).
    groups={}
    for row in states:
        key=row[0] if score_index==0 else row[4]
        g=groups.setdefault(key,[row[score_index],[],[]]);g[1].append(row[2]);g[2].append(row[3])
    used=0;power=0;boundary=None
    for _,(score,p0s,p1s) in sorted(groups.items(),key=lambda item:item[1][0],reverse=True):
        p0=math.fsum(p0s);p1=math.fsum(p1s)
        if p0==0:
            power+=p1;continue
        fraction=min(1,max(0,(ALPHA-used)/p0))
        used+=fraction*p0;power+=fraction*p1
        if fraction<1:
            boundary={'score':score,'fraction':fraction,'null_mass':p0,'signal_mass':p1};break
    return {'false_alarm':used,'power':power,'boundary':boundary,'score_groups':len(groups)}


def exact(a,sigma,decimals=12):
    if sigma==0:
        return {'sigma':0,'n':N,'threshold':1,'output_information_bits':0,'raw_information_bits':float(a>0),
                'np':{'false_alarm':ALPHA,'power':ALPHA,'boundary':{'fraction':ALPHA}},
                'projection':{'false_alarm':ALPHA,'power':ALPHA,'boundary':{'fraction':ALPHA}},
                'raw_lrt':{'false_alarm':ALPHA,'power':1.0 if a>0 else ALPHA},'mass0':1,'mass1':1,'note':'Comparator is identically zero; independent randomized final decision sets PFA=PD=alpha. Raw deterministic classes are perfectly separable when A>0.'}
    q0=exceedance(0,1,sigma);q1=[exceedance(a*w,1,sigma) for w in W]
    if not 0<q0<1 or not all(0<q<1 for q in q1):raise ValueError('nondegenerate probabilities required')
    states=[]
    for mask in range(1<<N):
        bits=[bool(mask&(1<<j)) for j in range(N)]
        count=sum(bits)
        p0=q0**count*(1-q0)**(N-count)
        p1=math.prod(q1[j] if bits[j] else 1-q1[j] for j in range(N))
        # Exact symmetry classes avoid inventing score differences from roundoff.
        coefficients=tuple(sum(SIGN[j] for j in range(N) if bits[j] and BIN[j]==k) for k in range(4))
        projection=2*math.fsum(c*w for c,w in zip(coefficients,POSITIVE))/N
        states.append((math.log(p1/p0),projection,p0,p1,coefficients))
    mass0=math.fsum(x[2] for x in states);mass1=math.fsum(x[3] for x in states)
    if max(abs(mass0-1),abs(mass1-1))>2e-12:raise ValueError('probability mass error')
    mi=math.fsum((.5*p0*math.log2(2*p0/(p0+p1)) if p0 else 0)+(.5*p1*math.log2(2*p1/(p0+p1)) if p1 else 0) for _,_,p0,p1,_ in states if p0+p1>0)
    normal=NormalDist();raw_power=normal.cdf(a*math.sqrt(N/2)/sigma-normal.inv_cdf(1-ALPHA))
    return {'sigma':sigma,'n':N,'threshold':1,'mass0':mass0,'mass1':mass1,'output_information_bits':mi,'raw_information_bits':raw_information(a,sigma),
            'np':randomized_roc(states,0),'projection':randomized_roc(states,1,decimals),
            'raw_lrt':{'false_alarm':ALPHA,'power':raw_power},'output_kl_nats':sum(q*math.log(q/q0)+(1-q)*math.log((1-q)/(1-q0)) for q in q1),'raw_kl_nats':N*a*a/(4*sigma*sigma)}


def main():
    start=time.perf_counter();rows=[exact(.25,s) for s in (0,.2,.3,.4,.5,.6,.7,.8,1,1.5,2,3,4,8)]
    checks={}
    checks['mass_conservation_max_error']=max(max(abs(r['mass0']-1),abs(r['mass1']-1)) for r in rows)
    checks['false_alarm_max_error']=max(abs(r[key]['false_alarm']-ALPHA) for r in rows for key in ('np','projection'))
    checks['raw_dominates_output_np']=all(r['raw_lrt']['power']+1e-10>=r['np']['power'] for r in rows)
    checks['np_dominates_projection']=all(r['np']['power']+1e-10>=r['projection']['power'] for r in rows)
    checks['raw_information_dominates']=all(r['raw_information_bits']+1e-10>=r['output_information_bits'] for r in rows)
    checks['raw_information_monotone']=all(rows[i+1]['raw_information_bits']<=rows[i]['raw_information_bits']+1e-10 for i in range(len(rows)-1))
    checks['output_kl_bounded']=all(r['output_kl_nats']<=r['raw_kl_nats']+1e-10 for r in rows if r['sigma']>0)
    checks['quadrature_refinement_error']=max(abs(raw_information(.25,s,steps=8192)-raw_information(.25,s,steps=4096)) for s in (.2,.8,4))
    checks['projection_exact_symmetry_groups']=all(r['projection']['score_groups']==625 for r in rows if r['sigma']>0)
    null=exact(0,.8)
    checks['null_power_minus_false_alarm']=null['np']['power']-null['np']['false_alarm']
    checks['null_information']=null['output_information_bits']
    assert checks['mass_conservation_max_error']<2e-10
    assert checks['false_alarm_max_error']<1e-12
    assert checks['projection_exact_symmetry_groups']
    assert all(checks[k] for k in ('raw_dominates_output_np','np_dominates_projection','raw_information_dominates','raw_information_monotone','output_kl_bounded'))
    assert checks['quadrature_refinement_error']<1e-10
    assert abs(checks['null_power_minus_false_alarm'])<1e-10 and abs(checks['null_information'])<1e-10
    data={'amplitude':.25,'threshold':1,'n':N,'samples_per_cycle':N,'cycles':1,'alpha':ALPHA,'enumerated_records_per_noise':1<<N,'rows':rows,'checks':checks,'seconds':time.perf_counter()-start,'limits':'Different N=16 budget, equal within each comparison; randomized boundary decisions achieve exact alpha. Direct probability products; exact integer symmetry classes group projection ties. Uses direct products and exact integer symmetry groups. No frequency search. Raw MI uses refined Simpson quadrature, not symbolic integration.'}
    (OUT/'exact-control.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'seconds':data['seconds'],'peak_np':max(rows,key=lambda r:r['np']['power'])['sigma'],'peak_output_mi':max(rows,key=lambda r:r['output_information_bits'])['sigma']},indent=2))
if __name__=='__main__':main()
