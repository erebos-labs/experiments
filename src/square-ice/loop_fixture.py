"""Validate the exact scientific coverage/schema, without running a count."""
EXPECTED = frozenset([('torus', n) for n in range(2, 6)] + [('free', n) for n in range(2, 7)])
FIELDS = frozenset(['boundary', 'cycle_rank', 'degree_two_histogram', 'ice_count', 'n', 'subgraphs', 'weighted_numerator'])

def canonical_rows(rows, allow_timing=False):
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise ValueError('Expected the exact nine-record loop matrix')
    seen = set(); result = []
    for row in rows:
        if not isinstance(row, dict) or set(row) - ({'seconds'} if allow_timing else set()) != FIELDS:
            raise ValueError('Unexpected loop record fields')
        if type(row['n']) is not int:
            raise ValueError('Loop size must be an integer')
        key = (row['boundary'], row['n'])
        if key not in EXPECTED or key in seen:
            raise ValueError('Missing, duplicate or unexpected loop case')
        seen.add(key); result.append({k: row[k] for k in FIELDS})
    if seen != EXPECTED:
        raise ValueError('Incomplete loop matrix')
    return result
