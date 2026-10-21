# Validation and limits

The public release candidate was checked in Chromium on 12 October 2026. This records actual checks, not a promise of compatibility with every browser.

| Check | Observed result |
| --- | --- |
| Phase model | 10 Node checks passed: analytic uncoupled motion, rotation invariance, mean drift, exact traveling wave, energy, linear stability, timestep refinement, noise convention and seed replay. |
| Note sequence and scheduler | 14 Node checks passed: crossings, seeds, quantization bounds, MIDI rounding, channel separation, pause/resume/reset, late-event skipping, voice cap and timestep convergence. |
| Synth lifecycle and headroom | 4 Node checks passed. Finite envelopes and oscillator stops, cancellation/disconnection, conservative peak bound below 0.5 at maximum UI level, clipping/nonfinite WAV rejection. |
| MIDI output | Six presets independently parsed with Python: 480 ticks/quarter, 130.00013 effective BPM, end tick 15360, positive note durations, source onset agreement, no dangling or ambiguous notes. Browser complete-grid bytes matched Node output. |
| Actual Web Audio output | Six OfflineAudioContext renders passed. The local repeated default was byte-identical; a hosted repeat differed at 2 of 664554 PCM16 samples, each by one least-significant bit. Exact WAV byte repeatability is not guaranteed by browser rendering. Each PCM16 WAV: mono, 44.1 kHz, 664554 frames, zero clipped samples, silent final 1000 samples. Highest float peak approximately 0.122; no auditory listening assessment claimed. |
| Traffic routing | 17,940 allocations checked against an independent edge-incidence active-set KKT oracle. Both cited numeric examples reproduced. Conservation error below 2e-15, selfish residual below 3e-14, coordinated marginal-cost residual below 6e-14. Boundary oracle allocation difference below 3e-9. |
| Interaction and layout | 12 grouped browser checks passed: landing links; sound initially off; live audio Start/Mute/Unmute/Pause/Resume/Stop; all six presets; keyboard focus-visible and Enter activation; reduced motion; traffic model/shortcut/policy/zero-demand/reset flows; widths 320, 390, 768, 1200 and 1440 as relevant. No horizontal document overflow observed. |
| Offline and network | Individual local-file pages reloaded with network disabled and remained interactive. No external network request or page exception observed during the local browser checks. |
| Static packaging | All three pages have viewport and language metadata, unique IDs, valid native label references, working local links, inline assets, and no network/persistence API. |

The live-control test set hardware output gain to zero, preserving scheduling and voice creation without claiming listening. Audio renders were computed separately at the fixed default preset level.

The tests use standard Node.js and Python libraries and can be rerun from README instructions. The repository check workflow runs these model and packaging checks and verifies that rebuilding leaves the generated pages unchanged. Actual hosted-page and CI status should be checked for the exact commit being reviewed.

Untested: physical phones, Safari/Firefox/Edge engines, screen-reader combinations, browser download permission differences, and empirical biological/traffic validity. Browser emulation does not establish physical-device compatibility. On a downloaded standalone page, the back-to-collection link requires retaining the collection folder; the experiment itself is self-contained.
# Riffle-shuffle addition — 15 October 2026

This educational addition reproduces established GSR shuffle and carries
calculations; no new research result is claimed. Fresh data regeneration took
17.992 seconds in the release review environment. Every regenerated table
matches the earlier checked explorer data after removing runtime-only fields.

Checks actually run for this addition:

- `python3 src/riffle/test_model.py -v`: 13 methods pass (24.845 seconds).
- `python3 tests/verify_riffle.py`: 15 literal repeated-riffle laws, 15 independently
  recomputed 52-card full-deck TV values, the five-riffle top marginal, random
  rotation counterexample, embedded data equality and JavaScript syntax pass.
- `python3 tests/check_package.py`: four pages pass language, viewport, label,
  ID, local link and dependency-free structure checks.
- Existing clocks (10), sequence (14), synthesis (4), six-file independent MIDI
  parsing and 17,940 traffic KKT cases pass unchanged.

The independent release checker does not import the production model. It uses
literal cut/interleave evolution and an explicit Eulerian-number sum. The
headline top marginal check rederives its finite rank-mixture formula; it is
not independent evidence that the ideal model describes real hand shuffling.

Browser interaction checks on the unchanged script were completed during the
earlier browser checks: presets, keyboard endpoints, sample regeneration,
separation toggle, methods and narrow layout. This release adds clearer copy
and rounded-number explanations. Those copy changes were source-checked;
no second browser pass, physical-phone check or assistive-technology audit is
claimed.

# Phantom places validation

The Phantom module bounds grid work, reads UTF-8, writes LF output, uses standard-library UTC handling, declares referrer metadata and requests idle audio-context cleanup. These code changes have numerical and mock-event checks; no device or listening validation is inferred.
The build copies its self-contained page into `docs/phantom-sound/index.html`.
Numerical replay, collection packaging and browser checks for this integration
are separate from the historical collection results above. No new listening,
physical-device or assistive-technology claim follows from integration.

# Educational additions — scoped validation

- Does a flower have an ear?: exact module [validation](src/flower-evidence/VALIDATION.json), [provenance](src/flower-evidence/PROVENANCE.json) and [limits](src/flower-evidence/README.md). Those observed module checks and static-review limits are not empirical certification.
- The shortcut trap, one day later: exact module [validation](src/route-learning/VALIDATION.json), [provenance](src/route-learning/PROVENANCE.json) and [limits](src/route-learning/README.md). Those observed module checks and static-review limits are not empirical certification.
- Square ice: boundaries, loops and counts: exact module [validation](src/square-ice/VALIDATION.json), [provenance](src/square-ice/PROVENANCE.json) and [limits](src/square-ice/README.md). Those observed module checks and static-review limits are not empirical certification.

The collection includes source checks and a static Square Ice guide. Earlier browser results do not imply physical-device or screen-reader coverage. Code checks do not establish scientific validity or empirical calibration.

# The vanishing wobble — scoped validation

`python3 -B tests/verify_spinning_disk.py` runs five bounded, dependency-free check suites. They cover the combined-loss quadrature, analytic crossover, asymptotic exponents, boundary-layer prefactor, algebraic layer/gap equality at the validity cutoff, a 500-case seeded parameter stress, quadrature convergence, fixed and jointly fitted endpoint sensitivity, mixed-loss window fits, and direct 4/9-versus-1/2 synthetic selection. The exact published 100-point mixed-window values and 200-repetition candidate counts are asserted with their full sampling, noise, endpoint, and search-bound scenarios. The check also requires byte equality between the source page and built page, checks the key limitation and referrer metadata, rejects named script network/storage sinks, and structurally checks automatic HTML/CSS remote-request surfaces while permitting ordinary citation links.

`node tests/verify_spinning_disk.js` executes the actual inline page script against bounded dependency-free DOM/canvas stubs. A small structural tokenizer builds the element manifest from real start tags while ignoring comments and raw script/style text; it rejects duplicate or missing IDs, checks required tag types and range-input defaults, and derives select defaults from their options. Negative fixtures cover ghost IDs, removed required elements, and wrong element types. The behavior checks cover the default render, device-pixel-ratio canvas sizes, model-parameter changes, exponent and endpoint-mode changes, offset enablement, and dependent numerical readouts. This is JavaScript behavior coverage, not a browser-engine, visual, accessibility, or physical-device test.

These are finite numerical and synthetic-estimator checks. They do not reproduce a physical disk experiment, validate the fitted effective rolling coefficient, establish a universal collapse sequence, or independently confirm the cited primary literature. Browser checks for this addition are recorded separately for the exact release candidate; physical phones, non-Chromium engines, screen readers, and contact/acoustic measurements remain untested unless explicitly reported.

## Same coin, two finish lines

`python3 -B src/same-coin/verify.py` checks exact fair-coin headline probabilities, 2,040 finite-string boundary identities, source/page equality, 532 race cases and 2,128 fixed-horizon cases against a separate exact Python absorbing-state implementation for races and a literal-tail count dynamic program for fixed-horizon scores: 9,044 JavaScript value assertions plus sequence and error checks. Fixtures are regenerated temporarily. These are bounded deterministic checks, not browser-engine or empirical-coin tests. Independent flips, empty history, uncapped first-arrival races and retained fixed-horizon ties are explicit. See [module limits](src/same-coin/README.md).
