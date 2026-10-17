"""Independent exact checks; run with python3 test_model.py -v."""

from collections import Counter
from fractions import Fraction
from itertools import combinations, permutations, product
from math import comb, factorial
import unittest

from model import (apply_positions, carry_counts, descents, enumerate_forward,
                   eulerian, forward_from_word, inverse, inverse_descent_counts,
                   permutation_weight, stable_deal, summarize, top_card_counts,
                   tv_counts)
from joint import conditional_summary, joint_eulerian


def direct_cut_interleave(n):
    """Enumerate binomial cuts then uniformly chosen interleavings.

    Every cut/interleaving path has weight 1/2**n: the binomial cut mass
    C(n,c)/2**n cancels the C(n,c) possible interleavings. This construction
    does not use permutation inversion or the closed-form weight.
    """
    outcomes = Counter()
    for cut in range(n + 1):
        for left_positions in combinations(range(n), cut):
            left_positions = set(left_positions)
            left, right = iter(range(cut)), iter(range(cut, n))
            deck = tuple(next(left) if j in left_positions else next(right)
                         for j in range(n))
            outcomes[deck] += 1
    return outcomes


class ExactShuffleChecks(unittest.TestCase):
    def test_inverse_round_trip(self):
        for n in range(1, 8):
            for deck in permutations(range(n)):
                self.assertEqual(inverse(inverse(deck)), deck)

    def test_eulerian_against_all_permutations(self):
        for n in range(1, 9):
            actual = Counter(descents(p) for p in permutations(range(n)))
            self.assertEqual(tuple(actual[j] for j in range(n)), eulerian(n))

    def test_forward_labels_against_cut_and_interleave(self):
        for n in range(1, 9):
            self.assertEqual(enumerate_forward(n, 2), direct_cut_interleave(n))

    def test_permutation_probability_and_both_marginals(self):
        for n, a in [(1, 3), (3, 4), (4, 2), (5, 3), (6, 4), (7, 3)]:
            distribution = enumerate_forward(n, a)
            visible, hidden, top = Counter(), Counter(), Counter()
            for deck in permutations(range(n)):
                weight = permutation_weight(n, a, descents(inverse(deck)))
                self.assertEqual(distribution[deck], weight, (n, a, deck))
                visible[descents(deck)] += distribution[deck]
                hidden[descents(inverse(deck))] += distribution[deck]
                top[deck[0]] += distribution[deck]
            self.assertEqual([visible[j] for j in range(n)], carry_counts(n, a))
            self.assertEqual([hidden[j] for j in range(n)], inverse_descent_counts(n, a))
            self.assertEqual([top[j] for j in range(n)], top_card_counts(n, a))

    def test_shuffle_composition(self):
        for n, a, b in [(3, 2, 3), (4, 2, 2), (4, 2, 3)]:
            first, second = enumerate_forward(n, a), enumerate_forward(n, b)
            composed = Counter()
            for p, pcount in first.items():
                for q, qcount in second.items():
                    composed[apply_positions(p, q)] += pcount * qcount
            self.assertEqual(composed, enumerate_forward(n, a * b))

    def test_carry_formula_against_direct_digit_sums(self):
        for n, base in [(2, 2), (3, 10), (4, 3), (5, 4)]:
            words = tuple(product(range(base), repeat=n))
            for incoming in range(n):
                actual = Counter((incoming + sum(w)) // base for w in words)
                self.assertEqual([actual[j] for j in range(n)],
                                 carry_counts(n, base, incoming))

    def test_carry_semigroup_and_stationarity(self):
        for n, a, b in [(3, 2, 10), (5, 2, 3), (8, 3, 4)]:
            pa = [carry_counts(n, a, i) for i in range(n)]
            pb = [carry_counts(n, b, i) for i in range(n)]
            for i in range(n):
                composed = [sum(pa[i][h] * pb[h][j] for h in range(n))
                            for j in range(n)]
                self.assertEqual(composed, carry_counts(n, a * b, i))
            stationary = eulerian(n)
            self.assertEqual([sum(stationary[i] * pa[i][j] for i in range(n))
                              for j in range(n)],
                             [x * a ** n for x in stationary])

    def test_joint_counts_against_all_permutations(self):
        for n in range(1, 9):
            actual = Counter((descents(inverse(p)), descents(p))
                             for p in permutations(range(n)))
            matrix = joint_eulerian(n)
            self.assertEqual(matrix, [[actual[i, j] for j in range(n)]
                                      for i in range(n)])

    def test_whole_deck_tv_equals_hidden_statistic_tv(self):
        for n, a in [(3, 2), (4, 3), (6, 4)]:
            distribution = enumerate_forward(n, a)
            actual = sum(abs(Fraction(distribution[p], a ** n)
                             - Fraction(1, factorial(n)))
                         for p in permutations(range(n))) / 2
            self.assertEqual(actual, tv_counts(inverse_descent_counts(n, a),
                                              a ** n, eulerian(n), factorial(n)))

    def test_visible_and_hidden_are_not_interchangeable(self):
        deck = (0, 2, 4, 1, 3, 5)
        self.assertEqual(descents(deck), 1)
        self.assertEqual(descents(inverse(deck)), 2)
        self.assertEqual(permutation_weight(6, 2, descents(inverse(deck))), 0)
        self.assertNotEqual(permutation_weight(6, 2, descents(deck)), 0)

    def test_paper_table_rounded_values(self):
        expected = [1, 1, 1, 1, .924, .614, .334, .167, .085, .043]
        for k, rounded in enumerate(expected, 1):
            self.assertAlmostEqual(summarize(52, k, include_top=False)["deck_tv"],
                                   rounded, delta=.0005)

    def test_52_joint_marginals_and_carries(self):
        n, matrix = 52, joint_eulerian(52)
        self.assertTrue(all(x >= 0 for row in matrix for x in row))
        self.assertEqual([sum(row) for row in matrix], list(eulerian(n)))
        self.assertEqual(matrix, list(map(list, zip(*matrix))))
        for k in range(13):
            a = 2 ** k
            weighted = [sum(matrix[i][j] * permutation_weight(n, a, i)
                            for i in range(n)) for j in range(n)]
            self.assertEqual(weighted, carry_counts(n, a))
            self.assertEqual(sum(weighted), a ** n)

    def test_normalization_and_data_processing(self):
        for n in [2, 8, 16, 32, 52, 104, 208, 312]:
            for k in range(16):
                a, den = 2 ** k, 2 ** (n * k)
                hidden, visible = inverse_descent_counts(n, a), carry_counts(n, a)
                self.assertEqual(sum(hidden), den)
                self.assertEqual(sum(visible), den)
                self.assertTrue(all(x >= 0 for x in hidden + visible))
                deck_tv = tv_counts(hidden, den, eulerian(n), factorial(n))
                visible_tv = tv_counts(visible, den, eulerian(n), factorial(n))
                separation = 1 - Fraction(factorial(n) * comb(a, n), den) if a >= n else 1
                self.assertLessEqual(visible_tv, deck_tv)
                self.assertLessEqual(deck_tv, separation)


if __name__ == '__main__':
    unittest.main()
