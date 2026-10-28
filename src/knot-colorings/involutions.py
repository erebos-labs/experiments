"""Bounded enumeration for involutory quandle colorings from a signed Gauss code.

No orientation-sign data is needed: operation is its own inverse in the second
argument, so the two underpasses are interchangeable. Results depend on supplied
realizable source data. Not a knot-recognition program.
"""
from itertools import combinations, permutations, product


def crossings(code):
    labels=sorted({abs(x) for x in code})
    if len(code) != 2*len(labels) or any(code.count(x) != 1 or code.count(-x) != 1 for x in labels):
        raise ValueError('Invalid single-component Gauss code')
    if not code:
        return [],1
    n=len(labels); current=n-1; overs={}; unders={}
    for event in code:
        if event > 0:
            overs[event]=current
        else:
            unders[-event]=(current,(current+1)%n); current=(current+1)%n
    return [(overs[x],*unders[x]) for x in labels],n


def make_plan(n,equations,seeds):
    known=set(seeds); plan=[]
    while len(known) < n:
        changed=False
        for over,u,v in equations:
            if over not in known:
                continue
            if u in known and v not in known:
                plan.append((u,over,v)); known.add(v); changed=True
            elif v in known and u not in known:
                plan.append((v,over,u)); known.add(u); changed=True
        if not changed:
            return None
    return plan


def find_seeds(n,equations,max_seeds=4):
    for k in range(1,min(max_seeds,n)+1):
        for seeds in combinations(range(n),k):
            plan=make_plan(n,equations,seeds)
            if plan is not None:
                return seeds,plan
    raise ValueError('No propagation seed set within budget')


def solutions(code,table):
    equations,n=crossings(code); q=len(table)
    seeds,plan=find_seeds(n,equations)
    budget=q**len(seeds)
    if budget > 100_000:
        raise ValueError('Seed-assignment budget exceeded')
    result=[]
    for seed_values in product(range(q),repeat=len(seeds)):
        values=[None]*n
        for index,value in zip(seeds,seed_values):
            values[index]=value
        for under,over,target in plan:
            values[target]=table[values[under]][values[over]]
        if all(values[v] == table[values[u]][values[o]] for o,u,v in equations):
            result.append(tuple(values))
    return {'seeds':seeds,'plan':plan,'assignments':budget,'solutions':result}


def compose(a,b):
    return tuple(a[b[i]] for i in range(len(a)))


def conjugation_table(elements):
    indices={element:i for i,element in enumerate(elements)}
    return [[indices[compose(compose(over,under),over)] for over in elements] for under in elements]


def involutions(n,moved):
    identity=tuple(range(n))
    return [p for p in permutations(range(n)) if compose(p,p)==identity and sum(p[i] != i for i in range(n))==moved]


def fox_table(q):
    return [[(2*over-under)%q for over in range(q)] for under in range(q)]


def check_axioms(table):
    q=len(table)
    assert all(len(row)==q and all(type(x) is int and 0 <= x < q for x in row) for row in table)
    assert all(table[x][x] == x for x in range(q)), 'idempotence'
    assert all(table[table[x][y]][y] == x for x,y in product(range(q),repeat=2)), 'involutivity'
    assert all(table[table[x][y]][z] == table[table[x][z]][table[y][z]] for x,y,z in product(range(q),repeat=3)), 'self-distributivity'
    return True
