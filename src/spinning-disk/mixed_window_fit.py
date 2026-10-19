#!/usr/bin/env python3
"""Fit one power law to windows of the two-loss toy model.

This is model-on-model stress testing, not empirical evidence. It quantifies
what an analyst would infer by forcing a single exponent onto a trajectory whose
rolling and air-loss shares change continuously.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from identifiability import estimated_fit, fixed_fit, sample_tau
from model import Params, interpolate_theta_at_time, make_curve


WINDOWS_S = ((0.002, 0.02), (0.005, 0.1), (0.02, 0.2), (0.1, 1.0), (1.0, 10.0))


def rows() -> list[dict[str, object]]:
    # At millisecond windows, the omitted time from theta=0 to 1e-9 rad is
    # negligible. Calling the floor t=0 remains a numerical convention.
    curve = make_curve(Params(), theta_min=1e-9, count=60001)
    output: list[dict[str, object]] = []
    for lo, hi in WINDOWS_S:
        for sampling in ("log", "linear"):
            tau = sample_tau(lo, hi, 100, sampling)
            points = [interpolate_theta_at_time(curve, value) for value in tau]
            y = [math.log(point["theta_rad"]) for point in points]
            air_mean = sum(point["air_fraction"] for point in points) / len(points)
            fits = {
                "fixed_model_endpoint": (*fixed_fit(tau, y, 0.0), 0.0),
                "estimated_endpoint": estimated_fit(tau, y),
            }
            for method, result in fits.items():
                exponent, _, rms, offset_s = result
                output.append(
                    {
                        "window_min_s": lo,
                        "window_max_s": hi,
                        "sampling": sampling,
                        "method": method,
                        "fit_exponent": exponent,
                        "fit_endpoint_offset_ms": offset_s * 1000,
                        "log_rms": rms,
                        "mean_air_loss_fraction": air_mean,
                        "closer_candidate": "1/2" if abs(exponent - 0.5) < abs(exponent - 4 / 9) else "4/9",
                    }
                )
    return output


def checks() -> list[str]:
    data = rows()
    assert len(data) == 20
    assert all(math.isfinite(float(row["fit_exponent"])) for row in data)

    fixed_log = [
        row for row in data
        if row["method"] == "fixed_model_endpoint" and row["sampling"] == "log"
    ]
    fixed_log.sort(key=lambda row: float(row["window_min_s"]))
    assert all(0.43 < float(row["fit_exponent"]) < 0.67 for row in fixed_log)
    assert float(fixed_log[-1]["fit_exponent"]) > float(fixed_log[0]["fit_exponent"])

    for sampling in ("log", "linear"):
        for lo, hi in WINDOWS_S:
            pair = [
                row for row in data
                if row["sampling"] == sampling
                and row["window_min_s"] == lo
                and row["window_max_s"] == hi
            ]
            fixed = next(row for row in pair if row["method"] == "fixed_model_endpoint")
            joint = next(row for row in pair if row["method"] == "estimated_endpoint")
            assert float(joint["log_rms"]) <= float(fixed["log_rms"]) + 1e-12

    assert max(abs(float(row["fit_endpoint_offset_ms"])) for row in data) > 0.1
    assert {str(row["closer_candidate"]) for row in data} == {"4/9", "1/2"}

    published = {
        str(row["method"]): row
        for row in data
        if row["window_min_s"] == 0.005
        and row["window_max_s"] == 0.1
        and row["sampling"] == "log"
    }
    assert abs(float(published["fixed_model_endpoint"]["fit_exponent"]) - 0.4724954560510557) < 1e-12
    assert abs(float(published["estimated_endpoint"]["fit_exponent"]) - 0.4811675533302203) < 1e-12
    assert abs(float(published["fixed_model_endpoint"]["mean_air_loss_fraction"]) - 0.7701106875937476) < 1e-12
    return [
        "20 mixed-model window fits are finite: PASS",
        "fixed-endpoint exponents stay between asymptotic candidates: PASS",
        "earlier windows shift toward the rolling exponent: PASS",
        "joint endpoint fits never increase in-sample residual: PASS",
        "pure-law fit invents a nonzero endpoint shift for curved data: PASS",
        "window choice changes 4/9-versus-1/2 classification: PASS",
        "published 100-point log-sampled mixed-window values: PASS",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    if args.check or not args.csv:
        print("\n".join(checks()))
    if args.csv:
        data = rows()
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
        print(f"wrote {len(data)} rows to {args.csv}")


if __name__ == "__main__":
    main()
