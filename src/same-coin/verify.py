"""Exact, dependency-free checks for the educational demo."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations,product
import json,subprocess,tempfile,sys
from pattern_races import words,markov,fixed_count_distribution,score_outcomes
base=Path(__file__).resolve().parent
subprocess.run([sys.executable,'-B',str(base/'build.py'),'--check'],check=True)
c=markov(('HHT','THH'));assert tuple(c.wins)==(F(1,4),F(3,4))
assert markov(('HHT',)).mean==markov(('THH',)).mean==8
for n in (4,5,40,100):
    assert score_outcomes(fixed_count_distribution('HHT','THH',n))=={'a_more':F(3,16),'tie':F(5,8),'b_more':F(3,16)}
count=0
for n in range(3,11):
    for letters in product('HT',repeat=n):
        s=''.join(letters)
        delta=sum(s[i:i+3]=='HHT' for i in range(n-2))-sum(s[i:i+3]=='THH' for i in range(n-2))
        assert delta==int(s.startswith('HH'))-int(s.endswith('HH'));count+=1
print('PASS fair-coin headline values and',count,'boundary identities')
cases=[]
for h in range(1,20):
    p=F(h,20)
    for a,b in combinations(words(3),2):
        c=markov((a,b),p)
        row={'a':a,'b':b,'h':h,'race':{'a':str(c.wins[0]),'b':str(c.wins[1]),'mean':str(c.mean),'meanA':str(markov((a,),p).mean),'meanB':str(markov((b,),p).mean)},'fixed':{}}
        for n in (3,4,40,100):
            s=score_outcomes(fixed_count_distribution(a,b,n,p));row['fixed'][str(n)]={'a':str(s['a_more']),'tie':str(s['tie']),'b':str(s['b_more'])}
        cases.append(row)
with tempfile.TemporaryDirectory(prefix='coin-pattern-check-') as d:
    fixture=Path(d)/'cases.json';fixture.write_text(json.dumps(cases))
    subprocess.run(['node',str(base/'test_exhibit.cjs'),str(fixture)],check=True)
