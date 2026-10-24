"""Independent phase/field energy identity check; not a time-domain simulation.

For real nondispersive layers with both exterior indices=1, the stored
EM energy / incident power equals T*darg(t)/domega + R*darg(r)/domega.
This follows by differentiating the two first-order Maxwell equations and
integrating the resulting boundary identity. The reflected term matters for
asymmetric reflectors. No group velocity or trajectory is inferred here.
"""
from pathlib import Path
import cmath,csv,json,math,random
from model import *
OUT=Path(__file__).resolve().parent/'output'
OUT.mkdir(exist_ok=True)
C=299.792458 # vacuum light speed in nm/fs, exactly 299792458 m/s.


def energy_over_input(layers,wavelength):
    # Time-averaged EM energy includes electric AND magnetic terms. For a
    # lossless homogeneous layer n^2|E|^2+|H|^2 is constant, even though E^2
    # and H^2 separately form a standing-wave pattern. A midpoint is exact.
    points=field_profile(layers,wavelength,samples_per_layer=2)
    value=0.;max_layer_variation=0.
    for j,layer in enumerate(layers):
        part=points[j*3:(j+1)*3]
        vals=[layer.n**2*p['E2']+abs(p['H'])**2 for p in part]
        value+=layer.d*vals[1]/(2*C)
        max_layer_variation=max(max_layer_variation,(max(vals)-min(vals))/max(1.,max(vals)))
    return value,max_layer_variation


def delays(layers,wavelength,h):
    s=solve(layers,wavelength);left=solve(layers,wavelength-h);right=solve(layers,wavelength+h)
    factor=-wavelength*wavelength/(2*math.pi*C)/(2*h)
    tau_t=factor*cmath.phase(right['t']/left['t'])
    # Phase of a zero reflected amplitude is undefined. A vanishing R weight
    # is omitted explicitly, rather than fitted to numerical phase noise.
    tau_r=None if s['R']<1e-20 else factor*cmath.phase(right['r']/left['r'])
    weighted=s['T']*tau_t+(0. if tau_r is None else s['R']*tau_r)
    energy,variation=energy_over_input(layers,wavelength)
    return {'T':s['T'],'R':s['R'],'tau_t_fs':tau_t,'tau_r_fs':tau_r,
            'weighted_delay_fs':weighted,'energy_over_input_fs':energy,
            'absolute_difference_fs':abs(weighted-energy),'max_relative_layer_energy_variation':variation}


def write_csv(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    resonances=[]
    for m in [2,4,6,8]:
        b=stacks(m)[1];width=fwhm(b,600,1.)
        for divisor in [100,1000,10000,100000]:
            row={'m':m,'fwhm_nm':width,'phase_half_step_nm':width/divisor,
                 'Lorentzian_narrow_line_estimate_fs':600**2/(math.pi*C*width)}
            row.update(delays(b,600,width/divisor));resonances.append(row)
    write_csv('phase-delay-convergence.csv',resonances)
    controls=[]
    for name,b,w in [('uniform_900nm',[Layer(1,900)],600.),('ordinary_m6',stacks(6)[0],600.),
                     ('symmetric_off_peak',stacks(6)[1],590.),
                     ('independent_index_error',stacks(6,.08,seed=7,kind='index')[1],600.),
                     ('single_slab',[Layer(2,83)],600.)]:
        row={'name':name,'wavelength_nm':w};row.update(delays(b,w,1e-4));controls.append(row)
    write_csv('phase-delay-controls.csv',controls)
    assert abs(controls[0]['tau_t_fs']-900/C)<1e-7
    assert abs(controls[1]['tau_t_fs']-controls[1]['energy_over_input_fs'])>.5
    assert max(r['absolute_difference_fs'] for r in controls)<1e-6
    rng=random.Random(38402026);errors=[];variations=[]
    for _ in range(200):
        b=stacks(rng.randint(2,8),rng.random()*.08,seed=rng.getrandbits(32),kind=rng.choice(['thickness','index']))[rng.randrange(2)]
        w=rng.uniform(480,720);d=delays(b,w,1e-5)
        errors.append(d['absolute_difference_fs']);variations.append(d['max_relative_layer_energy_variation'])
    assert max(errors)<1e-3
    assert max(variations)<1e-12
    checks={'status':'PASS','resonance_rows':len(resonances),'control_cases':len(controls),
            'random_cases':200,'seed':38402026,'max_random_absolute_difference_fs':max(errors),
            'max_layer_energy_relative_variation':max(variations),
            'ideal_m8_finest_step':[r for r in resonances if r['m']==8][-1],
            'limits':'Finite-difference phase derivatives, real nondispersive layers, equal exterior indices. Weighted identity tested; transmission delay alone can fail for asymmetric reflectors. Not time-domain pulse propagation, not measured transit times, and no group velocity claim.'}
    (OUT/'delay-checks.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
