"""Joint visible/inverse descent counts via a bivariate Eulerian identity.

D[i][j] counts permutations with i inverse descents and j visible descents.
Diaconis--Fulman (2009), Section 2, uses the identity

 sum D[i][j] s**(i+1)t**(j+1) / ((1-s)**(n+1)(1-t)**(n+1))
     = sum_{a,b>=0} C(n+a*b-1,n) s**a t**b.

Finite differences extract the coefficients. No floating arithmetic enters
the counts. The model tests verify these against literal permutation counts.
"""

from fractions import Fraction
from math import comb, factorial

from model import choose, permutation_weight


def joint_eulerian(n):
    h = [[choose(n + a * b - 1, n) for b in range(1, n + 1)]
         for a in range(1, n + 1)]
    differences = [[(-1) ** (i - a) * comb(n + 1, i - a)
                    for a in range(i + 1)] for i in range(n)]
    left = [[sum(c * h[a][b] for a, c in enumerate(differences[i]))
             for b in range(n)] for i in range(n)]
    return [[sum(c * left[i][b] for b, c in enumerate(differences[j]))
             for j in range(n)] for i in range(n)]


def joint_probabilities(joint, a):
    n = len(joint)
    denominator = a ** n
    return [[float(Fraction(count * permutation_weight(n, a, i), denominator))
             for count in row] for i, row in enumerate(joint)]


def conditional_summary(joint, a, visible_values):
    """Compare shuffled vs uniform, both conditioned on the same visible event."""
    n, fact, den = len(joint), factorial(len(joint)), a ** len(joint)
    multiplicities = [sum(row[j] for j in visible_values) for row in joint]
    shuffled_counts = [count * permutation_weight(n, a, i)
                       for i, count in enumerate(multiplicities)]
    shuffled_total, uniform_total = sum(shuffled_counts), sum(multiplicities)
    if not shuffled_total or not uniform_total:
        return {"visible_values": list(visible_values), "possible": False}
    tv = Fraction(sum(abs(q * uniform_total - u * shuffled_total)
                      for q, u in zip(shuffled_counts, multiplicities)),
                  2 * shuffled_total * uniform_total)
    return {
        "visible_values": list(visible_values), "possible": True,
        "event_probability_shuffled": float(Fraction(shuffled_total, den)),
        "event_probability_uniform": float(Fraction(uniform_total, fact)),
        "conditional_deck_tv": float(tv),
        "conditional_hidden_mean_shuffled": float(Fraction(
            sum(i * q for i, q in enumerate(shuffled_counts)), shuffled_total)),
        "conditional_hidden_mean_uniform": float(Fraction(
            sum(i * u for i, u in enumerate(multiplicities)), uniform_total)),
        "conditional_inverse_descents_shuffled": [
            float(Fraction(q, shuffled_total)) for q in shuffled_counts],
        "conditional_inverse_descents_uniform": [
            float(Fraction(u, uniform_total)) for u in multiplicities],
    }
