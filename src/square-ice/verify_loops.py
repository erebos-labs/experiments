"""Check loop identity, independent finite counts, and a four-event example."""

if not __debug__:
    raise RuntimeError('Validation requires Python without -O or PYTHONOPTIMIZE')

import itertools
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from ice import free_count, torus_count
from loop_fixture import canonical_rows

OUT = Path(__file__).resolve().parent / 'output'


def run():
    OUT.mkdir(exist_ok=True)
    result = {'started': datetime.now(timezone.utc).isoformat()}
    local = []
    for signs in itertools.product((-1, 1), repeat=4):
        pairs = sum(signs[i] * signs[j] for i in range(4) for j in range(i + 1, 4))
        product = signs[0] * signs[1] * signs[2] * signs[3]
        fourier = Fraction(3, 8) - Fraction(pairs, 8) + Fraction(3 * product, 8)
        assert fourier == int(sum(signs) == 0)
        local.append({'signs': signs, 'indicator': int(fourier)})
    result['fourier_all_16_inputs'] = local
    loop_rows = [json.loads(line) for line in (Path(__file__).resolve().parent / 'data' / 'loops.jsonl').read_text().splitlines()]
    loop_rows = canonical_rows(loop_rows)
    for row in loop_rows:
        n = row['n']
        count = torus_count(n, n)[0] if row['boundary'] == 'torus' else free_count(n)
        assert count == int(row['ice_count'])
        histogram = list(map(int, row['degree_two_histogram']))
        assert sum(histogram) == row['subgraphs'] == 2 ** row['cycle_rank']
        weighted = sum(amount * 3 ** (n * n - k) for k, amount in enumerate(histogram))
        assert weighted == int(row['weighted_numerator'])
        row['independent_transfer_match'] = True
    result['loop_transfer_comparisons'] = loop_rows
    # n=2 has four internal vertices, four internal and eight exterior edges.
    joint_counts = [0] * 16
    for assignment in range(1 << 12):
        events = 0
        for r in range(2):
            for c in range(2):
                l = (assignment >> (r * 3 + c)) & 1
                right = (assignment >> (r * 3 + c + 1)) & 1
                up = (assignment >> (6 + r * 2 + c)) & 1
                down = (assignment >> (6 + (r + 1) * 2 + c)) & 1
                if l + 1 - right + up + 1 - down == 2:
                    events |= 1 << (r * 2 + c)
        for subset in range(16):
            joint_counts[subset] += (events & subset) == subset
    rows = []
    for subset in range(16):
        k = subset.bit_count()
        independence_count = 3 ** k * 2 ** (12 - 3 * k)
        if subset != 15:
            assert joint_counts[subset] == independence_count
        else:
            assert joint_counts[subset] == 82 and independence_count == 81
        rows.append({'event_subset': subset, 'vertices': k,
                     'observed_assignments': joint_counts[subset],
                     'independence_prediction': independence_count})
    result['four_junction_joint_events'] = {'assignments_checked': 4096, 'subsets': rows,
                                           'all_proper_subsets_independent': True,
                                           'all_four_independent': False}
    result['status'] = 'PASS'
    result['ended'] = datetime.now(timezone.utc).isoformat()
    (OUT / 'loop-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS:16 local Fourier cases;9 independent loop/transfer matches;4096 edge assignments;15 proper subsets independent;four-way82 rather than81.')


if __name__ == '__main__':
    run()
