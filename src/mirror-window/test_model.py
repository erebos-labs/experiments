import unittest, random, math
from dataclasses import replace
from model import *
from perturbation import certificate

class OpticsChecks(unittest.TestCase):
    def test_empty_equal_ports(self):
        for wavelength in [450,600,800]:
            s=solve([],wavelength)
            self.assertEqual(s['T'],1)
            self.assertEqual(s['R'],0)

    def test_fresnel_unequal_ports(self):
        s=solve([],600,1,1.5)
        self.assertAlmostEqual(s['R'],.04,15)
        self.assertAlmostEqual(s['T'],.96,15)

    def test_uniform_medium(self):
        layers=[Layer(1.45,20),Layer(1.45,100),Layer(1.45,77)]
        for w in [480,601,720]:
            s=solve(layers,w,1.45,1.45)
            self.assertLess(s['R'],1e-29)
            self.assertAlmostEqual(s['T'],1,14)

    def test_single_slab_airy(self):
        for n in [1.2,1.45,2.3]:
            for w in [450,600,777]:
                d=137
                F=((n*n-1)/(2*n))**2
                exact=1/(1+F*math.sin(2*math.pi*n*d/w)**2)
                self.assertAlmostEqual(solve([Layer(n,d)],w)['T'],exact,14)

    def test_halfwave_slab(self):
        for n in [1.2,1.45,2.3]:
            s=solve([Layer(n,600/(2*n))],600)
            self.assertLess(s['R'],1e-29)

    def test_quarterwave_closed_form(self):
        for pairs in range(1,9):
            ordinary,cavity=stacks(pairs)
            N=2*pairs
            q=(NH/NL)**(2*N)
            exact=((q-1)/(q+1))**2
            self.assertAlmostEqual(solve(ordinary,600)['R'],exact,14)

    def test_cavity_identity(self):
        for m in range(1,9):
            b=stacks(m)[1]
            a,bb,c,d=matrix(b,600)
            self.assertAlmostEqual(a,1,14)
            self.assertAlmostEqual(d,1,14)
            self.assertLess(abs(bb),3e-12)
            self.assertLess(abs(c),3e-12)
            self.assertLess(solve(b,600)['R'],1e-23)

    def test_same_layer_inventory(self):
        for kind in ['thickness','index']:
            for mode in ['independent','mirrored','common']:
                a,b=stacks(8,.08,mode,20261024,kind=kind)
                self.assertEqual(sorted(a,key=lambda x:x.token),sorted(b,key=lambda x:x.token))
                self.assertAlmostEqual(sum(x.d for x in a),sum(x.d for x in b),10)
                self.assertEqual(''.join(x.label for x in a),'HL'*16)
                self.assertEqual(''.join(x.label for x in b),'HL'*8+'LH'*8)

    def test_mirrored_structure(self):
        for kind in ['thickness','index']:
            b=stacks(6,.08,'mirrored',1729,kind=kind)[1]
            self.assertEqual([(x.n,x.d) for x in b],[(x.n,x.d) for x in reversed(b)])
            self.assertLess(peak(b)['R'],1e-22)

    def test_common_thickness_scaling(self):
        for m in [2,6,8]:
            b=stacks(m,.08,'common',19)[1]
            exact=600*(1+.08*uniform_sequence(19,1)[0])
            p=peak(b)
            self.assertAlmostEqual(p['wavelength'],exact,8)
            self.assertLess(p['R'],1e-22)

    def test_independent_fresnel_recursion(self):
        rng=random.Random(20261024)
        max_error=0
        for _ in range(400):
            layers=[Layer(rng.uniform(1,2.6),rng.uniform(0,220)) for _ in range(rng.randrange(33))]
            w=rng.uniform(450,800); n0=rng.uniform(1,1.6);ns=rng.uniform(1,1.6)
            a=solve(layers,w,n0,ns);b=fresnel_reference(layers,w,n0,ns)
            max_error=max(max_error,abs(a['T']-b['T']),abs(a['R']-b['R']))
            self.assertLess(abs(a['t']-b['t']),2e-11)
            self.assertLess(abs(a['r']-b['r']),2e-11)
        self.assertLess(max_error,2e-11)

    def test_energy_balance(self):
        rng=random.Random(128)
        for _ in range(300):
            a,b=stacks(rng.randint(1,8),rng.random()*.08,rng.choice(['independent','mirrored','common']),rng.getrandbits(32),kind=rng.choice(['thickness','index']))
            for layers in [a,b]:
                s=solve(layers,rng.uniform(450,800),1,rng.choice([1,1.5]))
                self.assertLess(s['balance_error'],3e-12)
                self.assertGreaterEqual(s['R'],0)
                self.assertGreaterEqual(s['T'],0)

    def test_reciprocity_unequal_ports(self):
        b=stacks(6,.08,seed=777,kind='index')[1]
        for w in [450,584.7,600,638.1,800]:
            f=solve(b,w,1,1.5)
            r=solve(list(reversed(b)),w,1.5,1)
            self.assertAlmostEqual(f['T'],r['T'],12)
            self.assertAlmostEqual(f['R'],r['R'],12)

    def test_zero_thickness_layer(self):
        a=stacks(4,.04,seed=900)[1]
        b=a[:7]+[Layer(1.9,0)]+a[7:]
        for w in [480,600,720]:
            self.assertAlmostEqual(solve(a,w)['T'],solve(b,w)['T'],14)

    def test_split_layer(self):
        a=stacks(4,.04,seed=900)[1]
        x=a[5]
        b=a[:5]+[replace(x,d=x.d*.31),replace(x,d=x.d*.69)]+a[6:]
        for w in [480,600,720]:
            self.assertAlmostEqual(solve(a,w)['T'],solve(b,w)['T'],13)

    def test_length_scale_invariance(self):
        b=stacks(6,.08,seed=55)[1]
        for factor in [.2,3,1000]:
            scaled=[replace(x,d=x.d*factor) for x in b]
            self.assertAlmostEqual(solve(b,603)['T'],solve(scaled,603*factor)['T'],12)

    def test_field_boundaries_and_flux(self):
        for m,e,kind,ns in [(4,0,'thickness',1),(8,.08,'thickness',1),(6,.05,'index',1.5)]:
            b=stacks(m,e,seed=1729,kind=kind)[1]
            w=peak(b,ns=ns)['wavelength']
            s=solve(b,w,ns=ns)
            f=field_profile(b,w,ns=ns,samples_per_layer=12)
            self.assertLess(abs(f[0]['E']-(1+s['r'])),3e-10)
            self.assertLess(abs(f[0]['H']-(1-s['r'])),3e-10)
            self.assertLess(abs(f[-1]['E']-s['t']),3e-12)
            self.assertLess(abs(f[-1]['H']-ns*s['t']),3e-12)
            self.assertLess(max(abs(x['flux']-s['T']) for x in f),1e-10)
            for j in range(len(b)-1):
                left=f[(j+1)*13-1];right=f[(j+1)*13]
                self.assertLess(abs(left['E']-right['E']),1e-10)
                self.assertLess(abs(left['H']-right['H']),1e-10)

    def test_peak_resolution(self):
        for kind in ['thickness','index']:
            b=stacks(8,.08,seed=50,kind=kind)[1]
            results=[peak(b,intervals=n) for n in [150,300,600,1200,2400]]
            for p in results:
                self.assertFalse(p['at_boundary'])
                self.assertAlmostEqual(p['wavelength'],results[-1]['wavelength'],6)
                self.assertAlmostEqual(p['T'],results[-1]['T'],10)

    def test_fixed_versus_retuned(self):
        b=stacks(6,.05,seed=7)[1]
        self.assertLess(solve(b,600)['T'],.006)
        self.assertGreater(peak(b)['T'],.9999)

    def test_unequal_surroundings_control(self):
        b=stacks(6)[1]
        s=solve(b,600,1,1.5)
        self.assertAlmostEqual(s['T'],.96,14)
        self.assertAlmostEqual(s['R'],.04,14)

    def test_sensitivity_normalization(self):
        for m in range(1,9):
            weights=sensitivity(m)
            self.assertAlmostEqual(sum(weights),1,14)
            self.assertTrue(all(w>0 for w in weights))
            for a,b in zip(weights,reversed(weights)):self.assertAlmostEqual(a,b,14)

    def test_sensitivity_numerical(self):
        b=stacks(4)[1];weights=sensitivity(4)
        for j in [0,3,7,8,15]:
            e=1e-5
            changed=b.copy();changed[j]=replace(b[j],d=b[j].d*(1+e))
            p=peak(changed)
            self.assertAlmostEqual((p['wavelength']-600)/e,600*weights[j],4)

    def test_taylor_powers_and_coefficients(self):
        for kind,power in [('thickness',4),('index',2)]:
            c=certificate(kind=kind)
            self.assertEqual(c['leading_reflectance_power'],power)
            rs=[]
            for e in [.0005,.001]:
                p=peak(stacks(6,e,seed=7,kind=kind)[1])
                predicted=c['leading_reflectance_coefficient']*e**power
                self.assertLess(abs(p['R']/predicted-1),.002)
                rs.append(p['R'])
            slope=math.log(rs[1]/rs[0])/math.log(2)
            self.assertLess(abs(slope-power),.003)
            self.assertLess(abs(c['numerator_imag_coefficients'][1]),1e-10)

    def test_fwhm_crossings(self):
        b=stacks(8)[1];p=peak(b)
        w=fwhm(b,p['wavelength'],p['T'])
        self.assertGreater(w,.12);self.assertLess(w,.123)
        # Wavelength line shape need not be exactly symmetric.
        self.assertLess(abs(solve(b,600+w/2)['T']-.5),.0002)
        self.assertLess(abs(solve(b,600-w/2)['T']-.5),.0002)

    def test_gaussian_narrow_and_broad(self):
        b=stacks(8)[1];p=peak(b)
        self.assertAlmostEqual(band_average(b,600,0)['T'],1,14)
        a=band_average(b,600,.1,peak_info=p)
        c=band_average(b,600,1.,peak_info=p)
        self.assertFalse(a['capped']);self.assertFalse(c['capped'])
        self.assertGreater(a['T'],c['T'])
        self.assertAlmostEqual(c['T'],.16033727079,8)

    def test_gaussian_uniform_control(self):
        a=band_average([Layer(1,300)],600,5)
        self.assertFalse(a['capped'])
        self.assertAlmostEqual(a['T'],1,8)

    def test_gaussian_integrator_independent_grid(self):
        b=stacks(8,.03,seed=50)[1];p=peak(b)
        center=p['wavelength']+.3;fw=1.
        sigma=fw/(2*math.sqrt(2*math.log(2)))
        lo=center-8*sigma;hi=center+8*sigma
        n=16000;step=(hi-lo)/n
        vals=[]
        for i in range(n+1):
            w=lo+step*i
            vals.append(solve(b,w)['T']*math.exp(-.5*((w-center)/sigma)**2)/(sigma*math.sqrt(2*math.pi)))
        grid=step/3*(vals[0]+vals[-1]+4*sum(vals[1:-1:2])+2*sum(vals[2:-1:2]))
        adaptive=band_average(b,center,fw,peak_info=p)
        self.assertFalse(adaptive['capped'])
        self.assertLess(abs(grid-adaptive['T']),2e-9)

    def test_invalid_inputs(self):
        for w in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):solve([],w)
        for e in [-.01,.081,float('nan')]:
            with self.assertRaises(ValueError):stacks(error=e)
        for pairs in [0,9,2.5,True]:
            with self.assertRaises(ValueError):stacks(pairs)
        for seed in [-1,2**32,True]:
            with self.assertRaises(ValueError):stacks(seed=seed)
        for kind in ['bad']:
            with self.assertRaises(ValueError):stacks(kind=kind)
        with self.assertRaises(ValueError):solve([Layer(1,-1)],600)
        with self.assertRaises(ValueError):solve([Layer(float('nan'),1)],600)
        with self.assertRaises(ValueError):solve([Layer(1,1)]*65,600)
        with self.assertRaises(ValueError):band_average([],600,-1)
        with self.assertRaises(ValueError):peak([],lo=0)
        with self.assertRaises(ValueError):peak([],intervals=0)

if __name__=='__main__':unittest.main(verbosity=2)
