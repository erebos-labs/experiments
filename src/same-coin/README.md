# Same coin, two finish lines

An interactive educational reproduction of established results about overlapping coin patterns. Choose two three-flip patterns, vary the probability of heads, compare first-arrival races with fixed-horizon scores, or inspect an H/T sequence.

HHT and THH have identical entire waiting-time distributions when observed separately from empty history. On the **same stream of independent fair-coin flips**, THH arrives first with probability **3/4**, while HHT arrives first with probability **1/4**. Each has a mean waiting time of eight flips. These are dependent arrival times on one stream, not two independent coins.

For any fixed horizon of at least four iid fair flips, each pattern outscores the other with probability 3/16, with tie probability 5/8. The deterministic identity is

```
#HHT - #THH = 1{first two flips are HH} - 1{last two flips are HH}.
```

Reversal exchanges HHT and THH in every finite string without changing its iid probability, so their avoidance probabilities and marginal waiting laws agree. Reversal does not exchange their first-arrival ordering on a shared stream. HHT wins the race exactly when the first two flips are HH; otherwise the first eventual HH completes THH first.

## Run and reproduce

Open `index.html` in a modern browser. It is self-contained and uses BigInt exact rational arithmetic. No installation, server or network is needed for the model. Source links open only when selected.

With Python 3 and Node.js available, run:

```sh
python3 -B build.py --check
python3 -B verify.py
```

The verifier checks the headline probabilities, 2,040 finite-string boundary identities, 532 exact race cases and 2,128 fixed-horizon cases. It regenerates temporary Python rational fixtures and compares 9,044 JavaScript values, plus invalid-input and sequence checks. It does not claim browser automation.

## Scope and limitations

Flips are iid; histories start empty. Races are uncapped; fixed-horizon ties are retained. Interactive patterns have length three, heads probabilities are 5% through 95% in 5% steps, and fixed horizons are 3 through 100. Horizon three differs from the at-least-four formula. Decimal displays are rounded. This is a mathematical model with no measured physical-coin data, no new theorem claim, and no finance or gambling advice. The exact solver rejects duplicate and contained patterns.

Original implementation and presentation with AI assistance. Primary references and rights are in [SOURCES.md](SOURCES.md) and [COPYRIGHT.txt](COPYRIGHT.txt).
