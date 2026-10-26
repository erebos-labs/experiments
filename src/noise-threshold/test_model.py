import unittest,math,json
from model import *
class ModelTests(unittest.TestCase):
 def test_repeatability(self):
  self.assertEqual(simulate(keep=True),simulate(keep=True))
  self.assertNotEqual(simulate(seed=1),simulate(seed=2))
 def test_seed_boundaries(self):
  for seed in (0,1,4294967295):
   rng=RNG(seed)
   for _ in range(10000):self.assertTrue(math.isfinite(rng.normal()))
 def test_gaussian_sanity(self):
  rng=RNG(88);z=[rng.normal() for _ in range(100000)]
  self.assertLess(abs(sum(z)/len(z)),.012)
  self.assertLess(abs(sum(x*x for x in z)/len(z)-1),.025)
 def test_strict_threshold(self):
  self.assertEqual(exceedance(1,1,0),0)
  self.assertEqual(exceedance(1.00001,1,0),1)
  self.assertEqual(exceedance(0,0,0),0)
  self.assertEqual(exceedance(0,0,1),.5)
 def test_dead_comparator(self):
  r=simulate(.25,1,0);self.assertEqual(r['crossing_rate'],0);self.assertEqual(r['balanced_accuracy'],.5);self.assertEqual(r['phase_mi'],0)
 def test_retuning(self):
  r=simulate(.25,0,0);self.assertEqual(r['balanced_accuracy'],1);self.assertEqual(r['phase_mi'],1)
  d=detection(.25,0,0,train=20,test=20)
  self.assertEqual(d['power']['rate'],1);self.assertEqual(d['false_alarm']['rate'],0)
 def test_null_exact(self):
  for s in (0,.1,.8,4,1e6):
   r=theory(0,1,s);self.assertAlmostEqual(r['balanced_accuracy'],.5);self.assertAlmostEqual(r['phase_mi'],0);self.assertAlmostEqual(r['projection'],0)
 def test_null_bias(self):
  b=ensemble(0,1,.8,batches=128)
  self.assertGreater(b['null']['magnitude']['mean'],.01)
  self.assertGreater(b['null']['phase_mi']['mean'],0)
  self.assertLess(abs(b['null']['projection']['mean']),.005)
 def test_moderate_improvement(self):
  mid=theory(.25,1,.8);high=theory(.25,1,4)
  self.assertGreater(mid['balanced_accuracy'],.53);self.assertGreater(mid['phase_mi'],high['phase_mi']);self.assertGreater(mid['projection'],high['projection'])
 def test_huge_noise(self):
  r=theory(.25,1,1e6)
  self.assertLess(abs(r['balanced_accuracy']-.5),1e-6);self.assertLess(r['phase_mi'],1e-10);self.assertLess(abs(r['null_crossing']-.5),1e-6)
 def test_metric_peaks_differ(self):
  rows=[(s/100,theory(.25,1,s/100)) for s in range(1,301)]
  ba=max(rows,key=lambda x:x[1]['balanced_accuracy'])[0]
  mi=max(rows,key=lambda x:x[1]['phase_mi'])[0]
  self.assertGreater(ba-mi,.2)
 def test_analytic_vs_monte_carlo(self):
  expected=theory(.25,1,.8);batch=ensemble(.25,1,.8,batches=256)
  for k in ('crossing_rate','phase_hit','phase_false','balanced_accuracy','projection','mse'):
   observed=batch['signal'][k]
   self.assertLess(abs(observed['mean']-expected[k]),5*observed['se']+1e-12,k)
 def test_calibration_and_disjoint_seeds(self):
  seeds={family_seed(20261025,f,i) for f in range(1,6) for i in range(512)}
  self.assertEqual(len(seeds),5*512)
  d=detection(.25,1,.8)
  self.assertLessEqual(d['training_false'],.05)
  self.assertGreater(d['power']['rate'],d['false_alarm']['rate']+.2)
 def test_matched_null_control(self):
  d=detection(0,1,.8)
  self.assertLess(abs(d['power']['rate']-d['false_alarm']['rate']),.08)
 def test_finite_bounds(self):
  for a in (0,.25,2):
   for t in (-2,0,2):
    for s in (0,.1,4,1e6):
     r=simulate(a,t,s,n=64)
     self.assertTrue(all(math.isfinite(x) for x in r.values()))
     for k in ('crossing_rate','phase_hit','phase_false','balanced_accuracy','phase_mi'):self.assertTrue(0<=r[k]<=1)
 def test_bad_inputs(self):
  for args in ((-1,1,.8,0,256),(.2,1,-1,0,256),(.2,1,.8,-1,256),(.2,1,.8,0,65),(.2,float('nan'),.8,0,256),(.2,1,.8,0,8192)):
   with self.assertRaises(ValueError):simulate(*args)
 def test_wilson(self):
  self.assertAlmostEqual(wilson(0,128)['lo95'],0)
  self.assertGreater(wilson(0,128)['hi95'],0)
  self.assertLess(wilson(128,128)['lo95'],1)
if __name__=='__main__':unittest.main(verbosity=2)
