"""Bounded discrete-time comparator; no physical continuous-white-noise claim."""
import math

PERIOD = 64
METRICS = ('crossing_rate','phase_hit','phase_false','balanced_accuracy','phase_mi','projection','magnitude','mse')


def validate(amplitude, threshold, sigma, n):
    if not all(math.isfinite(x) for x in (amplitude,threshold,sigma)):
        raise ValueError('finite parameters required')
    if not 0 <= amplitude <= 2 or not -2 <= threshold <= 2 or not 0 <= sigma <= 1e6:
        raise ValueError('parameter out of bounds')
    if not isinstance(n,int) or not PERIOD <= n <= 4096 or n % PERIOD:
        raise ValueError('n must be 64..4096 and a multiple of 64')


class RNG:
    """Mulberry32 + uncached Box-Muller, deliberately mirrored in core.js."""
    def __init__(self, seed):
        if not isinstance(seed,int) or not 0 <= seed <= 0xffffffff:
            raise ValueError('seed must be an unsigned 32-bit integer')
        self.state=seed
    def uniform(self):
        self.state=(self.state+0x6D2B79F5)&0xffffffff
        t=self.state
        t=((t^(t>>15))*(t|1))&0xffffffff
        t ^= (t+(((t^(t>>7))*(t|61))&0xffffffff))&0xffffffff
        return ((t^(t>>14))&0xffffffff)/4294967296
    def normal(self):
        # Open interval prevents log(0); keep one value per two uniforms.
        u=(int(self.uniform()*4294967296)+0.5)/4294967296
        return math.sqrt(-2*math.log(u))*math.cos(2*math.pi*self.uniform())


def entropy(p):
    return 0.0 if p <= 0 or p >= 1 else -p*math.log2(p)-(1-p)*math.log2(1-p)


def phase_information(hit, false):
    return max(0.0,entropy((hit+false)/2)-(entropy(hit)+entropy(false))/2)


def phase_grid(n):
    return [math.sin(2*math.pi*((i%PERIOD)+0.5)/PERIOD) for i in range(n)]


def measure(outputs, wave, errors=None):
    n=len(outputs)
    hit=2*sum(y for y,s in zip(outputs,wave) if s>0)/n
    false=2*sum(y for y,s in zip(outputs,wave) if s<0)/n
    projection=2*sum(y*s for y,s in zip(outputs,wave))/n
    quadrature=2*sum(y*math.cos(2*math.pi*((i%PERIOD)+0.5)/PERIOD) for i,y in enumerate(outputs))/n
    return {'crossing_rate':sum(outputs)/n,'phase_hit':hit,'phase_false':false,
            'balanced_accuracy':(1+hit-false)/2,'phase_mi':phase_information(hit,false),
            'projection':projection,'magnitude':math.hypot(projection,quadrature),
            'mse':sum(e*e for e in errors)/n if errors is not None else 0.0}


def simulate(amplitude=.25,threshold=1.0,sigma=.8,seed=20261025,n=256,keep=False):
    validate(amplitude,threshold,sigma,n)
    rng=RNG(seed)
    wave=phase_grid(n)
    errors=[sigma*rng.normal() for _ in range(n)]
    clean=[amplitude*s for s in wave]
    noisy=[s+e for s,e in zip(clean,errors)]
    outputs=[int(x>threshold) for x in noisy] # strict comparator, including ties
    result=measure(outputs,wave,errors)
    if keep: result.update(clean=clean,noisy=noisy,outputs=outputs,wave=wave)
    return result


def exceedance(x,threshold,sigma):
    return float(x>threshold) if sigma==0 else .5*math.erfc((threshold-x)/(math.sqrt(2)*sigma))


def theory(amplitude,threshold,sigma,n=256):
    validate(amplitude,threshold,sigma,n)
    wave=phase_grid(PERIOD)
    q=[exceedance(amplitude*s,threshold,sigma) for s in wave]
    out=measure(q,wave)
    # magnitude of E[Fourier coefficient], NOT E[magnitude]. No empirical bias.
    out['magnitude_of_mean']=out.pop('magnitude')
    out['mse']=sigma*sigma
    out['null_crossing']=exceedance(0,threshold,sigma)
    return out


def family_seed(base, family, index):
    # Integer mixing only. Families disjoint for stated bounds (indices < 1000).
    return (base+family*1000003+index*7919)&0xffffffff


def summarize(values):
    n=len(values); mean=sum(values)/n
    sd=math.sqrt(sum((x-mean)**2 for x in values)/(n-1)) if n>1 else 0
    sorted_values=sorted(values)
    return {'mean':mean,'sd':sd,'se':sd/math.sqrt(n),
            'lo95_mean':mean-1.96*sd/math.sqrt(n),'hi95_mean':mean+1.96*sd/math.sqrt(n),
            'p10':sorted_values[int(.1*(n-1))],'p90':sorted_values[int(.9*(n-1))]}


def ensemble(amplitude,threshold,sigma,base=20261025,n=256,batches=64):
    if not 2<=batches<=512: raise ValueError('2..512 batches required')
    signal=[simulate(amplitude,threshold,sigma,family_seed(base,1,i),n) for i in range(batches)]
    null=[simulate(0,threshold,sigma,family_seed(base,2,i),n) for i in range(batches)]
    return {'signal':{k:summarize([r[k] for r in signal]) for k in METRICS},
            'null':{k:summarize([r[k] for r in null]) for k in METRICS}}


def wilson(k,n):
    z=1.959963984540054; p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return {'count':k,'total':n,'rate':p,'lo95':mid-half,'hi95':mid+half}


def detection(amplitude,threshold,sigma,base=20261025,n=256,train=128,test=256):
    """Calibrate one-sided projection cutoff on null only, then held-out tests.

    Target 5% empirical training false alarms; NOT a guarantee for held-out PFA.
    Strict > cutoff conservatively handles degenerate sigma=0 and tied scores.
    """
    validate(amplitude,threshold,sigma,n)
    if not 20<=train<=512 or not 20<=test<=512: raise ValueError('batch bounds')
    calibration=sorted(simulate(0,threshold,sigma,family_seed(base,3,i),n)['projection'] for i in range(train))
    cutoff=calibration[math.ceil(.95*train)-1]
    null=[simulate(0,threshold,sigma,family_seed(base,4,i),n)['projection'] for i in range(test)]
    signal=[simulate(amplitude,threshold,sigma,family_seed(base,5,i),n)['projection'] for i in range(test)]
    return {'cutoff':cutoff,'target_training_pfa':.05,'training_false':sum(x>cutoff for x in calibration)/train,
            'false_alarm':wilson(sum(x>cutoff for x in null),test),
            'power':wilson(sum(x>cutoff for x in signal),test)}
