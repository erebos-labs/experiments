"""Bounded, reproducible parameter study. Standard library only."""
from pathlib import Path
import csv,json,random,math,statistics
from dataclasses import asdict
from model import *
from perturbation import certificate

OUT=Path(__file__).resolve().parent/'output'
OUT.mkdir(exist_ok=True)

def write_csv(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def quantile_summary(values):
    xs=sorted(values)
    return {'min':xs[0],'median':statistics.median(xs),'max':xs[-1],
            'q10':xs[round((len(xs)-1)*.1)],'q90':xs[round((len(xs)-1)*.9)]}

def main():
    rng=random.Random(20261024);seeds=[rng.getrandbits(32) for _ in range(64)]
    ideal=[]
    for m in range(1,9):
        a,b=stacks(m);p=peak(b)
        ideal.append({'pairs_per_side':m,'layers':4*m,'ordinary_T600':solve(a,600)['T'],
                      'cavity_T600':solve(b,600)['T'],'peak_nm':p['wavelength'],
                      'fwhm_nm':fwhm(b,p['wavelength'],p['T']),
                      'cavity_E2_max':max(x['E2'] for x in field_profile(b,600)),
                      'gaussian_1nm_T':band_average(b,600,1,peak_info=p)['T']})
    write_csv('ideal-layers.csv',ideal)
    ensemble=[]
    for m in [4,6,8]:
        for error in [.01,.03,.08]:
            for kind in ['thickness','index']:
                for mode in ['independent','mirrored','common']:
                    for seed in seeds:
                        a,b=stacks(m,error,mode,seed,kind=kind)
                        p=peak(b,intervals=300)
                        ensemble.append({'m':m,'error':error,'kind':kind,'mode':mode,'seed':seed,
                                         'fixed_T600':solve(b,600)['T'],'peak_T':p['T'],'peak_R':p['R'],
                                         'peak_nm':p['wavelength'],'boundary':p['at_boundary'],
                                         'coarse_grid_T':p['grid_max_T'],
                                         'predicted_shift_nm':predicted_shift(m,error,mode,seed),
                                         'ordinary_T600':solve(a,600)['T']})
                    print('ensemble',m,error,kind,mode,flush=True)
    write_csv('error-ensemble.csv',ensemble)
    summaries=[]
    for m in [4,6,8]:
        for error in [.01,.03,.08]:
            for kind in ['thickness','index']:
                for mode in ['independent','mirrored','common']:
                    rows=[r for r in ensemble if (r['m'],r['error'],r['kind'],r['mode'])==(m,error,kind,mode)]
                    summaries.append({'m':m,'error':error,'kind':kind,'mode':mode,'count':len(rows),
                                      'fixed_T600':quantile_summary([r['fixed_T600'] for r in rows]),
                                      'peak_T':quantile_summary([r['peak_T'] for r in rows]),
                                      'peak_R':quantile_summary([r['peak_R'] for r in rows]),
                                      'absolute_shift_nm':quantile_summary([abs(r['peak_nm']-600) for r in rows]),
                                      'linear_shift_error_nm':quantile_summary([abs(r['peak_nm']-600-r['predicted_shift_nm']) for r in rows]),
                                      'boundary_count':sum(r['boundary'] for r in rows)})
    (OUT/'ensemble-summary.json').write_text(json.dumps(summaries,indent=2))
    scaling=[];slopes=[];certificates=[]
    for kind in ['thickness','index']:
        for seed in seeds:
            c=certificate(6,seed,kind);certificates.append(c)
            rows=[]
            for error in [.0005,.001,.002,.004,.008,.016,.032,.064]:
                b=stacks(6,error,seed=seed,kind=kind)[1]
                p=peak(b,intervals=300)
                pred=c['leading_reflectance_coefficient']*error**c['leading_reflectance_power']
                row={'kind':kind,'seed':seed,'error':error,'peak_nm':p['wavelength'],
                     'peak_R':p['R'],'predicted_R':pred,'ratio':p['R']/pred if pred else None}
                rows.append(row);scaling.append(row)
            # Fit in log space over the first four amplitudes only.
            xs=[math.log(r['error']) for r in rows[:4]];ys=[math.log(r['peak_R']) for r in rows[:4]]
            mx,my=statistics.mean(xs),statistics.mean(ys)
            slope=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs)
            slopes.append({'kind':kind,'seed':seed,'log_log_slope':slope,
                           'leading_coefficient':c['leading_reflectance_coefficient'],
                           'ratio_at_smallest_error':rows[0]['ratio']})
    write_csv('error-scaling.csv',scaling);write_csv('scaling-slopes.csv',slopes)
    (OUT/'taylor-certificates.json').write_text(json.dumps(certificates,indent=2))
    # Independent recursion and conservation stress cases; no use of a fitted curve.
    stress_rng=random.Random(21472026);max_balance=0;max_reference=0;max_reciprocity=0
    for _ in range(5000):
        m=stress_rng.randint(1,8);error=stress_rng.random()*.08
        kind=stress_rng.choice(['thickness','index']);mode=stress_rng.choice(['independent','mirrored','common'])
        layers=stacks(m,error,mode,stress_rng.getrandbits(32),kind=kind)[stress_rng.randrange(2)]
        wavelength=stress_rng.uniform(450,800);ns=stress_rng.choice([1.,1.5])
        a=solve(layers,wavelength,ns=ns);b=fresnel_reference(layers,wavelength,ns=ns)
        back=solve(list(reversed(layers)),wavelength,n0=ns,ns=1.)
        max_balance=max(max_balance,a['balance_error'])
        max_reference=max(max_reference,abs(a['R']-b['R']),abs(a['T']-b['T']))
        max_reciprocity=max(max_reciprocity,abs(a['T']-back['T']))
    assert max_balance < 1e-10 and max_reference<1e-10 and max_reciprocity<1e-10
    # Shared fixtures cover spectra, peaks, fields, seeded layers, finite linewidth.
    fixtures=[]
    for _ in range(160):
        m=rng.randint(1,8);error=rng.choice([0,.001,.01,.03,.08]);seed=rng.getrandbits(32)
        kind=rng.choice(['thickness','index']);mode=rng.choice(['independent','mirrored','common']);ns=rng.choice([1.,1.5])
        a,b=stacks(m,error,mode,seed,kind=kind);w=rng.uniform(480,720);p=peak(b,ns=ns,intervals=300)
        f=field_profile(b,w,ns=ns,samples_per_layer=8)
        fixture={'m':m,'error':error,'seed':seed,'kind':kind,'mode':mode,'ns':ns,'wavelength':w,
                 'ordinary_T':solve(a,w,ns=ns)['T'],'cavity_T':solve(b,w,ns=ns)['T'],
                 'peak':p,'layers':[asdict(x) for x in b],
                 'field_E2_max':max(x['E2'] for x in f),
                 'sensitivity':sensitivity(m),'predicted_shift':predicted_shift(m,error,mode,seed)}
        if len(fixtures)<16:fixture['band']=band_average(b,p['wavelength'],1.,ns=ns,peak_info=p)
        fixtures.append(fixture)
    (OUT/'reference-fixtures.json').write_text(json.dumps(fixtures,indent=2))
    spectral=[]
    for m in [4,6,8]:
        for e,kind,seed in [(0,'thickness',7),(.05,'thickness',7),(.05,'index',7)]:
            b=stacks(m,e,seed=seed,kind=kind)[1];p=peak(b)
            for center_kind,center in [('original',600.),('retuned',p['wavelength'])]:
                for width in [0,.1,.5,1.,2.,5.]:
                    q=band_average(b,center,width,peak_info=p)
                    spectral.append({'m':m,'error':e,'kind':kind,'seed':seed,'center_kind':center_kind,
                                     'center_nm':center,'line_fwhm_nm':width,'T':q['T'],
                                     'quadrature_evaluations':q['evaluations'],'depth_cap':q['capped']})
    write_csv('finite-linewidth.csv',spectral)
    checks={'ensemble_rows':len(ensemble),'ensemble_seed':20261024,
            'scaling_rows':len(scaling),'stress_cases':5000,'stress_seed':21472026,
            'max_energy_balance_error':max_balance,'max_independent_method_error':max_reference,
            'max_reciprocity_error':max_reciprocity,
            'slope_summaries':{k:quantile_summary([r['log_log_slope'] for r in slopes if r['kind']==k]) for k in ['thickness','index']},
            'spectral_depth_caps':sum(r['depth_cap'] for r in spectral),
            'boundary_peaks':sum(r['boundary'] for r in ensemble),
            'scope':'bounded synthetic ensembles, not measured fabrication yield or proof of unrestricted robustness'}
    (OUT/'study-checks.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2),flush=True)

if __name__=='__main__':main()
