"""Separate passive-absorption control; the browser bench remains lossless.

Complex n=n_real+i*kappa, exp(-i*omega*t); real exterior indices. Power
normalization and the absorption density follow Byrnes arXiv1603.02720v5,
sections2.1 and4.4-4.5. All indices/absorption are illustrative, not a named
material fit. No gain, oblique incidence or dispersive model is implemented.
"""
from pathlib import Path
from math import pi, isfinite
import cmath,json,csv,random
from model import Layer,stacks,solve,field_profile,golden_max,validate
OUT=Path(__file__).resolve().parent/'output'
OUT.mkdir(exist_ok=True)


def scattering(layers,wavelength,kappa=0.,n0=1.,ns=1.):
    validate(layers,wavelength,n0,ns)
    if not isfinite(kappa) or not 0<=kappa<=.01:
        raise ValueError('bounded passive kappa must be finite in [0,.01]')
    indices=[complex(n0)]+[complex(x.n,kappa) for x in layers]+[complex(ns)]
    r=(indices[-2]-ns)/(indices[-2]+ns);t=2*indices[-2]/(indices[-2]+ns)
    for j in range(len(layers)-1,-1,-1):
        phase=cmath.exp(2j*pi*indices[j+1]*layers[j].d/wavelength)
        rr=(indices[j]-indices[j+1])/(indices[j]+indices[j+1]);tt=2*indices[j]/(indices[j]+indices[j+1])
        den=1+rr*r*phase*phase
        t=tt*t*phase/den;r=(rr+r*phase*phase)/den
    R,T=abs(r)**2,ns/n0*abs(t)**2
    return {'R':R,'T':T,'A':1-R-T,'r':r,'t':t}


def complex_matrix_reference(layers,wavelength,kappa=0.,n0=1.,ns=1.):
    # Different calculation from scattering(): generic complex matrix products.
    a,b,c,d=1+0j,0j,0j,1+0j
    for layer in layers:
        n=complex(layer.n,kappa);phase=2*pi*n*layer.d/wavelength
        co,si=cmath.cos(phase),cmath.sin(phase)
        e,f,g,h=co,-1j*si/n,-1j*n*si,co
        a,b,c,d=a*e+b*g,a*f+b*h,c*e+d*g,c*f+d*h
    denominator=n0*a+n0*ns*b+c+ns*d
    r=(n0*a+n0*ns*b-c-ns*d)/denominator;t=2*n0/denominator
    R,T=abs(r)**2,ns/n0*abs(t)**2
    return {'R':R,'T':T,'A':1-R-T}


def transmission_peak(layers,kappa,n0=1.,ns=1.,intervals=600):
    # In absorbing media, maximizing T is NOT equivalent to minimizing R.
    f=lambda w:scattering(layers,w,kappa,n0,ns)['T']
    lo,hi=540.,660.
    ws=[lo+(hi-lo)*j/intervals for j in range(intervals+1)];ys=[f(w) for w in ws]
    choices=[(ws[0],ys[0]),(ws[-1],ys[-1])]
    for j in range(1,intervals):
        if ys[j]>=ys[j-1] and ys[j]>=ys[j+1]:choices.append(golden_max(f,ws[j-1],ws[j+1]))
    w,T=max(choices,key=lambda z:z[1]);s=scattering(layers,w,kappa,n0,ns)
    return {'wavelength':w,'T':T,'R':s['R'],'A':s['A'],'boundary':w==lo or w==hi}


def weak_absorption_coefficient(layers,wavelength=600,samples=128):
    """dA/dkappa at kappa=0 from the unperturbed field.

    For common kappa in every layer and real exterior n0=1,
    a(x)=4*pi*n*kappa/lambda * |E(x)|^2 + O(kappa^2).
    Composite Simpson integrates each individual layer, preserving interface
    discontinuities of n. The field E itself is continuous.
    """
    field=field_profile(layers,wavelength,samples_per_layer=samples)
    value=0.
    for j,layer in enumerate(layers):
        points=field[j*(samples+1):(j+1)*(samples+1)]
        values=[p['E2'] for p in points]
        integral=(layer.d/samples)/3*(values[0]+values[-1]+4*sum(values[1:-1:2])+2*sum(values[2:-1:2]))
        value+=4*pi*layer.n/wavelength*integral
    return value


def main():
    rows=[]
    for m in range(2,9):
        ordinary,b=stacks(m);coeff=weak_absorption_coefficient(b)
        for k in [0.,1e-8,1e-7,1e-6,1e-5,1e-4,1e-3]:
            p=transmission_peak(b,k)
            s=scattering(b,600,k)
            rows.append({'m':m,'layers':4*m,'kappa':k,'T600':s['T'],'R600':s['R'],'A600':s['A'],
                         'peak_nm':p['wavelength'],'peak_T':p['T'],'peak_R':p['R'],'peak_A':p['A'],
                         'weak_loss_coefficient':coeff,'linear_A_prediction':k*coeff,
                         'ordinary_T600':scattering(ordinary,600,k)['T'],'boundary':p['boundary']})
    with (OUT/'absorption-control.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    rng=random.Random(24102026);max_cross=0.;min_A=1.;zero_residual=0.;reciprocity=0.
    for _ in range(400):
        b=stacks(rng.randint(2,8),rng.random()*.08,seed=rng.getrandbits(32),kind=rng.choice(['thickness','index']))[rng.randrange(2)]
        w=rng.uniform(480,720);k=10**rng.uniform(-9,-3);ns=rng.choice([1.,1.5])
        a=scattering(b,w,k,ns=ns);c=complex_matrix_reference(b,w,k,ns=ns)
        max_cross=max(max_cross,abs(a['T']-c['T']),abs(a['R']-c['R']),abs(a['A']-c['A']))
        min_A=min(min_A,a['A'])
        z=scattering(b,w,0,ns=ns);reference=solve(b,w,ns=ns)
        zero_residual=max(zero_residual,abs(z['T']-reference['T']),abs(z['R']-reference['R']))
        back=scattering(list(reversed(b)),w,k,n0=ns,ns=1.)
        reciprocity=max(reciprocity,abs(back['T']-a['T']))
    linear=[]
    for m in [2,4,6,8]:
        b=stacks(m)[1];c=weak_absorption_coefficient(b);measured=scattering(b,600,1e-10)['A']/1e-10
        linear.append({'m':m,'field_coefficient':c,'finite_kappa_derivative':measured,'relative_difference':abs(measured/c-1)})
    slab=[Layer(1,200)]
    slab_A=scattering(slab,600,1e-8)['A']
    slab_expected=4*pi*1e-8*200/600
    assert max_cross<1e-10 and min_A>=-1e-12 and zero_residual<1e-10 and reciprocity<1e-10
    assert max(r['relative_difference'] for r in linear)<5e-5
    assert abs(slab_A/slab_expected-1)<1e-6
    try:scattering([],600,-1e-4)
    except ValueError:pass
    else:raise AssertionError('negative absorption accepted')
    checks={'status':'PASS','rows':len(rows),'random_cases':400,'seed':24102026,
            'max_complex_matrix_vs_scattering_difference':max_cross,'minimum_random_A':min_A,
            'max_zero_loss_reference_difference':zero_residual,'max_reciprocity_T_difference':reciprocity,
            'field_integral_derivative_checks':linear,'matched_index_weak_slab_ratio':slab_A/slab_expected,
            'boundary_peaks':sum(r['boundary'] for r in rows),
            'limits':'Illustrative common, wavelength-independent extinction coefficient. No material fit. Browser model remains lossless. Spectral search restricted to540..660nm; optimize T rather than R.'}
    (OUT/'absorption-checks.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))
    for m in [4,6,8]:
        print('EXAMPLES',*[r for r in rows if r['m']==m and r['kappa'] in [0.,1e-6,1e-4]],sep='\n')

if __name__=='__main__':main()
