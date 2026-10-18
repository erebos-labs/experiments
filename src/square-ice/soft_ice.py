"""Toy soft constraint: weight1 for six ice vertices, q for ten others.

This is an authored comparison model, not a quantitative material model.
For q>0 every internal edge assignment has positive weight. A frontier
contraction uses O(2**n) memory and O(n**2 * 2**n) scalar work.
"""

if not __debug__:
    raise RuntimeError('Validation requires Python without -O or PYTHONOPTIMIZE')

import argparse
import json
import math
import time
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from ice import domain_count

OUT = Path(__file__).resolve().parent / 'output'


def partition(n, q, top, bottom, left, right):
    if type(n) is not int or not 1 <= n <= 16 or not math.isfinite(q) or not 0 <= q <= 1:
        raise ValueError('bounded n1..16, q0..1')
    if any(type(v) is not int or not 0 <= v < (1 << n) for v in (top, bottom)) or left not in (0,1) or right not in (0,1):
        raise ValueError('Invalid fixed boundary')
    if 0 < q < 1 and n*n*math.log(q) < math.log(sys.float_info.min):
        raise ValueError('q is below the conservative binary64 numerical domain for this n')
    q = int(q) if q in (0, 1) else q
    zero = 0 if q in (0, 1) else 0.0
    size = 1 << n
    dp = [zero] * size
    dp[top] = 1 if q in (0, 1) else 1.0
    for row in range(n):
        h0, h1 = [zero] * size, [zero] * size
        (h0 if left == 0 else h1)[:] = dp
        for col in range(n):
            bit = 1 << col
            out0, out1 = [zero] * size, [zero] * size
            for block in range(0, size, bit * 2):
                for base in range(block, block + bit):
                    other = base + bit
                    a, b, c, d = h0[base], h0[other], h1[base], h1[other]
                    middle = b + c + q * (a + d)
                    out0[base] = a + q * (b + c + d)
                    out0[other] = middle
                    out1[base] = middle
                    out1[other] = d + q * (a + b + c)
            h0, h1 = out0, out1
        dp = h0 if right == 0 else h1
    return dp[bottom]


def defect_histogram(n, top, bottom, left, right):
    """Independent full edge-assignment enumeration; n<=3 only."""
    if type(n) is not int or not 1 <= n <= 3:
        raise ValueError('oracle bounded at n3')
    histogram = [0] * (n * n + 1)
    hbits = n * (n - 1)
    for assignment in range(1 << (2 * hbits)):
        defects = 0
        for row in range(n):
            for col in range(n):
                l = left if col == 0 else (assignment >> (row * (n - 1) + col - 1)) & 1
                r = right if col == n - 1 else (assignment >> (row * (n - 1) + col)) & 1
                u = (top >> col) & 1 if row == 0 else (
                    assignment >> (hbits + (row - 1) * n + col)) & 1
                d = (bottom >> col) & 1 if row == n - 1 else (
                    assignment >> (hbits + row * n + col)) & 1
                defects += (l + u != r + d)
        histogram[defects] += 1
    return histogram


def run(max_n):
    OUT.mkdir(exist_ok=True)
    if type(max_n) is not int or not 3 <= max_n <= 8:
        raise ValueError('soft sweep max n must be 3..8 (conservative floating-point domain)')
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    tests = []
    for n in range(1, 9):
        mask = (1 << n) - 1
        assert partition(n, 0, mask, 0, 0, 1) == domain_count(n)
        assert partition(n, 0, mask, mask, 1, 1) == 1
        expected = 2 ** (2 * n * (n - 1))
        assert partition(n, 1, mask, 0, 0, 1) == expected
        assert partition(n, 1, mask, mask, 1, 1) == expected
    tests.append('q0 exact hard counts and q1 unconstrained edge counts: n1..8')
    oracle = []
    for n in (2, 3):
        mask = (1 << n) - 1
        for name, bottom, left, right in (('domain_wall', 0, 0, 1),
                                         ('polarized', mask, 1, 1)):
            hist = defect_histogram(n, mask, bottom, left, right)
            for q in (Fraction(1, 8), Fraction(1, 2)):
                expected = sum(Fraction(count) * q ** k for k, count in enumerate(hist))
                measured = partition(n, float(q), mask, bottom, left, right)
                assert math.isclose(measured, float(expected), rel_tol=1e-13)
                reversed_z = partition(n, float(q), 0, bottom ^ mask, 1 - left, 1 - right)
                assert math.isclose(measured, reversed_z, rel_tol=1e-13)
            oracle.append({'n': n, 'boundary': name, 'defect_count_histogram': hist})
    tests.append('independent defect polynomials at rational q=1/8,1/2; arrow reversal: n2,3')
    rows = []
    for q in (0.0, 0.001, 0.01, 0.1, 0.5, 1.0):
        for n in range(2, max_n + 1):
            mask = (1 << n) - 1
            a = partition(n, q, mask, 0, 0, 1)
            b = partition(n, q, mask, mask, 1, 1)
            delta = (math.log(a) - math.log(b)) / (n * n)
            boundary_vertices = 4 * n - 4
            bound = boundary_vertices * math.log(1 / q) / n ** 2 if q else None
            if bound is not None:
                assert abs(delta) <= bound + 1e-12
            record = {'n': n, 'q': q, 'domain_logZ_per_vertex': math.log(a) / n ** 2,
                      'polarized_logZ_per_vertex': math.log(b) / n ** 2,
                      'difference_per_vertex': delta, 'universal_boundary_bound': bound}
            rows.append(record)
        print('q', q, 'n', max_n, 'delta', rows[-1]['difference_per_vertex'], flush=True)
    result = {'started': started, 'ended': datetime.now(timezone.utc).isoformat(),
              'elapsed_seconds': time.monotonic() - t0, 'tests': tests, 'oracle': oracle,
              'rows': rows, 'status': 'PASS',
              'limits': 'Integer contraction for q=0/1; bounded binary64 contraction for interior q, conservative term-underflow rejection. CLI sweep n<=8. No material calibration or convergence proof.'}
    (OUT / 'soft-constraint.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS', result['elapsed_seconds'], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--max-n', type=int, default=8)
    args = p.parse_args()
    run(args.max_n)
