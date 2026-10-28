import itertools
import math
import random
import unittest
from fractions import Fraction
import model as m


def rational_det(a):
    a = [list(map(Fraction,row)) for row in a]; out = Fraction(1)
    for j in range(len(a)):
        k = next((i for i in range(j,len(a)) if a[i][j]),None)
        if k is None:
            return 0
        if k != j:
            a[j],a[k] = a[k],a[j]; out = -out
        p = a[j][j]; out *= p
        for i in range(j+1,len(a)):
            scale = a[i][j]/p
            a[i] = [x-scale*y for x,y in zip(a[i],a[j])]
    assert out.denominator == 1
    return int(out)


class ColoringChecks(unittest.TestCase):
    def test_reference_counts(self):
        expected = {'unknot':[3,5,7,9,15], 'trefoil':[9,5,7,27,45],
                    'figure8':[3,25,7,9,75], 'nine_twists':[9,5,7,81,45],
                    'double_trefoil':[27,5,7,81,135]}
        for key,v in m.PRESETS.items():
            with self.subTest(key=key):
                self.assertEqual(len(m.components(v['strands'],v['word'])),1)
                self.assertEqual([len(m.enumerate_colorings(v['strands'],v['word'],q)) for q in (3,5,7,9,15)],expected[key])

    def test_two_strand_closed_formula(self):
        for twists in range(-11,12):
            word = [1 if twists > 0 else -1]*abs(twists)
            for q in range(2,16):
                with self.subTest(twists=twists,q=q):
                    self.assertEqual(len(m.enumerate_colorings(2,word,q)),q*math.gcd(q,abs(twists)))

    def test_connected_sum_formula(self):
        for q in range(2,16):
            self.assertEqual(len(m.enumerate_colorings(3,[1,1,1,2,2,2],q)),q*math.gcd(q,3)**2)

    def test_small_braid_words_three_methods(self):
        # Exhaustive universe: 3 strands, every signed word up to length 5.
        words = (w for length in range(6) for w in itertools.product((-2,-1,1,2),repeat=length))
        for word in words:
            for q in (2,3,5):
                count = len(m.enumerate_colorings(3,word,q))
                a,n = m.braid_arc_matrix(3,word)
                self.assertEqual(count,m.linear_count(3,word,q),(word,q,'transfer'))
                self.assertEqual(count,q**(n-m.rank_mod(a,q,columns=n)),(word,q,'arcs'))

    def test_seeded_four_strand_cases(self):
        rng = random.Random(27102026)
        for case in range(60):
            n = rng.randint(2,4); length = rng.randint(0,14)
            word = [rng.choice((-1,1))*rng.randrange(1,n) for _ in range(length)]
            q = rng.choice((2,3,5,7))
            count = len(m.enumerate_colorings(n,word,q))
            a,arcs = m.braid_arc_matrix(n,word)
            self.assertEqual(count,m.linear_count(n,word,q),(case,word,q))
            self.assertEqual(count,q**(arcs-m.rank_mod(a,q,columns=arcs)),(case,word,q))

    def test_canceling_pair_map(self):
        for q in range(2,16):
            for colors in itertools.product(range(q),repeat=2):
                self.assertEqual(m.propagate(colors,[1,-1],q),colors)
                self.assertEqual(m.propagate(colors,[-1,1],q),colors)

    def test_braid_relation_map(self):
        # Type III: exact input-output equality, stronger than matching counts.
        for q in (2,3,5,7,9):
            for colors in itertools.product(range(q),repeat=3):
                self.assertEqual(m.propagate(colors,[1,2,1],q),m.propagate(colors,[2,1,2],q))
                self.assertEqual(m.propagate(colors,[-1,-2,-1],q),m.propagate(colors,[-2,-1,-2],q))

    def test_closure_transformations(self):
        for v in m.PRESETS.values():
            n,w = v['strands'],v['word']
            for q in (3,5,9):
                count = len(m.enumerate_colorings(n,w,q))
                self.assertEqual(count,len(m.enumerate_colorings(n,w+[1,-1],q)))
                self.assertEqual(count,len(m.enumerate_colorings(n,w[1:]+w[:1],q)))
                self.assertEqual(count,len(m.enumerate_colorings(n,[-i for i in w],q)))
                if n < 4:
                    for sign in (-1,1):
                        self.assertEqual(count,len(m.enumerate_colorings(n+1,w+[sign*n],q)))

    def test_crossing_change_can_change_answer(self):
        self.assertEqual(len(m.enumerate_colorings(2,[1,1,1],3)),9)
        self.assertEqual(len(m.enumerate_colorings(2,[1,-1,1],3)),3)

    def test_empty_braid_is_a_link(self):
        for n in range(1,5):
            self.assertEqual(len(m.components(n,[])),n)
            self.assertEqual(len(m.enumerate_colorings(n,[],3)),3**n)

    def test_all_monochrome_solutions_present(self):
        for v in m.PRESETS.values():
            n,w = v['strands'],v['word']
            for q in (3,5,9):
                values=m.enumerate_colorings(n,w,q)
                self.assertEqual(sum(len(set(x)) == 1 for x in values),q)

    def test_gauss_references(self):
        for key,det in (('trefoil',3),('figure8',5),('conway',1)):
            a,n = m.gauss_matrix(m.GAUSS[key])
            self.assertTrue(all(sum(row) == 0 for row in a))
            self.assertEqual(abs(m.determinant(m.minor(a))),det)
            self.assertEqual(m.determinant(m.minor(a)),rational_det(m.minor(a)))
            for q in (2,3,5,7,11,13,17,19,23,29,31):
                count = q**(n-m.rank_mod(a,q))
                if key == 'conway':
                    self.assertEqual(count,q)
                else:
                    v=m.PRESETS[key]
                    self.assertEqual(count,m.linear_count(v['strands'],v['word'],q))

    def test_gauss_basepoint_and_direction(self):
        for code in m.GAUSS.values():
            a,n=m.gauss_matrix(code); expected=abs(m.determinant(m.minor(a)))
            for cut in range(len(code)):
                for changed in (code[cut:]+code[:cut],list(reversed(code[cut:]+code[:cut]))):
                    b,k=m.gauss_matrix(changed)
                    self.assertEqual(abs(m.determinant(m.minor(b))),expected)
                    self.assertEqual(k,n)

    def test_bareiss_against_rational(self):
        rng=random.Random(1962)
        for n in range(1,8):
            for case in range(20):
                a=[[rng.randint(-5,5) for _ in range(n)] for _ in range(n)]
                self.assertEqual(m.determinant(a),rational_det(a),(n,case,a))
        self.assertEqual(m.determinant([]),1)
        self.assertEqual(m.determinant([[0,1],[1,0]]),-1)

    def test_composite_is_not_a_field(self):
        for q in (4,6,8,9,10,12,15):
            with self.assertRaisesRegex(ValueError,'prime'):
                m.linear_count(2,[1,1,1],q)
        # Explicit counterexample to the overbroad "n divides determinant" claim.
        self.assertEqual(len(m.enumerate_colorings(2,[1,1,1],9)),27)
        self.assertNotEqual(3 % 9,0)

    def test_invalid_and_budget_inputs(self):
        for n,w in ((0,[]),(5,[]),(2,[0]),(2,[2]),(2,[1.0]),(2,[True]),(2,[1]*17)):
            with self.assertRaises(ValueError):
                m.enumerate_colorings(n,w,3)
        for q in (0,1,32,3.0,True):
            with self.assertRaises(ValueError):
                m.enumerate_colorings(2,[1],q)
        with self.assertRaisesRegex(ValueError,'budget'):
            m.enumerate_colorings(4,[1],31)
        for code in ([1,1],[-1,-1],[1,0],[1,-1,2], [True,-1]):
            with self.assertRaises(ValueError):
                m.gauss_matrix(code)


if __name__ == '__main__':
    unittest.main(verbosity=2)
