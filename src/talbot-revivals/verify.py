"""Identity and counterexample checks, not physical validation."""
import cmath,math,unittest
from model import *

class Identities(unittest.TestCase):
 def test_integer_revival_and_half_shift(self):
    for chirp in (-.06,0,.06):
     c=coefficients(.025,32,chirp)
     for j in range(97):
      x=j/97
      self.assertLess(abs(field(propagate(c,1),x)-field(c,x)),2e-12)
      self.assertLess(abs(field(propagate(c,.5),x)-field(c,x-.5)),2e-12)
 def test_parseval_and_lossless_mean(self):
    c=coefficients()
    for exact in (False,True):
     for t in (0,1/3,.5,.739,1):
      e=propagate(c,t,.025,exact)
      self.assertAlmostEqual(sum(intensity(e,j/257) for j in range(257))/257,1,places=12)
 def test_three_mode_closed_form(self):
    c=coefficients(profile='three')
    for j in range(101):
     x=j/101;co=math.cos(TAU*x)
     self.assertAlmostEqual(intensity(c,x),(1+.5*co)**2/1.125,places=13)
     self.assertAlmostEqual(intensity(propagate(c,.25),x),(1+.25*co*co)/1.125,places=13)
 def test_replica_decomposition_coprime_and_nonreduced(self):
    for chirp in (0,.06):
     c=coefficients(.08,16,chirp)
     for p,q in ((1,2),(1,3),(1,4),(1,5),(1,6),(1,8),(2,6),(3,7),(5,12)):
      for j in range(37):
       x=j/37
       self.assertLess(abs(field(propagate(c,p/q),x)-replica_field(c,x,p,q)),2e-12)
 def test_gauss_kernel_parseval(self):
    for q in range(1,17):
     for p in range(q):
      self.assertAlmostEqual(sum(abs(k)**2 for k in replicas(p,q)),1,places=12)
 def test_quarter_kernel_analytic(self):
    k=replicas(1,4)
    for a,b in zip(k,((1-1j)/2,0,(1+1j)/2,0)):self.assertLess(abs(a-b),1e-14)
 def test_quarter_real_input_is_null_control(self):
    c=coefficients(.12)
    for j in range(79):
     self.assertAlmostEqual(intensity(propagate(c,.25),j/79),incoherent_replica_intensity(c,j/79,1,4),places=12)
 def test_mixture_fails_for_complex_input(self):
    c=coefficients(.025,32,.06)
    error=max(abs(intensity(propagate(c,.25),j/128)-incoherent_replica_intensity(c,j/128,1,4)) for j in range(128))
    self.assertGreater(error,.1)
 def test_mixture_fails_for_overlapping_thirds(self):
    c=coefficients(.12)
    error=max(abs(intensity(propagate(c,1/3),j/128)-incoherent_replica_intensity(c,j/128,1,3)) for j in range(128))
    self.assertGreater(error,.1)
 def test_equal_intensity_twins_can_diverge(self):
    a,b=(coefficients(.025,32,s*.06) for s in (1,-1))
    for j in range(79):self.assertAlmostEqual(intensity(a,j/79),intensity(b,j/79),places=13)
    self.assertGreater(intensity(propagate(a,.06),0)/intensity(propagate(b,.06),0),10)
 def test_exact_dispersion_against_direct_sqrt(self):
    for alpha in (.001,.01,.025):
     for n in (-32,-10,-1,0,1,10,32):
      t=.739;direct=4*math.pi*t/alpha**2*(math.sqrt(1-(n*alpha)**2)-1)
      self.assertLess(abs(phase(n,t,alpha,True)-direct),2e-9)
 def test_quartic_limit_and_small_angle_failure(self):
    n=10
    self.assertGreater(abs(residual_phase(n,1,.01)),1.5)
    for a in (.0001,.0002,.0005):
     leading=-math.pi*a*a*n**4/2
     self.assertLess(abs(residual_phase(n,1,a)/leading-1),1.3e-5)
 def test_fidelity_bounds_and_global_phase(self):
    c=coefficients();rot=[(n,a*cmath.exp(.73j)) for n,a in c]
    self.assertAlmostEqual(fidelity(c,rot),1,places=14)
    self.assertAlmostEqual(fidelity(c,propagate(c,1)),1,places=14)
    self.assertLess(fidelity(c,propagate(c,1,.01,True)),.9)
 def test_three_order_exact_return_at_shifted_distance(self):
    c=coefficients(profile='three');alpha=.025
    t=(1+math.sqrt(1-alpha**2))/2
    for j in range(41):self.assertLess(abs(field(propagate(c,t,alpha,True),j/41)-field(c,j/41)),1e-13)
 def test_bounded_retuning_improves_but_does_not_restore_pulse(self):
    c=coefficients();r=find_return(c,.01)
    self.assertTrue(.996<r['t']<.999)
    self.assertTrue(.95<r['fidelity']<.98)
    self.assertGreater(r['fidelity'],fidelity(c,propagate(c,1,.01,True)))
 def test_limits_and_invalid_parameters(self):
    for args in ((0,0,0),(0,1,float('nan')),(32,1,.04),(1,9,.01)):
     if args==(0,0,0):self.assertEqual(residual_phase(*args),0)
     else:
      with self.assertRaises(ValueError):residual_phase(*args)
    with self.assertRaises(ValueError):coefficients(0)
    with self.assertRaises(ValueError):replicas(1,33)

if __name__=='__main__':unittest.main(verbosity=2)
