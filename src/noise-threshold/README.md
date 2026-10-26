# Can noise help a detector?

A self-contained interactive educational comparator model, built with AI assistance. The underlying stochastic-resonance ideas are established work. This is not a physical experiment, a neuron model, a discovery, or evidence of sensory benefit.

The page compares a fixed binary threshold readout with a retuned threshold and an optimal raw-measurement reference. More threshold activity or a louder harmonic can coexist with worse information or detection. False-alarm constraints and observation budgets are explicit.

## Model and controls

`x_i=A sin(2 pi (i+1/2)/64)`; independent standard-normal `z_i`; `y_i=1[x_i+sigma z_i>threshold]`. Default amplitude 0.25, threshold 1, noise SD 0.8, N256 and fixed seed 20261025. Units are dimensionless. There is no hysteresis, refractory period, continuous-time noise bandwidth or unknown-frequency search.

Phase-label information, full-record signal-presence information, harmonic amplitude and detection power are different scores. All within-setting comparisons use the same observation budget. The separate exact N16 control enumerates 65,536 records and randomizes boundary decisions to match 5% false alarms. It does not replace the N256 interactive model. Intervals, finite-sample information bias and correlated-noise stress controls are explained in the page.

## Build and check

Existing Python3 and Node.js only; no installation, backend or remote data is needed.

```sh
python3 -B build.py
python3 -B verify.py
```

The verifier runs 17 Python unit tests, cross-language numerical fixtures, a pure Node DOM-stub control check, static package checks and selected saved-result replays. DOM stubs do not establish rendered layout, accessibility-tree behavior, real downloads or browser-console correctness. Rendered layout, accessibility-tree behavior, real downloads and browser-console correctness require separate browser tests.

To recompute the complete saved numerical study, run `run_study.py`, `controls.py`, `exact_control.py`, `analysis_controls.py`, `correlation_control.py`, `noisy_measurement_control.py`, then `adversarial_checks.py` with `python3 -B`. These bounded scripts write only `data/` and can take several minutes. Rebuild afterward. Runtime measurements can vary. No physical data is collected.

## Sources and attribution

- [Gingl, Kiss and Moss (1995)](https://www.inf.u-szeged.hu/~gingl/Publications/A06.pdf): physical directional-crossing experiment with band-limited noise. This occupancy comparator does not replicate its pulse process or spectral normalization.
- [Kosko and Mitaim (2003)](https://sipi.usc.edu/~kosko/NN2003.pdf): noisy binary threshold neurons; their bipolar-input theorem is not a proof specifically for these sinusoidal-phase scores.
- [Chen et al. (2007)](https://digitalcommons.uri.edu/ele_facpubs/1324/): primary repository abstract, including detection/false-alarm constraints; full-text methods not assessed.
- [Polyanskiy and Wu](https://people.lids.mit.edu/yp/homepage/data/simple-IMA.pdf): data-processing inequality; only the ordinary Markov-chain bound is used.

Original implementation and presentation: Erebos Labs, with AI assistance. Cited publications retain their own copyrights; no paper bodies, third-party images or libraries are included. See the repository copyright notice. Pages add no telemetry; hosting may log visits.
