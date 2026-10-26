"""Analytic weak-signal, estimator-bias and sample-budget controls."""
import math,json,time
from pathlib import Path
from model import theory,exceedance,entropy,phase_grid
OUT=Path(__file__).resolve().parent/'data'

def expected_empirical_entropy(n,p):
    if p==0 or p==1:return 0.0
    terms=[];mass=[]
    for k in range(n+1):
        probability=math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)+k*math.log(p)+(n-k)*math.log1p(-p))
        mass.append(probability);terms.append(probability*entropy(k/n))
    if abs(math.fsum(mass)-1)>5e-12:raise ArithmeticError('binomial mass error')
    return math.fsum(terms)

def exact_null_plugin_bias(n,q):
    # K_total~Binomial(n,q), each half K_half~Binomial(n/2,q).
    # E[I_plugin] = E[h(K_total/n)] - E[h(K_half/(n/2))].
    return expected_empirical_entropy(n,q)-expected_empirical_entropy(n//2,q)

def golden_max(fn,left,right,steps=80):
    g=(math.sqrt(5)-1)/2;c=right-g*(right-left);d=left+g*(right-left);fc=fn(c);fd=fn(d)
    for _ in range(steps):
        if fc>fd:right,d,fd=d,c,fc;c=right-g*(right-left);fc=fn(c)
        else:left,c,fc=c,d,fd;d=left+g*(right-left);fd=fn(d)
    x=(left+right)/2;return x,fn(x)

def weak_scores(sigma,threshold=1):
    r=threshold/sigma;phi=math.exp(-r*r/2)/math.sqrt(2*math.pi);q=exceedance(0,threshold,sigma)
    c_per_A=phi/sigma
    phase_delta_per_A=2*sum(s for s in phase_grid(64) if s>0)/64*phi/sigma
    # delta=(q_positive-q_negative)/2; phase means use midpoint-grid sine.
    info_per_A2=phase_delta_per_A**2/(2*math.log(2)*q*(1-q)) if q*(1-q)>0 else 0
    return {'projection_per_amplitude':c_per_A,'accuracy_gain_per_amplitude':phase_delta_per_A,
            'phase_information_per_amplitude_squared':info_per_A2,'deflection_per_NA2':phi*phi/(2*sigma*sigma*q*(1-q)) if q*(1-q)>0 else 0}

def main():
    started=time.perf_counter()
    optimum={k:golden_max(lambda s:weak_scores(s)[k],.15,3)[0] for k in weak_scores(1)}
    # Smooth analytic exact finite-amplitude scores (no simulation seed selection).
    exact_optima=[]
    for a in (.001,.01,.05,.25,.5,.9):
        row={'amplitude':a}
        for k in ('projection','balanced_accuracy','phase_mi'):
            s,value=golden_max(lambda sigma:theory(a,1,sigma)[k],.15,3)
            row[k]={'sigma':s,'value':value}
        exact_optima.append(row)
    bias=[]
    for n in (64,256,1024):
        for s in (0,.2,.4,.8,1,4):
            q=exceedance(0,1,s)
            bias.append({'n':n,'sigma':s,'null_crossing':q,'true_phase_information':0,'expected_plugin_bits':exact_null_plugin_bias(n,q),'large_n_bias_bits':1/(2*n*math.log(2))})
    # Verify finite phase-grid quadrature separately from adding observations.
    phase_refinement=[]
    for m in (16,32,64,128,256,512,1024):
        w=[math.sin(2*math.pi*(i+.5)/m) for i in range(m)]
        q=[exceedance(.25*s,1,.8) for s in w]
        h=2*sum(p for p,s in zip(q,w) if s>0)/m;f=2*sum(p for p,s in zip(q,w) if s<0)/m
        phase_refinement.append({'quadrature_bins':m,'accuracy':(1+h-f)/2,'projection':2*sum(p*s for p,s in zip(q,w))/m,'note':'Probability quadrature only. No synthetic extra measurement or independent noise sample generated.'})
    # Counterexample: treating repeated samples as fresh independent observations.
    budget=[]
    q=exceedance(0,1,.4)
    for repeats in (1,2,4,8,16):
        budget.append({'copies_per_observation':repeats,'distinct_independent_observations':256,'wrong_assumption_independent_count':256*repeats,'actual_any_active_pfa':-math.expm1(256*math.log1p(-q)),'incorrect_if_copies_treated_as_iid':-math.expm1(256*repeats*math.log1p(-q))})
    # Small-amplitude expansions checked at fixed non-extreme noise levels.
    expansion_checks=[]
    for sigma in (.4,.6,.8,1,2):
        a=1e-3;t=theory(a,1,sigma);weak=weak_scores(sigma)
        expansion_checks.append({'sigma':sigma,'projection_relative_error':abs(t['projection']/a-weak['projection_per_amplitude'])/weak['projection_per_amplitude'],
                                 'accuracy_relative_error':abs((t['balanced_accuracy']-.5)/a-weak['accuracy_gain_per_amplitude'])/weak['accuracy_gain_per_amplitude'],
                                 'information_relative_error':abs(t['phase_mi']/a**2-weak['phase_information_per_amplitude_squared'])/weak['phase_information_per_amplitude_squared']})
    checks={'expansion_max_relative_error':max(v for r in expansion_checks for k,v in r.items() if k!='sigma'),'projection_optimum_equals_threshold_error':abs(optimum['projection_per_amplitude']-1),
            'phase_grid_projection_spread':max(r['projection'] for r in phase_refinement)-min(r['projection'] for r in phase_refinement),
            'bias_nonnegative':all(r['expected_plugin_bits']>=-1e-12 for r in bias),'bias_null_boundary_zero':all(abs(r['expected_plugin_bits'])<1e-12 for r in bias if r['sigma']==0)}
    assert checks['expansion_max_relative_error']<1e-4
    assert checks['projection_optimum_equals_threshold_error']<1e-7
    assert checks['bias_nonnegative'] and checks['bias_null_boundary_zero']
    data={'weak_signal_optima_sigma_over_threshold':optimum,'exact_finite_amplitude_optima':exact_optima,'null_plugin_bias':bias,'phase_probability_quadrature':phase_refinement,'copying_is_not_new_data':budget,'expansion_checks':expansion_checks,'checks':checks,'seconds':time.perf_counter()-started}
    (OUT/'analytic-controls.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'weak_signal_optima':optimum,'seconds':data['seconds']},indent=2))
if __name__=='__main__':main()
