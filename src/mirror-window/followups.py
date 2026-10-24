"""Focused checks prompted by actual outliers and UI parameter limits."""
from pathlib import Path
from dataclasses import replace
import csv,json,math,random,statistics
from model import *
from perturbation import certificate
OUT=Path(__file__).resolve().parent/'output'
OUT.mkdir(exist_ok=True)

def csvout(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

# Check the actual finite-fit outliers rather than discard them.
slopes=list(csv.DictReader((OUT/'scaling-slopes.csv').open()))
index=sorted([r for r in slopes if r['kind']=='index'],key=lambda r:float(r['log_log_slope']))
seeds=[int(r['seed']) for r in index[:2]+index[-2:]]
refinement=[]
for seed in seeds:
    c=certificate(seed=seed,kind='index');previous=None
    for e in [.00003125,.0000625,.000125,.00025,.0005,.001,.002,.004]:
        p=peak(stacks(6,e,seed=seed,kind='index')[1],intervals=300)
        refinement.append({'seed':seed,'error':e,'peak_R':p['R'],
                           'ratio_to_asymptotic':p['R']/(c['leading_reflectance_coefficient']*e*e),
                           'adjacent_slope':None if previous is None else math.log(p['R']/previous,2)})
        previous=p['R']
csvout('outlier-refinement.csv',refinement)

# Keep all optical phases exactly quarter-wave, vary only impedance, and use
# an analytic center reflectance that does not require peak optimization.
phase_controls=[]
for m in [4,6,8]:
    for seed in [7,15,50,1729]:
        for e in [.001,.01,.05,.08]:
            b=stacks(m,e,seed=seed,kind='index')[1]
            b=[replace(x,d=600/(4*x.n)) for x in b]
            logA=sum(math.log(b[j+1].n/b[j].n) for j in range(0,len(b),2))
            analytic_R=math.tanh(logA)**2
            s=solve(b,600);p=peak(b,intervals=300)
            phase_controls.append({'m':m,'seed':seed,'error':e,'T600':s['T'],
                                   'R600':s['R'],'analytic_R':analytic_R,
                                   'absolute_residual':abs(s['R']-analytic_R),
                                   'peak_nm':p['wavelength'],'peak_R':p['R']})
csvout('phase-fixed-index-control.csv',phase_controls)
assert max(r['absolute_residual'] for r in phase_controls)<1e-12

# Verify that the full index-error coefficient is the same alternating-index
# mismatch appearing in the phase-fixed control, for every ensemble seed.
coef_checks=[]
for r in slopes:
    if r['kind']!='index':continue
    seed=int(r['seed']);u=uniform_sequence(seed,24)
    analytic=sum((-1 if j%2==0 else 1)*e for j,e in enumerate(u))**2
    actual=certificate(seed=seed,kind='index')['leading_reflectance_coefficient']
    coef_checks.append(abs(analytic-actual))
assert max(coef_checks)<1e-11

# Independent composite Simpson integration across broad off-peak UI settings.
# Absolute, not relative, error is tested; tiny transmissions can have larger
# relative discrepancies under an absolute adaptive tolerance of 1e-9.
rng=random.Random(19102026);quadrature=[]
for i in range(100):
    m=rng.choice([4,6,8]);e=rng.choice([0,.03,.08]);seed=rng.getrandbits(32)
    kind=rng.choice(['thickness','index']);mode=rng.choice(['independent','mirrored'])
    b=stacks(m,e,mode,seed,kind=kind)[1];p=peak(b,intervals=300)
    center=rng.uniform(480,720);fw=rng.choice([.1,1,5]);sigma=fw/(2*math.sqrt(2*math.log(2)))
    lo=center-8*sigma;hi=center+8*sigma;n=4000;step=(hi-lo)/n
    vals=[]
    for j in range(n+1):
        w=lo+j*step
        vals.append(solve(b,w)['T']*math.exp(-.5*((w-center)/sigma)**2)/(sigma*math.sqrt(2*math.pi)))
    grid=step/3*(vals[0]+vals[-1]+4*sum(vals[1:-1:2])+2*sum(vals[2:-1:2]))
    q=band_average(b,center,fw,peak_info=p)
    quadrature.append({'m':m,'error':e,'seed':seed,'kind':kind,'mode':mode,'center_nm':center,
                       'fwhm_nm':fw,'adaptive_T':q['T'],'grid_T':grid,
                       'absolute_difference':abs(grid-q['T']),'depth_cap':q['capped']})
csvout('off-peak-quadrature.csv',quadrature)
assert max(r['absolute_difference'] for r in quadrature)<2e-9
assert not any(r['depth_cap'] for r in quadrature)

weights=[]
for m in [2,4,6,8]:
    b=stacks(m)[1]
    for j,(layer,w) in enumerate(zip(b,sensitivity(m))):
        weights.append({'m':m,'layer_position':j+1,'family':layer.label,'sensitivity_weight':w})
csvout('layer-sensitivity.csv',weights)
checks={'status':'PASS','outlier_seeds':seeds,'outlier_rows':len(refinement),
        'smallest_error_adjacent_slopes':[r['adjacent_slope'] for r in refinement if r['error']==.0000625],
        'phase_fixed_index_cases':len(phase_controls),
        'max_phase_fixed_analytic_R_residual':max(r['absolute_residual'] for r in phase_controls),
        'max_index_Taylor_coefficient_residual':max(coef_checks),
        'off_peak_quadrature_cases':100,'off_peak_seed':19102026,
        'max_off_peak_quadrature_absolute_difference':max(r['absolute_difference'] for r in quadrature),
        'limits':'Finite sample, finite quadrature grids, and double precision. Fits are not exact exponents at finite errors.'}
(OUT/'followup-checks.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
