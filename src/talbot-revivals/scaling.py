"""One bounded asymptotic check using cancellation-resistant infidelity."""
import csv,json,math
from pathlib import Path
from model import coefficients,residual_phase,propagate,fidelity
ART=Path(__file__).resolve().parent/'data'

def stable_infidelity(cs,alpha):
    weights=[abs(c)**2 for n,c in cs];total=sum(weights);weights=[w/total for w in weights]
    phases=[residual_phase(n,1,alpha) for n,c in cs]
    return math.fsum(4*weights[j]*weights[k]*math.sin((phases[j]-phases[k])/2)**2 for j in range(len(cs)) for k in range(j+1,len(cs)))

def main():
 rows=[]
 for width in (.02,.025,.04,.08):
    cs=coefficients(width,64);total=sum(abs(c)**2 for n,c in cs)
    mu4=sum(abs(c)**2*n**4 for n,c in cs)/total
    var4=sum(abs(c)**2*(n**4-mu4)**2 for n,c in cs)/total
    for alpha in (.00001,.00003,.0001,.0003,.001):
        observed=stable_infidelity(cs,alpha)
        quartic=math.pi**2/4*alpha**4*var4
        gaussian=3*alpha**4/(512*math.pi**6*width**8)
        rows.append({'width':width,'alpha':alpha,'orders':64,'infidelity_stable':observed,
          'one_minus_direct_fidelity':1-fidelity(cs,propagate(cs,1,alpha,True)),
          'quartic_moment_prediction':quartic,'gaussian_continuum_prediction':gaussian,
          'observed_to_quartic':observed/quartic,'discrete_to_continuum':quartic/gaussian})
        if alpha<=.0001:assert abs(observed/quartic-1)<1e-5
        assert abs(quartic/gaussian-1)<1e-8
 with (ART/'scaling.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary={'rows':rows,'checks':'PASS: all 12 alpha<=1e-4 cases within 1e-5 relative error of moment prediction; all 20 moment/continuum coefficients within 1e-8',
   'method':'1-F = 4 sum_{j<k} w_j w_k sin^2((delta_j-delta_k)/2), normalized w; no cancellation by subtraction from 1',
   'derivation':'delta_n = -(pi/2) alpha^2 n^4 + O(alpha^4 n^6). Hence 1-F ~ (pi^2/4) alpha^4 Var_w(n^4). Gaussian continuum w(n) proportional to exp(-4 pi^2 sigma^2 n^2) has Var(n^4)=96/(8 pi^2 sigma^2)^4, giving 3 alpha^4/(512 pi^6 sigma^8).',
   'limits':'Asymptotic fixed-spectrum, alpha -> 0. Continuum Gaussian approximation, not universal slit-width law; no finite aperture, sharp-edge or material prediction. Established quartic phase mechanism; algebra and checks performed here without originality claim.'}
 (ART/'scaling.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({'status':'PASS','rows':len(rows),'small_alpha_cases':12,'largest_relative_small_alpha_error':max(abs(r['observed_to_quartic']-1) for r in rows if r['alpha']<=.0001),'width_halving_ratio_at_alpha_1e_4':rows[2]['infidelity_stable']/rows[12]['infidelity_stable'],'tiny_case':rows[-5]},indent=2))

if __name__=='__main__':main()
