# Finite illumination: center recovery and a persistent edge deficit

The periodic model is a useful limit for the **interior** of a sufficiently wide illuminated grating. It cannot be used unchanged at its last illuminated slot. Adding remote slots improves central reconstruction but leaves that last slot missing neighbors on one side. This is a local boundary limitation even when a normalized picture appears recognizable.

## Defined finite input and analytic expectations

U0(X)=A Σj exp[−(X−j)²/(2σ²)], j=−M…M, N=2M+1, σ=.04, A=(σ√π)^−1/2. The grating has a finite number of Gaussian transmitting/illuminated slots; tails outside the last half-period are negligible but not mathematically compact. This is **not a hard rectangular aperture** and no sharp-edge diffraction result is inferred from it. Nearest slots do not overlap appreciably at input; each one-period input window has mean|U|²≈1 and RMS contrast2.995589593.

Use X=x/d, τ=z/(2d²/λ)=1, λ/d=.01. The common incident carrier is removed. The infinite-domain Fresnel solution follows from the Gaussian Fourier transform:

`q = σ² + iτ/π`
`U_N(X,τ) = Aσ/sqrt(q) Σ_j exp[−(X−j)²/(2q)]`.

Each beamlet's intensity envelope width is s=|q|/σ≈7.96 periods here. Central reconstruction needs the illuminated half-width M to extend well beyond this spreading scale. Narrowing the slots therefore requires more illuminated periods at the same normalized distance. This is a scale argument, not a universal N threshold.

At an interior slot of the infinite periodic array, quadratic modal phases rephase atτ=1. At the last slot center of a very large finite array, symmetry instead gives

`U_edge = (U_periodic + U_single)/2`.

For these parameters the predicted last-slot-center intensity is **0.276385664** times the infinite-array peak. The N65 complex field agrees with this limit to2.68e−14. This ratio concerns the pulse-center intensity, not a claim that the deformed profile's maximum is exactly at that coordinate.

For all|X|≤.5, an envelope bound on missing central neighbors is

`|U_infinite − U_N| ≤ 2 Aσ/sqrt(|q|) s sqrt(π/2) erfc[(M−.5)/(sqrt(2)s)]`.

It follows by bounding the absolute Gaussian tail sum by its decreasing integral. For N65, the bound is4.00828e−4 and the measured maximum field error on128 central-window points is1.69819e−4. The bound is for paraxial Gaussian propagation; it is not a rigorous error bound for the exact scalar FFT calculation.

## What was computed

N=5,9,17,33,65; paraxial and exact scalar transfer; three **fixed** one-period observation windows centered at0, floor(M/2), and M. Each window uses128 samples and is compared with its actual initial pulse on the same coordinates. No spatial registration or distance optimization was performed; the prior coherence study covers their distinct role. There are30 rows,31 domain/reference/resolution comparisons, and five central tail-bound checks.

The FFT uses an explicitly zero-background padded domain of128 periods and128 samples per period (16,384 points). The continuous Gaussian input has negligible tails at these boundaries. A periodic FFT grid is a computational device, not the physical boundary condition being claimed.

For frequency f in cycles per period, the transfer is exp(−i2πτf²) paraxially, and exp{−i4πτf²/[1+sqrt(1−(λf/d)²)]} for exact scalar dispersion. The latter is stable against square-root cancellation. The grid Nyquist frequency is64, below the propagating cutoff100. Omitted higher Gaussian spectral amplitudes at frequency64 are proportional to exp(−129.36); this smooth-input assumption is essential. No evanescent or vector calculation is claimed.

## Results in absolute units

| N / model / window | Field overlap | Mean intensity | Absolute RMS contrast | Centered shape cosine |
| --- | ---: | ---: | ---: | ---: |
|5 / paraxial / center |.357392|.341842|.308541|.578244|
|17 / paraxial / center |.872154|.867261|1.915883|.936119|
|33 / paraxial / center |.996812|.996474|2.894221|.998361|
|65 / paraxial / center |.999999993|.999999991|2.995574|.999999997|
|65 / exact scalar / center |.991738|.999999989|2.902186|.998426|
|65 / paraxial / last slot |.537959|.535616|1.009326|.926920|
|65 / exact scalar / last slot |.535660|.535616|.989804|.908998|

The N33 and N65 paraxial edge-window means differ by only4.75e−8, while their center windows improve substantially. The edge settles faster into its degraded limit because it has many slots on one side and none on the other. Its recognizable normalized shape does not restore missing mean intensity or absolute contrast.

The N65 exact central field differs from the infinite periodic exact model by at most1.98539e−4 on the sample grid. Its overlap≈.991738 matches the earlier σ=.04 infinite-periodic case; the residual limitation there is non-paraxial modal phase, rather than missing illuminated neighbors. The original bench's narrowerσ=.025 case should not be confused with this width.

## Avoiding periodic-wraparound false evidence

For N17 at64 samples/period, comparing FFT output to the independent finite Gaussian Fresnel sum gives:

| Domain / periods | Central-window max field error | Last-slot-window max field error |
| --- | ---: | ---: |
|32|.0119883|.0987709|
|64|1.21e−11|5.83e−9|
|128|8.41e−14|5.35e−14|

The underpadded32-period result is deliberately retained as an inaccurate control. It is periodic-image contamination, not physical recurrence. Final128-period paraxial outputs match the nonperiodic analytic reference across all15 N/window cases. For exact scalar propagation,128→256-period domain changes were checked for N17/33/65 at center and edge.64→128 samples/period were checked separately for N33 in both models. The largest field change across all final analytic/domain/resolution controls is1.82e−12. This supports convergence for these smooth cases; it is not an unrestricted infinite-domain theorem for exact Helmholtz propagation.

Scalar integrals of|U|² over the padded domain remain N within the recorded tolerance, and local reductions therefore reflect redistribution, not modeled absorption. This scalar norm is not electromagnetic normal flux.

## Verification and artifacts

The supplied finite-array calculation and verifier reproduce the numerical results. Ten unittest groups cover FFT/direct-DFT/inverse identities, Gaussian initial condition and spreading, direct exact dispersion, independent metric scaling, intentionally bad padding, convergence controls, center/edge behavior, edge symmetry, central tail bound and finite/exact-periodic agreement. Some groups cover several related assertions. No unexpected test failure occurred in this extension.

The metric scaling test explicitly verifies that multiplying a field by1/2 keeps normalized field overlap and shape cosine at1 while reducing mean intensity and absolute RMS contrast to1/4. Thus normalized similarity alone cannot certify aperture survival.

[Scientific figure](data/finite-array-center-edge.png), [numeric results](data/finite-array-results.json), [CSV](data/finite-array-sweep.csv), reproduction commands listed in README.md. The figure uses the same absolute intensity scale for center and edge. Plot coordinates follow the numerical sampling j/128.

## Provenance and limits

Berry–Klein1996 [section5, equations55–58](https://michaelberryphysics.wordpress.com/wp-content/uploads/2013/07/berry274.pdf) discusses finite-N walk-off and blurring. It motivated the distinction between illuminated extent and angular-order cutoff. This extension uses the analytically propagating finite Gaussian sum as its own reference; it does not assert that the paper's finite rectangular-beam approximation is this input model. The Gaussian Fourier solution and missing-tail/edge identities were derived and checked here; no originality claim. No additional experimental claim or source-data reanalysis was made.

Remaining scientific limits: one width, one nominal return distance, one wavelength ratio; smooth slots rather than a hard stop; scalar forward propagation; finite windows/grids; no simultaneous source incoherence and finite illumination, grating material dispersion, polarization, detector or laboratory validation. The fixed edge-window loss does not establish what a differently positioned detector/window, optimized propagation distance or redesigned illumination would achieve.

