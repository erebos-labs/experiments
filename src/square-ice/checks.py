"""Independent edge-orientation oracles and exact graph checks."""

if not __debug__:
    raise RuntimeError('Validation requires Python without -O or PYTHONOPTIMIZE')

import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ice import (asm_formula, domain_count, fixed_count, plaquette_neighbors,
                 row_choices, torus_count, torus_flux, torus_states)

OUT = Path(__file__).resolve().parent / 'output'


def valid_torus(state, n):
    def h(r, c):
        return (state >> ((r % n) * n + c % n)) & 1

    def v(r, c):
        return (state >> (n * n + (r % n) * n + c % n)) & 1

    return all(h(r, c - 1) + (1 - h(r, c)) + v(r - 1, c) + (1 - v(r, c)) == 2
               for r in range(n) for c in range(n))


def brute_fixed(n, top, bottom, left, right):
    count = 0
    horizontal_count = n * (n - 1)
    for state in range(1 << (2 * horizontal_count)):
        def h(r, c):
            if c == 0:
                return left
            if c == n:
                return right
            return (state >> (r * (n - 1) + c - 1)) & 1

        def v(r, c):
            if r == 0:
                return (top >> c) & 1
            if r == n:
                return (bottom >> c) & 1
            return (state >> (horizontal_count + (r - 1) * n + c)) & 1

        if all(h(r, c) + 1 - h(r, c + 1) + v(r, c) + 1 - v(r + 1, c) == 2
               for r in range(n) for c in range(n)):
            count += 1
    return count


def run():
    OUT.mkdir(exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    result = {'started': started, 'checks': []}
    # Exhaustive edge assignment does not call the row-recursion implementation.
    for n in (2, 3):
        brute = {s for s in range(1 << (2 * n * n)) if valid_torus(s, n)}
        generated = list(torus_states(n))
        assert len(set(generated)) == len(generated)
        assert set(generated) == brute
        count, sectors = torus_count(n, n)
        assert count == len(brute)
        result['checks'].append({'kind': 'torus exhaustive edge oracle', 'n': n,
                                 'assignments_checked': 1 << (2 * n * n), 'valid': count})
    for n in (1, 2, 3):
        mask = (1 << n) - 1
        for label, top, bottom, left, right in (
                ('domain wall', mask, 0, 0, 1),
                ('polarized', mask, mask, 1, 1),
                ('impossible net flux', mask, 0, 1, 1)):
            brute = brute_fixed(n, top, bottom, left, right)
            transfer = fixed_count(n, n, top, bottom, left, right)
            assert transfer == brute
            result['checks'].append({'kind': 'fixed exhaustive edge oracle', 'boundary': label,
                                     'n': n, 'assignments_checked': 1 << (2 * n * (n - 1)),
                                     'valid': transfer})
    counts = []
    for n in range(1, 11):
        measured = domain_count(n)
        assert measured == asm_formula(n)
        assert fixed_count(n, n, (1 << n) - 1, (1 << n) - 1, 1, 1) == 1
        counts.append({'n': n, 'domain': measured})
    result['checks'].append({'kind': 'published ASM product and unique polarized boundary',
                             'counts': counts})
    # All 2x2/3x3 rectangular periodic systems agree after rotation.
    for width, height in ((2, 3), (3, 4), (4, 5)):
        a, _ = torus_count(width, height)
        b, _ = torus_count(height, width)
        assert a == b
        result['checks'].append({'kind': 'rectangular rotation', 'width': width,
                                 'height': height, 'count': a})

    n = 4
    states = set(torus_states(n))
    assert len(states) == torus_count(n, n)[0]
    assert all(valid_torus(s, n) for s in states)
    assert {s ^ ((1 << (2 * n * n)) - 1) for s in states} == states
    edges = {s: set(plaquette_neighbors(s, n)) for s in states}
    assert all(t in states and s in edges[t] and torus_flux(s, n) == torus_flux(t, n)
               for s in states for t in edges[s])
    unseen = set(states)
    components = []
    while unseen:
        root = min(unseen)
        unseen.remove(root)
        stack = [root]
        size = 0
        while stack:
            s = stack.pop()
            size += 1
            for t in edges[s]:
                if t in unseen:
                    unseen.remove(t)
                    stack.append(t)
        components.append({'flux': list(torus_flux(root, n)), 'size': size, 'example': root})
    components.sort(key=lambda item: (item['flux'], item['example']))
    sector_sizes = defaultdict(list)
    for component in components:
        sector_sizes[tuple(component['flux'])].append(component['size'])
    graph = {'n': n, 'states': len(states), 'undirected_edges': sum(map(len, edges.values())) // 2,
             'components': components,
             'sector_component_sizes': [{'flux': list(k), 'sizes': sorted(v, reverse=True)}
                                        for k, v in sorted(sector_sizes.items())],
             'frozen_states': sum(not edges[s] for s in states),
             'degree_histogram': dict(sorted(Counter(map(len, edges.values())).items()))}
    (OUT / 'plaquette-graph.json').write_text(json.dumps(graph, indent=2) + '\n')
    result['checks'].append({'kind': 'full 4x4 state/move graph', 'states': len(states),
                             'components': len(components), 'frozen_states': graph['frozen_states'],
                             'directed_moves_checked': sum(map(len, edges.values()))})
    result['elapsed_seconds'] = time.monotonic() - t0
    result['ended'] = datetime.now(timezone.utc).isoformat()
    result['status'] = 'PASS'
    (OUT / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    run()
