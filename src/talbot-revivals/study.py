"""Bounded deterministic study; writes module-relative numerical data."""
import csv,json,math
from pathlib import Path
from model import *

ART=Path(__file__).resolve().parent/'data'

def run():
    cs=coefficients()
    xs=[j/512 for j in range(512)]
    para=propagate(cs,1)
    exact=propagate(cs,1,.01,True)
    half=propagate(cs,.5)
    twins=[coefficients(.025,32,s*.06) for s in (1,-1)]
    twins_at=[propagate(c,.06) for c in twins]
    controls=[]
    for width,chirp,p,q in [(.08,0,1,4),(.12,0,1,3),(.025,.06,1,4),(.025,0,1,8)]:
        c=coefficients(width,32,chirp)
        d=propagate(c,p/q)
        controls.append({'width':width,'chirp':chirp,'p':p,'q':q,
          'max_coherent_field_residual':max(abs(field(d,x)-replica_field(c,x,p,q)) for x in xs),
          'max_coherent_minus_mixture_intensity':max(abs(intensity(d,x)-incoherent_replica_intensity(c,x,p,q)) for x in xs)})
    rows=[]
    for width in (.02,.025,.04,.08):
        c=coefficients(width)
        for alpha in (.0001,.001,.002,.005,.01,.02,.025):
            e=propagate(c,1,alpha,True)
            rows.append({'width':width,'alpha':alpha,'orders':32,'fidelity_at_full_return':fidelity(c,e),
              'max_intensity_difference':max(abs(intensity(c,x)-intensity(e,x)) for x in xs)})
    with (ART/'revival-sweep.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    convergence=[]
    # Compare a common 1024-point grid. All modes propagate even for M=64.
    for width in (.02,.025):
        ref=propagate(coefficients(width,64),1,.01,True)
        for m in (16,24,32,48):
            c=coefficients(width,m);e=propagate(c,1,.01,True)
            convergence.append({'width':width,'orders':m,'fidelity':fidelity(c,e),
              'max_intensity_error_vs_M64':max(abs(intensity(e,j/1024)-intensity(ref,j/1024)) for j in range(1024))})
    # Cross-language fixtures cover interior propagation, endpoints, profiles and chirps.
    fixtures=[]
    for width,chirp,profile in [(.025,0,'pulse'),(.08,.06,'pulse'),(.025,-.06,'pulse'),(.1,0,'three')]:
        c=coefficients(width,32,chirp,profile)
        for t in (0,1/3,.5,.739,1):
            for alpha,exact_mode in ((.01,False),(.01,True),(.001,True)):
                e=propagate(c,t,alpha,exact_mode)
                fixtures.append({'width':width,'chirp':chirp,'profile':profile,'t':t,'alpha':alpha,'exact':exact_mode,
                  'fidelity':fidelity(c,e),'fields':[[x,field(e,x).real,field(e,x).imag] for x in (0,.117,.25,.5,.911)]})
    (ART/'fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n')
    summary={'assumptions':{'transverse_extent':'infinite periodic','orders_default':32,'field':'scalar, monochromatic, coherent, carrier removed','exact_scope':'forward propagating Helmholtz modes; no evanescent/polarization/finite aperture','normalization':'mean intensity per period = 1','grid_samples':512,'seed':'none; deterministic'},
      'default':{'width':.025,'alpha':.01,'paraxial_field_return_error':max(abs(field(para,x)-field(cs,x)) for x in xs),
        'paraxial_half_shift_error':max(abs(field(half,x)-field(cs,x-.5)) for x in xs),
        'exact_full_return_fidelity':fidelity(cs,exact),'exact_full_return_peak_intensity':intensity(exact,0),'input_peak_intensity':intensity(cs,0)},
      'retuning':{'pulse':find_return(cs,.01),'three_order_reference':{'t':(1+math.sqrt(1-.01**2))/2,'fidelity':fidelity(coefficients(profile='three'),propagate(coefficients(profile='three'),(1+math.sqrt(1-.01**2))/2,.01,True))}},
      'small_angle_example':{'order':10,'alpha':.01,'angle_degrees':math.degrees(math.asin(.1)),
        'exact_residual_radians':residual_phase(10,1,.01),'quartic_estimate_radians':-math.pi*.01**2*10**4/2},
      'twins':{'chirp_plus_minus':.06,'max_initial_intensity_difference':max(abs(intensity(twins[0],x)-intensity(twins[1],x)) for x in xs),
        'comparison_distance':.06,'plus_center_intensity':intensity(twins_at[0],0),'minus_center_intensity':intensity(twins_at[1],0),
        'max_propagated_intensity_difference':max(abs(intensity(twins_at[0],x)-intensity(twins_at[1],x)) for x in xs)},
      'replica_controls':controls,'order_convergence':convergence,'sweep_rows':len(rows),'fixture_rows':len(fixtures),
      'limits':['Fidelity is a complex-field overlap, not percent transmitted power.','No physical measurement or finite grating simulation.','Gaussian inputs are smooth finite Fourier series; carpet is not evidence of a mathematical fractal.','Reported errors and maxima refer to stated finite grids.']}
    (ART/'study.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':run()
