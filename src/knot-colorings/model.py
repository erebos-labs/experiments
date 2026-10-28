"""Exact Fox-coloring experiments; standard library only.

Convention: positive i means left strand i passes OVER strand i+1.
Numbers in words are one-based; arrays are zero-based.
No knot-recognition or simplification algorithm is claimed.
"""
from itertools import product
from math import isqrt


def validate(strands, word):
    if type(strands) is not int or not 1 <= strands <= 4:
        raise ValueError("Use 1 to 4 strands")
    if len(word) > 16 or any(type(x) is not int or not 0 < abs(x) < strands for x in word):
        raise ValueError("Use at most 16 signed crossing indices between 1 and strands-1")


def modulus_ok(q):
    if type(q) is not int or not 2 <= q <= 31:
        raise ValueError("Use an integer modulus from 2 to 31")


def prime(q):
    return q >= 2 and all(q % d for d in range(2, isqrt(q) + 1))


def propagate(colors, word, q):
    """One crossing follows directly from 2*over = under_in + under_out."""
    out = list(colors)
    for crossing in word:
        i = abs(crossing)-1
        a, b = out[i:i+2]
        out[i:i+2] = [(2*a-b) % q, a] if crossing > 0 else [b, (2*b-a) % q]
    return tuple(out)


def enumerate_colorings(strands, word, q):
    validate(strands, word); modulus_ok(q)
    if q ** strands > 200_000:
        raise ValueError("Enumeration budget exceeded")
    return [x for x in product(range(q), repeat=strands) if propagate(x, word, q) == x]


def components(strands, word):
    validate(strands, word)
    perm = list(range(strands))
    for crossing in word:
        i = abs(crossing)-1
        perm[i], perm[i+1] = perm[i+1], perm[i]
    seen = set(); cycles = []
    for start in range(strands):
        if start in seen:
            continue
        cycle = []; j = start
        while j not in seen:
            seen.add(j); cycle.append(j); j = perm[j]
        cycles.append(cycle)
    return cycles


def transfer_matrix(strands, word):
    """Integer matrix: bottom colors = M * top colors, reduced modulo q later."""
    validate(strands, word)
    rows = [[int(i == j) for j in range(strands)] for i in range(strands)]
    for crossing in word:
        i = abs(crossing)-1
        a, b = rows[i:i+2]
        rows[i:i+2] = [[2*x-y for x, y in zip(a,b)], a] if crossing > 0 else [b, [2*y-x for x,y in zip(a,b)]]
    return rows


def fixed_matrix(strands, word):
    return [[v-int(i == j) for j,v in enumerate(row)] for i,row in enumerate(transfer_matrix(strands,word))]


def rank_mod(matrix, q, columns=None):
    """Field elimination ONLY. Composite moduli must use enumeration or certificates."""
    modulus_ok(q)
    if not prime(q):
        raise ValueError("Gaussian elimination requires prime modulus")
    a = [[x % q for x in row] for row in matrix]
    n = len(a[0]) if a else (columns or 0)
    r = 0
    for c in range(n):
        pivot = next((k for k in range(r,len(a)) if a[k][c]), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        inv = pow(a[r][c],-1,q)
        a[r] = [(v*inv) % q for v in a[r]]
        for k in range(len(a)):
            if k == r:
                continue
            f = a[k][c]
            a[k] = [(v-f*w) % q for v,w in zip(a[k],a[r])]
        r += 1
        if r == len(a):
            break
    return r


def linear_count(strands, word, q):
    return q ** (strands-rank_mod(fixed_matrix(strands,word),q,columns=strands))


def braid_arc_matrix(strands, word):
    """Independent representation: explicit arcs joined by closure, one crossing equation each."""
    validate(strands,word)
    positions = list(range(strands)); equations = []; parent = list(range(strands))
    for crossing in word:
        i = abs(crossing)-1
        left,right = positions[i:i+2]
        new = len(parent); parent.append(new)
        over,under = (left,right) if crossing > 0 else (right,left)
        equations.append((over,under,new))
        positions[i:i+2] = [new,over] if crossing > 0 else [over,new]
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i,bottom in enumerate(positions):
        parent[find(bottom)] = find(i)
    roots = sorted({find(i) for i in range(len(parent))}); indices = {x:i for i,x in enumerate(roots)}
    matrix = []
    for over,u,v in equations:
        row = [0]*len(roots)
        for arc,coefficient in ((over,2),(u,-1),(v,-1)):
            row[indices[find(arc)]] += coefficient
        matrix.append(row)
    return matrix,len(roots)


def gauss_matrix(code):
    """Single-component Knot Atlas code: positive=over, negative=under.

    This accepts signed event data, not arbitrary geometric realizability claims.
    """
    if not code:
        return [],1
    if any(type(x) is not int or x == 0 for x in code):
        raise ValueError("Gauss events must be nonzero integers")
    labels = sorted({abs(x) for x in code})
    if len(code) != 2*len(labels) or any(code.count(x) != 1 or code.count(-x) != 1 for x in labels):
        raise ValueError("Each crossing must occur once over and once under")
    m = len(labels); arc = m-1; over = {}; under = {}
    for event in code:
        if event < 0:
            under[-event] = (arc,(arc+1) % m); arc = (arc+1) % m
        else:
            over[event] = arc
    matrix = []
    for crossing in labels:
        row = [0]*m; row[over[crossing]] += 2
        for endpoint in under[crossing]:
            row[endpoint] -= 1
        matrix.append(row)
    return matrix,m


def determinant(matrix):
    """Fraction-free Bareiss elimination, with exact divisibility checks."""
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("Determinant requires square matrix")
    if n == 0:
        return 1
    a = [row[:] for row in matrix]; previous = 1; sign = 1
    for k in range(n-1):
        pivot = next((i for i in range(k,n) if a[i][k]),None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k],a[pivot] = a[pivot],a[k]; sign *= -1
        p = a[k][k]
        for i in range(k+1,n):
            for j in range(k+1,n):
                numerator = a[i][j]*p-a[i][k]*a[k][j]
                if numerator % previous:
                    raise ArithmeticError("Bareiss division was not exact")
                a[i][j] = numerator//previous
            a[i][k] = 0
        previous = p
    return sign*a[-1][-1]


def minor(matrix,row=0,column=0):
    return [[x for j,x in enumerate(values) if j != column] for i,values in enumerate(matrix) if i != row]


PRESETS = {
    "unknot": {"name":"Unknot with a curl", "strands":2,"word":[1]},
    "trefoil": {"name":"Trefoil", "strands":2,"word":[1,1,1]},
    "figure8": {"name":"Figure-eight", "strands":3,"word":[1,-2,1,-2]},
    "nine_twists": {"name":"Nine-twist torus knot T(2,9)","strands":2,"word":[1]*9},
    "double_trefoil": {"name":"Connected pair of trefoils","strands":3,"word":[1,1,1,2,2,2]},
}
GAUSS = {
    "trefoil":[-1,3,-2,1,-3,2],
    "figure8":[1,-4,3,-1,2,-3,4,-2],
    "conway":[1,-4,2,-1,3,-7,4,-2,-5,11,-6,-3,7,10,-8,5,-9,6,-10,8,-11,9],
}
