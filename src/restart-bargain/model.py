"""Finite discrete search with reset-before-move; Python standard library only.

Sites 0..L. 0 absorbs. A non-reset step moves +/-1 with equal chance;
an attempted move beyond L stays at L. A reset consumes one tick and returns
any transient site to s, including s itself. Optional cost c adds c frozen
ticks AFTER that reset tick; no reset decisions occur during frozen ticks.
"""
from math import isfinite


def validate(length, start, reset, cost=0):
    if not isinstance(length, int) or not 1 <= length <= 200:
        raise ValueError('length must be an integer in 1..200')
    if not isinstance(start, int) or not 1 <= start <= length:
        raise ValueError('start must be an integer in 1..length')
    if not isfinite(reset) or not 0 <= reset <= 1:
        raise ValueError('reset must be in [0,1]')
    if not isinstance(cost, int) or not 0 <= cost <= 100:
        raise ValueError('extra reset cost must be an integer in 0..100')


def tridiagonal(lower, diag, upper, rhs):
    """Thomas elimination; callers supply diagonally dominant systems."""
    n=len(diag)
    b=list(diag); d=list(rhs)
    for i in range(1,n):
        f=lower[i-1]/b[i-1]
        b[i]-=f*upper[i-1]; d[i]-=f*d[i-1]
    x=[0.0]*n; x[-1]=d[-1]/b[-1]
    for i in range(n-2,-1,-1):
        x[i]=(d[i]-upper[i]*x[i+1])/b[i]
    return x


def base_resolvent(length, reset, rhs):
    q=1-reset
    diag=[1.0]*length; diag[-1]-=q/2
    return tridiagonal([-q/2]*(length-1),diag,[-q/2]*(length-1),rhs)


def mean_time(length, start, reset, cost=0):
    validate(length,start,reset,cost)
    if reset == 1: return float('inf')
    a=base_resolvent(length,reset,[1.0]*length)[start-1]
    # Solve success-before-reset separately: 1-r*a loses significance for
    # large reset probabilities, especially with a distant target.
    f=base_resolvent(length,reset,[(1-reset)/2]+[0.0]*(length-1))[start-1]
    if not f: raise ArithmeticError('success probability underflow; use higher precision')
    result=(1+reset*cost)*a/f
    if not isfinite(result): raise ArithmeticError('mean exceeds floating-point range')
    return result


def moments(length, start, reset):
    """First two raw moments, without extra reset delay."""
    validate(length,start,reset)
    if reset == 1: return float('inf'),float('inf')
    a=base_resolvent(length,reset,[1.0]*length)
    den=base_resolvent(length,reset,[(1-reset)/2]+[0.0]*(length-1))[start-1]
    if not den: raise ArithmeticError('success probability underflow; use higher precision')
    means=[x/den for x in a]
    b=base_resolvent(length,reset,[2*x-1 for x in means])
    second=b[start-1]/den
    return means[start-1],second


def distribution(length, start, reset, horizon, cost=0):
    """Forward mass propagation. Returns S(t)=P(T>t), t=0..horizon.

    Delay buckets implement an explicit reset cost. Finite-horizon survival
    stays as survival; it is never relabeled completed or renormalized.
    """
    validate(length,start,reset,cost)
    if not isinstance(horizon,int) or not 0 <= horizon <= 200000:
        raise ValueError('horizon must be an integer in 0..200000')
    p=[0.0]*(length+1); p[start]=1.0
    delay=[0.0]*cost
    survival=[1.0]
    for _ in range(horizon):
        out=[0.0]*(length+1)
        ready=delay[0] if cost else 0.0
        reset_mass=reset*sum(p)
        if cost:
            delay=delay[1:]+[reset_mass]
        else: out[start]+=reset_mass
        out[start]+=ready
        for i in range(1,length+1):
            mass=(1-reset)*p[i]/2
            if i>1: out[i-1]+=mass
            out[min(length,i+1)]+=mass
        p=out
        survival.append(sum(p)+sum(delay))
    return survival


def quantile(survival, probability):
    for t,s in enumerate(survival):
        if s <= 1-probability+1e-13: return t
    return None


def deadline_success(length,start,reset,deadline,cost=0):
    return 1-distribution(length,start,reset,deadline,cost)[-1]
