"""Independent compressed-probability and PRNG-stream audits of final claims."""
import itertools,math,json,time
from pathlib import Path
from model import theory,family_seed
OUT=Path(__file__).resolve().parent/'data'

def compressed(sigma):
    # Eight distinct signed phase values, each observed twice: 3^8 count vectors.
    positives=[math.sin(math.pi*(2*j+1)/16) for j in range(4)]
    weights=positives+[-x for x in positives]
    from statistics import NormalDist
    normal=NormalDist();q0=normal.cdf(-1/sigma)
    # Use erfc, rather than 1-cdf, for stable tiny tails.
    q0=.5*math.erfc(1/(math.sqrt(2)*sigma))
    q1=[.5*math.erfc((1-.25*w)/(math.sqrt(2)*sigma)) for w in weights]
    groups=[]
    for counts in itertools.product(range(3),repeat=8):
        p0=math.prod(math.comb(2,k)*q0**k*(1-q0)**(2-k) for k in counts)
        p1=math.prod(math.comb(2,k)*q**k*(1-q)**(2-k) for k,q in zip(counts,q1))
        coefficients=tuple(counts[j]-counts[j+4] for j in range(4))
        score=math.fsum(k*w for k,w in zip(coefficients,positives))/8
        groups.append((p0,p1,p1/p0,score,coefficients))
    def roc(which):
        # Independent cumulative implementation; average within exactly equal
        # projection symmetry classes, rather than rounding real coefficients.
        if which=='lr':ordered=[(r[0],r[1]) for r in sorted(groups,key=lambda r:r[2],reverse=True)]
        else:
            aggregated={}
            for p0,p1,lr,score,key in groups:
                group=aggregated.setdefault(key,{'score':score,'p0':[],'p1':[]});group['p0'].append(p0);group['p1'].append(p1)
            ordered=[(math.fsum(g['p0']),math.fsum(g['p1'])) for g in sorted(aggregated.values(),key=lambda r:r['score'],reverse=True)]
        power=0;false=0
        for p0,p1 in ordered:
            remaining=.05-false
            if p0<=remaining:false+=p0;power+=p1
            else:power+=remaining*p1/p0;false=.05;break
        return false,power
    mi=math.fsum(.5*p0*math.log2(2*p0/(p0+p1))+.5*p1*math.log2(2*p1/(p0+p1)) for p0,p1,*_ in groups)
    return {'np':roc('lr'),'projection':roc('projection'),'mi':mi,'mass0':math.fsum(r[0] for r in groups),'mass1':math.fsum(r[1] for r in groups),'states':len(groups)}


def stream_audit(entries,uniforms):
    inverse=pow(0x6D2B79F5,-1,2**32)
    positions=sorted((seed*inverse)%2**32 for seed in entries)
    gaps=[(positions[(j+1)%len(positions)]-pos)%2**32 for j,pos in enumerate(positions)]
    return {'seed_count':len(entries),'distinct_seed_count':len(set(entries)),'uniforms_per_record':uniforms,'minimum_start_separation_uniforms':min(gaps),'overlapping_substreams':sum(gap<uniforms for gap in gaps),'scope':'Exact state-overlap check for this bounded schedule; not a proof of statistical independence or PRNG quality.'}


def main():
    start=time.perf_counter();exact=json.loads((OUT/'exact-control.json').read_text());rows=[]
    for r in exact['rows']:
        if r['sigma']==0:continue
        other=compressed(r['sigma'])
        errors={'np_power':abs(other['np'][1]-r['np']['power']),'projection_power':abs(other['projection'][1]-r['projection']['power']),'presence_information':abs(other['mi']-r['output_information_bits']),'mass0':abs(other['mass0']-1),'mass1':abs(other['mass1']-1)}
        assert max(errors.values())<1e-12
        rows.append({'sigma':r['sigma'],'compressed_count_states':other['states'],'errors':errors})
    stream={
        'main_families_max_n':stream_audit([family_seed(20261025,f,i) for f in range(1,6) for i in range(512)],2*4096),
        'paired_measurements':stream_audit([family_seed(20261025,f,i) for f in (6,7) for i in range(2048)],2*256),
        'calibration_replicates':stream_audit([family_seed((20261025+offset*10000019)&0xffffffff,f,i) for offset in range(12) for f in (3,4,5) for i in range(512)],2*256)}
    assert all(r['overlapping_substreams']==0 and r['seed_count']==r['distinct_seed_count'] for r in stream.values())
    retuned=[]
    for a in (.01,.25,1.5):
        values=[theory(a,0,j/10) for j in range(41)]
        monotonic={k:all(values[j+1][k]<=values[j][k]+1e-14 for j in range(40)) for k in ('balanced_accuracy','phase_mi','projection')}
        assert all(monotonic.values());retuned.append({'amplitude':a,'monotone_decrease_under_threshold_zero':monotonic,'initial_accuracy':values[0]['balanced_accuracy'],'initial_information':values[0]['phase_mi']})
    # Rigorous tail bound for the raw Gaussian MI integral truncated at |z|12:
    # softplus(-dz-d^2/2) <= d|z| + d^2/2 + log2; integral |z|phi = 2phi12.
    phi12=math.exp(-72)/math.sqrt(2*math.pi);q12=.5*math.erfc(12/math.sqrt(2));tails=[]
    for r in exact['rows']:
        if r['sigma']==0:continue
        d=.25*math.sqrt(8)/r['sigma'];bound=(2*d*phi12+(d*d/2+math.log(2))*2*q12)/math.log(2)
        tails.append({'sigma':r['sigma'],'absolute_information_tail_bound_bits':bound})
    limit=compressed(1e6)
    assert abs(limit['np'][1]-.05)<1e-6 and abs(limit['mi'])<1e-10
    from model import phase_grid
    clean=[.25*w for w in phase_grid(256)]
    assert [int(x+1>1) for x in clean]==[int(x>0) for x in clean]
    data={'huge_noise_limit':{'sigma':1e6,'np_false_alarm':limit['np'][0],'np_power':limit['np'][1],'presence_information':limit['mi']},'constant_offset_equals_threshold_retuning':True,'compressed_probability_crosscheck':rows,'maximum_crosscheck_error':max(v for row in rows for v in row['errors'].values()),'prng_stream_audits':stream,'retuned_negative_controls':retuned,'raw_information_tail_bounds':tails,'maximum_raw_information_tail_bound':max(r['absolute_information_tail_bound_bits'] for r in tails),'seconds':time.perf_counter()-start,'status':'PASS'}
    (OUT/'adversarial-checks.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'PASS','maximum_crosscheck_error':data['maximum_crosscheck_error'],'maximum_tail_bound':data['maximum_raw_information_tail_bound'],'stream_audits':stream,'seconds':data['seconds']},indent=2))
if __name__=='__main__':main()
