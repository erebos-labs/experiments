"""Exact pattern races for an iid binary coin, using only the standard library.

Independent formulations:
  1. Proper-prefix absorbing Markov chain, exact Fraction elimination.
  2. Weighted suffix/prefix overlap formula, with no Markov state use.
  3. Finite-horizon raw-tail enumeration, with rigorous surviving-mass bounds.

Domain: distinct, nonempty H/T patterns with no containment; 0 < p(H) < 1.
All waiting times count flips from empty history. No simulation is required.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product


def words(n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("word length must be a positive integer")
    return ["".join(x) for x in product("HT", repeat=n)]


def validate(patterns, p):
    patterns = tuple(patterns)
    p = F(p)
    if not 0 < p < 1:
        raise ValueError("p(H) must be strictly between 0 and 1")
    if not patterns or any(not isinstance(x, str) or not x or set(x)-set("HT") for x in patterns):
        raise ValueError("nonempty H/T patterns required")
    if len(set(patterns)) != len(patterns):
        raise ValueError("patterns must be distinct")
    if any(x in y for i, x in enumerate(patterns) for j, y in enumerate(patterns) if i != j):
        raise ValueError("contained patterns have ambiguous/forced first-hit semantics")
    return patterns, p


def solve_linear(matrix, rhs):
    """Gauss-Jordan elimination for one or more exact right hand sides."""
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix) or len(rhs) != n:
        raise ValueError("invalid dimensions")
    k = len(rhs[0])
    if not k or any(len(row) != k for row in rhs):
        raise ValueError("inconsistent right hand sides")
    a = [[F(x) for x in matrix[i] + rhs[i]] for i in range(n)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if a[r][col]), None)
        if pivot is None:
            raise ValueError("singular system")
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [v / scale for v in a[col]]
        for r in range(n):
            if r != col and a[r][col]:
                scale = a[r][col]
                a[r] = [x - scale*y for x, y in zip(a[r], a[col])]
    return [row[n:] for row in a]


@dataclass
class Chain:
    patterns: tuple
    p_heads: F
    states: list
    transitions: dict
    matrix: list
    probabilities: list
    means: list
    variances: list
    winner_time_moments: list

    @property
    def wins(self):
        return self.probabilities[0]

    @property
    def mean(self):
        return self.means[0]

    @property
    def variance(self):
        return self.variances[0]

    @property
    def conditional_means(self):
        return [h/q if q else None for h, q in zip(self.winner_time_moments[0], self.wins)]


def markov(patterns, p=F(1, 2)):
    patterns, p = validate(patterns, p)
    states = sorted({""} | {w[:k] for w in patterns for k in range(1, len(w))}, key=lambda x:(len(x), x))
    index = {s:i for i, s in enumerate(states)}
    m, k = len(states), len(patterns)
    matrix = [[F(i == j) for j in range(m)] for i in range(m)]
    rhs = [[F(0)]*k + [F(1)] for _ in states]
    transitions = {}
    for i, state in enumerate(states):
        for symbol, probability in (("H", p), ("T", 1-p)):
            tail = state + symbol
            terminal = next((j for j,w in enumerate(patterns) if tail.endswith(w)), None)
            if terminal is not None:
                rhs[i][terminal] += probability
                transitions[state, symbol] = ("winner", terminal)
            else:
                following = max((s for s in states if tail.endswith(s)), key=len)
                matrix[i][index[following]] -= probability
                transitions[state, symbol] = ("state", following)
    result = solve_linear(matrix, rhs)
    probabilities = [r[:k] for r in result]
    means = [r[k] for r in result]
    # M E[T^2] = 2 E[T] - 1. M E[T 1_win_j] = P(win_j).
    moment_rhs = [[2*means[i]-1] + probabilities[i] for i in range(m)]
    moments = solve_linear(matrix, moment_rhs)
    variances = [moments[i][0] - means[i]**2 for i in range(m)]
    return Chain(patterns, p, states, transitions, matrix, probabilities, means, variances,
                 [r[1:] for r in moments])


def word_probability(word, p=F(1, 2)):
    p = F(p)
    return p**word.count("H") * (1-p)**word.count("T")


def overlap(terminal, target, p=F(1, 2)):
    """Sum 1/P(target prefix) for nonempty suffix/prefix matches.

    Direction matters: terminal's suffix matches target's prefix.
    For a fair coin this is twice the usual Conway leading number.
    """
    return sum((1/word_probability(target[:k], p)
                for k in range(1, min(len(terminal), len(target))+1)
                if terminal[-k:] == target[:k]), F(0))


def pair_formula(a, b, p=F(1, 2)):
    (a, b), p = validate((a, b), p)
    aa, ab, ba, bb = (overlap(x,y,p) for x,y in ((a,a),(a,b),(b,a),(b,b)))
    denominator = aa-ab+bb-ba
    p_b = (aa-ab)/denominator
    mean = (aa*bb-ab*ba)/denominator
    return {"p_b":p_b, "mean":mean, "overlaps":[[aa, ab],[ba, bb]]}


def finite_horizon(patterns, horizon, p=F(1, 2)):
    """Exact masses by literal last max_length-1 flips, no prefix automaton.

    The survival probability is an absolute error bound on each eventual win
    probability. Mean lies between truncated_mean and mean_upper: after any
    surviving history, a fresh block spelling the first pattern ends the game,
    so expected remaining time <= len(first)/P(first).
    """
    patterns, p = validate(patterns, p)
    if not isinstance(horizon, int) or horizon < 0:
        raise ValueError("nonnegative integer horizon required")
    width = max(map(len, patterns))-1
    live, wins = {"":F(1)}, [F(0)]*len(patterns)
    truncated_mean, trace = F(0), []
    for t in range(1, horizon+1):
        truncated_mean += sum(live.values())
        following = {}
        for tail, mass in live.items():
            for letter, chance in (("H",p),("T",1-p)):
                extended = tail+letter
                terminal = next((j for j,w in enumerate(patterns) if extended.endswith(w)), None)
                branch = mass*chance
                if terminal is not None:
                    wins[terminal] += branch
                else:
                    suffix = extended[-width:] if width else ""
                    following[suffix] = following.get(suffix,F(0))+branch
        live = following
        survival = sum(live.values(),F(0))
        trace.append({"flips":t,"wins":wins[:],"survival":survival})
    survival = sum(live.values(),F(0))
    bound = F(len(patterns[0]))/word_probability(patterns[0],p)
    return {"wins":wins, "survival":survival, "trace":trace,
            "truncated_mean":truncated_mean, "mean_upper":truncated_mean+survival*bound}


def brute_horizon(patterns, horizon, p=F(1,2)):
    """Enumerate complete horizon-long strings and scan their first hits."""
    patterns, p = validate(patterns,p)
    wins, survival = [F(0)]*len(patterns), F(0)
    for letters in product("HT",repeat=horizon):
        sequence = "".join(letters)
        mass = word_probability(sequence,p)
        winner = None
        for t in range(1,horizon+1):
            winner = next((j for j,w in enumerate(patterns) if sequence[:t].endswith(w)),None)
            if winner is not None:
                wins[winner] += mass
                break
        if winner is None:
            survival += mass
    return {"wins":wins,"survival":survival}


def best_responses(a, p=F(1,2)):
    choices = [(b,pair_formula(a,b,p)["p_b"]) for b in words(len(a)) if b != a]
    best = max(q for _,q in choices)
    return [b for b,q in choices if q == best], best


def complement(word):
    return word.translate(str.maketrans("HT","TH"))


def fair_integer_overlap(x,y):
    return sum(1 << (k-1) for k in range(1,min(len(x),len(y))+1) if x[-k:] == y[:k])


def fair_best_responses(a, choices=None):
    """Integer overlap computation for bounded exhaustive fair-coin searches."""
    choices = words(len(a)) if choices is None else choices
    aa = fair_integer_overlap(a,a)
    best, selected = None, []
    for b in choices:
        if b == a:
            continue
        ab,ba,bb = (fair_integer_overlap(x,y) for x,y in ((a,b),(b,a),(b,b)))
        value = F(aa-ab,aa-ab+bb-ba)
        if best is None or value > best:
            best, selected = value,[b]
        elif value == best:
            selected.append(b)
    return selected,best


def count_occurrences(sequence, pattern):
    """All overlapping occurrences, unlike str.count."""
    return sum(sequence[i:i+len(pattern)] == pattern
               for i in range(len(sequence)-len(pattern)+1))


def fixed_count_distribution(a, b, horizon, p=F(1,2)):
    """Exact distribution of N_a-N_b after a fixed number of flips.

    Integer path weights avoid repeated Fraction arithmetic. If p=h/d,
    each H branch multiplies its weight by h and each T branch by d-h;
    normalize by d**horizon only at the end. States retain literal tails.
    This experiment keeps going after either pattern first appears.
    """
    (a,b),p=validate((a,b),p)
    if len(a)!=len(b):
        raise ValueError("fixed-count comparison uses equal-length patterns")
    if not isinstance(horizon,int) or horizon<0:
        raise ValueError("nonnegative integer horizon required")
    width=len(a)-1
    live={("",0):1}
    for _ in range(horizon):
        following={}
        for (tail,delta),mass in live.items():
            for letter,weight in (("H",p.numerator),("T",p.denominator-p.numerator)):
                extended=tail+letter
                change=int(extended.endswith(a))-int(extended.endswith(b))
                suffix=extended[-width:] if width else ""
                key=(suffix,delta+change)
                following[key]=following.get(key,0)+mass*weight
        live=following
    histogram={}
    for (tail,delta),mass in live.items():
        histogram[delta]=histogram.get(delta,0)+mass
    denominator=p.denominator**horizon
    return {delta:F(mass,denominator) for delta,mass in sorted(histogram.items())}


def score_outcomes(distribution):
    return {"a_more":sum((p for d,p in distribution.items() if d>0),F(0)),
            "tie":distribution.get(0,F(0)),
            "b_more":sum((p for d,p in distribution.items() if d<0),F(0))}


def overlap_race(patterns,p=F(1,2)):
    """Multi-pattern first-hit law from fair betting-chain payoff balances.

    Unknowns: probability of each terminal pattern and E[T]. For each target
    j, sum_i P(terminal_i) C(terminal_i,target_j) = E[T], plus sum_i P_i=1.
    Shares only the generic exact elimination routine with markov().
    """
    patterns,p=validate(patterns,p)
    k=len(patterns)
    matrix=[[overlap(terminal,target,p) for terminal in patterns]+[F(-1)]
            for target in patterns]
    matrix.append([F(1)]*k+[F(0)])
    rhs=[[F(0)] for _ in patterns]+[[F(1)]]
    result=solve_linear(matrix,rhs)
    return {"wins":[r[0] for r in result[:-1]],"mean":result[-1][0]}
