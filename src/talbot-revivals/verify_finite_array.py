import unittest,json
from finite_array import *
class FiniteArrayChecks(unittest.TestCase):
 def test_fft_against_direct_dft_and_inverse(self):
  a=[complex(math.sin(j*.73),math.cos(j*.37)) for j in range(16)]
  ref=[sum(v*cmath.exp(-2j*math.pi*j*k/16) for j,v in enumerate(a)) for k in range(16)]
  self.assertLess(max(abs(x-y) for x,y in zip(fft(a),ref)),1e-13)
  self.assertLess(max(abs(x-y) for x,y in zip(a,fft(fft(a),True))),1e-14)
 def test_fresnel_initial_condition(self):
  for n in (5,17):
   for x in (0,.13,n//2+.2):self.assertLess(abs(fresnel(x,n,0)-initial(x,n)),1e-14)
 def test_single_gaussian_width(self):
  q=SIGMA**2+1j/math.pi;s=abs(q)/SIGMA
  self.assertAlmostEqual(abs(fresnel(s,1))**2/abs(fresnel(0,1))**2,math.exp(-1),places=13)
 def test_exact_transfer_direct_sqrt(self):
  for f in (.1,2,7,30):
   direct=cmath.exp(1j*4*math.pi/.01**2*(math.sqrt(1-(.01*f)**2)-1))
   self.assertLess(abs(transfer(f,exact=True)-direct),1e-11)
 def test_window_metric_scaling_trap(self):
  ref=[complex(initial(-.5+j/128,1)) for j in range(128)]
  m=metrics([v*.5 for v in ref],ref)
  self.assertAlmostEqual(m['field_overlap'],1,places=13)
  self.assertAlmostEqual(m['centered_intensity_shape_cosine'],1,places=13)
  self.assertAlmostEqual(m['window_mean_I'],.25,places=13)
  self.assertAlmostEqual(m['RMS_contrast_ratio'],.25,places=13)
 def test_saved_domain_and_resolution_controls(self):
  d=json.loads((ART/'finite-array-results.json').read_text())
  bad=[v for v in d['convergence'] if v['kind']=='padding_vs_Fresnel' and v['domain']==32]
  self.assertGreater(max(v['max_field_error'] for v in bad),.09)
  good=[v for v in d['convergence'] if v['kind']!='padding_vs_Fresnel']
  self.assertLess(max(v['max_field_error'] for v in good),1e-8)
 def test_center_improves_but_edge_saturates(self):
  d=json.loads((ART/'finite-array-results.json').read_text());rows=d['rows']
  def get(n,w):return next(v for v in rows if v['count']==n and v['window']==w and v['model']=='paraxial')
  fs=[get(n,'center')['field_overlap'] for n in (5,9,17,33,65)]
  self.assertEqual(fs,sorted(fs));self.assertGreater(fs[-1],.999999)
  self.assertLess(abs(get(65,'edge')['window_mean_I']-get(33,'edge')['window_mean_I']),1e-6)
  self.assertLess(get(65,'edge')['RMS_contrast_ratio'],.34)
 def test_edge_center_symmetry_reference(self):
  pred=(AMPLITUDE+fresnel(0,1))/2
  self.assertLess(abs(fresnel(32,65)-pred),1e-10)
  self.assertAlmostEqual(abs(pred)**2/AMPLITUDE**2,.276385663883657,places=13)
 def test_analytic_central_tail_bound(self):
  d=json.loads((ART/'finite-array-results.json').read_text())
  for row in d['paraxial_central_tail_bounds']:self.assertLessEqual(row['max_central_window_field_error'],row['analytic_envelope_upper_bound'])
  self.assertLess(d['paraxial_central_tail_bounds'][-1]['analytic_envelope_upper_bound'],.00041)
 def test_exact_large_array_matches_periodic_in_center(self):
  d=json.loads((ART/'finite-array-results.json').read_text());u=[complex(re,im) for x,re,im in d['profiles']['65_True_center']]
  periodic=propagate(coefficients(.04,32),1,.01,True)
  err=max(abs(v-field(periodic,-.5+j/128)) for j,v in enumerate(u))
  self.assertLess(err,5e-4);print('finite65_vs_infinite_periodic_exact_max_center_field_error',err)
if __name__=='__main__':unittest.main(verbosity=2)
