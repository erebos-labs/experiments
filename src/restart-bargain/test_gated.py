import unittest
import random
from model import mean_time as blind_mean, distribution as blind_S
from gated import mean_time,distribution
from test_model import transition,dense_solve


def dense_gated(L,s,r,c):
    q=transition(L,s,r,c)
    for i in range(s):
        # Sites 1..s never reset; rebuild just these active rows.
        q[i]=[0.]*(L+c)
        if i>0:q[i][i-1]=.5
        q[i][min(L-1,i+1)]+=.5
    a=[[int(i==j)-v for j,v in enumerate(row)] for i,row in enumerate(q)]
    return dense_solve(a,[1.]*(L+c))[s-1]


class GatedTests(unittest.TestCase):
    def test_independent_dense_solver(self):
        rng=random.Random(2302)
        for _ in range(200):
            L=rng.randrange(1,20);s=rng.randrange(1,L+1);r=rng.choice([0,.001,.1,.5,1]);c=rng.randrange(0,6)
            ref=dense_gated(L,s,r,c)
            self.assertAlmostEqual(mean_time(L,s,r,c)/ref,1,delta=2e-12)

    def test_zero_reset_and_far_wall(self):
        for L in range(1,30):
            for s in [1,max(1,L//2),L]:
                self.assertAlmostEqual(mean_time(L,s,0),blind_mean(L,s,0),delta=1e-9)
            for r in [.01,.5,1]:
                self.assertAlmostEqual(mean_time(L,L,r),blind_mean(L,L,0),delta=1e-9)

    def test_certain_reset_closed_form(self):
        for L in [2,10,40,100]:
            for s in [1,max(1,L//2),L-1]:
                for c in [0,5,80]:
                    self.assertAlmostEqual(mean_time(L,s,1,c),s*(s+2+c),delta=1e-8)

    def test_stochastic_dominance_no_cost(self):
        for L,s,r in [(10,1,.2),(10,5,.01),(10,9,1),(40,20,.00168),(40,30,.1),(40,40,1)]:
            base=blind_S(L,s,0,10000)
            gate=distribution(L,s,r,10000)
            self.assertTrue(all(a<=b+2e-12 for a,b in zip(gate,base)))

    def test_cost_breaks_dominance(self):
        self.assertGreater(mean_time(40,20,1,80),blind_mean(40,20,0))
        base=blind_S(40,20,0,1000)
        gate=distribution(40,20,1,1000,80)
        self.assertTrue(any(a>b+.01 for a,b in zip(gate,base)))

    def test_distribution_mean_with_delay(self):
        for L,s,r,c in [(10,5,.1,0),(10,5,.2,3),(10,5,1,5)]:
            S=distribution(L,s,r,5000,c)
            self.assertAlmostEqual(sum(S[:-1]),mean_time(L,s,r,c),delta=1e-8)

if __name__=='__main__':unittest.main(verbosity=2)
