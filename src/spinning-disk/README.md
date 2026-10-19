# The vanishing wobble

This dependency-free educational module explores a small-angle scaling model for a rolling disk. The page integrates a combined effective rolling-loss and viscous-boundary-layer law, then uses synthetic data to show how the fitted power-law exponent can trade off against the assumed terminal time.

Open `index.html` directly, or run the checks from the repository root:

```sh
python3 -B src/spinning-disk/model.py --check
python3 -B src/spinning-disk/fit_sensitivity.py --check
python3 -B src/spinning-disk/identifiability.py --check
python3 -B src/spinning-disk/mixed_window_fit.py --check
python3 -B src/spinning-disk/candidate_selection.py --check
python3 -B tests/verify_spinning_disk.py
```

The page is not a rigid-body or contact-dynamics solver. Its continuation below the marked thin-layer limit is an extrapolation, not a prediction. The cited v1 preprint prints a boundary-layer thickness and transition formula that differ by a factor of 4 algebraically; the module uses the direct, more conservative consequence of the displayed thickness convention and regression-checks the equality of layer thickness and gap at that cutoff. The synthetic fitting experiment is evidence about the estimator under its stated assumptions, not evidence that one physical dissipation mechanism governs a real disk. Surface, edge geometry, base plate, intermittent contact, impacts, deformation, and slipping can change the observed motion. Nearby fitted exponents should not be interpreted in isolation from parameter and control experiments.

The browser panel uses a fixed sine-hash noise sequence and a single bounded endpoint grid for fast interaction. The published ensemble counts come from the separate standard-library Python checks using seeded Gaussian noise and a coarse-to-fine endpoint search; their complete scenarios and exact results are regression-locked. A dependency-free Node harness executes the actual inline browser script with bounded DOM/canvas stubs and checks default and changed-control readouts.

The scripts use only the Python standard library. No paper bodies, datasets, third-party code, images, audio, fonts, or packages are bundled. AI assistance is acknowledged; citations remain the primary sources for scientific claims.
