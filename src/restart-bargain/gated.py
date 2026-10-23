"""Selective reset: reset only from sites strictly farther than the start.

Uses position information. Not the same admissible policy as blind restart.
The direct coupling comparison with no reset applies only to zero extra cost.
"""
from model import validate, tridiagonal


def resolvent(length,start,reset,rhs):
    rates=[reset if i>start else 0.0 for i in range(1,length+1)]
    qs=[1-r for r in rates]
    diag=[1.0]*length;diag[-1]-=qs[-1]/2
    return tridiagonal([-qs[i]/2 for i in range(1,length)],diag,[-qs[i]/2 for i in range(length-1)],rhs)


def mean_time(length,start,reset,cost=0):
    validate(length,start,reset,cost)
    rates=[reset if i>start else 0.0 for i in range(1,length+1)]
    a=resolvent(length,start,reset,[1+r*cost for r in rates])
    b=resolvent(length,start,reset,rates)
    return a[start-1]/(1-b[start-1])


def distribution(length,start,reset,horizon,cost=0):
    validate(length,start,reset,cost)
    if not isinstance(horizon,int) or not 0 <= horizon <= 200000:
        raise ValueError('horizon must be an integer in 0..200000')
    p=[0.]*(length+1);p[start]=1.;delay=[0.]*cost
    S=[1.]
    for _ in range(horizon):
        out=[0.]*(length+1)
        ready=delay[0] if cost else 0.
        reset_mass=reset*sum(p[start+1:])
        if cost:delay=delay[1:]+[reset_mass]
        else:out[start]+=reset_mass
        out[start]+=ready
        for i in range(1,length+1):
            r=reset if i>start else 0.
            mass=(1-r)*p[i]/2
            if i>1:out[i-1]+=mass
            out[min(length,i+1)]+=mass
        p=out
        S.append(sum(p)+sum(delay))
    return S
