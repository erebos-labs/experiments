"""Exact ideal-riffle calculations, Python standard library only.

Conventions matter: a deck is a tuple of zero-based original card labels in
top-to-bottom order. d(deck) counts adjacent downward steps. d(inverse(deck))
counts original consecutive labels whose positions are reversed. The latter
determines the probability of a *forward* GSR riffle shuffle.

Sources: Bayer & Diaconis (1992), Theorem 1; Diaconis & Fulman (2009),
equations (1.1), (1.2), Theorem 2.3. Primary links are listed in README.md and THIRD_PARTY_NOTICES.md.
"""

from collections import Counter
from fractions import Fraction
from functools import lru_cache
from itertools import product
from math import comb, factorial, log2


def choose(n, k):
    """Combinatorial binomial, zero outside its nonnegative support."""
    return comb(n, k) if n >= k >= 0 else 0


def descents(deck):
    return sum(a > b for a, b in zip(deck, deck[1:]))


def inverse(deck):
    result = [0] * len(deck)
    for position, label in enumerate(deck):
        result[label] = position
    return tuple(result)


def stable_deal(labels):
    """Inverse a-shuffle of the identity, one independent label per card."""
    return tuple(sorted(range(len(labels)), key=labels.__getitem__))


def forward_from_word(word):
    """An exact forward a-shuffle represented by an equiprobable label word."""
    return inverse(stable_deal(word))


def apply_positions(deck, permutation):
    return tuple(deck[i] for i in permutation)


@lru_cache(maxsize=None)
def eulerian(n):
    """A(n,j), j=0,...,n-1, via insertion of the largest label."""
    if n < 1:
        raise ValueError("n must be positive")
    if n == 1:
        return (1,)
    previous = eulerian(n - 1)
    return tuple(
        (j + 1) * (previous[j] if j < n - 1 else 0)
        + (n - j) * (previous[j - 1] if j > 0 else 0)
        for j in range(n)
    )


def permutation_weight(n, a, inverse_descent_count):
    """Probability numerator with common denominator a**n."""
    return choose(a + n - inverse_descent_count - 1, n)


def inverse_descent_counts(n, a):
    """Whole-deck likelihood classes, counted among a**n equiprobable words."""
    return [
        count * permutation_weight(n, a, j)
        for j, count in enumerate(eulerian(n))
    ]


def carry_counts(n, a, incoming=0):
    """Counts for floor((incoming + sum(n iid digits 0..a-1))/a).

    Exact inclusion-exclusion for bounded compositions, with integer
    cancellation before conversion to probabilities. `incoming` belongs to
    0..n-1 when used as a carries-chain state.
    """
    return [
        sum(
            (-1) ** ell * choose(n + 1, ell)
            * choose(n - 1 - incoming + (j + 1 - ell) * a, n)
            for ell in range(j + 1)
        )
        for j in range(n)
    ]


def top_card_counts(n, a):
    """Forward shuffle top-label probabilities, numerator over a**n.

    Its top label is the position of original label 0 after the inverse
    shuffle. Conditional on 0's random label ell, its new position counts
    the other n-1 labels strictly below ell; ties follow it by stable sorting.
    """
    return [
        comb(n - 1, j) * sum(
            ell ** j * (a - ell) ** (n - 1 - j) for ell in range(a)
        )
        for j in range(n)
    ]


def tv_counts(left, left_den, right, right_den):
    return Fraction(
        sum(abs(x * right_den - y * left_den) for x, y in zip(left, right)),
        2 * left_den * right_den,
    )


def probabilities(counts, denominator):
    return [float(Fraction(value, denominator)) for value in counts]


def mean_counts(counts, denominator):
    return Fraction(sum(i * value for i, value in enumerate(counts)), denominator)


def summarize(n, k, include_top=True):
    a, den, fact = 2 ** k, 2 ** (k * n), factorial(n)
    uniform = eulerian(n)
    hidden = inverse_descent_counts(n, a)
    visible = carry_counts(n, a)
    deck_tv = tv_counts(hidden, den, uniform, fact)
    visible_tv = tv_counts(visible, den, uniform, fact)
    min_ratio = Fraction(fact * choose(a, n), den)
    max_ratio = Fraction(fact * choose(a + n - 1, n), den)
    # The optimal binary event contains precisely the likelihood classes > 1.
    optimal_classes = [j for j in range(n)
                       if fact * permutation_weight(n, a, j) > den]
    cutoff = max(optimal_classes, default=-1)
    result = {
        "n": n, "k": k, "a": a,
        "deck_tv": float(deck_tv),
        "deck_tv_fraction": str(deck_tv),
        "visible_descents_tv": float(visible_tv),
        "separation": float(1 - min_ratio),
        "reverse_order_likelihood_ratio": float(min_ratio),
        "identity_likelihood_ratio": float(max_ratio),
        "hidden_mean": float(mean_counts(hidden, den)),
        "visible_mean": float(mean_counts(visible, den)),
        "uniform_mean": float(Fraction(n - 1, 2)),
        "uniform_probability": probabilities(uniform, fact),
        "inverse_descents_probability": probabilities(hidden, den),
        "visible_descents_probability": probabilities(visible, den),
        "optimal_event": {
            "inverse_descents_at_most": cutoff,
            "under_shuffle": float(Fraction(sum(hidden[:cutoff + 1]), den)),
            "under_uniform": float(Fraction(sum(uniform[:cutoff + 1]), fact)),
            "equal_prior_classification_accuracy": float((1 + deck_tv) / 2),
        },
        "entropy_deficit_bits": sum(
            float(Fraction(count, den)) * log2(float(Fraction(fact * weight, den)))
            for j, count in enumerate(hidden)
            if (weight := permutation_weight(n, a, j)) and count
        ),
    }
    if include_top:
        top = top_card_counts(n, a)
        result.update(top_card_tv=float(tv_counts(top, den, [1] * n, n)),
                      top_card_probability=probabilities(top, den))
    return result


def enumerate_forward(n, a):
    """Independent finite sample space used only for small-deck checks."""
    return Counter(forward_from_word(word) for word in product(range(a), repeat=n))
