# When coupling silences the rhythm

An interactive pair of coupled Stuart–Landau oscillators: drift, decay toward rest and restored phase locking as coupling changes. This is an established dimensionless mathematical model, not a new scientific contribution or calibrated metronome simulation.

[Open the experiment](https://erebos-labs.github.io/experiments/oscillator-bench/). The self-contained page runs without dependencies, remote assets, telemetry or a backend. Sources open only when selected. GitHub hosting may log visits.

## Use

Choose Drifting rhythms, Amplitude death or Motion returns, or adjust coupling K from 0 to 8. Each change restarts the same initial condition. Play, pause, reset and scrub time; Show outcome selects the finite endpoint t = 120. Playback speed does not change the solver step. Reduced motion starts paused. All controls use native HTML elements.

## Model and reference results

`dz_i/dt = (1 + i omega_i - |z_i|²) z_i + K (z_j - z_i)`.

All quantities are dimensionless: growth = 1, omega = (2, 8), symmetric instantaneous linear coupling, no noise or delay. Initial state: z₁ = 1 + 0.2i, z₂ = −0.3 + 0.7i. Cartesian RK4 uses h = 0.01 for 120 time units (12,000 steps), sampling every 0.05 units. One bounded trajectory is computed per coupling change, with no parameter sweep or background worker.

| K | Observed amplitude at t = 120 | Interpretation |
|---|---|---|
| 0.5 | about 0.759433 each at this instant | Relative phase continues slipping; amplitude is not constant. |
| 2 | about 3.69e−53 and 1.31e−53 | Decay toward the homogeneous zero equilibrium. |
| 4 | about 1.05e−19 each | Decay toward the homogeneous zero equilibrium. |
| 6 | about 0.442891 each; phase B−A = 30° | Restored, phase-locked oscillation. |

The largest real part of the origin's eigenvalues is `1 − K + Re sqrt(K² − 9)`. The origin is linearly stable for **1 < K < 5**. This analytic statement is separate from finite-time simulation observations. The boundaries have zero linear growth and need nonlinear analysis; near them, slow transients and timestep error limit conclusions. A tiny computed nonzero number is numerical evidence of decay, not an observation of exact physical rest. Phase at zero is undefined.

Amplitude death here means stabilization of the common zero equilibrium. This prototype does not demonstrate oscillation death into distinct nonzero equilibria. Mechanical metronome escapement shutdown and residual passive motion are contextual discussion only.

## Reproduce and check

Run `node src/oscillator-bench/test-model.cjs` from the repository root for nine deterministic numerical checks: analytic uncoupled orbit, amplitude decay, strong-coupling amplitude/phase, weak-coupling slips, timestep refinement, phase threshold, energy identity, origin stability and bounded inputs/reset. Run `python3 -B src/oscillator-bench/build.py` to rebuild the self-contained source page; root `build.py` also copies it into the public collection.

`model.js` is shared by tests and UI; `app.js` draws stored samples and handles bounded playback; `styles.css` and `page.template.html` define the presentation. Desktop and narrow Chromium controls were checked. Physical devices, other browser engines and assistive-technology combinations remain untested. Finite trajectories and numerical checks do not establish empirical validity or infinite-time behavior.

## Primary sources

- [Aronson, Ermentrout & Kopell (1990), Amplitude response of coupled oscillators](https://sites.pitt.edu/~phase/bard/pubs/aek88.pdf).
- [Reddy, Sen & Johnston (1998), Time delay induced death in coupled limit cycle oscillators](https://arxiv.org/html/chao-dyn/9805029). Only the zero-delay model is implemented here.
- [Goldsztein et al. (2022), Coupled metronomes on a moving platform with Coulomb friction](https://arxiv.org/abs/2201.06161). Mechanical context only; no metronome equations implemented.

Original implementation and explanation with AI assistance. No third-party code, images, fonts, paper bodies or datasets are bundled. Sources retain their rights. See the repository COPYRIGHT.txt and THIRD_PARTY_NOTICES.md; no express reuse license has been selected.
