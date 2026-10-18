#!/usr/bin/env python3
"""Recompute only transparent contrasts from published summary statistics.

This generator does not read flower-level records. The separate
raw_reanalysis.py descriptively audits the verified deposited archive; neither
script replicates the biological experiment or reconstructs its mixed model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SOURCES = {
    "original": "https://doi.org/10.1111/ele.13331",
    "critique": "https://doi.org/10.1111/ele.13490",
    "reply": "https://doi.org/10.1111/ele.13534",
    "data": "https://doi.org/10.5061/dryad.6n5h0pb",
}


EXPERIMENTS = {
    "combined_2014_2015": {
        "label": "Experiment 1, outdoor 2014 + indoor 2015",
        "groups": {
            "Silence": {"mean_brix_pct": 16.3, "se": 0.5, "n": 71},
            "High": {"mean_brix_pct": 16.0, "se": 0.4, "n": 72},
            "Low": {"mean_brix_pct": 19.8, "se": 0.6, "n": 72},
            "Bee": {"mean_brix_pct": 19.1, "se": 0.7, "n": 42},
        },
    },
    "fall_2016": {
        "label": "Experiment 2, indoor fall 2016",
        "groups": {
            "High": {"mean_brix_pct": 12.8, "se": 0.7, "n": 49},
            "Intermediate": {"mean_brix_pct": 12.3, "se": 0.77, "n": 51},
            "Low": {"mean_brix_pct": 15.9, "se": 0.57, "n": 81},
        },
    },
}


def contrast(a: float, b: float) -> dict[str, float]:
    """Return arithmetic contrasts; no inferential statistics are reconstructed."""
    return {
        "percentage_point_difference": round(a - b, 3),
        "ratio": round(a / b, 4),
        "relative_percent": round((a / b - 1.0) * 100.0, 2),
    }


def sugar_proxy(volume_ul: float, concentration_pct: float) -> float:
    """A volume-weighted concentration proxy, in microlitres × mass fraction.

    Brix is a mass fraction and nectar density varies, so this intentionally is
    not labelled as milligrams or used as a biological estimate.
    """
    return volume_ul * concentration_pct / 100.0


def build_summary() -> dict:
    exp1 = EXPERIMENTS["combined_2014_2015"]["groups"]
    exp2 = EXPERIMENTS["fall_2016"]["groups"]
    counterfactual = {
        "reference": {"volume_ul": 1.0, "concentration_pct": 16.3},
        "treatment": {"volume_ul": 0.82, "concentration_pct": 19.8},
    }
    reference_proxy = sugar_proxy(**counterfactual["reference"])
    treatment_proxy = sugar_proxy(**counterfactual["treatment"])
    flat_proxy_volume = (
        counterfactual["reference"]["volume_ul"]
        * counterfactual["reference"]["concentration_pct"]
        / counterfactual["treatment"]["concentration_pct"]
    )
    return {
        "kind": "published-summary arithmetic, not raw-data reanalysis",
        "experiments": EXPERIMENTS,
        "contrasts": {
            "exp1_low_minus_silence": contrast(
                exp1["Low"]["mean_brix_pct"], exp1["Silence"]["mean_brix_pct"]
            ),
            "exp1_bee_minus_silence": contrast(
                exp1["Bee"]["mean_brix_pct"], exp1["Silence"]["mean_brix_pct"]
            ),
            "exp2_low_minus_intermediate": contrast(
                exp2["Low"]["mean_brix_pct"],
                exp2["Intermediate"]["mean_brix_pct"],
            ),
        },
        "counterfactual_endpoint_demo": {
            **counterfactual,
            "reference_proxy": round(reference_proxy, 5),
            "treatment_proxy": round(treatment_proxy, 5),
            "flat_proxy_treatment_volume_ul": round(flat_proxy_volume, 5),
            "proxy_relative_percent": round((treatment_proxy / reference_proxy - 1) * 100, 2),
            "warning": (
                "Teaching counterfactual only. The original paper reports no "
                "significant treatment decrease in mean nectar volume."
            ),
        },
        "sources": SOURCES,
        "limits": [
            "This summary generator does not read flower-level records; raw_reanalysis.py is a separate descriptive archive audit.",
            "SE values are transcribed from the original paper's figure captions.",
            "The two experiment panels differ by season and should not be pooled.",
            "The sugar proxy omits solution density and is not sugar mass in mg.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    text = json.dumps(build_summary(), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
