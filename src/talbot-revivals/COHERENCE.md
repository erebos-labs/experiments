# Coherence: a returning image needs more than one score

A separate incoherent-ensemble calculation accompanying the periodic-field explorer. Run `python3 -B coherence.py` and `python3 -B verify_coherence.py` from this directory.

## Analytic model and predictions

Retain49 Fourier orders (n=−24…24) of the smooth σ=.04 pulse train. α0=λ0/d; τ=z/(2d²/λ0). Spectral members have λ=λ0(1+ε), with ε uniform on[−b,b]. Angular members have transverse incident frequencyν uniform on[ν0−a,ν0+a] cycles per period, so sinθ=α0ν at nominal wavelength. Study the two distributions separately. The input Fourier coefficients are wavelength-independent: this is not a dispersive physical grating.

Each member propagates coherently. Different members are mutually incoherent; average their **intensities**. Relative to that member's incident axial carrier,

- paraxial φn=−2πτ(1+ε)(n²+2nν);
- exact scalar φn=−4πτ(1+ε)(n²+2nν)/[sqrt(1−α0²(1+ε)²(n+ν)²)+sqrt(1−α0²(1+ε)²ν²)].

The rationalized exact expression avoids subtracting square roots. All retained members propagate. Removing the member's transverse carrier exp(i2πνX) changes no intensity; it defines the periodic grating envelope used for the conditional overlaps below. This pair matrix is not claimed to describe the complete angular mutual-coherence function.

Let Cnm=cn cm* E[exp(iφn−iφm)]. Then I(X)=Σnm Cnm exp[i2π(n−m)X]. For normal mean incidence, analytic paraxial averages multiply each pair by:

- angular: sinc[4πτa(n−m)],
- spectral: sinc[2πτb(n²−m²)],

where sinc(x)=sin(x)/x. Atτ=1,a=1/4, every nonzero intensity harmonic vanishes. Atτ=1,b=1/2, equal n² groups survive: ±n coherence remains, producing a half-period pattern rather than a flat image. Exact scalar normal-incidence dispersion also preserves ±n degeneracy, although it changes the other cancellations. The sinc factors give analytic controls for the numerical quadrature.

## Direct numerical results

Forty fixed cases: two source types, five spreads, α0=.001/.01, and paraxial/exact scalar propagation. Mean intensity is1 within roundoff.

- Angular washout a=.25: paraxial intensity is uniform to~1e−15. Exact scalar atα0=.01 leaves only0.00120534 of the original RMS contrast; nevertheless the spatially registered centered shape cosine is0.99965828. Calling that99.966% image recovery would conceal99.879% contrast loss.
- Broad spectrum b=.5: paraxial intensity ranges0.85820369…1.85820369, retains0.09451346 of input RMS contrast, and has a half-period pattern. Atα0=.01 the exact scalar range is0.85693225…1.87901533. Surviving pattern does not imply full coherent field revival.
- Tilt-onlyν0=.07: paraxial unshifted conditional field overlap is0.00218749; a common spatial registration of0.14 periods restores overlap1 and intensity within numerical search tolerance. Exact scalar best spatial registration gives overlap0.99172631 and relative intensity error0.0634580. Report displacement separately from intrinsic deformation.
- Weak input cn∝(0.01,1,0.01): angular washout erases all intensity contrast while mean per-member overlap remains0.99960014. That high overlap is dominated by the unmodulated component, not faithful recovery of its weak pattern.
- A bounded81-point distance scan [.98,1], α0=.01, no spatial registration, gives mean component overlap0.95804040 for a=.01 atτ=.999 and0.88196299 for b=.01 atτ=.99925. Distance adjustment does not undo source averaging. These are sampled maxima, not certified global optima.
- The intensity error can rank cases differently from component field overlap: at b=.01, nominalτ=1, exact scalar relative L2 intensity error .27419077 is slightly smaller than paraxial .27428283, while its mean component field overlap is smaller (.88123884 versus .88229392). No monotonic “more exact means worse image by every metric” claim is justified.

## Metrics and interpretation

There is no single complex field for an incoherent mixture. The field column is E[|⟨u_input,u_member(z)⟩|²] per period, with each member compared to its own carrier-matched input. It is not fidelity of an averaged amplitude, a source purity, or transmitted-power percentage. Averaging amplitudes incorrectly would give mean intensity only0.14179631 in the angular-washout example, instead of1.

Intensity error uses the L2 difference of non-DC harmonics divided by the input non-DC norm. RMS contrast ratio reports the output/input non-DC norms. Centered shape cosine removes contrast amplitude and therefore can be misleading by itself. When contrast vanishes, this cosine and spatial registration are reported as undefined. Spatial shifts use a256-point grid plus40 local refinement steps. Field-optimal and intensity-optimal shifts are separate objectives; neither is an unrestricted certificate.

## Verification, failures and uncertainty

-10 independent unittest groups PASS: Legendre moments; direct square-root dispersion; direct incoherent intensity averaging versus pair/harmonic construction; analytic washout; spectral degenerate-pair survival; shifted return; Hermitian/trace/positive sampled intensities; weak-modulation metric trap; incorrect amplitude averaging; modal truncation.
- Four numerical paraxial averages agree with analytic sinc factors to at most6.27e−16 per pair at final quadrature resolutions. Exact angular256→512 and spectral1024→1536 comparisons change pairs by at most2.50e−16.
- Initial broad-spectrum quadrature failed:256 nodes gave1.5479e−4 maximum pair error;512 nodes still gave3.0943e−7;1024 gave1.39e−16. This is an integration-resolution failure, not physical loss of coherence. Resolution was increased; no analytic tolerance was relaxed.
- M24→M32 sampled exact angular-case intensity difference1.2971e−9 on257 points. This is one controlled truncation check, not a universal bound. Tiny computed minima down to~−2.5e−14 are floating-point cancellation, not physical negative intensity.
- Infinite aperture remains. Finite aperture, combined angular-and-spectral distributions, dispersive gratings, detector response, polarization and laboratory validation are deferred. No finite-aperture result is inferred from order truncation.

## Sources

See SOURCES.md for the source-specific reading scope, attribution and limits.


