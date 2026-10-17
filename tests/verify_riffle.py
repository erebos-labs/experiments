"""Independent release checks: explicit permutations, closed Eulerian sum, data.

Uses a literal cut/interleave Markov process for small decks, without importing
the implementation. The full-deck oracle uses the published probability law
with an independent explicit Eulerian-number formula, rather than its recurrence.
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations, permutations
from math import comb, factorial
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'src/riffle/data.json').read_text())

def desc(p):
    return sum(p[i] > p[i+1] for i in range(len(p)-1))

def inv(p):
    return tuple(p.index(i) for i in range(len(p)))

def tv(q, uniform):
    return sum(abs(x-y) for x, y in zip(q, uniform))/2

def literal_riffle(deck):
    n = len(deck)
    for cut in range(n+1):
        for positions in combinations(range(n), cut):
            positions = set(positions)
            left, right = iter(deck[:cut]), iter(deck[cut:])
            yield tuple(next(left) if i in positions else next(right) for i in range(n))

def explicit_eulerian(n, d):
    return sum((-1)**j*comb(n+1, j)*(d+1-j)**n for j in range(d+1))

small_cases = 0
for n in range(2, 7):
    orders = list(permutations(range(n)))
    weights = Counter({tuple(range(n)): 1})
    for k in range(1, 4):
        next_weights = Counter()
        for deck, count in weights.items():
            for shuffled in literal_riffle(deck):
                next_weights[shuffled] += count
        weights = next_weights
        denominator, a = 2**(n*k), 2**k
        assert sum(weights.values()) == denominator
        for deck in orders:
            h = desc(inv(deck))
            expected = comb(a+n-h-1, n) if a > h else 0
            assert weights[deck] == expected, (n, k, deck)
        small_cases += 1

uniform = [Fraction(explicit_eulerian(52, d), factorial(52)) for d in range(52)]
assert sum(uniform) == 1
for row in DATA['rows']:
    a = 2**row['k']
    shuffled = [Fraction(explicit_eulerian(52, d)*comb(a+51-d, 52), a**52)
                if a > d else Fraction(0) for d in range(52)]
    exact_tv = tv(shuffled, uniform)
    assert exact_tv == Fraction(row['deck_tv_fraction'])
    assert abs(float(exact_tv)-row['deck_tv']) < 1e-14
    assert sum(Fraction(x) for x in row['top_card_probability']) > Fraction(999999, 1000000)
    assert abs(sum(row['top_card_probability'])-1) < 1e-12
    top_tv = sum(abs(x-Fraction(1,52)) for x in row['top_card_probability'])/2
    assert abs(float(top_tv)-row['top_card_tv']) < 1e-12

# Independent one-card rank oracle at the headline five-riffle point.
# Condition on the chosen original first card's pile label, then count lower
# pile labels among the other 51 independent assignments.
a, row = 32, DATA['rows'][5]
top = [Fraction(comb(51, rank)*sum(t**rank*(a-t)**(51-rank)
                                  for t in range(a)), a**52) for rank in range(52)]
assert sum(top) == 1
assert all(abs(float(x)-y) < 1e-14 for x, y in zip(top, row['top_card_probability']))
assert abs(float(tv(top, [Fraction(1,52)]*52))-0.01986397) < 5e-9

# The plain-English counterexample: uniform random rotation has uniform top
# label but TV = 1 - n/n! for the complete order.
for n in [4, 5, 6]:
    ordered = tuple(range(n))
    rotations = {ordered[i:]+ordered[:i] for i in range(n)}
    assert len(rotations) == n
    assert Counter(p[0] for p in rotations) == Counter(range(n))
    full = [Fraction(1,n) if p in rotations else Fraction(0)
            for p in permutations(range(n))]
    assert tv(full, [Fraction(1,factorial(n))]*factorial(n)) == 1-Fraction(n,factorial(n))

page = (ROOT/'docs/riffle-shuffles/index.html').read_text()
assert 'One random-looking card is not enough' in page
assert '0.000 can mean a small difference' in page
payloads = [body for attrs, body in re.findall(r'<script(\b[^>]*)>(.*?)</script>', page, re.S)
            if 'application/json' in attrs and 'experiment-data' in attrs]
assert len(payloads) == 1
embedded = json.loads(payloads[0])
assert embedded == DATA
for attrs, script in re.findall(r'<script(\b[^>]*)>(.*?)</script>', page, re.S):
    if 'application/json' not in attrs:
        result = subprocess.run(['node','--check','-'], input=script, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
print(f'PASS riffle: {small_cases} literal repeated-riffle laws, 15 independent 52-card TV rows, headline top marginal, random-rotation counterexample, payload equality and JS syntax.')
