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

The first release-check attempt failed only at a script-attribute-order
assumption while locating embedded JSON. The parser was corrected and the
complete check passed. A prepared documentation patch initially failed to match
the remote baseline README; it was corrected without touching a separate staged
traffic edit. Reference checking corrected the full names of the 2025 authors
before publication.

Browser interaction checks on the unchanged script were completed during the
preceding private playtest: presets, keyboard endpoints, sample regeneration,
separation toggle, methods and narrow layout. This release adds clearer copy
and rounded-number explanations. Those copy changes were source-checked;
no second browser pass, physical-phone check or assistive-technology audit is
claimed. Chrome was reserved for separate work during release review.
