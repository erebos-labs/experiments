#!/usr/bin/env python3
"""Dependency-free checks for a two-loss Euler-disk toy model.

The model follows Eqs. (1), (2), (4), and (5) in Thorne et al. (2026).
It is a scaling-model explorer, not a rigid-body/contact solver.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path


G = 9.81
ETA = 1.85e-5


@dataclass(frozen=True)
class Params:
    mass_kg: float = 0.445
    radius_m: float = 0.0375
    density_kg_m3: float = 1.18
    rolling_mu: float = 1.0e-4


def omega(theta: float, p: Params) -> float:
    """Precession angular frequency in rad/s."""
    return math.sqrt(4.0 * G / (p.radius_m * math.sin(theta)))


def air_rate(theta: float, p: Params) -> float:
    """Positive magnitude of d(theta)/dt due to boundary-layer air drag."""
    return (
        (8.0 / 3.0)
        * G**0.25
        * p.radius_m**1.75
        * math.sqrt(ETA * p.density_kg_m3)
        / p.mass_kg
        * theta**-1.25
    )


def rolling_rate(theta: float, p: Params) -> float:
    """Positive magnitude of d(theta)/dt due to the fitted rolling term."""
    return (2.0 / 3.0) * p.rolling_mu * math.cos(theta) * omega(theta, p)


def crossover_angle(p: Params) -> float:
    """Small-angle estimate where air and rolling losses are equal."""
    ratio = (
        2.0
        * p.radius_m**2.25
        * math.sqrt(ETA * p.density_kg_m3)
        / (p.rolling_mu * p.mass_kg * G**0.25)
    )
    return ratio ** (4.0 / 3.0)


def thin_layer_limit(p: Params) -> float:
    """Self-consistent angle where sqrt(2 eta/(rho Omega)) equals R theta."""
    return (ETA**2 / (G * p.radius_m**3 * p.density_kg_m3**2)) ** (1.0 / 3.0)


def make_curve(
    p: Params, theta_min: float = 1e-4, theta_max: float = 0.25, count: int = 2401
) -> list[dict[str, float]]:
    """Return a log-spaced curve with remaining time obtained by quadrature."""
    if not (0 < theta_min < theta_max < math.pi / 2):
        raise ValueError("angles must satisfy 0 < min < max < pi/2")
    if count < 3:
        raise ValueError("count must be at least 3")
    ratio = theta_max / theta_min
    thetas = [theta_min * ratio ** (i / (count - 1)) for i in range(count)]
    rows: list[dict[str, float]] = []
    remaining = 0.0
    previous_theta = thetas[0]
    previous_inverse_rate = 1.0 / (
        air_rate(previous_theta, p) + rolling_rate(previous_theta, p)
    )
    for i, theta in enumerate(thetas):
        air = air_rate(theta, p)
        roll = rolling_rate(theta, p)
        inverse_rate = 1.0 / (air + roll)
        if i:
            remaining += 0.5 * (inverse_rate + previous_inverse_rate) * (
                theta - previous_theta
            )
        rows.append(
            {
                "theta_rad": theta,
                "remaining_s": remaining,
                "frequency_hz": omega(theta, p) / (2.0 * math.pi),
                "air_fraction": air / (air + roll),
                "air_rate_rad_s": air,
                "rolling_rate_rad_s": roll,
            }
        )
        previous_theta = theta
        previous_inverse_rate = inverse_rate
    return rows


def local_log_slope(xs: list[float], ys: list[float]) -> float:
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    mx = sum(lx) / len(lx)
    my = sum(ly) / len(ly)
    numerator = sum((x - mx) * (y - my) for x, y in zip(lx, ly))
    denominator = sum((x - mx) ** 2 for x in lx)
    return numerator / denominator


def run_checks() -> list[str]:
    p = Params()
    curve = make_curve(p)
    assert all(b["remaining_s"] > a["remaining_s"] for a, b in zip(curve, curve[1:]))
    assert all(b["frequency_hz"] < a["frequency_hz"] for a, b in zip(curve, curve[1:]))

    theta_c = crossover_angle(p)
    balance = air_rate(theta_c, p) / rolling_rate(theta_c, p)
    assert abs(balance - 1.0) < 0.03, balance

    # Pure-mechanism quadrature should recover theta ~ tau^(4/9) and tau^(2/3).
    def mechanism_slope(which: str) -> float:
        angles = [1e-4 * (400.0 ** (i / 1000)) for i in range(1001)]
        tau = 0.0
        taus: list[float] = []
        previous_angle = angles[0]
        rate_fn = air_rate if which == "air" else rolling_rate
        previous_inverse = 1.0 / rate_fn(previous_angle, p)
        for angle in angles:
            inverse = 1.0 / rate_fn(angle, p)
            tau += 0.5 * (inverse + previous_inverse) * (angle - previous_angle)
            taus.append(tau)
            previous_angle = angle
            previous_inverse = inverse
        # Fit away from the artificial theta_min boundary: near that boundary,
        # tau is an integral to theta_min rather than the ideal integral to zero.
        subset = [(t, a) for t, a in zip(taus, angles) if t > 0][650:950]
        return local_log_slope([x[0] for x in subset], [x[1] for x in subset])

    air_slope = mechanism_slope("air")
    rolling_slope = mechanism_slope("rolling")
    assert abs(air_slope - 4 / 9) < 0.01, air_slope
    assert abs(rolling_slope - 2 / 3) < 0.02, rolling_slope
    paper_air_prefactor = (
        6 ** (4 / 9)
        * G ** (1 / 9)
        * (ETA * p.density_kg_m3) ** (2 / 9)
        * p.radius_m ** (7 / 9)
        / p.mass_kg ** (4 / 9)
    )
    air_rate_coefficient = air_rate(1.0, p)
    integrated_air_prefactor = ((9 / 4) * air_rate_coefficient) ** (4 / 9)
    assert abs(integrated_air_prefactor / paper_air_prefactor - 1.0) < 1e-12

    heavy = crossover_angle(Params(mass_kg=0.445))
    light = crossover_angle(Params(mass_kg=0.100))
    assert light > heavy
    low_density = crossover_angle(Params(density_kg_m3=0.118))
    assert low_density < heavy
    assert thin_layer_limit(Params(density_kg_m3=0.118)) > thin_layer_limit(p)
    expected_limit = (ETA**2 / (G * p.radius_m**3 * p.density_kg_m3**2)) ** (1 / 3)
    assert abs(thin_layer_limit(p) / expected_limit - 1) < 1e-15
    omega_at_limit = omega(expected_limit, p)
    boundary_thickness = math.sqrt(2 * ETA / (p.density_kg_m3 * omega_at_limit))
    small_angle_gap = p.radius_m * expected_limit
    assert abs(boundary_thickness / small_angle_gap - 1) < 2e-3

    rng = random.Random(20261019)
    for _ in range(500):
        trial = Params(
            mass_kg=rng.uniform(0.040, 0.800),
            radius_m=rng.uniform(0.025, 0.060),
            density_kg_m3=rng.uniform(0.100, 1.200),
            rolling_mu=10 ** rng.uniform(-5.0, -3.0),
        )
        trial_curve = make_curve(trial, count=101)
        values = [value for row in trial_curve for value in row.values()]
        assert all(math.isfinite(value) for value in values)
        assert all(
            b["remaining_s"] > a["remaining_s"]
            for a, b in zip(trial_curve, trial_curve[1:])
        )
    browser_resolution = next(row for row in convergence_rows(p) if row["sample_count"] == 1400)
    assert abs(browser_resolution["relative_error_vs_40001"]) < 1e-5

    return [
        "monotonic remaining-time curve: PASS",
        "frequency rises as tilt falls: PASS",
        f"analytic crossover balance: PASS (air/rolling={balance:.6f})",
        f"air-only exponent: PASS ({air_slope:.6f}, target 4/9)",
        f"rolling-only exponent: PASS ({rolling_slope:.6f}, target 2/3)",
        "boundary-layer prefactor matches Eq. 4: PASS",
        "lighter disk crosses to air dominance earlier (larger angle): PASS",
        "lower air density delays crossover (smaller angle): PASS",
        "lower air density makes the thin-boundary-layer limit occur earlier: PASS",
        "thin-layer cutoff is algebraically consistent with displayed thickness: PASS",
        "500-case seeded parameter stress: PASS",
        "browser quadrature resolution vs. 40,001-point reference: PASS",
    ]


def sensitivity_rows() -> list[dict[str, float]]:
    rows = []
    for mass in (0.100, 0.445, 0.800):
        for density in (0.118, 0.590, 1.180):
            for rolling_mu in (3e-5, 1e-4, 3e-4):
                p = Params(mass_kg=mass, density_kg_m3=density, rolling_mu=rolling_mu)
                tc = crossover_angle(p)
                tl = thin_layer_limit(p)
                rows.append(
                    {
                        "mass_kg": mass,
                        "density_kg_m3": density,
                        "rolling_mu": rolling_mu,
                        "crossover_rad": tc,
                        "crossover_deg": math.degrees(tc),
                        "thin_layer_limit_rad": tl,
                        "thin_layer_limit_deg": math.degrees(tl),
                        "crossover_inside_thin_layer_regime": float(tc >= tl),
                    }
                )
    return rows


def window_rows(p: Params = Params()) -> list[dict[str, float]]:
    """Sample the local log-log tilt exponent across a mixed-loss trajectory."""
    curve = make_curve(p, theta_min=1e-7, count=12001)
    rows = []
    for target in (0.2, 0.1, 0.05, 0.03, 0.015, 0.008, 0.005):
        i = min(range(5, len(curve) - 5), key=lambda j: abs(curve[j]["theta_rad"] - target))
        before, point, after = curve[i - 5], curve[i], curve[i + 5]
        exponent = math.log(after["theta_rad"] / before["theta_rad"]) / math.log(
            after["remaining_s"] / before["remaining_s"]
        )
        rows.append(
            {
                "theta_rad": point["theta_rad"],
                "theta_deg": math.degrees(point["theta_rad"]),
                "remaining_s": point["remaining_s"],
                "air_fraction": point["air_fraction"],
                "local_tilt_exponent": exponent,
                "inside_thin_layer_regime": float(point["theta_rad"] >= thin_layer_limit(p)),
            }
        )
    return rows


def mechanism_rows() -> list[dict[str, float | str]]:
    """Map idealized loss laws Phi ~ Omega^p to observable exponents."""
    mechanisms = (
        ("rolling friction", 1.0),
        ("viscous rolling or turbulent drag", 2.0),
        ("viscous boundary layer", 2.5),
        ("full-gap viscous drag (Moffatt)", 4.0),
    )
    return [
        {
            "mechanism": name,
            "loss_power_p_in_phi_proportional_omega_p": p,
            "tilt_exponent_n": 2.0 / (p + 2.0),
            "precession_divergence_exponent": 1.0 / (p + 2.0),
        }
        for name, p in mechanisms
    ]


def interpolate_theta_at_time(curve: list[dict[str, float]], remaining_s: float) -> dict[str, float]:
    if not (curve[0]["remaining_s"] <= remaining_s <= curve[-1]["remaining_s"]):
        raise ValueError("requested time is outside the modeled curve")
    for left, right in zip(curve, curve[1:]):
        if left["remaining_s"] <= remaining_s <= right["remaining_s"]:
            span = right["remaining_s"] - left["remaining_s"]
            weight = (remaining_s - left["remaining_s"]) / span
            return {
                key: left[key] + weight * (right[key] - left[key])
                for key in left
            }
    return curve[-1]


def pressure_rows() -> list[dict[str, float]]:
    ambient = Params(density_kg_m3=1.18)
    partial_vacuum = Params(density_kg_m3=0.118)
    ambient_curve = make_curve(ambient, theta_min=1e-7, count=12001)
    vacuum_curve = make_curve(partial_vacuum, theta_min=1e-7, count=12001)
    rows = []
    for remaining in (10.0, 1.0, 0.1, 0.03, 0.01):
        a = interpolate_theta_at_time(ambient_curve, remaining)
        v = interpolate_theta_at_time(vacuum_curve, remaining)
        rows.append(
            {
                "remaining_s": remaining,
                "ambient_theta_rad": a["theta_rad"],
                "vacuum_theta_rad": v["theta_rad"],
                "vacuum_to_ambient_theta_ratio": v["theta_rad"] / a["theta_rad"],
                "ambient_frequency_hz": a["frequency_hz"],
                "vacuum_frequency_hz": v["frequency_hz"],
                "ambient_thin_layer_valid": float(a["theta_rad"] >= thin_layer_limit(ambient)),
                "vacuum_thin_layer_valid": float(
                    v["theta_rad"] >= thin_layer_limit(partial_vacuum)
                ),
            }
        )
    return rows


def convergence_rows(p: Params = Params()) -> list[dict[str, float]]:
    reference = make_curve(p, count=40001)[-1]["remaining_s"]
    rows = []
    for count in (51, 101, 301, 1001, 1400, 2401, 5001, 10001):
        duration = make_curve(p, count=count)[-1]["remaining_s"]
        rows.append(
            {
                "sample_count": count,
                "modeled_interval_s": duration,
                "relative_error_vs_40001": (duration - reference) / reference,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--sensitivity-csv", type=Path)
    parser.add_argument("--window-csv", type=Path)
    parser.add_argument("--mechanisms-csv", type=Path)
    parser.add_argument("--pressure-csv", type=Path)
    parser.add_argument("--convergence-csv", type=Path)
    args = parser.parse_args()
    checks = run_checks()
    if args.check or not args.csv:
        print("\n".join(checks))
    if args.csv:
        rows = make_curve(Params())
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.csv}")
    if args.sensitivity_csv:
        rows = sensitivity_rows()
        args.sensitivity_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.sensitivity_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.sensitivity_csv}")
    if args.window_csv:
        rows = window_rows()
        args.window_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.window_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.window_csv}")
    if args.mechanisms_csv:
        rows = mechanism_rows()
        args.mechanisms_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.mechanisms_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.mechanisms_csv}")
    if args.pressure_csv:
        rows = pressure_rows()
        args.pressure_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.pressure_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.pressure_csv}")
    if args.convergence_csv:
        rows = convergence_rows()
        args.convergence_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.convergence_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.convergence_csv}")


if __name__ == "__main__":
    main()
