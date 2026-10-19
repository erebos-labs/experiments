#!/usr/bin/env python3
"""Synthetic identifiability study for Euler-disk power-law fits.

This script never reads experimental disk data. It generates

    theta = A * (t_f - t)**n * lognormal_noise

and compares three analyses: the true collapse time fixed, a collapse time
fixed 3 ms late, and collapse time estimated jointly with n. It varies noise,
sampling window, and linear versus logarithmic sampling. Only the standard
library is used so the calculation is reproducible without installation.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
from pathlib import Path


WINDOWS_MS = ((2.0, 20.0), (5.0, 100.0), (20.0, 100.0))
NOISE_LEVELS = (0.01, 0.02, 0.05)
SAMPLING_MODES = ("log", "linear")
TRUE_EXPONENTS = (4 / 9, 0.5)


def sample_tau(lo_s: float, hi_s: float, count: int, mode: str) -> list[float]:
    if mode == "log":
        return [lo_s * (hi_s / lo_s) ** (i / (count - 1)) for i in range(count)]
    if mode == "linear":
        return [lo_s + (hi_s - lo_s) * i / (count - 1) for i in range(count)]
    raise ValueError(f"unknown sampling mode: {mode}")


def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)
    denominator = sum((x - mx) ** 2 for x in xs)
    if denominator <= 0:
        raise ValueError("degenerate predictor")
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denominator
    intercept = my - slope * mx
    rms = math.sqrt(
        statistics.fmean((y - intercept - slope * x) ** 2 for x, y in zip(xs, ys))
    )
    return slope, intercept, rms


def generate(
    true_n: float,
    lo_ms: float,
    hi_ms: float,
    sampling: str,
    noise_sigma: float,
    rng: random.Random,
    count: int = 80,
    amplitude: float = 0.1,
) -> tuple[list[float], list[float]]:
    tau = sample_tau(lo_ms / 1000, hi_ms / 1000, count, sampling)
    log_theta = [
        math.log(amplitude) + true_n * math.log(value) + rng.gauss(0, noise_sigma)
        for value in tau
    ]
    return tau, log_theta


def fixed_fit(
    true_tau: list[float], log_theta: list[float], offset_s: float
) -> tuple[float, float, float]:
    assumed_tau = [value + offset_s for value in true_tau]
    if min(assumed_tau) <= 0:
        return math.nan, math.nan, math.inf
    n_fit, log_a, rms = linear_fit(
        [math.log(value) for value in assumed_tau], log_theta
    )
    return n_fit, math.exp(log_a), rms


def estimated_fit(
    true_tau: list[float], log_theta: list[float]
) -> tuple[float, float, float, float]:
    """Estimate collapse offset with a bounded coarse-to-fine profile search."""
    lo = -0.95 * min(true_tau)
    hi = 0.50 * max(true_tau)

    def scan(a: float, b: float, count: int) -> tuple[float, tuple[float, float, float]]:
        candidates = [a + (b - a) * i / (count - 1) for i in range(count)]
        if a <= 0 <= b:
            candidates.append(0.0)
        scored = [(delta, fixed_fit(true_tau, log_theta, delta)) for delta in candidates]
        return min(scored, key=lambda item: item[1][2])

    best_delta, best = scan(lo, hi, 81)
    coarse_step = (hi - lo) / 80
    refine_lo = max(lo, best_delta - coarse_step)
    refine_hi = min(hi, best_delta + coarse_step)
    best_delta, best = scan(refine_lo, refine_hi, 81)
    n_fit, amplitude, rms = best
    return n_fit, amplitude, rms, best_delta


def classification_error(n_fit: float, true_n: float) -> bool:
    other = 0.5 if true_n == 4 / 9 else 4 / 9
    return abs(n_fit - other) < abs(n_fit - true_n)


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summary_rows(repetitions: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for true_n in TRUE_EXPONENTS:
        for lo_ms, hi_ms in WINDOWS_MS:
            for noise in NOISE_LEVELS:
                for sampling in SAMPLING_MODES:
                    seed = f"20261019:{true_n}:{lo_ms}:{hi_ms}:{noise}:{sampling}"
                    rng = random.Random(seed)
                    values: dict[str, list[tuple[float, float, float, bool]]] = {
                        "fixed_true_tf": [],
                        "fixed_tf_plus_3ms": [],
                        "estimated_tf": [],
                    }
                    for _ in range(repetitions):
                        tau, y = generate(true_n, lo_ms, hi_ms, sampling, noise, rng)
                        n0, _, rms0 = fixed_fit(tau, y, 0.0)
                        n3, _, rms3 = fixed_fit(tau, y, 0.003)
                        ne, _, rmse, delta = estimated_fit(tau, y)
                        values["fixed_true_tf"].append((n0, 0.0, rms0, False))
                        values["fixed_tf_plus_3ms"].append((n3, 3.0, rms3, False))
                        lower_bound = -0.95 * min(tau)
                        upper_bound = 0.50 * max(tau)
                        at_bound = abs(delta - lower_bound) < 1e-12 or abs(delta - upper_bound) < 1e-12
                        values["estimated_tf"].append((ne, delta * 1000, rmse, at_bound))

                    for method, fits in values.items():
                        exponents = [fit[0] for fit in fits]
                        offsets = [fit[1] for fit in fits]
                        residuals = [fit[2] for fit in fits]
                        rows.append(
                            {
                                "true_exponent": true_n,
                                "window_min_ms": lo_ms,
                                "window_max_ms": hi_ms,
                                "sampling": sampling,
                                "log_noise_sigma": noise,
                                "repetitions": repetitions,
                                "method": method,
                                "fit_exponent_mean": statistics.fmean(exponents),
                                "fit_exponent_sd": statistics.stdev(exponents),
                                "fit_exponent_p05": quantile(exponents, 0.05),
                                "fit_exponent_median": quantile(exponents, 0.50),
                                "fit_exponent_p95": quantile(exponents, 0.95),
                                "fit_offset_ms_mean": statistics.fmean(offsets),
                                "fit_offset_ms_sd": statistics.stdev(offsets),
                                "fit_offset_ms_p05": quantile(offsets, 0.05),
                                "fit_offset_ms_median": quantile(offsets, 0.50),
                                "fit_offset_ms_p95": quantile(offsets, 0.95),
                                "log_rms_mean": statistics.fmean(residuals),
                                "fit_at_search_bound_fraction": statistics.fmean(
                                    fit[3] for fit in fits
                                ),
                                "misclassified_fraction": statistics.fmean(
                                    classification_error(value, true_n)
                                    for value in exponents
                                ),
                            }
                        )
    return rows


def profile_rows() -> list[dict[str, float]]:
    rng = random.Random("20261019:profile")
    tau, y = generate(4 / 9, 5, 100, "log", 0.02, rng)
    rows = []
    for index in range(121):
        offset_ms = -4 + 12 * index / 120
        n_fit, _, rms = fixed_fit(tau, y, offset_ms / 1000)
        rows.append(
            {
                "assumed_offset_ms": offset_ms,
                "profiled_exponent": n_fit,
                "log_rms": rms,
            }
        )
    best = min(row["log_rms"] for row in rows)
    for row in rows:
        row["rms_above_best"] = row["log_rms"] - best
    return rows


def checks() -> list[str]:
    tau, y = generate(4 / 9, 5, 100, "log", 0.0, random.Random(1))
    n0, a0, rms0 = fixed_fit(tau, y, 0.0)
    assert abs(n0 - 4 / 9) < 1e-12 and abs(a0 - 0.1) < 1e-12 and rms0 < 1e-12

    ne, ae, rmse, de = estimated_fit(tau, y)
    assert abs(ne - 4 / 9) < 1e-10 and abs(ae - 0.1) < 1e-10
    assert rmse < 1e-10 and abs(de) < 1e-10

    n3, _, _ = fixed_fit(tau, y, 0.003)
    assert abs(n3 - 0.5131820328) < 1e-8

    rows = summary_rows(80)
    assert len(rows) == 108
    assert all(math.isfinite(float(row["fit_exponent_mean"])) for row in rows)
    assert all(
        float(row["fit_exponent_p05"])
        <= float(row["fit_exponent_median"])
        <= float(row["fit_exponent_p95"])
        for row in rows
    )

    scenario = [
        row
        for row in rows
        if row["true_exponent"] == 4 / 9
        and row["window_min_ms"] == 5
        and row["window_max_ms"] == 100
        and row["sampling"] == "log"
        and row["log_noise_sigma"] == 0.02
    ]
    fixed = next(row for row in scenario if row["method"] == "fixed_true_tf")
    estimated = next(row for row in scenario if row["method"] == "estimated_tf")
    wrong = next(row for row in scenario if row["method"] == "fixed_tf_plus_3ms")
    assert abs(float(fixed["fit_exponent_mean"]) - 4 / 9) < 0.002
    assert float(estimated["fit_exponent_sd"]) > float(fixed["fit_exponent_sd"])
    assert float(wrong["misclassified_fraction"]) > 0.95

    short_window = next(
        row for row in rows
        if row["true_exponent"] == 4 / 9
        and row["window_min_ms"] == 2
        and row["window_max_ms"] == 20
        and row["sampling"] == "log"
        and row["log_noise_sigma"] == 0.02
        and row["method"] == "fixed_tf_plus_3ms"
    )
    early_window = next(
        row for row in rows
        if row["true_exponent"] == 4 / 9
        and row["window_min_ms"] == 20
        and row["window_max_ms"] == 100
        and row["sampling"] == "log"
        and row["log_noise_sigma"] == 0.02
        and row["method"] == "fixed_tf_plus_3ms"
    )
    assert float(short_window["fit_exponent_mean"]) - float(early_window["fit_exponent_mean"]) > 0.15

    early_joint = next(
        row for row in rows
        if row["true_exponent"] == 4 / 9
        and row["window_min_ms"] == 20
        and row["window_max_ms"] == 100
        and row["sampling"] == "log"
        and row["log_noise_sigma"] == 0.02
        and row["method"] == "estimated_tf"
    )
    assert float(early_joint["misclassified_fraction"]) > float(estimated["misclassified_fraction"])

    profile = profile_rows()
    assert len(profile) == 121
    assert min(row["log_rms"] for row in profile) < 0.03
    return [
        "noise-free fixed-t_f recovery: PASS",
        "noise-free joint n/t_f recovery: PASS",
        "3 ms offset regression snapshot: PASS",
        "108-row design matrix is finite: PASS",
        "Monte Carlo quantile ordering: PASS",
        "correct fixed t_f is unbiased in reference ensemble: PASS",
        "joint t_f estimation increases exponent variance: PASS",
        "3 ms misspecification changes mechanism classification: PASS",
        "endpoint bias depends strongly on sampling window: PASS",
        "restricted dynamic range raises joint-fit confusion: PASS",
        "seeded profile regression: PASS",
    ]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument("--profile-csv", type=Path)
    parser.add_argument("--repetitions", type=int, default=200)
    args = parser.parse_args()
    if args.check or (not args.summary_csv and not args.profile_csv):
        print("\n".join(checks()))
    if args.summary_csv:
        rows = summary_rows(args.repetitions)
        write_csv(args.summary_csv, rows)
        print(f"wrote {len(rows)} summary rows to {args.summary_csv}")
    if args.profile_csv:
        rows = profile_rows()
        write_csv(args.profile_csv, rows)
        print(f"wrote {len(rows)} profile rows to {args.profile_csv}")


if __name__ == "__main__":
    main()
