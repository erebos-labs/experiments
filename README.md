# Erebos Labs · Experiments

A small static collection of interactive educational and artistic experiments:

- **Local clocks, audible tension** — a Kuramoto-style phase model mapped to a finite eight-bar synthesized instrument, with MIDI/WAV export.
- **The shortcut trap** — Braess’s paradox, using exact stationary continuous-flow solutions for two attributed congestion models.

The mathematical ideas are established work. Sources, assumptions, objective choices, and limitations are visible within each experiment and in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Built with AI assistance; models and outputs are checked by reproducible tests.

## Play

[Open the collection](https://erebos-labs.github.io/experiments/).

For offline use, download the repository ZIP and open `docs/index.html`, or download an individual experiment’s self-contained HTML from its page. Sound starts off and requires pressing **Start audio**. Browser support for downloaded local files varies on phones; hosted HTTPS is the simplest phone route.

No package dependencies, application server, authentication, analytics scripts, external assets, or sample libraries are required. GitHub Pages may log visitor IP addresses for security; these pages add no telemetry.

## Rebuild and check

Requires existing Python 3 and Node.js; no dependency installation.

```sh
python3 build.py
node tests/test_clocks.js
node tests/test_sequence.js /tmp/erebos-midi-check
node tests/test_synth.js
python3 tests/parse_midi.py /tmp/erebos-midi-check
python3 tests/verify_traffic.py /tmp/erebos-traffic-check
python3 tests/check_package.py
```

`src/` contains the original model, UI, and synthesis implementations. `docs/` contains the self-contained generated pages for GitHub Pages. `tests/` contains model checks, scheduler/envelope checks, and an independent MIDI parser and traffic KKT oracle. The continuous integration workflow rebuilds and checks that generated pages match the checked-in version.

## Important limits

Clocks are dimensionless identical phase oscillators. Onsets are phase crossings; pitch, tempo, and kick are artistic choices. A low global order parameter does not rule out a stable traveling wave. This is not a biological or mechanical simulation. MIDI instruments can sound different from the synthesized patch. Offline audio output is numerically checked; no listening evaluation is claimed.

Traffic has fixed demand, directed edges, identical infinitesimal drivers, continuous flow and toy costs. Animation illustrates route shares; it does not model queues or learning. Coordinated routing minimizes the average and can assign unequal individual journey times. The experiment is not a recommendation for real road policy.

Browser checks cover Chromium desktop and mobile emulation. Physical phones, other browser engines, and assistive-technology combinations remain untested. Download/render behavior can differ across browsers.

No express open-source reuse license has been selected; see [COPYRIGHT.txt](COPYRIGHT.txt). Source citations retain their original copyrights and licenses.
