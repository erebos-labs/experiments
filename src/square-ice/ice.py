"""Exact, equally weighted six-vertex counts; standard library only.

Coordinates grow right/down. A 1 on an edge points right/down. At a
vertex with incoming row-state bit u and outgoing row-state bit d,
the ice rule is l + u == r + d. External arrows are actual fixed edges,
not missing neighbors. Periodic edges remain distinct for width 2.
"""
from collections import defaultdict
from functools import cache
from math import factorial


MAX_WIDTH = 14
MAX_HEIGHT = 14


def dimension(value, limit=MAX_WIDTH, name='dimension'):
    if type(value) is not int or not 1 <= value <= limit:
        raise ValueError(f'{name} must be an integer in 1..{limit}')
    return value


@cache
def row_choices(width, above, left, right=None):
    """Return (below_mask, horizontal_right_mask) without multiplicities.

    left=0/1 fixes the left boundary; right=None leaves the right free.
    The mask stores the edge immediately right of each vertex, including
    the external right edge. The external left edge is separate.
    """
    if type(width) is not int or not 1 <= width <= MAX_WIDTH:
        raise ValueError("width must be 1..14 (bounded experiment)")
    if above not in range(1 << width) or left not in (0, 1):
        raise ValueError("invalid row input")
    if right not in (None, 0, 1):
        raise ValueError("invalid right boundary")
    result = []

    def visit(col, h, below, horizontal):
        if col == width:
            if right is None or h == right:
                result.append((below, horizontal))
            return
        u = (above >> col) & 1
        for r in (0, 1):
            d = h + u - r
            if d in (0, 1):
                visit(col + 1, r, below | (d << col), horizontal | (r << col))

    visit(0, left, 0, 0)
    return tuple(result)


@cache
def periodic_choices(width, above):
    return row_choices(width, above, 0, 0) + row_choices(width, above, 1, 1)


def fixed_count(width, height, top, bottom, left, right):
    """Exact count, constant left/right boundary values on every row."""
    dimension(width); dimension(height, MAX_HEIGHT, "height")
    return boundary_count(width, height, top, bottom, (left,) * height, (right,) * height)


def boundary_count(width, height, top, bottom, left, right):
    """Exact count with row-specific fixed horizontal boundary arrows."""
    dimension(width); dimension(height, MAX_HEIGHT, 'height')
    if type(top) is not int or type(bottom) is not int or not 0 <= top < (1 << width) or not 0 <= bottom < (1 << width):
        raise ValueError('Invalid top or bottom boundary mask')
    if len(left) != height or len(right) != height:
        raise ValueError('horizontal boundaries must have one entry per row')
    counts = {top: 1}
    for row in range(height):
        nxt = defaultdict(int)
        for above, count in counts.items():
            for below, _ in row_choices(width, above, left[row], right[row]):
                nxt[below] += count
        counts = nxt
    return counts.get(bottom, 0)


def domain_count(n):
    dimension(n)
    # Horizontal exterior arrows out; vertical exterior arrows in.
    return fixed_count(n, n, (1 << n) - 1, 0, 0, 1)


def free_count(n):
    """All four sets of exterior arrows are independently unconstrained."""
    dimension(n, 10)
    counts = {top: 1 for top in range(1 << n)}
    for _ in range(n):
        nxt = defaultdict(int)
        for above, ways in counts.items():
            for left in (0, 1):
                for below, _ in row_choices(n, above, left):
                    nxt[below] += ways
        counts = nxt
    return sum(counts.values())


def asm_formula(n):
    """Published product, kept separate from transfer recurrence."""
    if type(n) is not int or not 0 <= n <= 14:
        raise ValueError("ASM formula supports n=0..14; n=0 is the empty matrix")
    numerator = denominator = 1
    for j in range(n):
        numerator *= factorial(3 * j + 1)
        denominator *= factorial(n + j)
    quotient, remainder = divmod(numerator, denominator)
    if remainder != 0:raise ArithmeticError('ASM quotient must be integral')
    return quotient


def torus_count(width, height):
    """Trace(T**height), using exact integers and conserved flux blocks."""
    dimension(width, 6, "periodic width"); dimension(height, MAX_HEIGHT, "height")
    total = 0
    by_sector = {}
    for k in range(width + 1):
        states = [x for x in range(1 << width) if x.bit_count() == k]
        index = {s: i for i, s in enumerate(states)}
        rows = []
        for a in states:
            entries = defaultdict(int)
            for b, _ in periodic_choices(width, a):
                if b.bit_count() != k:raise ArithmeticError('Flux sector mismatch')
                entries[index[b]] += 1
            rows.append(tuple(entries.items()))
        subtotal = 0
        for initial in range(len(states)):
            counts = [0] * len(states)
            counts[initial] = 1
            for _ in range(height):
                nxt = [0] * len(states)
                for i, count in enumerate(counts):
                    if count:
                        for j, weight in rows[i]:
                            nxt[j] += count * weight
                counts = nxt
            subtotal += counts[initial]
        by_sector[k] = subtotal
        total += subtotal
    return total, by_sector


def domain_tables(n):
    """Forward/backward exact completion counts for uniform sampling."""
    dimension(n)
    forward = [{(1 << n) - 1: 1}]
    for _ in range(n):
        nxt = defaultdict(int)
        for above, ways in forward[-1].items():
            for below, _ in row_choices(n, above, 0, 1):
                nxt[below] += ways
        forward.append(dict(nxt))
    backward = [{} for _ in range(n + 1)]
    backward[n] = {0: 1}
    for r in reversed(range(n)):
        backward[r] = {
            above: sum(backward[r + 1].get(below, 0)
                       for below, _ in row_choices(n, above, 0, 1))
            for above in forward[r]
        }
    if forward[n].get(0) != backward[0][(1 << n) - 1]:raise ArithmeticError('Completion-count mismatch')
    return forward, backward


def domain_sample(n, backward, rng):
    """Exact integer-weight draw from the uniform finite DW ensemble."""
    dimension(n)
    above = (1 << n) - 1
    horizontal, vertical = [], []
    for r in range(n):
        choices = row_choices(n, above, 0, 1)
        ticket = rng.randrange(backward[r][above])
        for below, h in choices:
            ways = backward[r + 1].get(below, 0)
            if ticket < ways:
                horizontal.append(h)
                vertical.append(below)
                above = below
                break
            ticket -= ways
        else:
            raise AssertionError("completion weights do not sum")
    if above != 0:raise ArithmeticError('Sample ended at wrong boundary')
    return horizontal, vertical


def domain_marginals(n, forward, backward):
    """Exact one-vertex counts, indexed by (left,up,right,down)."""
    dimension(n)
    result = [[defaultdict(int) for _ in range(n)] for _ in range(n)]
    z = backward[0][(1 << n) - 1]
    for r in range(n):
        for a, prefixes in forward[r].items():
            for b, h in row_choices(n, a, 0, 1):
                weight = prefixes * backward[r + 1].get(b, 0)
                if not weight:
                    continue
                for c in range(n):
                    l = (h >> (c - 1)) & 1 if c else 0
                    kind = (l, (a >> c) & 1, (h >> c) & 1, (b >> c) & 1)
                    if kind[0] + kind[1] != kind[2] + kind[3]:raise ArithmeticError('Invalid vertex')
                    result[r][c][kind] += weight
        if not all(sum(cell.values()) == z for cell in result[r]):raise ArithmeticError('Marginal total mismatch')
    return result


def torus_states(n):
    """Enumerate actual states (small n only), encode H then V bits."""
    if not 2 <= n <= 4:
        raise ValueError("state listing bounded to n=2..4")
    size = n * n

    def visit(row, initial, above, hs, vs):
        if row == n:
            if above == initial:
                yield hs | (vs << size)
            return
        for below, horizontal in periodic_choices(n, above):
            yield from visit(row + 1, initial, below,
                             hs | (horizontal << (row * n)),
                             vs | (below << (row * n)))

    for initial in range(1 << n):
        yield from visit(0, initial, initial, 0, 0)


def torus_flux(state, n):
    size = n * n
    qx = sum((state >> (r * n)) & 1 for r in range(n))
    qy = sum((state >> (size + c)) & 1 for c in range(n))
    return 2 * qx - n, 2 * qy - n


def plaquette_neighbors(state, n):
    """Flip only directed elementary cycles; all wrap plaquettes included."""
    size = n * n
    for r in range(n):
        for c in range(n):
            bits = (r * n + c,
                    size + r * n + (c + 1) % n,
                    ((r + 1) % n) * n + c,
                    size + r * n + c)
            pattern = tuple((state >> bit) & 1 for bit in bits)
            if pattern in ((1, 1, 0, 0), (0, 0, 1, 1)):
                yield state ^ sum(1 << bit for bit in bits)
