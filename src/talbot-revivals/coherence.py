"""Bounded incoherent illumination study; standalone, no change to original model/UI."""
import cmath,csv,json,math,time
from pathlib import Path
from model import coefficients,TAU
ART=Path(__file__).resolve().parent/'data'

def sinc(x):return math.sin(x)/x if abs(x)>1e-12 else 1-x*x/6

def gauss(n):
    """Gauss-Legendre nodes/weights on [-1,1], Newton roots, standard library."""
    out=[]
    for i in range(1,(n+1)//2+1):
        x=math.cos(math.pi*(i-.25)/(n+.5))
        for _ in range(20):
            a,b=1.,x
            for j in range(2,n+1):a,b=b,((2*j-1)*x*b-(j-1)*a)/j
            d=n*(x*b-a)/(x*x-1);step=b/d;x-=step
            if abs(step)<1e-15:break
        # Re-evaluate derivative at final root for weights.
        a,b=1.,x
        for j in range(2,n+1):a,b=b,((2*j-1)*x*b-(j-1)*a)/j
        d=n*(x*b-a)/(x*x-1);w=2/((1-x*x)*d*d)
        out.extend([(-x,w),(x,w)] if abs(x)>1e-14 else [(x,w)])
    return sorted(out)

QUAD={}
def nodes(n):
    if n not in QUAD:QUAD[n]=gauss(n)
    return QUAD[n]

def phi(n,t,alpha,eps=0,nu=0,exact=False):
    r=1+eps
    if r<=0 or abs(alpha*r*(n+nu))>=1 or abs(alpha*r*nu)>=1:raise ValueError('Non-propagating retained mode')
    if exact:
        a=math.sqrt(1-(alpha*r*(n+nu))**2);b=math.sqrt(1-(alpha*r*nu)**2)
        return -4*math.pi*t*r*(n*n+2*n*nu)/(a+b)
    return -TAU*t*r*(n*n+2*n*nu)

def matrix(cs,t,alpha,kind='angular',spread=0,mean=0,exact=False,nq=128,analytic=True):
    """Pair matrix of grating envelopes. Angular carrier exp(i2pi nu X) removed per member.
    Diagonal gives mean intensity. Not a single coherent amplitude or full angular mutual coherence.
    """
    if kind not in ('angular','spectral') or spread<0:raise ValueError('Bad ensemble')
    if not exact and analytic:
        result=[]
        for n,c in cs:
            row=[]
            for m,d in cs:
                phase=-TAU*t*(n*n-m*m+ (2*(n-m)*mean if kind=='angular' else 0))
                arg=TAU*t*spread*(2*(n-m) if kind=='angular' else n*n-m*m)
                row.append(c*d.conjugate()*cmath.exp(1j*phase)*sinc(arg))
            result.append(row)
        return result
    ens=[(0,1)] if spread==0 else [(x*spread,w/2) for x,w in nodes(nq)]
    result=[[0j]*len(cs) for _ in cs]
    for x,w in ens:
        e=x if kind=='spectral' else 0;v=mean+x if kind=='angular' else 0
        u=[c*cmath.exp(1j*phi(n,t,alpha,e,v,exact)) for n,c in cs]
        for i,c in enumerate(u):
            for j,d in enumerate(u):result[i][j]+=w*c*d.conjugate()
    return result

def harmonics(cs,rho):
    h={}
    for i,(n,c) in enumerate(cs):
        for j,(m,d) in enumerate(cs):h[n-m]=h.get(n-m,0j)+rho[i][j]
    return h

def field_harmonics(cs,rho):
    h={}
    for i,(n,c) in enumerate(cs):
        for j,(m,d) in enumerate(cs):h[n-m]=h.get(n-m,0j)+c.conjugate()*rho[i][j]*d
    return h

def evaluate(h,x):return sum(v*cmath.exp(1j*TAU*k*x) for k,v in h.items()).real

def best_shift(h):
    """256 spatial shifts plus 40-step local refinement, no global certificate."""
    xs=[j/256 for j in range(256)];i=max(range(256),key=lambda i:evaluate(h,xs[i]));a=xs[i]-1/256;b=xs[i]+1/256;g=(math.sqrt(5)-1)/2
    for _ in range(40):
        x=b-g*(b-a);y=a+g*(b-a)
        if evaluate(h,x)>evaluate(h,y):b=y
        else:a=x
    candidates=[xs[i],(a+b)/2];x=max(candidates,key=lambda x:evaluate(h,x))
    return x%1,evaluate(h,x)

def metrics(cs,rho):
    h=harmonics(cs,rho);base=harmonics(cs,[[c*d.conjugate() for m,d in cs] for n,c in cs])
    p0=sum(abs(v)**2 for k,v in base.items() if k);p=sum(abs(v)**2 for k,v in h.items() if k)
    corr={k:v*base[k].conjugate() for k,v in h.items() if k}
    shift,dot=best_shift(corr) if p>1e-20 else (None,0.)
    def error(s):return math.sqrt(max(0,sum(abs(h[k]*cmath.exp(1j*TAU*k*s)-base[k])**2 for k in h if k)/p0))
    fh=field_harmonics(cs,rho);fs,f=best_shift(fh) if sum(abs(v) for k,v in fh.items() if k)>1e-14 else (None,evaluate(fh,0))
    return {'mean_intensity':h[0].real,'contrast_rms_ratio':math.sqrt(p/p0),'intensity_relative_L2_unshifted':error(0),
      'intensity_best_shift':shift,'intensity_relative_L2_shifted':error(shift or 0),'centered_shape_cosine_shifted':dot/math.sqrt(p*p0) if p>1e-20 else None,
      'mean_member_field_overlap_unshifted':evaluate(fh,0),'field_best_shift':fs,'mean_member_field_overlap_shifted':f,
      'peak':max(evaluate(h,j/512) for j in range(512)),'minimum':min(evaluate(h,j/512) for j in range(512))}

def run():
    started=time.perf_counter();cs=coefficients(.04,24);rows=[];checks=[]
    # Exact quadrature compared against analytic paraxial ensemble at identical inputs.
    for kind,spread in [('angular',.01),('angular',.25),('spectral',.01),('spectral',.5)]:
        analytic=matrix(cs,1,.001,kind,spread)
        numeric=matrix(cs,1,.001,kind,spread,nq=1024 if kind=='spectral' and spread==.5 else 256,analytic=False)
        err=max(abs(a-b) for ra,rb in zip(analytic,numeric) for a,b in zip(ra,rb))
        assert err<1e-11,(kind,spread,err)
        checks.append({'check':'quadrature_vs_sinc','kind':kind,'spread':spread,'max_pair_error':err})
    for alpha in (.001,.01):
      for kind,spreads in [('angular',(0,.002,.01,.05,.25)),('spectral',(0,.002,.01,.05,.5))]:
       for spread in spreads:
        for exact in (False,True):
          rho=matrix(cs,1,alpha,kind,spread,exact=exact,nq=1024 if kind=='spectral' and spread==.5 else 256)
          rows.append({'alpha':alpha,'kind':kind,'spread':spread,'exact':exact,'tau':1,**metrics(cs,rho)})
          assert abs(sum(rho[i][i].real for i in range(len(cs)))-1)<1e-12
    # Independent convergence check for the widest, most oscillatory cases.
    for kind,spread in [('angular',.25),('spectral',.5)]:
        q1,q2=(1024,1536) if kind=='spectral' else (256,512)
        a=matrix(cs,1,.01,kind,spread,exact=True,nq=q1);b=matrix(cs,1,.01,kind,spread,exact=True,nq=q2)
        err=max(abs(x-y) for ra,rb in zip(a,b) for x,y in zip(ra,rb));assert err<1e-10,(kind,err)
        checks.append({'check':'exact_quadrature_convergence','nodes':[q1,q2],'kind':kind,'max_pair_error':err})
    # Tilt-only: a shifted perfect paraxial return and an exact-dispersion control.
    tilted=[]
    for exact in (False,True):
      r=matrix(cs,1,.01,'angular',0,mean=.07,exact=exact);tilted.append({'exact':exact,'nu':.07,**metrics(cs,r)})
    # Distance search is separate from spatial registration; field-return objective only.
    distance=[]
    for kind,spread in [('angular',.01),('spectral',.01)]:
      values=[]
      for j in range(81):
        t=.98+.02*j/80
        # Mean member overlap needs only conditional modal fields, avoiding pair-matrix work.
        total=0
        for x,w in nodes(64):
          eps=x*spread if kind=='spectral' else 0;nu=x*spread if kind=='angular' else 0
          inner=sum(abs(c)**2*cmath.exp(1j*phi(n,t,.01,eps,nu,True)) for n,c in cs)
          total+=w/2*abs(inner)**2
        values.append((t,total))
      best=max(values,key=lambda v:v[1]);distance.append({'kind':kind,'spread':spread,'best_tau_grid':best[0],'mean_member_overlap':best[1],'interval':[.98,1],'points':81,'spatial_shift':'none'})
    with (ART/'coherence-sweep.csv').open('w',newline='') as f:
      wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
    weak=[(-1,.01+0j),(0,1+0j),(1,.01+0j)];norm=math.sqrt(sum(abs(c)**2 for n,c in weak));weak=[(n,c/norm) for n,c in weak]
    weak_metrics=metrics(weak,matrix(weak,1,.001,'angular',.25))
    data={'weak_modulation_counterexample':weak_metrics,'width':.04,'orders':24,'seed':'none','rows':rows,'checks':checks,'tilt_only':tilted,'distance_search':distance,
      'definition':'ensemble intensities are averaged; field values are mean per-member carrier-demodulated overlaps, not fidelity of a nonexistent single mixture amplitude',
      'limits':['Infinite aperture retained.','Uniform spectral and angular ensembles treated separately; no combined-source claim.','Source angular parameter nu is transverse cycles per grating period: sin(theta)=alpha*nu at nominal wavelength.','Same grating Fourier coefficients for every source member; no dispersive grating.','Static scalar forward model, no vector/evanescent/material/detector physics.','Spatial registration uses 256 shifts plus local search; distance scan uses only 81 points and no spatial shift.']}
    (ART/'coherence-results.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'checks':checks,'tilt_only':tilted,'distance_search':distance,'seconds':time.perf_counter()-started},indent=2))

if __name__=='__main__':run()
