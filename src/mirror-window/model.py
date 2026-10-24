"""Normal-incidence coherent lossless planar layers; no external dependencies.

Units are nm throughout. Phasors use exp(-i omega t). The characteristic
matrix maps right (E,H) to left (E,H), H in vacuum-admittance units.
Source: Byrnes arXiv:1603.02720v5, sections 3-4, for boundary conventions,
Fresnel recursion and power normalization. This restricted real-index
characteristic-matrix implementation is independently written here.
"""
from dataclasses import dataclass
from math import sin, cos, pi, isfinite, sqrt
import cmath

LAMBDA0 = 600.0
NH, NL = 2.3, 1.45

@dataclass(frozen=True)
class Layer:
    n: float
    d: float
    label: str = ''
    token: int = 0


def _positive(x, name):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not isfinite(x) or x <= 0:
        raise ValueError(f'{name} must be finite and positive')


def validate(layers, wavelength, n0, ns):
    _positive(wavelength, 'wavelength')
    _positive(n0, 'n0')
    _positive(ns, 'ns')
    if len(layers) > 64:
        raise ValueError('bounded model accepts at most 64 layers')
    for layer in layers:
        _positive(layer.n, 'layer index')
        if not isfinite(layer.d) or layer.d < 0:
            raise ValueError('layer thickness must be finite and nonnegative')


def matrix(layers, wavelength):
    # Matrix = [[a, -i*b], [-i*c, d]], with determinant a*d+b*c=1.
    a, b, c, d = 1., 0., 0., 1.
    for layer in layers:
        phase = 2*pi*layer.n*layer.d/wavelength
        co, si = cos(phase), sin(phase)
        a, b, c, d = (a*co-b*layer.n*si, a*si/layer.n+b*co,
                       c*co+d*layer.n*si, d*co-c*si/layer.n)
    return a, b, c, d


def solve(layers, wavelength, n0=1., ns=1.):
    validate(layers, wavelength, n0, ns)
    a, b, c, d = matrix(layers, wavelength)
    denom = complex(n0*a+ns*d, -(n0*ns*b+c))
    r = complex(n0*a-ns*d, c-n0*ns*b) / denom
    t = 2*n0/denom
    R, T = abs(r)**2, ns/n0*abs(t)**2
    return {'R':R, 'T':T, 'r':r, 't':t, 'balance_error':abs(R+T-1)}


def fresnel_reference(layers, wavelength, n0=1., ns=1.):
    """Independent scattering recursion; no characteristic matrix products."""
    validate(layers, wavelength, n0, ns)
    indices=[n0]+[x.n for x in layers]+[ns]
    r=(indices[-2]-ns)/(indices[-2]+ns)
    t=2*indices[-2]/(indices[-2]+ns)
    for j in range(len(layers)-1,-1,-1):
        phase=cmath.exp(2j*pi*layers[j].n*layers[j].d/wavelength)
        rr=(indices[j]-indices[j+1])/(indices[j]+indices[j+1])
        tt=2*indices[j]/(indices[j]+indices[j+1])
        denom=1+rr*r*phase*phase
        t=tt*t*phase/denom
        r=(rr+r*phase*phase)/denom
    return {'R':abs(r)**2,'T':ns/n0*abs(t)**2,'r':r,'t':t}


def uniform_sequence(seed, count):
    """32-bit LCG shared verbatim in JavaScript; values strictly inside [-1,1]."""
    if not isinstance(seed,int) or isinstance(seed,bool) or not 0 <= seed <= 0xffffffff:
        raise ValueError('seed must be an unsigned 32-bit integer')
    state=seed
    out=[]
    for _ in range(count):
        state=(1664525*state+1013904223) & 0xffffffff
        out.append(2*((state+.5)/4294967296)-1)
    return out


def stacks(pairs=4, error=0., mode='independent', seed=7, scale=1., kind='thickness'):
    """Return equal-inventory ordinary and cavity orderings.

    Cavity=(HL)^m (LH)^m. Ordinary=(HL)^(2m). The right half is reversed
    without changing any layer's thickness, index or token. Mirrored errors
    duplicate the first half in reverse spatial order, independently of
    the subsequent ordinary-order rearrangement.
    """
    if not isinstance(pairs,int) or isinstance(pairs,bool) or not 1 <= pairs <= 8:
        raise ValueError('pairs per side must be integer 1..8')
    if not isfinite(error) or not 0 <= error <= .08:
        raise ValueError('error amplitude must be in 0..0.08')
    if mode not in ('independent','mirrored','common'):
        raise ValueError('unknown error correlation')
    _positive(scale,'scale')
    if kind not in ('thickness','index'):
        raise ValueError('unknown perturbation kind')
    first=[(NH,'H'),(NL,'L')]*pairs
    materials=first+list(reversed(first))
    u=uniform_sequence(seed,4*pairs)
    if mode=='mirrored':
        u=u[:2*pairs]+list(reversed(u[:2*pairs]))
    if mode=='common':
        u=[u[0]]*(4*pairs)
    cavity=[Layer(n*(1+error*e) if kind=='index' else n,
                  LAMBDA0/(4*n)*(1+error*e if kind=='thickness' else 1)*scale,label,i)
            for i,((n,label),e) in enumerate(zip(materials,u))]
    ordinary=cavity[:2*pairs]+list(reversed(cavity[2*pairs:]))
    return ordinary,cavity


def golden_max(func, left, right, steps=64):
    """Bounded one-dimensional local refinement within an existing bracket."""
    g=(sqrt(5)-1)/2
    x1=right-g*(right-left); x2=left+g*(right-left)
    y1,y2=func(x1),func(x2)
    for _ in range(steps):
        if y1 < y2:
            left=x1; x1=x2; y1=y2; x2=left+g*(right-left); y2=func(x2)
        else:
            right=x2; x2=x1; y2=y1; x1=right-g*(right-left); y1=func(x1)
    choices=[(left,func(left)),(right,func(right)),(x1,y1),(x2,y2)]
    return max(choices,key=lambda x:x[1])


def peak(layers, n0=1., ns=1., lo=540., hi=660., intervals=600):
    """Best bracketed T peak on [lo,hi], not an unrestricted global claim.

    Uniform grid finds local-max brackets; golden refinement resolves narrow
    peaks. Endpoints remain candidates and are flagged. UI highlights a peak
    even when the drawing grid would miss it. No smoothing or clamping.
    """
    if not isfinite(lo) or not isfinite(hi) or lo <= 0 or hi <= lo:
        raise ValueError('invalid search interval')
    if not isinstance(intervals,int) or intervals < 4 or intervals > 10000:
        raise ValueError('intervals must be integer 4..10000')
    f=lambda w:-solve(layers,w,n0,ns)['R']
    grid=[(lo+(hi-lo)*i/intervals) for i in range(intervals+1)]
    vals=[f(w) for w in grid]
    candidates=[(grid[0],vals[0]),(grid[-1],vals[-1])]
    brackets=[]
    for i in range(1,intervals):
        if vals[i]>=vals[i-1] and vals[i]>=vals[i+1]:
            brackets.append((grid[i-1],grid[i+1]))
            candidates.append(golden_max(f,*brackets[-1]))
    w,_=max(candidates,key=lambda x:x[1])
    result=solve(layers,w,n0,ns)
    return {'wavelength':w,'T':result['T'],'R':result['R'],
            'at_boundary':w==lo or w==hi,'brackets':len(brackets),
            'grid_max_T':1+max(vals),'grid_step':(hi-lo)/intervals}


def fwhm(layers, peak_w, peak_T, n0=1.,ns=1.,lo=540.,hi=660.):
    """Nearest crossings at half peak height; None when unbracketed."""
    threshold=peak_T/2
    f=lambda w:solve(layers,w,n0,ns)['T']-threshold
    crossings=[]
    for direction,bound in [(-1,lo),(1,hi)]:
        x=peak_w; step=.0001
        for _ in range(64):
            y=max(lo,min(hi,peak_w+direction*step))
            if f(y)<=0:
                a,b=sorted((x,y))
                for _ in range(55):
                    mid=(a+b)/2
                    if (f(a)>0)==(f(mid)>0):a=mid
                    else:b=mid
                crossings.append((a+b)/2)
                break
            if y==bound:
                crossings.append(None); break
            x=y;step*=1.7
        else:crossings.append(None)
    return None if None in crossings else crossings[1]-crossings[0]


def field_profile(layers,wavelength,n0=1.,ns=1.,samples_per_layer=24):
    """Right-to-left reconstruction of E,H; |E|^2 is not net power flux."""
    result=solve(layers,wavelength,n0,ns)
    E,H=result['t'],ns*result['t']
    offset=sum(x.d for x in layers)
    sections=[]
    for layer in reversed(layers):
        left=offset-layer.d
        points=[]
        for j in range(samples_per_layer+1):
            u=layer.d*j/samples_per_layer
            phase=2*pi*layer.n*(layer.d-u)/wavelength
            e=cos(phase)*E-1j*sin(phase)/layer.n*H
            h=-1j*layer.n*sin(phase)*E+cos(phase)*H
            points.append({'x':left+u,'E2':abs(e)**2,
                           'flux':(e*h.conjugate()).real/n0,
                           'E':e,'H':h,'label':layer.label})
        sections.append(points)
        E,H=points[0]['E'],points[0]['H']
        offset=left
    return [p for section in reversed(sections) for p in section]


def multiply(X,Y):
    a,b,c,d=X;e,f,g,h=Y
    return a*e-b*g,a*f+b*h,c*e+d*g,d*h-c*f


def sensitivity(pairs=4):
    """Exact-quarter-wave first-order wavelength weights, sum one.

    Differentiate one layer at a time with respect to fractional thickness.
    At lambda0 its derivative matrix is -pi/2 times the identity.
    The reflection numerator has imaginary component c-b. A fractional
    wavelength increase negates the sum of the thickness derivatives.
    """
    layers=stacks(pairs)[1]
    matrices=[(0.,1/x.n,x.n,0.) for x in layers]
    gs=[]
    for j in range(len(layers)):
        prod=(1.,0.,0.,1.)
        for k,M in enumerate(matrices):
            prod=multiply(prod,(-pi/2,0.,0.,-pi/2) if j==k else M)
        gs.append(prod[2]-prod[1])
    return [g/sum(gs) for g in gs]


def predicted_shift(pairs,error,mode,seed):
    _,layers=stacks(pairs,error,mode,seed)
    weights=sensitivity(pairs)
    return LAMBDA0*sum(w*(layer.n*layer.d/(LAMBDA0/4)-1)
                       for w,layer in zip(weights,layers))


def adaptive_simpson(f,a,b,tol=1e-10,max_depth=18):
    """Return integral, evaluation count and whether depth cap was reached."""
    count=0; capped=False
    def ev(x):
        nonlocal count
        count+=1
        return f(x)
    def rec(a,b,fa,fm,fb,whole,tol,depth):
        nonlocal capped
        mid=(a+b)/2
        l=(a+mid)/2;r=(mid+b)/2
        fl,fr=ev(l),ev(r)
        left=(mid-a)/6*(fa+4*fl+fm)
        right=(b-mid)/6*(fm+4*fr+fb)
        delta=left+right-whole
        if abs(delta)<=15*tol:return left+right+delta/15
        if depth==0:
            capped=True
            return left+right+delta/15
        return (rec(a,mid,fa,fl,fm,left,tol/2,depth-1)+
                rec(mid,b,fm,fr,fb,right,tol/2,depth-1))
    fa,fm,fb=ev(a),ev((a+b)/2),ev(b)
    value=rec(a,b,fa,fm,fb,(b-a)/6*(fa+4*fm+fb),tol,max_depth)
    return value,count,capped


def band_average(layers,center,line_fwhm,n0=1.,ns=1.,peak_info=None,tol=1e-9):
    """Gaussian incident power density per nm, integrated over +/-8 sigma.

    This is a spectral average, not a time-domain simulation. Explicit peak
    breakpoints prevent an adaptive integrator from skipping the narrow mode.
    The result is normalized by the same truncated Gaussian's analytic mass.
    """
    from math import exp, log, erf
    _positive(center,'center')
    if not isfinite(line_fwhm) or line_fwhm < 0 or line_fwhm > 10:
        raise ValueError('line FWHM must be finite in 0..10 nm')
    if line_fwhm==0:return {'T':solve(layers,center,n0,ns)['T'],'evaluations':1,'capped':False}
    sigma=line_fwhm/(2*sqrt(2*log(2)))
    lo,hi=center-8*sigma,center+8*sigma
    if lo<=0:raise ValueError('spectrum would include nonpositive wavelengths')
    p=peak_info if peak_info is not None else peak(layers,n0,ns)
    width=fwhm(layers,p['wavelength'],p['T'],n0,ns)
    knots=[lo,hi,center]+[center+s*sigma for s in [-4,-2,-1,1,2,4]]
    if width is not None:
        knots += [p['wavelength']+s*width for s in [-8,-4,-2,-1,-.5,0,.5,1,2,4,8]]
    knots=sorted(set(x for x in knots if lo<=x<=hi))
    f=lambda w:solve(layers,w,n0,ns)['T']*exp(-.5*((w-center)/sigma)**2)/(sigma*sqrt(2*pi))
    total=0.;evaluations=0;capped=False
    for a,b in zip(knots,knots[1:]):
        v,n,c=adaptive_simpson(f,a,b,tol/(len(knots)-1))
        total+=v;evaluations+=n;capped|=c
    return {'T':total/erf(8/sqrt(2)),'evaluations':evaluations,'capped':capped}
