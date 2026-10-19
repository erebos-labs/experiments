#!/usr/bin/env python3
"""Synthetic sensitivity of power-law fits to collapse-time uncertainty.

This does not fit experimental data. It asks how a known theta=A*tau^n law is
recovered when multiplicative noise is added and the analyst shifts tau by a
small collapse-time offset.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
from pathlib import Path


def log_spaced(lo: float, hi: float, count: int) -> list[float]:
    return [lo * (hi / lo) ** (i / (count - 1)) for i in range(count)]


def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Return slope, intercept, and root-mean-square residual."""
    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)
    denominator = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denominator
    intercept = my - slope * mx
    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    rms = math.sqrt(statistics.fmean(r * r for r in residuals))
    return slope, intercept, rms


def one_fit(
    true_n: float,
    assumed_offset_s: float,
    rng: random.Random,
    noise_sigma: float = 0.02,
    amplitude: float = 0.1,
) -> tuple[float, float, float]:
    true_tau = log_spaced(0.005, 0.1, 120)
    theta = [
        amplitude * tau**true_n * math.exp(rng.gauss(0.0, noise_sigma))
        for tau in true_tau
    ]
    assumed_tau = [tau + assumed_offset_s for tau in true_tau]
    if min(assumed_tau) <= 0:
        raise ValueError("offset moves a modeled sample past the assumed collapse")
    n_fit, log_a_fit, rms = linear_fit(
        [math.log(tau) for tau in assumed_tau], [math.log(value) for value in theta]
    )
    return n_fit, math.exp(log_a_fit), rms


def summary_rows(repetitions: int = 500) -> list[dict[str, float]]:
    rows = []
    for true_n in (4 / 9, 0.5):
        for offset_ms in (-3.0, -1.0, 0.0, 1.0, 3.0, 5.0):
            rng = random.Random(f"20261019:{true_n}:{offset_ms}")
            fits = [one_fit(true_n, offset_ms / 1000.0, rng) for _ in range(repetitions)]
            exponents = [fit[0] for fit in fits]
            amplitudes = [fit[1] for fit in fits]
            residuals = [fit[2] for fit in fits]
            rows.append(
                {
                    "true_tilt_exponent": true_n,
                    "assumed_collapse_offset_ms": offset_ms,
                    "repetitions": repetitions,
                    "fit_exponent_mean": statistics.fmean(exponents),
                    "fit_exponent_sd": statistics.stdev(exponents),
                    "fit_amplitude_mean": statistics.fmean(amplitudes),
                    "log_fit_rms_mean": statistics.fmean(residuals),
                    "fraction_closer_to_other_exponent": statistics.fmean(
                        abs(value - (0.5 if true_n == 4 / 9 else 4 / 9))
                        < abs(value - true_n)
                        for value in exponents
                    ),
                }
            )
    return rows


def checks() -> list[str]:
    n, amplitude, rms = one_fit(4 / 9, 0.0, random.Random(1), noise_sigma=0.0)
    assert abs(n - 4 / 9) < 1e-12
    assert abs(amplitude - 0.1) < 1e-12
    assert rms < 1e-12

    rows = summary_rows(100)
    exact = next(
        row
        for row in rows
        if row["true_tilt_exponent"] == 4 / 9
        and row["assumed_collapse_offset_ms"] == 0.0
    )
    assert abs(exact["fit_exponent_mean"] - 4 / 9) < 0.002
    return [
        "noise-free recovery of exponent and amplitude: PASS",
        "seeded zero-offset ensemble is unbiased within tolerance: PASS",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--repetitions", type=int, default=500)
    args = parser.parse_args()
    if args.check or not args.csv:
        print("\n".join(checks()))
    if args.csv:
        rows = summary_rows(args.repetitions)
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
