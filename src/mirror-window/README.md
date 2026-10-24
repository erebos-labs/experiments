# The window inside a mirror

[Explore the optical bench](https://erebos-labs.github.io/experiments/mirror-window/).

Exactly the same transparent layer chunks can form a strong mirror or a narrow resonant window. This bench distinguishes a window moving, losing peak transmission, and becoming too narrow for the incident spectrum. It is an educational implementation of established wave optics, not a scientific discovery or a measured coating.

## Model

The design wavelength is 600 nm. Nominal indices are H = 2.3 and L = 1.45, with each chunk's optical thickness n d = 150 nm. These are illustrative real, nondispersive materials. Ordinary order is (HL)^(2m); reordered order is (HL)^m(LH)^m, using the same 4m chunks, actual indices and physical thicknesses. The ideal central L pair forms a half-wave cavity.

A characteristic matrix solves coherent, normally incident plane waves through infinite, smooth, nonmagnetic, isotropic layers. R = |r|² and T = (n_out/n_in)|t|² are power fractions. The field graph is electric-field magnitude squared, not power flux. The main interactive model is lossless. An optional glass exterior on the right breaks whole-system mirror symmetry.

## Controlled observations

- Sixteen ordinary ideal layers transmit 0.248749% at 600 nm; the same chunks in cavity order transmit unity within floating-point precision.
- With 24 layers, a 5% independent thickness-error bound and seed 7, transmission is 0.527356% at 600 nm and 99.992928% after retuning to about 605.379217 nm. The corresponding index-error example retunes to about 91.068%, because interface matching also changes.
- Ideal 32-layer transmission reaches unity at one wavelength, but the central mode is only about 0.121333 nm wide. A Gaussian power spectrum per nm with 1 nm FWHM centered at 600 nm transmits 16.0337% in total.
- For generic small errors in this quarter-wave, equal-surroundings family, retuned reflected power begins at fourth order in thickness error and second order in index error. These are local asymptotic statements, not universal fabrication laws. The effect and symmetry mechanism are established; see SOURCES.md.

Try the guided examples, then **Retune to peak**. Correlation choices give independent, mirror-paired or shared errors. The **small-error evidence** view sweeps its own fixed amplitudes and retunes at every point. Fits use 0.05%–0.4% errors; special small leading coefficients can distort finite-range slopes. Paired/shared and unequal-surroundings controls do not receive a misleading zero-baseline fit.

## Reproduce

Existing Python 3 and Node.js are sufficient. From the repository root:

```sh
python3 -B build.py
python3 -B src/mirror-window/verify.py
```

The verifier runs 28 Python groups, 9,080 cross-language checks across 160 fixtures plus 22 scaling checks, independent passive-loss and phase/energy controls, and source/generated parity. It writes only the module's ignored output directory. No package install or network call is needed.

For the full bounded studies use `python3 -B src/mirror-window/verify.py --full`. This regenerates 3,456 error cases, 1,024 scaling measurements, 1,152 matched-inventory correlation cases, outlier refinement and quadrature controls into `src/mirror-window/output/`. Published compact tables and fixed reference fixtures are in `data/`. Main model.py, core.js, ui.js and Python test logic retain the checked scientific implementation. Packaging changes add portable paths, navigation and attribution.

[RESEARCH.md](RESEARCH.md) explains the derivation, controlled comparisons and limitations. [SOURCES.md](SOURCES.md) identifies primary references and reading scope. No source paper bodies, third-party implementation, fonts, images or measured material dataset are bundled. Original implementation and explanation with AI assistance. Scientific references retain their rights; repository COPYRIGHT.txt applies and no express open-source reuse license has been selected.

## Practical limits

Peak search is bracketed on 540–660 nm, then locally refined; it is not a proof of an unrestricted unique optimum. Gaussian averages use an absolute adaptive tolerance and explicit narrow-mode breakpoints. Double precision can produce tiny near-zero residuals or values slightly above unity; these are not physical gain. The source wavelength distribution is Gaussian per nm, not per frequency.

A separate common-extinction-coefficient control illustrates absorption: at kappa = 0.0001, the ideal 32-layer stack transmits about 39.81% at 600 nm rather than unity. This synthetic control is not a material prediction and is not multiplied by the bandwidth result. Phase-delay controls are not time-domain pulse simulations or measured traversal times.

Dispersion, roughness, oblique incidence, finite beams, nonlinear response and actual manufacturing statistics are outside scope. Chromium desktop and narrow layouts/controls were checked. Other engines, physical devices and assistive-technology combinations remain untested. Runtime computation uses no remote data, backend, credentials, telemetry or persistence; links open only when selected. GitHub hosting may log visits.
