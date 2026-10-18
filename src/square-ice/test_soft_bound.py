import itertools,math,unittest
from soft_ice import partition
class BoundaryBound(unittest.TestCase):
 def test_boundary_bound_including_one_vertex(self):
  for n in (1,2,3):
   for q in (.1,.5,1):
    values=[partition(n,q,t,b,l,r) for t in range(1<<n) for b in range(1<<n) for l,r in itertools.product((0,1),repeat=2)]
    observed=math.log(max(values)/min(values))
    self.assertLessEqual(observed,max(1,4*n-4)*math.log(1/q)+1e-12)
    if n==1 and q<1:self.assertGreater(observed,0)
if __name__=='__main__':unittest.main(verbosity=2)
