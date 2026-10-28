"""Inspect the two central certificates without importing the experiment models.

This verifies the all-moduli Fox conclusion and explicit nonconstant matrix
witnesses. Exhaustiveness of the 728 count is checked by the study enumerator.
"""
from pathlib import Path
import json

ART=Path(__file__).resolve().parent/'data'
c=json.loads((ART/'conway-certificate.json').read_text())
code=c['gauss_code'];n=len(code)//2
arc=n-1;overs={};unders={}
for event in code:
    if event>0:overs[event]=arc
    else:unders[-event]=(arc,(arc+1)%n);arc=(arc+1)%n
matrix=[]
for crossing in sorted(overs):
    row=[0]*n;row[overs[crossing]]+=2
    for under in unders[crossing]:row[under]-=1
    matrix.append(row)
assert matrix==c['matrix'] and all(sum(row)==0 for row in matrix)
B=[row[1:] for row in matrix[1:]];inverse=c['integer_inverse'];k=n-1
assert B==c['reduced_matrix']
assert all(type(x) is int for row in inverse for x in row)
assert all(sum(B[i][r]*inverse[r][j] for r in range(k))==int(i==j) for i in range(k) for j in range(k))
# The displayed determinant is not needed for the proof: an integer inverse
# itself certifies invertibility over every Z/qZ.

def canonical(a):
    a=tuple(x%7 for x in a);b=tuple((-x)%7 for x in a)
    return min(a,b)

def multiply(a,b):
    return canonical((a[0]*b[0]+a[1]*b[2],a[0]*b[1]+a[1]*b[3],a[2]*b[0]+a[3]*b[2],a[2]*b[1]+a[3]*b[3]))

def invert(a):
    assert (a[0]*a[3]-a[1]*a[2])%7==1
    return canonical((a[3],-a[1],-a[2],a[0]))

w=json.loads((ART/'matrix-colorings.json').read_text());labels=w['labels'];r=w['results']['conway']
nonconstant=0
for solution in r['solutions']:
    values=[labels[i] for i in solution]
    for a,b,c,d in r['pd']:
        # Source PD convention: edge numbers increase around the component.
        edge=lambda x:values[r['edge_arcs'][str(x)]]
        assert edge(b)==edge(d)
        if d%(2*len(r['pd']))+1==b:
            predicted=multiply(multiply(invert(edge(b)),edge(a)),edge(b))
        else:
            assert b%(2*len(r['pd']))+1==d
            predicted=multiply(multiply(edge(b),edge(a)),invert(edge(b)))
        assert canonical(edge(c))==predicted
    nonconstant+=len(set(map(tuple,values)))>1
assert nonconstant==12
print('PASS: reconstructed Fox equations; exact integer inverse; all 13 fixed-label matrix witnesses, including 12 nonconstant, satisfy every source PD crossing.')
print('This establishes the two central claims. Exhaustive totals are recorded separately in study.json and checked by the enumerator tests.')
