"""Hold the physical layer inventory fixed while breaking error correlation."""
from pathlib import Path
from collections import Counter
import csv,json,random,statistics
from model import *
OUT=Path(__file__).resolve().parent/'output'
OUT.mkdir(exist_ok=True)
rng=random.Random(20261024);seeds=[rng.getrandbits(32) for _ in range(64)]
rows=[]
for m in [4,6,8]:
    for e in [.01,.03,.08]:
        for kind in ['thickness','index']:
            for seed in seeds:
                mirrored=stacks(m,e,'mirrored',seed,kind=kind)[1]
                shuffled=mirrored.copy();srng=random.Random(seed^0x5bf03635)
                for label in ['H','L']:
                    positions=[j for j,x in enumerate(mirrored) if x.label==label]
                    chunks=[mirrored[j] for j in positions];srng.shuffle(chunks)
                    for j,chunk in zip(positions,chunks):shuffled[j]=chunk
                assert Counter(mirrored)==Counter(shuffled)
                a=peak(mirrored,intervals=300);b=peak(shuffled,intervals=300)
                palindrome=[(x.n,x.d) for x in shuffled]==[(x.n,x.d) for x in reversed(shuffled)]
                rows.append({'m':m,'error':e,'kind':kind,'seed':seed,'same_inventory':True,
                             'mirrored_fixed_T':solve(mirrored,600)['T'],'shuffled_fixed_T':solve(shuffled,600)['T'],
                             'mirrored_peak_T':a['T'],'mirrored_peak_R':a['R'],'mirrored_peak_nm':a['wavelength'],
                             'shuffled_peak_T':b['T'],'shuffled_peak_R':b['R'],'shuffled_peak_nm':b['wavelength'],
                             'shuffled_still_palindrome':palindrome,'boundary':a['at_boundary'] or b['at_boundary']})
with (OUT/'matched-correlation.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
examples=[]
for kind in ['thickness','index']:
    sub=[r for r in rows if r['m']==6 and r['error']==.08 and r['kind']==kind]
    examples.append({'m':6,'error':.08,'kind':kind,'count':len(sub),
                     'mirrored_max_R':max(r['mirrored_peak_R'] for r in sub),
                     'shuffled_min_R':min(r['shuffled_peak_R'] for r in sub),
                     'shuffled_median_R':statistics.median(r['shuffled_peak_R'] for r in sub),
                     'shuffled_max_R':max(r['shuffled_peak_R'] for r in sub)})
checks={'status':'PASS','cases':len(rows),'seed_generator':20261024,
        'shuffle_xor':hex(0x5bf03635),'same_inventory_cases':sum(r['same_inventory'] for r in rows),
        'shuffled_still_palindrome':sum(r['shuffled_still_palindrome'] for r in rows),
        'boundary_peaks':sum(r['boundary'] for r in rows),'examples':examples,
        'limits':'Matched multiset including actual n,d and token. Nominal H/L order held fixed; errors permuted within H and L. Finite tested ensembles; asymmetry is not a proof that exact transmission is impossible.'}
(OUT/'matched-correlation-checks.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
