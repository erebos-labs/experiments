"""Hold the original noisy measurements fixed and add independent dither.

An important counterexample: intrinsic SD0.8 -> total SD1 increases harmonic
amplitude, yet reduces information and optimal record detection power.
"""
import math,json,time
from pathlib import Path
from model import RNG,phase_grid,measure,theory,summarize,family_seed
from controls import raw_power
OUT=Path(__file__).resolve().parent/'data'

def main():
    start=time.perf_counter();wave=phase_grid(256);a=.25;threshold=1;base_sd=.8;added=.6;B=2048
    paired=[]
    for i in range(B):
        measurement_rng=RNG(family_seed(20261025,6,i))
        dither_rng=RNG(family_seed(20261025,7,i))
        # Families6 and7 are checked for collisions across this larger batch.
        measured=[a*w+base_sd*measurement_rng.normal() for w in wave]
        extra=[added*dither_rng.normal() for _ in wave]
        modified=[x+e for x,e in zip(measured,extra)]
        before=measure([int(x>threshold) for x in measured],wave)
        after=measure([int(x>threshold) for x in modified],wave)
        paired.append({'projection_change':after['projection']-before['projection'],
                       'phase_accuracy_change':after['balanced_accuracy']-before['balanced_accuracy'],
                       'plugin_information_change':after['phase_mi']-before['phase_mi'],
                       'squared_change_to_existing_measurement':sum(e*e for e in extra)/len(extra)})
    seeds=[family_seed(20261025,f,i) for f in (6,7) for i in range(B)]
    assert len(set(seeds))==len(seeds)
    summaries={k:summarize([r[k] for r in paired]) for k in paired[0]}
    before=theory(a,threshold,base_sd);after=theory(a,threshold,math.hypot(base_sd,added))
    expected_change=after['projection']-before['projection']
    assert abs(summaries['projection_change']['mean']-expected_change)<5*summaries['projection_change']['se']
    assert abs(summaries['squared_change_to_existing_measurement']['mean']-added**2)<5*summaries['squared_change_to_existing_measurement']['se']
    exact=json.loads((OUT/'exact-control.json').read_text())
    b16=next(r for r in exact['rows'] if r['sigma']==.8);a16=next(r for r in exact['rows'] if r['sigma']==1)
    curves=[]
    for intrinsic in (.2,.8,1.2):
        for j in range(81):
            dither=j/40;total=math.hypot(intrinsic,dither)
            curves.append({'intrinsic_sd':intrinsic,'added_sd':dither,'total_sd':total,'phase_scores':theory(a,threshold,total),
                           'raw_lrt_power_n256':raw_power(a,dither,256,intrinsic)})
    data={'parameters':{'amplitude':a,'threshold':threshold,'intrinsic_sd':base_sd,'added_sd':added,'n':256,'paired_trials':B,'base_seed':20261025},
          'paired_summaries':summaries,'analytic_before':before,'analytic_after':after,
          'n16_exact_before_after':{'before':b16,'after':a16,'interpretation':'Same N16 observation budget; an original SD0.8 Gaussian measurement plus independent SD0.6 dither has total SD1. These reuse the exact distribution results, not new empirical trials.'},
          'curves':curves,'checks':{'distinct_seed_count':len(set(seeds)),'expected_seed_count':len(seeds),'expected_projection_change':expected_change,'expected_added_mse':added**2},'seconds':time.perf_counter()-start,
          'scope':'Original measurements are fixed within each pair. New dither adds no new physical measurement. Probabilistic detector does not receive noise-realization side information.'}
    (OUT/'noisy-measurement-control.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'seconds':data['seconds'],'analytic_projection_change':expected_change,'analytic_information_change':after['phase_mi']-before['phase_mi'],'paired_summaries':summaries},indent=2))
if __name__=='__main__':main()
