#!/usr/bin/env python3
"""Direct synthetic selection between fixed 4/9 and 1/2 exponent models.

Each candidate gets its own amplitude. The collapse time is either fixed at the
true synthetic value or profiled independently for each candidate. The script
reports how often residual error chooses the wrong exponent. This is a
controlled identifiability test, not evidence about a physical disk.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
from pathlib import Path

from identifiability import NOISE_LEVELS, SAMPLING_MODES, TRUE_EXPONENTS, WINDOWS_MS, generate, quantile


def fit_fixed_exponent(
    tau: list[float], log_theta: list[float], exponent: float, offset_s: float
) -> tuple[float, float]:
    shifted = [value + offset_s for value in tau]
    if min(shifted) <= 0:
        return math.inf, math.nan
    residual_base = [y - exponent * math.log(t) for t, y in zip(shifted, log_theta)]
    log_amplitude = statistics.fmean(residual_base)
    rms = math.sqrt(statistics.fmean((value - log_amplitude) ** 2 for value in residual_base))
    return rms, math.exp(log_amplitude)


def profile_fixed_exponent(
    tau: list[float], log_theta: list[float], exponent: float
) -> tuple[float, float, float]:
    lo = -0.95 * min(tau)
    hi = 0.50 * max(tau)

    def scan(a: float, b: float, count: int) -> tuple[float, float, float]:
        candidates = [a + (b - a) * i / (count - 1) for i in range(count)]
        if a <= 0 <= b:
            candidates.append(0.0)
        scored = [(delta, *fit_fixed_exponent(tau, log_theta, exponent, delta)) for delta in candidates]
        return min(scored, key=lambda item: item[1])

    delta, rms, amplitude = scan(lo, hi, 81)
    step = (hi - lo) / 80
    delta, rms, amplitude = scan(max(lo, delta - step), min(hi, delta + step), 81)
    return rms, amplitude, delta


def selection_rows(repetitions: int) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for true_n in TRUE_EXPONENTS:
        for lo_ms, hi_ms in WINDOWS_MS:
            for noise in NOISE_LEVELS:
                for sampling in SAMPLING_MODES:
                    rng = random.Random(f"20261019:select:{true_n}:{lo_ms}:{hi_ms}:{noise}:{sampling}")
                    results = {"fixed_true_tf": [], "candidate_specific_tf": []}
                    for _ in range(repetitions):
                        tau, y = generate(true_n, lo_ms, hi_ms, sampling, noise, rng)
                        fixed = {
                            n: (*fit_fixed_exponent(tau, y, n, 0.0), 0.0)
                            for n in TRUE_EXPONENTS
                        }
                        profiled = {n: profile_fixed_exponent(tau, y, n) for n in TRUE_EXPONENTS}
                        for method, fits in (("fixed_true_tf", fixed), ("candidate_specific_tf", profiled)):
                            other_n = 0.5 if true_n == 4 / 9 else 4 / 9
                            correct_rms = fits[true_n][0]
                            other_rms = fits[other_n][0]
                            selected = min(fits, key=lambda n: fits[n][0])
                            results[method].append(
                                (
                                    selected != true_n,
                                    other_rms - correct_rms,
                                    fits[true_n][2] * 1000,
                                    fits[other_n][2] * 1000,
                                )
                            )

                    for method, values in results.items():
                        margins = [value[1] for value in values]
                        correct_offsets = [value[2] for value in values]
                        other_offsets = [value[3] for value in values]
                        output.append(
                            {
                                "true_exponent": true_n,
                                "window_min_ms": lo_ms,
                                "window_max_ms": hi_ms,
                                "sampling": sampling,
                                "log_noise_sigma": noise,
                                "repetitions": repetitions,
                                "endpoint_treatment": method,
                                "wrong_candidate_fraction": statistics.fmean(value[0] for value in values),
                                "rms_margin_other_minus_true_mean": statistics.fmean(margins),
                                "rms_margin_p05": quantile(margins, 0.05),
                                "rms_margin_median": quantile(margins, 0.50),
                                "rms_margin_p95": quantile(margins, 0.95),
                                "true_candidate_offset_ms_mean": statistics.fmean(correct_offsets),
                                "other_candidate_offset_ms_mean": statistics.fmean(other_offsets),
                            }
                        )
    return output


def headline_rows(repetitions: int = 200) -> list[dict[str, object]]:
    """Exact public scenario without recomputing the full design matrix."""
    true_n, lo_ms, hi_ms, noise = 4 / 9, 20.0, 100.0, 0.05
    output: list[dict[str, object]] = []
    for sampling in SAMPLING_MODES:
        rng = random.Random(
            f"20261019:select:{true_n}:{lo_ms}:{hi_ms}:{noise}:{sampling}"
        )
        wrong = {"fixed_true_tf": 0, "candidate_specific_tf": 0}
        for _ in range(repetitions):
            tau, y = generate(true_n, lo_ms, hi_ms, sampling, noise, rng)
            fixed = {
                n: fit_fixed_exponent(tau, y, n, 0.0)[0] for n in TRUE_EXPONENTS
            }
            profiled = {
                n: profile_fixed_exponent(tau, y, n)[0] for n in TRUE_EXPONENTS
            }
            wrong["fixed_true_tf"] += min(fixed, key=fixed.get) != true_n
            wrong["candidate_specific_tf"] += min(profiled, key=profiled.get) != true_n
        for method, count in wrong.items():
            output.append(
                {
                    "true_exponent": true_n,
                    "window_min_ms": lo_ms,
                    "window_max_ms": hi_ms,
                    "sample_count": 80,
                    "sampling": sampling,
                    "log_noise_sigma": noise,
                    "repetitions": repetitions,
                    "endpoint_treatment": method,
                    "endpoint_search_min_ms": 0.0 if method == "fixed_true_tf" else -19.0,
                    "endpoint_search_max_ms": 0.0 if method == "fixed_true_tf" else 50.0,
                    "wrong_candidate_count": count,
                    "wrong_candidate_fraction": count / repetitions,
                }
            )
    return output


def checks() -> list[str]:
    tau, y = generate(4 / 9, 5, 100, "log", 0.0, random.Random(1))
    true_rms, _ = fit_fixed_exponent(tau, y, 4 / 9, 0.0)
    other_rms, _ = fit_fixed_exponent(tau, y, 0.5, 0.0)
    assert true_rms < 1e-12 and other_rms > true_rms

    true_profile = profile_fixed_exponent(tau, y, 4 / 9)
    other_profile = profile_fixed_exponent(tau, y, 0.5)
    assert true_profile[0] < 1e-12 and abs(true_profile[2]) < 1e-12
    assert other_profile[0] > true_profile[0]

    data = selection_rows(40)
    assert len(data) == 72
    assert all(0 <= float(row["wrong_candidate_fraction"]) <= 1 for row in data)
    fixed_errors = [float(row["wrong_candidate_fraction"]) for row in data if row["endpoint_treatment"] == "fixed_true_tf"]
    free_errors = [float(row["wrong_candidate_fraction"]) for row in data if row["endpoint_treatment"] == "candidate_specific_tf"]
    assert statistics.fmean(free_errors) > statistics.fmean(fixed_errors)

    headline = headline_rows()
    expected = {
        ("log", "fixed_true_tf"): 1,
        ("log", "candidate_specific_tf"): 62,
        ("linear", "fixed_true_tf"): 2,
        ("linear", "candidate_specific_tf"): 62,
    }
    assert len(headline) == 4
    for row in headline:
        key = (str(row["sampling"]), str(row["endpoint_treatment"]))
        assert int(row["wrong_candidate_count"]) == expected[key]
        assert row["sample_count"] == 80
        if row["endpoint_treatment"] == "candidate_specific_tf":
            assert row["endpoint_search_min_ms"] == -19.0
            assert row["endpoint_search_max_ms"] == 50.0
    return [
        "noise-free fixed-endpoint candidate selection: PASS",
        "noise-free candidate-specific endpoint selection: PASS",
        "72-row selection design is bounded and finite: PASS",
        "candidate-specific endpoint freedom raises mean confusion: PASS",
        "published 200-repetition 4/9 selection counts and bounds: PASS",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--repetitions", type=int, default=150)
    args = parser.parse_args()
    if args.check or not args.csv:
        print("\n".join(checks()))
    if args.csv:
        data = selection_rows(args.repetitions)
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
        print(f"wrote {len(data)} rows to {args.csv}")


if __name__ == "__main__":
    main()
