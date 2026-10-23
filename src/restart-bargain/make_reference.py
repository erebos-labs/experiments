"""Regenerate the seeded cross-language fixtures and selective-policy table."""
import random,json
from pathlib import Path
import model,gated

out=Path(__file__).resolve().parent/'data'
rng=random.Random(2303);rows=[]
for _ in range(80):
    L=rng.randrange(1,61);s=rng.randrange(1,L+1);r=rng.choice([0,1e-10,.0001,.00168,.012,.1,.25]);c=rng.randrange(0,9);H=1000
    mode=rng.choice(['blind','gated']);m=model if mode=='blind' else gated
    S=m.distribution(L,s,r,H,c)
    rows.append({'length':L,'start':s,'reset':r,'cost':c,'mode':mode,'H':H,'mean':m.mean_time(L,s,r,c),'survivals':[(t,S[t]) for t in [0,1,2,10,100,400,1000]]})
(out/'js-reference.json').write_text(json.dumps(rows,indent=2)+'\n')
rows=[]
for s,r,c in [(20,.00168,0),(20,.00168,80),(20,.25,80),(20,1,0),(20,1,80),(40,.00168,0)]:
    S=gated.distribution(40,s,r,10000,c)
    rows.append({'length':40,'start':s,'reset':r,'extra_cost':c,'mean':gated.mean_time(40,s,r,c),'median':model.quantile(S,.5),'q90':model.quantile(S,.9),'q99':model.quantile(S,.99),'success400':1-S[400]})
(out/'selective-results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Regenerated 80 seeded Python references and 6 selective-policy cases.')
