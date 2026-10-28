"""Finite Gaussian grating: analytic Fresnel sum + domain-tested scalar FFT."""
import cmath,csv,json,math,time
from pathlib import Path
from model import TAU,coefficients,field,propagate
ART=Path(__file__).resolve().parent/'data'
SIGMA=.04;AMPLITUDE=1/math.sqrt(SIGMA*math.sqrt(math.pi))

def fft(values,inverse=False):
    a=list(values);n=len(a)
    if n<2 or n&(n-1):raise ValueError('Power of two required')
    j=0
    for i in range(1,n):
        bit=n>>1
        while j&bit:j^=bit;bit>>=1
        j^=bit
        if i<j:a[i],a[j]=a[j],a[i]
    length=2
    while length<=n:
        wlen=cmath.exp((2j if inverse else -2j)*math.pi/length)
        for start in range(0,n,length):
            w=1+0j
            for k in range(start,start+length//2):
                u=a[k];v=a[k+length//2]*w;a[k]=u+v;a[k+length//2]=u-v;w*=wlen
        length*=2
    return [v/n for v in a] if inverse else a

def initial(x,count):
    m=count//2
    return AMPLITUDE*sum(math.exp(-(x-j)**2/(2*SIGMA**2)) for j in range(-m,m+1))

def fresnel(x,count,t=1):
    q=SIGMA**2+1j*t/math.pi;m=count//2
    return AMPLITUDE*SIGMA/cmath.sqrt(q)*sum(cmath.exp(-(x-j)**2/(2*q)) for j in range(-m,m+1))

def transfer(f,t=1,alpha=.01,exact=False):
    if abs(alpha*f)>=1:raise ValueError('Grid includes grazing/evanescent modes outside this bounded implementation')
    phase=-4*math.pi*t*f*f/(1+math.sqrt(1-(alpha*f)**2)) if exact else -TAU*t*f*f
    return cmath.exp(1j*phase)

def simulate(count,length=128,resolution=128,exact=False):
    n=length*resolution
    if count>=length:raise ValueError('Input array must fit padded domain')
    u=[complex(initial(-length/2+j/resolution,count)) for j in range(n)]
    spectrum=fft(u)
    out=fft([v*transfer((j if j<n//2 else j-n)/length,exact=exact) for j,v in enumerate(spectrum)],True)
    return out,{'count':count,'domain_periods':length,'samples_per_period':resolution,'exact':exact,'input_integral':sum(abs(v)**2 for v in u)/resolution,'output_integral':sum(abs(v)**2 for v in out)/resolution}

def window(out,length,resolution,center):
    return [out[round((length/2+center-.5)*resolution)+j] for j in range(resolution)]

def metrics(u,reference):
    a=[abs(v)**2 for v in u];b=[abs(v)**2 for v in reference];n=len(u)
    ma=sum(a)/n;mb=sum(b)/n;va=sum((v-ma)**2 for v in a)/n;vb=sum((v-mb)**2 for v in b)/n
    return {'window_mean_I':ma,'input_mean_I':mb,'absolute_RMS_contrast':math.sqrt(va),'input_RMS_contrast':math.sqrt(vb),'RMS_contrast_ratio':math.sqrt(va/vb),
      'field_overlap':abs(sum(x.conjugate()*y for x,y in zip(reference,u)))**2/(sum(abs(v)**2 for v in reference)*sum(abs(v)**2 for v in u)),
      'centered_intensity_shape_cosine':sum((x-ma)*(y-mb) for x,y in zip(a,b))/(n*math.sqrt(va*vb)),
      'absolute_intensity_relative_L2':math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/sum(y*y for y in b)),
      'peak_I_sampled':max(a),'I_at_pulse_center':a[n//2]}

def run():
    tick=time.perf_counter();rows=[];profiles={};convergence=[];energy=[]
    xs=[-.5+j/128 for j in range(128)];ref=[complex(initial(x,1)) for x in xs]
    for count in (5,9,17,33,65):
      for exact in (False,True):
        out,e=simulate(count,exact=exact);energy.append(e);m=count//2
        assert abs(e['input_integral']-count)<1e-10
        assert abs(e['output_integral']-e['input_integral'])<1e-8
        for name,c in [('center',0),('interior',m//2),('edge',m)]:
          u=window(out,128,128,c);rows.append({'count':count,'model':'exact_scalar' if exact else 'paraxial','window':name,'window_center':c,**metrics(u,ref)})
          profiles[f'{count}_{exact}_{name}']=[[x,z.real,z.imag] for x,z in zip(xs,u)]
          if not exact:
            err=max(abs(v-fresnel(x+c,count)) for x,v in zip(xs,u));assert err<1e-8,(count,name,err)
            convergence.append({'kind':'FFT_vs_analytic_Fresnel','count':count,'window':name,'domain':128,'resolution':128,'max_field_error':err})
    # Deliberately test insufficient padding, against an independent nonperiodic reference.
    for length in (32,64,128):
      out,_=simulate(17,length,64)
      for c in (0,8):
        u=window(out,length,64,c)
        err=max(abs(v-fresnel(c-.5+j/64,17)) for j,v in enumerate(u))
        convergence.append({'kind':'padding_vs_Fresnel','count':17,'window_center':c,'domain':length,'resolution':64,'max_field_error':err})
    # Exact scalar reference: increase domain and resolution separately.
    for count in (17,33,65):
      a,_=simulate(count,128,128,True);b,_=simulate(count,256,128,True)
      for c in (0,count//2):
        err=max(abs(x-y) for x,y in zip(window(a,128,128,c),window(b,256,128,c)))
        assert err<1e-8,(count,c,err)
        convergence.append({'kind':'exact_domain_128_vs_256','count':count,'window_center':c,'max_field_error':err})
    for exact in (False,True):
      a,_=simulate(33,128,64,exact);b,_=simulate(33,128,128,exact)
      for c in (0,16):
        err=max(abs(x-y) for x,y in zip(window(a,128,64,c),window(b,128,128,c)[::2]))
        assert err<1e-8,(exact,c,err)
        convergence.append({'kind':'resolution_64_vs_128','model':'exact' if exact else 'paraxial','window_center':c,'max_field_error':err})
    # Large-N edge-center identity from mirror-pair symmetry, independently derived.
    single=fresnel(0,1);pred=(AMPLITUDE+single)/2
    edge=complex(*profiles['65_False_edge'][64][1:]);assert abs(edge-pred)<1e-5,(edge,pred)
    tail_bounds=[]
    q=SIGMA**2+1j/math.pi;spread=abs(q)/SIGMA;pref=AMPLITUDE*SIGMA/math.sqrt(abs(q))
    for count in (5,9,17,33,65):
      bound=2*pref*spread*math.sqrt(math.pi/2)*math.erfc((count//2-.5)/(math.sqrt(2)*spread))
      err=max(abs(fresnel(x,count)-initial(x,65)) for x in xs)
      assert err<=bound
      tail_bounds.append({'count':count,'max_central_window_field_error':err,'analytic_envelope_upper_bound':bound})
    data={'paraxial_central_tail_bounds':tail_bounds,'sigma':SIGMA,'alpha':.01,'tau':1,'rows':rows,'profiles':profiles,'convergence':convergence,'integral_checks':energy,
      'edge_center_prediction':{'large_N_field_real':pred.real,'large_N_field_imag':pred.imag,'predicted_pulse_center_intensity_ratio':abs(pred)**2/AMPLITUDE**2,'N65_field_error':abs(edge-pred)},
      'limits':['Finite Gaussian beamlet array, not hard-edged illumination.','One propagation distance and source width; no universal finite-aperture threshold.','Scalar forward propagation, no vector/material effects.','Every retained grid mode propagates; neglected high frequencies are tiny for smooth input.','Output arrays are periodic numerically, but reported windows pass domain and analytic-reference checks.','No spatial registration or distance optimization performed; windows remain fixed to actual input slots.','Intensity is scalar |U|^2, not electromagnetic normal flux.']}
    with (ART/'finite-array-sweep.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (ART/'finite-array-results.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'convergence_checks':len(convergence),'edge_prediction':data['edge_center_prediction'],'seconds':time.perf_counter()-tick},indent=2))
if __name__=='__main__':run()
