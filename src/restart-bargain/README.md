# The restart bargain

A finite random search can finish sooner on average while taking longer to finish half its runs. [Explore the bench](https://erebos-labs.github.io/experiments/restart-bargain/). This is an educational implementation of established stochastic-resetting ideas, not a new scientific result or real-world search recommendation.

## Model and observations

A fair nearest-neighbor walker uses sites 0 through L. Site 0 absorbs; an outward attempt at L stays at L. Starting at s, each blind-reset decision replaces a movement with probability r and returns to s. A reset consumes one tick, even at s. Optional integer cost c adds frozen ticks without movement or reset decisions. The baseline mean is finite.

At L = 40, s = 20, r = 0.00168 and c = 0:

| Objective | No reset | Blind reset | Selective reset |
| --- | ---: | ---: | ---: |
| Mean time in ticks | 1220 | 1158.4714 | 973.6560 |
| First tick with 50% completed | 774 | 785 | 658 |
| First tick with 90% completed | 2908 | 2670 | 2231 |
| First tick with 99% completed | 5969 | 5367 | 4486 |
| Completion by tick 400 | 32.0163% | 29.9305% | 34.2125% |

Selective reset acts only from sites strictly greater than s and requires position information. With zero extra delay, a common-step order coupling shows that it cannot finish later than the no-reset walk: the reset goes to s, while a walker at least s+1 cannot move below s in one tick. Absorption preserves the order. Extra return delay breaks this guarantee; at r = 0.25 and c = 80 the selective mean is about 1341.62, above the baseline 1220. No universal ordering between blind and selective reset is asserted.

## Exact small example and numerical limits

For L = 10, s = 5 and r = 1/32, independent rational arithmetic gives mean 131244641039171584/1738513239266431, about 75.49246 ticks, versus 80 without reset. Median is 51 versus 49. The included exact certificate records survival fractions bracketing both medians; verify.py regenerates and compares those values.

Means solve full transient equations. Percentiles propagate probability through 10,000 ticks and retain later values as >10,000; they are not renormalized completions. Charts sample every fourth tick and can smooth small parity effects. The default crossing has a one-tick reversal near ticks 881–883. Low-mean search is bounded grid/refinement evidence, not a proof of a unique global optimum. Floating-point thresholds can shift an integer quantile by a tick.

The UI fixes L = 40, bounds r to 0–0.25 and extra delay to 0–100 ticks. Underflow outside the displayed range raises an explicit error rather than pretending the mathematical mean is infinite. Blind reset at r = 1 never moves. This is a one-dimensional known-target model; sensing cost, energy, physical return travel, drift and unknown targets are outside scope. It does not establish that most paired individual searches become slower.

## Reproduce

Requires existing Python 3 and Node.js, no packages or network. From the repository root run `python3 -B src/restart-bargain/verify.py`. This runs 19 Python tests using independent dense-matrix and exact-rational references, 640 JavaScript/Python value comparisons across 80 seeded fixtures, certificate reproduction and generated-page parity. Run `python3 -B src/restart-bargain/make_reference.py` to regenerate the reference fixtures and selective table; `python3 -B src/restart-bargain/build.py` rebuilds the standalone source page. Root build.py also copies it to docs/restart-bargain/index.html.

The browser core and Python solvers are inspectable and dependency-free. Desktop/narrow Chromium controls were checked. Other engines, physical devices and assistive technology remain untested. Runtime computation makes no network requests. Primary-source links open when selected; GitHub hosting may log visits.

## Primary sources and rights

- [Evans and Majumdar (2011), Diffusion with Stochastic Resetting](https://arxiv.org/abs/1102.2704): Brownian resetting and mean first passage; the finite discrete boundary here differs.
- [Evans and Majumdar (2011), Diffusion with Optimal Resetting](https://arxiv.org/abs/1107.4225): position-dependent rules; its window is not this one-sided finite gate.
- [Belan (2019 preprint, 2020 journal), Median and Mode in First Passage under Restart](https://arxiv.org/abs/1906.05619): quantile/deadline objectives, distinct from the mean.
- [Radice (2022), Non-homogeneous random walks with stochastic resetting](https://arxiv.org/abs/2208.10220): discrete renewal and moment criteria; no Gillis-specific replication is claimed.

Original educational implementation and explanation with AI assistance. No source paper bodies, third-party code, fonts, images or external datasets are bundled. Scientific references retain their rights. See the repository COPYRIGHT.txt and THIRD_PARTY_NOTICES.md; no express reuse license has been selected.
