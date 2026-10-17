"""Finite exact comparison of cut rules, not an asymptotic theorem test.

Eight distinct cards, up to twelve shuffles. Keep uniformly random
interleavings, vary the cut: binomial(n,1/2), uniform 0..n, or exact half.
Outputs full-deck TV and the TV visible from either descent count alone.
All distributions have exact integer weights with a common denominator.
"""

from collections import Counter, defaultdict
from datetime import datetime
from fractions import Fraction
from itertools import combinations, permutations
from math import comb, factorial, lcm
from pathlib import Path
from time import perf_counter
from zoneinfo import ZoneInfo
import argparse
import json

from model import descents, eulerian, inverse, inverse_descent_counts, tv_counts


def step_weights(n, rule):
    cuts = {c: (Fraction(comb(n, c), 2 ** n) if rule == 'gsr'
                else Fraction(1, n + 1) if rule == 'uniform'
                else Fraction(int(c == n // 2))) for c in range(n + 1)}
    weights = Counter()
    for cut, probability in cuts.items():
        if not probability:
            continue
        for positions in combinations(range(n), cut):
            positions = set(positions)
            left, right = iter(range(cut)), iter(range(cut, n))
            deck = bytes(next(left) if i in positions else next(right)
                         for i in range(n))
            weights[deck] += probability / comb(n, cut)
    denominator = lcm(*(value.denominator for value in weights.values()))
    return {p: int(w * denominator) for p, w in weights.items()}, denominator


def compare(n, kmax, rule, max_seconds):
    start, tic = datetime.now(ZoneInfo('Asia/Singapore')), perf_counter()
    all_permutations = list(map(bytes, permutations(range(n))))
    classes = {p: (descents(p), descents(inverse(p))) for p in all_permutations}
    step, step_den = step_weights(n, rule)
    fact, uniform = factorial(n), eulerian(n)
    current, denominator, rows = {bytes(range(n)): 1}, 1, []
    stop_reason = 'completed requested shuffle counts'
    for k in range(kmax + 1):
        visible, hidden = [0] * n, [0] * n
        for p, count in current.items():
            d, h = classes[p]
            visible[d] += count
            hidden[h] += count
        # Missing permutations have zero mass, contributing denominator each.
        tv = Fraction(sum(abs(count * fact - denominator) for count in current.values())
                      + (fact - len(current)) * denominator,
                      2 * denominator * fact)
        row = {'k': k, 'support': len(current), 'deck_tv': float(tv),
               'visible_tv': float(tv_counts(visible, denominator, uniform, fact)),
               'inverse_descents_tv': float(tv_counts(hidden, denominator, uniform, fact)),
               'mass_exactly_one': sum(current.values()) == denominator,
               'elapsed_seconds': perf_counter() - tic}
        rows.append(row)
        print(f"{rule} n={n} k={k}: TV={float(tv):.8f}, "
              f"hidden={row['inverse_descents_tv']:.8f}, "
              f"visible={row['visible_tv']:.8f}, {row['elapsed_seconds']:.1f}s", flush=True)
        if k == kmax:
            break
        if perf_counter() - tic > max_seconds:
            stop_reason = 'time budget reached between complete iterations'
            break
        next_counts = defaultdict(int)
        # bytes.translate composes q -> p[q] in C. Its unused table entries
        # do not matter because every q[i] < n. Build the table once per p.
        for p, count in current.items():
            table = p + bytes(256 - n)
            for q, step_count in step.items():
                next_counts[q.translate(table)] += count * step_count
        current, denominator = dict(next_counts), denominator * step_den
    return {'n': n, 'rule': rule, 'kmax_requested': kmax,
            'step_denominator': step_den, 'step_support': len(step),
            'started_sgt': start.isoformat(),
            'finished_sgt': datetime.now(ZoneInfo('Asia/Singapore')).isoformat(),
            'elapsed_seconds': perf_counter() - tic,
            'max_seconds': max_seconds, 'stop_reason': stop_reason,
            'rows': rows}
