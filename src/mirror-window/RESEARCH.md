# Resonant transmission: detuning, mismatch and bandwidth

An ideal layered mirror can transmit perfectly at an isolated resonance. The useful question is what survives when the layers, illumination or model assumptions change. All numerical observations below concern an idealized educational model, not a fabricated optical coating.

## Equal chunks, different order

At 600 nm every ideal chunk has quarter-wave optical thickness. With phasors exp(-i omega t), a layer's characteristic matrix maps the right (E,H) to the left (E,H):

```
M = [[cos(delta), -i sin(delta)/n],
     [-i n sin(delta), cos(delta)]]
delta = 2 pi n d / lambda
```

At a quarter wave, Q_H Q_L is diagonal with entries -n_L/n_H and -n_H/n_L; Q_L Q_H interchanges them. The ordinary (HL)^(2 m) product is a strong reflector. The reordered (HL)^m(LH)^m product is the identity, so it transmits unity with equal exterior indices. No extra material or energy is added. [Zhukovsky](https://arxiv.org/html/0911.5448v2) gives the general reflectivity/phase-matching interpretation and also explains why mirror symmetry is sufficient but not necessary for many perfect resonances.

## Errors: move the window or lower it?

Thickness errors change propagation phase while keeping interface indices fixed. Index errors also change admittance matching. Both use bounded synthetic deviations 1 + epsilon*u_j, with uniform pseudorandom u_j in (-1,1). They are not empirical fabrication distributions.

For m=6 and seed 7 at a 5% error bound, the thickness case transmits 0.527356% at 600 nm and 99.992928% after retuning to 605.379217 nm. The corresponding index-error case retunes to about 91.068%. Measuring only at 600 nm confounds detuning with the peak getting lower.

A 64-seed study over 0.05%–0.4% errors gives thickness log-log slopes 3.99777–4.00248, median 4.000045; index median 2.000515. Index fits range 1.69909–2.20817 at these finite errors. The four most extreme cases move toward 2 when the error interval is reduced. Small leading coefficients allow higher-order terms to matter early; finite fits are not exact exponents.

At the unperturbed quarter-wave cavity, pure phase errors produce an off-diagonal first-order perturbation of the total matrix. Tuning wavelength cancels the first-order reflection component. The remaining amplitude is generically second order, so reflected power begins at fourth order. Index changes introduce a first-order matching component that wavelength alone cannot cancel, producing quadratic power loss. The included Taylor-polynomial calculation provides explicit coefficients; for m 6,seed 7:

```
R_thickness ~ 11.7351248078 epsilon^4
R_index     ~ 36.5363999195 epsilon^2
Delta lambda ~ 107.842405690 epsilon nm
```

These statements require the particular quarter-wave family, equal surroundings, sufficiently small errors and a nonzero leading coefficient. [Kiorpelidis et al., section VI](https://arxiv.org/html/2406.07214v2) explicitly discusses the established quartic/quadratic mechanism in a different wave model; no scientific novelty is claimed here.

The full study has 3456 cases. Another 1152 comparisons start from mirror-paired errors, then shuffle the actual chunks only within H and L positions. This preserves their complete index/thickness multiset while breaking correlation. At 24 layers and 8% error, median retuned reflection after shuffling is 0.02534% for thickness errors and 1.85253% for index errors; the original mirror-paired cases retain near-zero reflection within numerical precision. Asymmetry alone does not prove that a perfect resonance is impossible.

A phase-fixed index control keeps every n*d exactly quarter-wave. Its peak stays near 600 nm but loses height. The exact center formula R=tanh(log A)^2, where log A is the sum over adjacent pairs of log(n_odd/n_even), agrees with 48 numerical controls to below 2.1e-16. At 5% error,seed 7,m 6, transmission is 91.4396%. This isolates matching from phase detuning.

## A narrower perfect peak can pass less light

| Ideal layers | Central mode FWHM | 1 nm FWHM Gaussian transmission |
| --- | ---: | ---: |
| 8 |39.0905 nm|99.9510%|
|16 |5.02509 nm|97.3546%|
|24 |0.771458 nm|62.5479%|
|32 |0.121333 nm|16.0337%|

Each ideal monochromatic peak reaches unity. The final column instead integrates a Gaussian power density per nm centered at 600 nm. It is a spectral average, not a pulse animation. Adaptive integration includes explicit breakpoints around the refined resonance. An independent dense grid and 100 additional off-peak cases give maximum absolute disagreement below 4.9e-10; tiny transmissions do not have an equivalent relative-error guarantee.

## Separate loss and stored-energy controls

The main bench is lossless. Assigning both ideal materials the same illustrative extinction coefficient kappa=0.0001 reduces 600 nm transmission to 97.1937% for 16 layers,83.8331% for 24 layers and 39.8087% for 32 layers. This is not a material fit. Transmission is optimized directly in this control because, with absorption, minimizing reflection no longer maximizes transmission.

The zero-loss field predicts the weak-loss derivative dA/dkappa from (4*pi/lambda)*sum n*integral|E|² dx. It is about 286.63 for 16 layers and 11696.37 for 32 layers; finite small-kappa checks agree within 1.4e-6 relative in the tested cases. Once kappa times that coefficient approaches one, the linear estimate fails. Absorption and bandwidth percentages here are separate calculations and must not be multiplied.

The electric-field graph is not power flow. The time-averaged electromagnetic stored-energy ratio includes both electric and magnetic contributions:

```
U/P_in = integral [n²|E|² + |H|²] dx / (2 c)
       = T darg(t)/domega + R darg(r)/domega
```

For the ideal 32-layer resonance both the transmission phase derivative and the stored-energy ratio are about 3151.486 fs. For an asymmetric reflecting control, transmission delay alone is 2.551686 fs while stored energy/input power is 1.177291 fs; including the reflected contribution recovers the latter. Five named controls and 200 random cases check the identity. Tiny finite-difference steps eventually hit a rounding floor. These are model phase derivatives, not measured travel times, photon trajectories, group velocities or time-domain propagation.

## Verification and scope

Analytic interface/slab/mirror checks, an independent Fresnel recursion, conservation, reciprocal transmission, field continuity, matched inventories, sensitivity derivatives, Taylor coefficients, spectral integration, input validation and source/generated parity are executable. Separate complex-index and field/phase implementations provide additional controls. No physical fabrication, FDTD, empirical coating validation or new general theorem is claimed. [SOURCES.md](SOURCES.md) records the primary references and reading scope.
