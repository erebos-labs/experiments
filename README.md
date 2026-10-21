# Erebos Labs · Experiments

A small static collection of interactive educational and artistic experiments:

- **Same coin, two finish lines** — identical marginal waiting laws can coexist with an asymmetric first-arrival race. [Explore the patterns](https://erebos-labs.github.io/experiments/same-coin/); [source, checks and assumptions](src/same-coin/README.md).

- **Local clocks, audible tension** — a Kuramoto-style phase model mapped to a finite eight-bar synthesized instrument, with MIDI/WAV export.
- **The shortcut trap** — Braess’s paradox, using exact stationary continuous-flow solutions for two attributed congestion models.
- **Random enough for what?** — ideal riffle shuffles, comparing the top card, visible neighboring descents and the complete deck order.
- **Phantom places** — explore what a pair of ideal arrival-time cues can and cannot distinguish, with a finite optional synthesized comparison.
- **The vanishing wobble** — a rolling-disk scaling model and a synthetic demonstration of why an exponent can trade off against the fitted end time.

- **The 120° compromise** — drag three anchors to explore the established equal-tension planar shortest-network geometry and its boundary transition. [Open the junction](https://erebos-labs.github.io/experiments/soap-junctions/). The standalone HTML includes sources and physical limits; it is not a fluid simulation.

The mathematical ideas are established work. Sources, assumptions, objective choices, and limitations are visible within each experiment and in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Built with AI assistance; models and outputs were checked with deterministic calculations.

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
python3 src/riffle/test_model.py -v
python3 tests/verify_riffle.py
python3 -B tests/verify_spinning_disk.py
node tests/verify_spinning_disk.js
python3 -B src/same-coin/verify.py
```

`src/` contains the original model, UI, and synthesis implementations. `docs/` contains the self-contained generated pages for GitHub Pages. `tests/` contains model checks, scheduler/envelope checks, and an independent MIDI parser and traffic KKT oracle. The continuous integration workflow rebuilds and checks that generated pages match the checked-in version.

## Important limits

Clocks are dimensionless identical phase oscillators. Onsets are phase crossings; pitch, tempo, and kick are artistic choices. A low global order parameter does not rule out a stable traveling wave. This is not a biological or mechanical simulation. MIDI instruments can sound different from the synthesized patch. Offline audio output is numerically checked; tiny browser rounding differences mean exact WAV bytes are not guaranteed across renders. No listening evaluation is claimed.

Traffic has fixed demand, directed edges, identical infinitesimal drivers, continuous flow and toy costs. Animation illustrates route shares; it does not model queues or learning. Coordinated routing minimizes the average and can assign unequal individual journey times. The experiment is not a recommendation for real road policy.

Browser checks cover Chromium desktop and mobile emulation. Physical phones, other browser engines, and assistive-technology combinations remain untested. Download/render behavior can differ across browsers.

No express open-source reuse license has been selected; see [COPYRIGHT.txt](COPYRIGHT.txt). Source citations retain their original copyrights and licenses.

## Why the top card is not the whole deck

Choose one of the 52 rotations of a sorted deck uniformly. Every card is equally
likely to be on top, yet the circular order never changes. Only 52 of the 52!
possible orders can occur. A random-looking top card therefore does not imply
a well-shuffled full deck.

The riffle explorer applies that distinction to the established ideal
Gilbert–Shannon–Reeds model. After five ideal riffles from sorted order, top-card
total variation distance is about 0.020, while whole-deck distance is about 0.924.
These are different probability distributions, not probabilities that the deck
is “still unshuffled.” Total variation is the largest probability gap for any
yes/no question about the selected observation. Displayed values are rounded.

The deck convention is `deck[position] = original zero-based label`. Visible
descents and inverse-permutation descents are different counts. The latter
determines the forward GSR likelihood and preserves whole-deck TV exactly.
The carries connection and joint conditioning follow attributed established
work. This is an educational implementation with AI assistance, not new research.

`src/riffle/data.json` contains every displayed numerical table. To regenerate it
without network access or third-party dependencies, run:

```sh
python3 src/riffle/rebuild_data.py
python3 build.py
python3 src/riffle/test_model.py -v
python3 tests/verify_riffle.py
```

The recomputation includes bounded exhaustive eight-card cut comparisons and
can take about a minute, depending on hardware. `verify_riffle.py` independently
enumerates repeated small-deck cut/interleave laws and uses an explicit
Eulerian-number sum to check all 15 displayed 52-card whole-deck TV values.
It also checks the top-card marginal and the rotation example. General results
come from the cited papers; finite code checks do not prove new theorems.

Riffle limits: 52 distinct labels, initially sorted, ideal binomial cuts and
uniform random interleaving. Human hand technique and game-specific fairness
were not measured. The eight-card comparison does not certify 52-card mixing
under other cut rules. The illustrated sample deck is deterministic. The
interaction script was browser-tested before release;
the public wording and package were source-checked without claiming a second
browser run.

## Phantom places

The self-contained sound-localization explorer is built from the original module
in `src/phantom/`. Sources, model assumptions and numerical checks are retained
there, including [source references](src/phantom/SOURCES.md). This is an educational
cue-geometry model, not an individualized headphone or human-perception test.
Sound is muted initially, requires a user gesture, and has finite playback.
No listening, device calibration or physical-headphone result is claimed.

Run its complete dependency-free checks with:

```sh
python3 -B src/phantom/scripts/verify.py
```

The earlier collection browser results do not extend automatically to this
addition. Desktop controls received a separate preview check; collection
integration, narrow layouts and assistive-technology coverage are reported
separately when actually checked.

## Additional educational modules

- **Does a flower have an ear?** — Compare reported nectar summaries, deposited rows and unresolved evidence limits. A critical evidence bench, not biological replication. See [module sources and limits](src/flower-evidence/README.md).
- **The shortcut trap, one day later** — Compare synchronous and gradual route updates in two toy models. Finite trajectories show how adjustment rules matter; no convergence guarantee. See [module sources and limits](src/route-learning/README.md).
- **Square ice: boundaries, loops and counts** — Read the source and finite checks for an arrow model. Boundary assumptions matter; this is a source/derivation module, not a water-ice simulation. See [module sources and limits](src/square-ice/README.md).
- **The vanishing wobble** — Explore a combined rolling-loss and boundary-layer toy model, then stress-test exponent fitting with synthetic data. It is not a contact solver or evidence for a universal dissipation sequence. See [module sources and limits](src/spinning-disk/README.md).

The modules include source code, reproducible checks and documented limits. Presentation revisions preserve the numerical models and fixtures. These checks do not establish empirical validity or prove new theorems. Square Ice is a source guide with command-line checks.

Run the module checks:

```sh
python3 -B src/flower-evidence/test_demo.py
node src/route-learning/verify.js
python3 -B src/route-learning/verify_equilibrium.py
node src/route-learning/test_review.js
python3 -B src/route-learning/test_validation.py
python3 -B src/square-ice/checks.py
python3 -B src/square-ice/verify_loops.py
python3 -B src/square-ice/boundary_paths.py
python3 -B src/square-ice/test_soft_bound.py
python3 -B src/square-ice/test_review.py
python3 -B src/square-ice/generate_fixtures.py --check
python3 -B tests/check_additions.py
python3 -B tests/verify_spinning_disk.py
node tests/verify_spinning_disk.js
```
