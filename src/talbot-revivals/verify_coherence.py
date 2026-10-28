"""Independent analytic identities, physical limits and quadrature checks."""
import unittest
from coherence import *
class CoherenceChecks(unittest.TestCase):
 def setUp(self):self.c=coefficients(.04,24)
 def test_legendre_moments(self):
  for q in (8,17,64):
   for k in range(8):self.assertAlmostEqual(sum(w*x**k/2 for x,w in nodes(q)),0 if k%2 else 1/(k+1),places=13)
 def test_direct_scalar_phase(self):
  for n in (-20,-1,0,7,20):
   a=.01;e=.05;v=.07;t=.739;r=1+e
   direct=4*math.pi*t/(a*a*r)*(math.sqrt(1-(a*r*(n+v))**2)-math.sqrt(1-(a*r*v)**2))
   self.assertAlmostEqual(phi(n,t,a,e,v,True),direct,places=9)
 def test_direct_intensity_average(self):
  c=coefficients(.08,12)
  for kind in ('angular','spectral'):
   rho=matrix(c,.913,.01,kind,.02,exact=True,nq=64);h=harmonics(c,rho)
   for x in (0,.137,.41):
    total=0
    for u,w in nodes(64):
     e=u*.02 if kind=='spectral' else 0;v=u*.02 if kind=='angular' else 0
     field=sum(z*cmath.exp(1j*(TAU*n*x+phi(n,.913,.01,e,v,True))) for n,z in c)
     total+=w/2*abs(field)**2
    self.assertAlmostEqual(evaluate(h,x),total,places=12)
 def test_angular_uniform_washout(self):
  h=harmonics(self.c,matrix(self.c,1,.001,'angular',.25))
  for j in range(31):self.assertAlmostEqual(evaluate(h,j/31),1,places=13)
  m=metrics(self.c,matrix(self.c,1,.001,'angular',.25));self.assertIsNone(m['centered_shape_cosine_shifted']);self.assertIsNone(m['intensity_best_shift'])
 def test_spectral_degenerate_pairs_survive(self):
  rho=matrix(self.c,1,.001,'spectral',.5);h=harmonics(self.c,rho)
  for i,(n,c) in enumerate(self.c):
   for j,(m,d) in enumerate(self.c):self.assertLess(abs(rho[i][j]-(c*d.conjugate() if n*n==m*m else 0)),1e-14)
  for j in range(31):
   x=j/31;expected=1+sum((c*d.conjugate()*cmath.exp(1j*TAU*(n-m)*x)).real for n,c in self.c for m,d in self.c if n==-m and n!=0)
   self.assertAlmostEqual(evaluate(h,x),expected,places=13)
  self.assertGreater(evaluate(h,0)-evaluate(h,.25),.9)
 def test_shifted_perfect_return(self):
  rho=matrix(self.c,1,.01,'angular',0,mean=.07);h=harmonics(self.c,rho);base=harmonics(self.c,matrix(self.c,0,.01))
  for j in range(31):self.assertAlmostEqual(evaluate(h,j/31+.14),evaluate(base,j/31),places=11)
  m=metrics(self.c,rho);self.assertLess(m['mean_member_field_overlap_unshifted'],.003);self.assertAlmostEqual(m['mean_member_field_overlap_shifted'],1,places=12)
 def test_hermitian_positive_intensity_trace(self):
  for kind in ('angular','spectral'):
   r=matrix(self.c,1,.01,kind,.05,exact=True,nq=128)
   for i in range(len(r)):
    for j in range(len(r)):self.assertLess(abs(r[i][j]-r[j][i].conjugate()),1e-14)
   self.assertAlmostEqual(sum(r[i][i].real for i in range(len(r))),1,places=13)
   h=harmonics(self.c,r)
   self.assertGreater(min(evaluate(h,j/97) for j in range(97)),-1e-12)
 def test_weak_modulation_fidelity_trap(self):
  c=[(-1,.01+0j),(0,1+0j),(1,.01+0j)];norm=math.sqrt(sum(abs(z)**2 for n,z in c));c=[(n,z/norm) for n,z in c]
  m=metrics(c,matrix(c,1,.001,'angular',.25))
  self.assertGreater(m['mean_member_field_overlap_unshifted'],.9995);self.assertLess(m['contrast_rms_ratio'],1e-14)
 def test_averaging_amplitudes_is_wrong_for_incoherent_source(self):
  # Analytic average amplitude retains only n=0 at this washout point.
  wrong_mean=sum(abs(c*sinc(TAU*2*.25*n))**2 for n,c in self.c)
  true=metrics(self.c,matrix(self.c,1,.001,'angular',.25))['mean_intensity']
  self.assertAlmostEqual(wrong_mean,dict(self.c)[0].real**2,places=13)
  self.assertAlmostEqual(true,1,places=13);self.assertLess(wrong_mean,.15)
 def test_angular_width_and_modal_truncation(self):
  # Same spectral coefficients, extra tail orders; compare observable Fourier harmonics.
  a=coefficients(.04,24);b=coefficients(.04,32)
  ha=harmonics(a,matrix(a,1,.01,'angular',.01,exact=True,nq=128));hb=harmonics(b,matrix(b,1,.01,'angular',.01,exact=True,nq=128))
  error=max(abs(evaluate(ha,j/257)-evaluate(hb,j/257)) for j in range(257))
  self.assertLess(error,2e-7);print('M24_vs_M32_max_sampled_intensity_error',error)
if __name__=='__main__':unittest.main(verbosity=2)
