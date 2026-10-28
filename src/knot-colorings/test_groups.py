import itertools
import json
import unittest
from pathlib import Path
import groups as g
import involutions as iq
import model as m

DATA=json.loads(Path(__file__).with_name('source_data.json').read_text())


class GroupColoringChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.G=g.psl(7);cls.identity=g.canonical((1,0,0,1),7)
        cls.base=g.canonical((0,1,-1,1),7);cls.Q=g.conjugacy_class(cls.G,cls.base,7)
        cls.f,cls.b=g.tables(cls.Q,7)

    def test_group_and_class(self):
        self.assertEqual([(p,len(g.psl(p))) for p in (3,5,7)],[(3,12),(5,60),(7,168)])
        self.assertEqual(len(self.Q),56)
        self.assertEqual(g.mul(g.mul(self.base,self.base,7),self.base,7),self.identity)
        self.assertNotEqual(self.base,self.identity)
        values=set(self.G)
        for a in self.G:
            self.assertEqual(g.mul(a,g.inverse(a,7),7),self.identity)
            self.assertEqual(g.mul(a,self.identity,7),a)
            self.assertEqual(g.canonical(tuple(-x for x in a),7),a)
            self.assertEqual((a[0]*a[3]-a[1]*a[2])%7,1)
            for b in self.G:
                self.assertIn(g.mul(a,b,7),values)

    def test_quandle_axioms(self):
        q=len(self.Q)
        for x in range(q):
            self.assertEqual(self.f[x][x],x)
        for x,y in itertools.product(range(q),repeat=2):
            self.assertEqual(self.b[self.f[x][y]][y],x)
            self.assertEqual(self.f[self.b[x][y]][y],x)
        for x,y,z in itertools.product(range(q),repeat=3):
            self.assertEqual(self.f[self.f[x][y]][z],self.f[self.f[x][z]][self.f[y][z]])

    def test_independent_source_encodings(self):
        for name,pd in DATA['pd'].items():
            events={};edges=2*len(pd)
            for k,(a,b,c,d) in enumerate(pd,1):
                events[a]=-k
                events[b if b % edges+1 == d else d]=k
            self.assertEqual([events[i] for i in range(1,edges+1)],DATA['gauss'][name])
            equations,n,_=g.pd_constraints(pd)
            a=[[0]*n for _ in equations]
            for row,(o,u,v,sign) in zip(a,equations):
                row[o]+=2;row[u]-=1;row[v]-=1
            independent,_=m.gauss_matrix(DATA['gauss'][name])
            self.assertEqual(abs(m.determinant(m.minor(a))),abs(m.determinant(m.minor(independent))))

    def test_pd_fox_against_gauss_enumerator(self):
        for q in (3,5,9,15):
            table=iq.fox_table(q)
            for name,pd in DATA['pd'].items():
                actual=g.count_fixed(pd,table,table)
                reference=iq.solutions(DATA['gauss'][name],table)
                self.assertEqual(q*actual['normalized_count'],len(reference['solutions']),(name,q))

    def test_published_order_three_counts(self):
        for name,expected in (('conway',13),('kinoshita_terasaka',7)):
            result=g.count_fixed(DATA['pd'][name],self.f,self.b)
            self.assertEqual(result['normalized_count'],expected)
            self.assertEqual(result['assignments'],3136)
            self.assertEqual(len(result['seeds']),3)
            self.assertEqual(sum(len(set(x))==1 for x in result['solutions']),1)

    def test_full_arc_enumeration_reference(self):
        equations,n,_=g.pd_constraints(DATA['pd']['trefoil'])
        self.assertEqual(n,3)
        count=sum(all(x[v]==(self.f if sign>0 else self.b)[x[u]][x[o]] for o,u,v,sign in equations) for x in itertools.product(range(56),repeat=n))
        fixed=g.count_fixed(DATA['pd']['trefoil'],self.f,self.b)
        self.assertEqual(count,392)
        self.assertEqual(count,56*fixed['normalized_count'])

    def test_witnesses_via_direct_matrices_and_conjugation(self):
        pd=DATA['pd']['conway'];result=g.count_fixed(pd,self.f,self.b)
        equations,n,edges=g.pd_constraints(pd);all_witnesses=set()
        first_seed=result['seeds'][0]
        for target in self.Q:
            # Find one conjugation carrying fixed color Q[0] to each target.
            conjugator=next(h for h in self.G if g.mul(g.mul(g.inverse(h,7),self.Q[0],7),h,7)==target)
            for solution in result['solutions']:
                values=tuple(g.mul(g.mul(g.inverse(conjugator,7),self.Q[i],7),conjugator,7) for i in solution)
                self.assertEqual(values[first_seed],target)
                for (a,b,c,d),(_,_,_,sign) in zip(pd,equations):
                    over=values[edges[b]];under=values[edges[a]]
                    self.assertEqual(values[edges[d]],over)
                    expected=g.mul(g.mul(g.inverse(over,7),under,7),over,7) if sign>0 else g.mul(g.mul(over,under,7),g.inverse(over,7),7)
                    self.assertEqual(values[edges[c]],expected)
                all_witnesses.add(values)
        self.assertEqual(len(all_witnesses),728)
        self.assertEqual(sum(len(set(x))==1 for x in all_witnesses),56)

    def test_involutory_null_reproduction(self):
        Q=g.conjugacy_class(g.psl(5),g.canonical((0,1,-1,0),5),5)
        self.assertEqual(len(Q),15)
        f,b=g.tables(Q,5);self.assertEqual(f,b);self.assertTrue(iq.check_axioms(f))
        for name,expected in (('trefoil',75),('figure8',135),('conway',15)):
            actual=g.count_fixed(DATA['pd'][name],f,b)
            self.assertEqual(15*actual['normalized_count'],expected)

    def test_same_group_different_label_classes(self):
        for order,raw,class_size,expected in ((2,(0,1,-1,0),21,1),(7,(1,1,0,1),24,15)):
            base=g.canonical(raw,7);Q=g.conjugacy_class(self.G,base,7);f,b=g.tables(Q,7)
            self.assertEqual(len(Q),class_size)
            value=self.identity
            for _ in range(order):value=g.mul(value,base,7)
            self.assertEqual(value,self.identity)
            self.assertNotEqual(base,self.identity)
            self.assertEqual(f==b,order==2)
            for name in ('conway','kinoshita_terasaka'):
                r=g.count_fixed(DATA['pd'][name],f,b)
                self.assertEqual(r['normalized_count'],expected)
                self.assertEqual(r['assignments'],class_size**2)

    def test_boundaries(self):
        for p in (2,9,11):
            with self.assertRaises(ValueError):g.psl(p)
        for pd in ([],[[1,2,3]],[[1,2,3,4]],[[1,2,1,2]]):
            with self.assertRaises(ValueError):g.pd_constraints(pd)
        with self.assertRaises(ValueError):g.count_fixed(DATA['pd']['conway'],self.f,self.b,fixed=-1)


if __name__=='__main__':unittest.main(verbosity=2)
