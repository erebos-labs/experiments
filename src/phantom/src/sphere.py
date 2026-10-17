"""Silent far-field rigid-sphere check; standard library, finite series, no audio output.

Based on Sridhar & Choueiri (2021), Eqs5–6, with exp(+iωt) and h^(2).
H(x,μ) = sum (2n+1) i^(n-1) P_n(μ) / (x² h_n^(2)'(x)).
x=ka; μ=ear-axis dot source-direction. The sphere is not an individualized head.
"""
from pathlib import Path
from datetime import datetime, timezone
import math,cmath,json,csv,time
R=.09;C=343
r=Path(__file__).resolve().parent;a=r.parent/'results';a.mkdir(exist_ok=True)

def hankel2(x,nmax):
 h=[1j*cmath.exp(-1j*x)/x,-cmath.exp(-1j*x)/x*(1-1j/x)]
 for n in range(1,nmax):h.append((2*n+1)/x*h[n]-h[n-1])
 return h[:nmax+1]

def derivative(h,x,n):return -h[1] if n==0 else h[n-1]-(n+1)/x*h[n]

def legendre(mu,nmax):
 p=[1.,mu]
 for n in range(1,nmax):p.append(((2*n+1)*mu*p[n]-n*p[n-1])/(n+1))
 return p[:nmax+1]

def bessel_j(x,nmax):
 # Miller downward recurrence, normalized with whichever of j0 or j1 is larger.
 top=nmax+50+int(x);b=[0.]*(top+2);b[top]=1
 for n in range(top,0,-1):
  b[n-1]=(2*n+1)/x*b[n]-b[n+1]
  if abs(b[n-1])>1e100:
   for k in range(n-1,top+2):b[k]*=1e-100
 j0=math.sin(x)/x;j1=math.sin(x)/x**2-math.cos(x)/x
 i=0 if abs(j0)>=abs(j1) else 1;scale=[j0,j1][i]/b[i]
 return [v*scale for v in b[:nmax+1]]

def hrtf(frequency,mu,order=64):
 if not 20<=frequency<=8000 or not -1<=mu<=1 or not 16<=order<=80:raise ValueError('bounded study domain only')
 x=2*math.pi*frequency*R/C;h=hankel2(x,order+1);p=legendre(mu,order)
 return sum((2*n+1)*1j**(n-1)*p[n]/(x*x*derivative(h,x,n)) for n in range(order+1))

def direct_field(frequency,mu,radius_multiple=1,order=48):
 x=2*math.pi*frequency*R/C;z=x*radius_multiple
 h=hankel2(x,order+1);j=bessel_j(x,order+1);hz=hankel2(z,order+1);jz=bessel_j(z,order+1);p=legendre(mu,order)
 return sum((2*n+1)*1j**n*(jz[n]-derivative(j,x,n)/derivative(h,x,n)*hz[n])*p[n] for n in range(order+1))

def run():
 start=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
 checks={};maxconv=0;maxplane=0;maxrepr=0;maxboundary=0;maxmirror=0;count=0
 for f in [50,100,200,500,1000,2000,4000,8000]:
  for az in range(-180,180,5):
   mu=math.sin(math.radians(az));v=hrtf(f,mu,64);v80=hrtf(f,mu,80)
   maxconv=max(maxconv,abs(v-v80));other=hrtf(f,math.sin(math.radians(180-az)),64)
   maxmirror=max(maxmirror,abs(v-other));count+=1
 assert maxconv<1e-12 and maxmirror<1e-12
 for f in [500,2000,8000]:
  x=2*math.pi*f*R/C;j=bessel_j(x,49)
  for mu in [-1,-.5,0,.5,1]:
   p=legendre(mu,48);plane=sum((2*n+1)*1j**n*j[n]*p[n] for n in range(49))
   maxplane=max(maxplane,abs(plane-cmath.exp(1j*x*mu)))
   maxrepr=max(maxrepr,abs(direct_field(f,mu)-hrtf(f,mu,64)))
   eps=1e-5;d=(direct_field(f,mu,1+eps)-direct_field(f,mu,1-eps))/(2*eps)
   maxboundary=max(maxboundary,abs(d))
 assert maxplane<1e-12 and maxrepr<1e-11 and maxboundary<2e-6
 low=[]
 for az in [30,60,90]:
  mu=math.sin(math.radians(az));ratio=hrtf(20,-mu)/hrtf(20,mu);tau=-cmath.phase(ratio)/(2*math.pi*20)*1e6;limit=3*R/C*mu*1e6
  assert abs(tau-limit)/limit<.001
  low.append({'azimuth_deg':az,'frequency_Hz':20,'computed_phase_delay_us':tau,'derived_low_frequency_limit_us':limit,'relative_error':abs(tau-limit)/limit})
 rows=[]
 for az in [30,60,90]:
  mu=math.sin(math.radians(az));previous=0;unwrapped=0
  for f in range(50,8001,25):
   left=hrtf(f,-mu);right=hrtf(f,mu);phase=cmath.phase(left/right)
   delta=(phase-previous+math.pi)%(2*math.pi)-math.pi;unwrapped+=delta;previous=phase
   rows.append({'azimuth_deg':az,'frequency_Hz':f,'sphere_phase_delay_us':-unwrapped/(2*math.pi*f)*1e6,'point_receiver_delay_us':2*R/C*mu*1e6,'sphere_right_minus_left_level_dB':20*math.log10(abs(right)/abs(left))})
 checks={'series_64_vs_80_max_complex_difference':maxconv,'front_back_max_complex_difference':maxmirror,'plane_wave_expansion_max_error':maxplane,'wronskian_vs_direct_representation_max_difference':maxrepr,'finite_difference_neumann_derivative_max_abs':maxboundary,'symmetry_and_convergence_cases':count,'low_frequency_checks':low}
 report={'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'runtime_seconds':time.perf_counter()-start,'status':'PASS','radius_m':R,'speed_m_s':C,'sphere_model':'Far-field plane wave; rigid sphere; diametrically opposite point receivers on surface; finite spherical-harmonic series through degree64','source':'https://3d3a.princeton.edu/document/276, Sridhar & Choueiri(2021), Eq5–6; exp(+iωt), second-kind spherical Hankel convention','computed_quantity':'phase delay from frequency-unwrapped interaural phase, not a pulse-onset or listener ITD estimate','checks':checks,'frequency_rows':len(rows),'key_rows':[row for row in rows if row['frequency_Hz'] in [50,200,500,1000,2000,4000,8000]],'interpretation':'Adding a symmetric rigid sphere changes phase delay and adds level differences, but front/back reflection still leaves both complex receiver responses identical at a fixed pose. The point-receiver numbers are model-specific.','limits':['No pinnae, torso, finite source range, individualization, headphone transfer or room.','No proof of perceived location or general human delay limit.','Series convergence checked against degree80 over a finite grid, not a rigorous all-parameter bound.','Computed spectra were not converted into playable audio.']}
 with (a/'sphere-study.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (a/'sphere-study.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 return report
if __name__=='__main__':run()
