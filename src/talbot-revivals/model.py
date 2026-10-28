"""Finite Fourier model of periodic scalar waves; Python standard library only.

X=x/d; T=z/(2*d*d/lambda); alpha=lambda/d. Common carrier exp(ikz)
is removed. Infinite periodic transverse boundary, finite angular spectrum.
All retained exact-model modes must propagate (abs(n*alpha)<1).
"""
import cmath
import math

TAU = 2 * math.pi


def coefficients(width=0.025, orders=32, chirp=0.0, profile='pulse'):
    if not (0.015 <= width <= 0.15 and isinstance(orders, int) and 1 <= orders <= 64):
        raise ValueError('width or orders outside bounded model')
    if not math.isfinite(chirp) or abs(chirp) > 0.1 or profile not in ('pulse', 'three'):
        raise ValueError('invalid chirp/profile')
    result = []
    for n in range(-orders, orders + 1):
        a = math.exp(-2 * math.pi**2 * width**2 * n**2) if profile == 'pulse' else (1 if n == 0 else 0.25 if abs(n) == 1 else 0)
        result.append((n, a * cmath.exp(1j * TAU * chirp * n*n)))
    norm = math.sqrt(sum(abs(c)**2 for _, c in result))
    return [(n, c/norm) for n,c in result]


def residual_phase(n, t, alpha):
    """Stable exact-minus-paraxial phase; avoids sqrt(1-u)-1 cancellation."""
    if not all(math.isfinite(v) for v in (t, alpha)) or abs(t) > 4 or not (0 <= alpha < 1):
        raise ValueError('invalid propagation parameters')
    if abs(n * alpha) >= 1:
        raise ValueError('retained mode is grazing or evanescent')
    s = math.sqrt(1 - (n*alpha)**2)
    return -TAU * t * alpha**2 * n**4 / (1 + s)**2


def phase(n, t, alpha=0.0, exact=False):
    residual = residual_phase(n, t, alpha)  # validate in both modes
    return -TAU * t * n*n + (residual if exact else 0.0)


def propagate(cs, t, alpha=0.0, exact=False):
    return [(n, c * cmath.exp(1j * phase(n,t,alpha,exact))) for n,c in cs]


def field(cs, x):
    return sum(c * cmath.exp(1j * TAU * n * x) for n,c in cs)


def intensity(cs, x):
    return abs(field(cs,x))**2


def fidelity(a,b):
    """Squared normalized field overlap, invariant under a global phase."""
    aa=dict(a); bb=dict(b)
    inner=sum(aa.get(n,0).conjugate()*bb.get(n,0) for n in aa.keys()|bb.keys())
    den=sum(abs(c)**2 for c in aa.values())*sum(abs(c)**2 for c in bb.values())
    return abs(inner)**2/den


def replicas(p,q):
    """Full-return convention: U(X,p/q)=sum_j K_j U(X-j/q,0)."""
    if not (isinstance(p,int) and isinstance(q,int) and 1<=q<=32):
        raise ValueError('bounded integer fraction required')
    return [sum(cmath.exp(1j*TAU*(r*j-p*r*r)/q) for r in range(q))/q for j in range(q)]


def replica_field(cs,x,p,q):
    return sum(k * field(cs,x-j/q) for j,k in enumerate(replicas(p,q)))


def incoherent_replica_intensity(cs,x,p,q):
    """Deliberately wrong for overlapping coherent replicas: a negative control."""
    return sum(abs(k)**2 * intensity(cs,x-j/q) for j,k in enumerate(replicas(p,q)))


def find_return(cs, alpha):
    """Best found near nominal return, not a certified unrestricted optimum."""
    left,right,steps=.98,1.0,256
    def score(t):return fidelity(cs,propagate(cs,t,alpha,True))
    grid=[left+(right-left)*j/steps for j in range(steps+1)]
    i=max(range(len(grid)),key=lambda j:score(grid[j]))
    a,b=grid[max(0,i-1)],grid[min(steps,i+1)]
    g=(math.sqrt(5)-1)/2
    x1=b-g*(b-a);x2=a+g*(b-a);f1=score(x1);f2=score(x2)
    for _ in range(64):
        if f1>f2:
            b=x2;x2=x1;f2=f1;x1=b-g*(b-a);f1=score(x1)
        else:
            a=x1;x1=x2;f1=f2;x2=a+g*(b-a);f2=score(x2)
    t=max((grid[i],left,right,a,b,x1,x2),key=score)
    return {'t':t,'fidelity':score(t),'interval':[left,right],'grid_points':steps+1,'golden_steps':64,'scope':'best found after refining the bracket of the best grid point; no global optimality claim'}
