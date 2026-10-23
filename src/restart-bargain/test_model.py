"""Independent transition-matrix and exact-rational checks for model.py."""
import math
import random
import unittest
from fractions import Fraction as F
from model import mean_time, moments, distribution, quantile, validate


def dense_solve(a,b):
    """Pivoted Gauss-Jordan, independent of the tridiagonal solver."""
    a=[list(row)+[v] for row,v in zip(a,b)]
    for i in range(len(b)):
        k=max(range(i,len(b)),key=lambda j:abs(a[j][i]))
        a[i],a[k]=a[k],a[i]
        pivot=a[i][i]
        a[i]=[x/pivot for x in a[i]]
        for j in range(len(b)):
            if j==i: continue
            factor=a[j][i]
            a[j]=[x-factor*y for x,y in zip(a[j],a[i])]
    return [row[-1] for row in a]


def transition(L,s,r,c=0):
    z=type(r)(0); one=type(r)(1)
    q=[[z]*(L+c) for _ in range(L+c)]
    for i in range(L):
        if i>0: q[i][i-1]+=(one-r)/2
        q[i][min(i+1,L-1)]+=(one-r)/2
        q[i][L+c-1 if c else s-1]+=r
    for k in range(c):
        q[L+k][L+k-1 if k else s-1]=one
    return q


def dense_mean(L,s,r,c=0):
    q=transition(L,s,r,c); one=type(r)(1); z=type(r)(0)
    return dense_solve([[int(i==j)-v for j,v in enumerate(row)] for i,row in enumerate(q)], [one]*(L+c))[s-1]


def exact_survival(L,s,r,H):
    q=transition(L,s,r); p=[F(0)]*L;p[s-1]=F(1)
    out=[F(1)]
    for _ in range(H):
        p=[sum(p[i]*q[i][j] for i in range(L)) for j in range(L)]
        out.append(sum(p))
    return out


class ModelTests(unittest.TestCase):
    def test_baseline_closed_form(self):
        for L in range(1,41):
            for s in range(1,L+1):
                self.assertAlmostEqual(mean_time(L,s,0),s*(2*L+1-s),delta=1e-8)

    def test_dense_means_and_reset_delay(self):
        rng=random.Random(2301)
        for _ in range(150):
            L=rng.randrange(1,15);s=rng.randrange(1,L+1)
            r=rng.choice([0,.0001,.005,.03,.1,.25]);c=rng.randrange(0,6)
            ref=dense_mean(L,s,r,c)
            self.assertAlmostEqual(mean_time(L,s,r,c)/ref,1,delta=2e-10)

    def test_dense_second_moments(self):
        for L,s,r in [(1,1,0),(1,1,.25),(6,3,.03),(10,5,.01),(20,10,.1)]:
            q=transition(L,s,r)
            a=[[int(i==j)-v for j,v in enumerate(row)] for i,row in enumerate(q)]
            m=dense_solve(a,[1.]*L)
            v=dense_solve(a,[2*x-1 for x in m])
            actual=moments(L,s,r)
            self.assertAlmostEqual(actual[0]/m[s-1],1,delta=1e-9)
            self.assertAlmostEqual(actual[1]/v[s-1],1,delta=1e-9)

    def test_geometric_one_site(self):
        for r in [0,.01,.25,.9]:
            for c in [0,1,5]:
                self.assertAlmostEqual(mean_time(1,1,r,c),2*(1+r*c)/(1-r),delta=1e-10)
            S=distribution(1,1,r,20)
            for t in range(21): self.assertAlmostEqual(S[t],((1+r)/2)**t,delta=1e-14)

    def test_rational_counterexample(self):
        old=dense_mean(10,5,F(0));new=dense_mean(10,5,F(1,32))
        self.assertEqual(old,80); self.assertLess(new,old)
        a=exact_survival(10,5,F(0),55);b=exact_survival(10,5,F(1,32),55)
        self.assertGreater(a[48],F(1,2));self.assertLessEqual(a[49],F(1,2))
        self.assertGreater(b[50],F(1,2));self.assertLessEqual(b[51],F(1,2))
        self.assertEqual(quantile(distribution(10,5,0,55),.5),49)
        self.assertEqual(quantile(distribution(10,5,1/32,55),.5),51)
        self.assertAlmostEqual(mean_time(10,5,1/32),float(new),delta=1e-10)

    def test_exact_distribution_with_cost(self):
        for L,s,r,c in [(2,1,F(1,4),3),(6,3,F(1,16),2),(10,5,F(1,32),0)]:
            q=transition(L,s,r,c);p=[F(0)]*(L+c);p[s-1]=F(1)
            actual=distribution(L,s,float(r),70,c)
            for t in range(71):
                self.assertAlmostEqual(actual[t],float(sum(p)),delta=5e-14)
                p=[sum(p[i]*q[i][j] for i in range(L+c)) for j in range(L+c)]

    def test_mean_tail_consistency(self):
        for L,s,r,c in [(8,4,0,0),(8,4,.02,3),(40,20,.00168,0)]:
            S=distribution(L,s,r,40000,c)
            # E[T]=sum_{t=0}^infinity S(t). The remaining tail is small here.
            self.assertAlmostEqual(sum(S[:-1]),mean_time(L,s,r,c),delta=1e-7)

    def test_local_derivative_with_cost(self):
        for s in [5,10,20,22,23,30,40]:
            m,b=moments(40,s,0);var=b-m*m
            for c in [0,10,80]:
                theory=(m*m+m-var)/2+c*m
                h=1e-8
                observed=(mean_time(40,s,h,c)-m)/h
                self.assertAlmostEqual(observed,theory,delta=max(2,abs(theory)*.0001))

    def test_mean_improves_median_worsens(self):
        self.assertLess(mean_time(40,20,.00168),mean_time(40,20,0))
        self.assertEqual(quantile(distribution(40,20,0,10000),.5),774)
        self.assertEqual(quantile(distribution(40,20,.00168,10000),.5),785)

    def test_negative_and_limit_cases(self):
        # From the furthest site a reset only throws away progress.
        for r in [.0001,.001,.01,.1]:
            self.assertGreater(mean_time(40,40,r),mean_time(40,40,0))
        self.assertTrue(math.isinf(mean_time(40,20,1)))
        self.assertEqual(distribution(40,20,1,100,3),[1.]*101)
        self.assertIsNone(quantile(distribution(40,40,.25,100),.9))
        self.assertEqual(distribution(40,20,.01,0),[1.])

    def test_survival_bounds_and_monotonicity(self):
        for s,r,c in [(1,0,0),(20,.00168,0),(40,.25,10)]:
            S=distribution(40,s,r,10000,c)
            self.assertTrue(all(-1e-12<=p<=1+1e-12 for p in S))
            self.assertTrue(all(a+1e-13>=b for a,b in zip(S,S[1:])))

    def test_underflow_is_not_mathematical_infinity(self):
        with self.assertRaises(ArithmeticError):mean_time(200,200,.9999)
        with self.assertRaises(ArithmeticError):moments(200,200,.9999)

    def test_input_validation(self):
        for args in [(0,1,0,0),(40,0,0,0),(40,41,0,0),(40,1,-.01,0),(40,1,1.01,0),(40,1,float('nan'),0),(40,1,.1,-1),(40,1,.1,1.5)]:
            with self.assertRaises(ValueError):validate(*args)
        for H in [-1,1.5,200001]:
            with self.assertRaises(ValueError):distribution(40,20,.1,H)

if __name__=='__main__':unittest.main(verbosity=2)
