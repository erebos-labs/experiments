"""Two flipped external arrows create one reversed monotone path."""

if not __debug__:
    raise RuntimeError('Validation requires Python without -O or PYTHONOPTIMIZE')

import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ice import (asm_formula, boundary_count, domain_marginals, domain_sample,
                 domain_tables, row_choices)

OUT = Path(__file__).resolve().parent / 'output'


def as_asm(n, horizontal):
    result = []
    for h in horizontal:
        row = []
        previous = 0
        for c in range(n):
            right = (h >> c) & 1
            row.append(right - previous)
            previous = right
        result.append(row)
    for line in result + [list(col) for col in zip(*result)]:
        nonzero = [a for a in line if a]
        assert nonzero == [1 if i % 2 == 0 else -1 for i in range(len(nonzero))]
        assert sum(line) == 1
    return result


def all_domain(n):
    def visit(row, above, hs, vs):
        if row == n:
            if above == 0:
                yield hs, vs
            return
        for below, h in row_choices(n, above, 0, 1):
            yield from visit(row + 1, below, hs + [h], vs + [below])
    yield from visit(0, (1 << n) - 1, [], [])


def validate_board(n, hs, vs, top, left, right, bottom):
    assert len(hs) == len(vs) == n
    assert vs[-1] == bottom
    for r in range(n):
        assert (hs[r] >> (n - 1)) & 1 == right[r]
        for c in range(n):
            l = (hs[r] >> (c - 1)) & 1 if c else left[r]
            u = ((vs[r - 1] if r else top) >> c) & 1
            out_r, d = (hs[r] >> c) & 1, (vs[r] >> c) & 1
            assert l + u + 1 - out_r + 1 - d == 2


def run():
    OUT.mkdir(exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    comparisons = 0
    for n in range(1, 11):
        mask = (1 << n) - 1
        for r in range(n):
            for c in range(n):
                left = [1] * n
                left[r] = 0
                count = boundary_count(n, n, mask, mask ^ (1 << c), left, [1] * n)
                expected = math.comb(c + n - 1 - r, c)
                assert count == expected
                comparisons += 1
    # Exact marginal oracle: enumerate every state, not products of table messages.
    enumeration_checks = []
    for n in range(1, 6):
        forward, backward = domain_tables(n)
        states = list(all_domain(n))
        assert len(states) == asm_formula(n)
        matrices = {tuple(map(tuple, as_asm(n, h))) for h, _ in states}
        assert len(matrices) == len(states)
        direct = [[Counter() for _ in range(n)] for _ in range(n)]
        for hs, vs in states:
            validate_board(n, hs, vs, (1 << n) - 1, [0] * n, [1] * n, 0)
            for r in range(n):
                for c in range(n):
                    l = (hs[r] >> (c - 1)) & 1 if c else 0
                    u = ((vs[r - 1] if r else (1 << n) - 1) >> c) & 1
                    direct[r][c][(l, u, (hs[r] >> c) & 1, (vs[r] >> c) & 1)] += 1
        assert direct == domain_marginals(n, forward, backward)
        # The rare top-left type gives a smaller ASM after deleting row/col.
        assert direct[0][0][(0, 1, 1, 0)] == asm_formula(n - 1)
        enumeration_checks.append({'n': n, 'states': len(states), 'distinct_asm': len(matrices)})
    n = 14
    mask = (1 << n) - 1
    rng = random.Random(1967)
    steps = ['R'] * (n - 1) + ['D'] * (n - 1)
    rng.shuffle(steps)
    hs, vs = [mask] * n, [mask] * n
    r = c = 0
    positions = [[r, c]]
    for step in steps:
        if step == 'R':
            hs[r] ^= 1 << c
            c += 1
        else:
            vs[r] ^= 1 << c
            r += 1
        positions.append([r, c])
    vs[-1] ^= 1 << (n - 1)
    left = [0] + [1] * (n - 1)
    validate_board(n, hs, vs, mask, left, [1] * n, mask ^ (1 << (n - 1)))
    path_count = boundary_count(n, n, mask, vs[-1], left, [1] * n)
    assert path_count == math.comb(2 * n - 2, n - 1)
    # Validate all six already-generated exact completion samples and their ASMs.
    marginal = json.loads((Path(__file__).resolve().parent / 'data' / 'domain-samples.json').read_text())
    assert marginal['n'] == n
    for sample in marginal['samples']:
        validate_board(n, sample['horizontal'], sample['vertical'], mask, [0] * n, [1] * n, 0)
        sample['asm'] = as_asm(n, sample['horizontal'])
    result = {'started': started, 'ended': datetime.now(timezone.utc).isoformat(),
              'status': 'PASS', 'single_path_boundary_cases_checked': comparisons,
              'domain_enumeration_checks': enumeration_checks,
              'path_sample': {'n': n, 'seed': 1967, 'count': path_count,
                              'steps': ''.join(steps), 'positions': positions,
                              'horizontal': hs, 'vertical': vs, 'left': left},
              'domain_sample_asms': [s['asm'] for s in marginal['samples']],
              'sample_count_validated': len(marginal['samples'])}
    (OUT / 'boundary-paths.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('path_sample', 'domain_sample_asms')}, indent=2))


if __name__ == '__main__':
    run()
