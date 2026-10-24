"""Truncated Taylor certificate for this quarter-wave, air-to-air family.

This is a model-specific derivation, not a new claim of scientific
priority. Coefficients retain powers epsilon^0..2, with no finite differences.
"""
from math import pi
from model import stacks, sensitivity, uniform_sequence, LAMBDA0


def add(a,b):return [x+y for x,y in zip(a,b)]
def neg(a):return [-x for x in a]
def mul(a,b):return [sum(a[k]*b[j-k] for k in range(j+1)) for j in range(3)]

def matmul(X,Y):
    a,b,c,d=X;e,f,g,h=Y
    return (add(mul(a,e),neg(mul(b,g))),add(mul(a,f),mul(b,h)),
            add(mul(c,e),mul(d,g)),add(mul(d,h),neg(mul(c,f))))


def certificate(pairs=6,seed=7,kind='thickness',mode='independent'):
    layers=stacks(pairs)[1]
    u=uniform_sequence(seed,len(layers))
    if mode=='mirrored':u=u[:len(u)//2]+list(reversed(u[:len(u)//2]))
    elif mode=='common':u=[u[0]]*len(u)
    elif mode!='independent':raise ValueError('unknown mode')
    a=sum(w*e for w,e in zip(sensitivity(pairs),u))
    product=([1.,0.,0.],[0.,0.,0.],[0.,0.,0.],[1.,0.,0.])
    for layer,e in zip(layers,u):
        # lambda/lambda0=1+a*epsilon, n*d/(n_nom*d_nom)=1+e*epsilon.
        phase1=pi/2*(e-a)
        phase2=pi/2*(a*a-a*e)
        co=[0.,-phase1,-phase2]
        if kind=='thickness':
            b=[1/layer.n,0.,-phase1*phase1/(2*layer.n)]
            c=[layer.n,0.,-layer.n*phase1*phase1/2]
        elif kind=='index':
            b=[1/layer.n,-e/layer.n,(e*e-phase1*phase1/2)/layer.n]
            c=[layer.n,layer.n*e,-layer.n*phase1*phase1/2]
        else:raise ValueError('unknown kind')
        product=matmul(product,(co,b,c,co))
    A,B,C,D=product
    diag=[x-y for x,y in zip(A,D)]
    imag=[x-y for x,y in zip(C,B)]
    order=4 if kind=='thickness' else 2
    power_coefficient=(diag[2] if kind=='thickness' else diag[1])**2/4
    return {'pairs':pairs,'seed':seed,'kind':kind,'mode':mode,
            'fractional_shift_coefficient':a,
            'nm_shift_per_fraction_error':LAMBDA0*a,
            'leading_reflectance_power':order,
            'leading_reflectance_coefficient':power_coefficient,
            'numerator_real_coefficients':diag,
            'numerator_imag_coefficients':imag,
            'matrix_coefficients':product,
            'scope':'local Taylor expansion; equal exterior indices=1; coherent lossless nondispersive quarter-wave family; generic nonzero leading coefficient'}

if __name__=='__main__':
    import json
    print(json.dumps([certificate(kind=k) for k in ['thickness','index']],indent=2))
