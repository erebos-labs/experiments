"""Small, dependency-free conjugacy colorings. No search beyond specified PSL(2,p)."""
from itertools import product
from involutions import find_seeds


def canonical(m,p):
    return min(tuple(x % p for x in m),tuple((-x) % p for x in m))


def mul(a,b,p):
    x,y,z,w=a; e,f,g,h=b
    return canonical((x*e+y*g,x*f+y*h,z*e+w*g,z*f+w*h),p)


def inverse(a,p):
    x,y,z,w=a
    return canonical((w,-y,-z,x),p)


def psl(p):
    if p not in (3,5,7):
        raise ValueError('Only the declared small prime fields are in scope')
    return sorted({canonical((a,b,c,d),p) for a,b,c,d in product(range(p),repeat=4) if (a*d-b*c)%p==1})


def conjugacy_class(group,base,p):
    return sorted({mul(mul(inverse(g,p),base,p),g,p) for g in group})


def tables(elements,p):
    index={x:i for i,x in enumerate(elements)}
    forward=[[index[mul(mul(inverse(o,p),u,p),o,p)] for o in elements] for u in elements]
    backward=[[index[mul(mul(o,u,p),inverse(o,p),p)] for o in elements] for u in elements]
    return forward,backward


def pd_constraints(pd):
    """Knot Atlas oriented PD: under-in a, then b,c,d counterclockwise.

    Edge numbers increase along the single component. Over d->b is positive;
    over b->d is negative. Relation is out = over^-epsilon * in * over^epsilon.
    """
    edge_count=2*len(pd)
    if not pd or any(len(x)!=4 for x in pd):
        raise ValueError('Expected nonempty four-edge PD crossings')
    flat=[edge for crossing in pd for edge in crossing]
    if sorted(set(flat)) != list(range(1,edge_count+1)) or any(flat.count(edge)!=2 for edge in set(flat)):
        raise ValueError('Edges must be 1..2c, each used twice')
    parent=list(range(edge_count+1))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    successor=lambda x: x % edge_count+1
    signs=[]
    for a,b,c,d in pd:
        if successor(a)!=c:
            raise ValueError('Under-edge orientation is inconsistent')
        if successor(d)==b:
            signs.append(1)
        elif successor(b)==d:
            signs.append(-1)
        else:
            raise ValueError('Over-edge orientation is inconsistent')
        parent[find(b)]=find(d)
    roots=sorted({find(x) for x in range(1,edge_count+1)}); indices={x:i for i,x in enumerate(roots)}
    edges={x:indices[find(x)] for x in range(1,edge_count+1)}
    return [(edges[b],edges[a],edges[c],sign) for (a,b,c,d),sign in zip(pd,signs)],len(roots),edges


def count_fixed(pd,forward,backward,fixed=0):
    equations,n,edges=pd_constraints(pd)
    q=len(forward)
    if not 0 <= fixed < q:
        raise ValueError('Invalid fixed color')
    seeds,_=find_seeds(n,[(o,u,v) for o,u,v,_ in equations])
    # Rebuild the plan with the sign attached to its direction.
    known=set(seeds); plan=[]
    while len(known)<n:
        changed=False
        for o,u,v,sign in equations:
            if o not in known:
                continue
            if u in known and v not in known:
                plan.append((u,o,v,sign));known.add(v);changed=True
            elif v in known and u not in known:
                plan.append((v,o,u,-sign));known.add(u);changed=True
        if not changed:
            raise ValueError('Propagation plan stalled')
    budget=q**(len(seeds)-1)
    if budget>100_000:
        raise ValueError('Fixed-seed assignment budget exceeded')
    solutions=[]
    for seed_values in product(range(q),repeat=len(seeds)-1):
        values=[None]*n; values[seeds[0]]=fixed
        for index,value in zip(seeds[1:],seed_values):
            values[index]=value
        for u,o,target,sign in plan:
            values[target]=(forward if sign>0 else backward)[values[u]][values[o]]
        if all(values[v]==(forward if sign>0 else backward)[values[u]][values[o]] for o,u,v,sign in equations):
            solutions.append(tuple(values))
    return {'seeds':seeds,'plan':plan,'fixed_color':fixed,'assignments':budget,'normalized_count':len(solutions),'solutions':solutions,'edge_arcs':edges}
