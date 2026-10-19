# Scaling notes for the vanishing wobble

These notes document the equations used by `model.py` and `index.html`. They are a
small-angle scaling argument, not a full rigid-body or contact model.

## Why the frequency rises while energy falls

For an approximately steady-rolling uniform disk, the precession rate `Omega` and
tilt angle `theta` obey

    Omega^2 sin(theta) = 4 g / R.

At small angle, `Omega` is therefore proportional to `theta^(-1/2)`. Meanwhile the
mechanical energy is proportional to `theta`:

    E approximately (3/2) m g R theta.

So energy can fall toward zero while the contact point precesses faster. The visible
face rotation and the precession are not the same angular motion.

## What a measured exponent can and cannot identify

Let the dissipated power scale as `Phi proportional to Omega^p`. Since
`Omega proportional to theta^(-1/2)`, the small-angle energy balance gives

    d(theta)/dt proportional to -theta^(-p/2).

Integrating to an extrapolated terminal time `t_f` gives

    theta proportional to (t_f - t)^n,  where n = 2 / (p + 2),
    Omega proportional to (t_f - t)^(-n/2).

This yields `n = 2/3` for a rolling-loss term proportional to `Omega`, `n = 1/2`
for a term proportional to `Omega^2`, `n = 4/9` for the viscous-boundary-layer
scaling, and `n = 1/3` for Moffatt's original full-gap viscous model. Because 4/9
and 1/2 are close, a fitted exponent alone is weak evidence. Parameter-dependent
prefactors and controls carry more identifying information.

## The combined model

The explorer integrates the positive descent magnitude

    -d(theta)/dt =
      (8/3) g^(1/4) R^(7/4) sqrt(eta rho) theta^(-5/4) / m
      + (2/3) mu cos(theta) sqrt(4g / (R sin(theta))).

The two terms are the boundary-layer and effective rolling-loss terms in Eq. 5 of
Thorne et al. The small-angle equal-loss estimate is

    theta_c = [2 R^(9/4) sqrt(eta rho) / (mu m g^(1/4))]^(4/3).

It scales strongly as `R^3 m^(-4/3) mu^(-4/3) rho^(2/3)`. This is why changing
mass, radius, pressure, and geometry is more diagnostic than measuring a single
power-law slope.

## Where the model stops earning trust

The boundary-layer thickness estimate is

    delta approximately sqrt(2 eta / (rho Omega)).

Equating it to the small-angle gap `R theta` gives

    theta_delta = [eta^2 / (g R^3 rho^2)]^(1/3).

The Thorne et al. v1 preprint prints the same thickness convention and then
reports a transition formula with an additional factor `4` in the denominator.
Those two displayed expressions are not algebraically consistent. This module
uses the direct consequence of the displayed thickness convention above, which
places the cutoff at a larger angle and is therefore the more conservative
validity boundary. This choice changes only the validity marker, not the
integrated loss law.

Below that angle the thin-boundary-layer assumption is no longer self-consistent.
The real disk can also lose contact, impact, deform, and briefly rotate after falling
flat. The interactive plot shows a mathematical continuation below `theta_delta`,
but labels it as extrapolated.

## Identifiability: the endpoint is part of the fit

The usual log-linear power-law fit assumes that the collapse time `t_f` is
known, because its predictor is `log(t_f - t)`. A small endpoint error bends
that predictor most strongly for the latest samples. `identifiability.py`
therefore compares three synthetic analyses of an exactly known law:

1. fix `t_f` at its true value;
2. fix `t_f` 3 ms late; or
3. estimate `t_f` jointly with the exponent by bounded profile search.

The calculation crosses three observation windows, two sampling patterns,
three log-noise levels, and both 4/9 and 1/2 ground truths. Joint estimation
recovers the exact synthetic law in the noise-free checks, while its extra
freedom widens the exponent distribution in the tested noisy scenarios. A
wrong fixed endpoint can be much more precise and still confidently select the
wrong candidate. These are estimator tests, not measurements of a disk and not
evidence for either mechanism.

`mixed_window_fit.py` then forces a single power law onto the combined-loss toy
model itself. With no noise and 100 log-spaced samples in the 5–100 ms window,
it returns `n=0.4725` when the model endpoint is fixed and `n=0.4812` when the
endpoint is profiled, even though the air term supplies 77.01% of the modeled
loss on average. Across 2 ms–
10 s windows, fitted exponents range from about 0.463 to 0.569 and switch their
nearest named candidate. This is expected model misspecification: a smooth
crossover has no single true exponent. It demonstrates that even a low-residual
fit does not establish which physical loss law generated measured data.

`candidate_selection.py` compares the two named exponents directly instead of
classifying an unconstrained slope by proximity. With the true endpoint fixed,
residual error almost always selects the generating synthetic exponent in the
tested design. Once each candidate may optimize its own endpoint, confusion
rises sharply when the observed dynamic range is restricted. For true 4/9 data,
80 samples over 20–100 ms, and 5% seeded independent Gaussian log-noise, 1 of
200 log-spaced repetitions and 2 of 200 linear-spaced repetitions chose 1/2
with the true endpoint fixed. When each candidate separately searched endpoint
offsets from -19 to +50 ms, 62 of 200 repetitions did so for each sampling
pattern. Endpoint freedom can therefore erase most of the residual separation
between candidate laws. The browser panel uses a separate deterministic
sine-hash noise sequence and a single bounded endpoint grid for responsive
exploration; its readouts are regression-tested separately and are not the
source of these ensemble counts.

## Why the regime sequence should stay provisional

The combined continuous-loss law is a useful coarse model, but the literature
does not establish a universal sequence. Ma et al. (2014) tracked all six rigid-
body degrees of freedom for a sharp-edged steel disk. Over their final three
seconds, the energy followed a 2/3 power law across a little more than four
decades of time, and a rolling-friction model reproduced the measured motion.
Their collapse-time measurement accuracy was 0.2 ms. This is a strong challenge
to treating late air dominance as geometry-independent. It is not a like-for-
like refutation of the 2026 preprint: Ma et al. used sharp-edged disks and ended
their numerical trajectories at 0.5 degrees, explicitly noting that their paper-
based contact test could not resolve the extremely-small-angle limit.

Contact also need not wait until a final, clean handoff. Borisov, Mamaev, and
Karavaev (2015) electrically measured random “microlosses” of contact up to
0.7 ms during the motion and terminal contact-loss intervals that depended on
disk mass and base-plate properties. Their stainless-sheet trials span 12.6–42
ms, and one disk averaged 102 ms on a thick duralumin plate. (The source table's
printed 36.97 ms mean for its first disk conflicts with the 39.67 ms arithmetic
mean of its three listed trials, so neither value is used as a headline result.)
That primary experiment challenges any claim that rolling, air drag, and contact
form sharply separated universal stages. It does not by itself identify the
energy-loss mechanism in the intervals that remain in contact.

## Primary sources

- B. G. Thorne et al., “Air Drag Controls the Finite-Time Singularity of Euler's
  Disk” (2026), arXiv preprint v1, <https://arxiv.org/abs/2603.14520v1>.
- H. K. Moffatt, “Euler's disk and its finite-time singularity” (2000),
  <https://doi.org/10.1038/35009017>.
- L. Bildsten, “Dissipation for Euler's Disk and a Desktop Demonstration of
  Coalescing Neutron Stars” (2001 preprint; published 2002),
  <https://arxiv.org/abs/gr-qc/0102046>.
- H. Caps et al., “Rolling/Slipping Motion of Euler's Disk” (2004),
  <https://arxiv.org/abs/cond-mat/0401278>.
- B. W. Collins and S. J. Hogan, “An Experimental and Theoretical Study of
  Euler's Disk” (2026), <https://doi.org/10.1137/24M1711741>.
- A. V. Borisov, I. S. Mamaev, and Y. L. Karavaev, “On the loss of contact of
  the Euler disk” (2015), <https://doi.org/10.1007/s11071-014-1811-5>.
- D. Ma, C. Liu, Z. Zhao, and H. Zhang, “Rolling friction and energy
  dissipation in a spinning disc” (2014),
  <https://doi.org/10.1098/rspa.2014.0191>.
