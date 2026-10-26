"""A constructed identifiability counterexample, NOT a germination model fit.

Two mechanisms have the same endpoint after an ordinary wash:
 A: the active chemical remains retained throughout the observation window;
 B: the chemical is gone but a downstream committed state persists.

Both latent fractions obey dx/dt = k(1-x) during a pulse, x(0)=0.
Their endpoint is 1-exp(-k*t), but chemical retention differs.
Times are dimensionless; k=1 is arbitrary. No seed data or rates are fitted.
Inspiration: Soos et al. 2012 washout experiments, doi:10.1111/j.1469-8137.2012.04358.x.
This proves non-uniqueness within these constructed assumptions only.
"""
import csv
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data"

def latent_fraction(pulse):
    if not math.isfinite(pulse) or pulse < 0:
        raise ValueError("pulse must be finite and nonnegative")
    return -math.expm1(-pulse)

def retention_model(pulse):
    retained = latent_fraction(pulse)
    return {"endpoint": retained, "chemical_retained": retained, "downstream_memory": 0.0}

def commitment_model(pulse):
    committed = latent_fraction(pulse)
    return {"endpoint": committed, "chemical_retained": 0.0, "downstream_memory": committed}

def reversible_control(pulse):
    # No retained chemical or downstream state survives an ideal wash.
    return {"endpoint": 0.0, "chemical_retained": 0.0, "downstream_memory": 0.0}

def check():
    pulses = [i / 20 for i in range(101)]
    assert retention_model(0)["endpoint"] == 0
    assert all(0 <= latent_fraction(t) <= 1 for t in pulses)
    assert all(latent_fraction(a) <= latent_fraction(b) for a,b in zip(pulses,pulses[1:]))
    assert all(retention_model(t)["endpoint"] == commitment_model(t)["endpoint"] for t in pulses)
    assert retention_model(1)["chemical_retained"] > commitment_model(1)["chemical_retained"]
    assert commitment_model(1)["downstream_memory"] > retention_model(1)["downstream_memory"]
    assert reversible_control(1)["endpoint"] != commitment_model(1)["endpoint"]
    assert latent_fraction(1000) == 1
    assert math.isclose(latent_fraction(1), 1-1/math.e, rel_tol=1e-15)
    rejected = 0
    for bad in (-1.0, math.nan, math.inf):
        try: latent_fraction(bad)
        except ValueError: rejected += 1
    assert rejected == 3
    return {"property_checks_passed":10,"grid_points":len(pulses),"negative_inputs_rejected":rejected,
            "max_endpoint_difference":max(abs(retention_model(t)["endpoint"]-commitment_model(t)["endpoint"]) for t in pulses)}

def main():
    checks=check()
    rows=[]
    for t in (0,0.1,0.25,0.5,1,2,3,5):
        for name,model in (("retention",retention_model),("commitment",commitment_model),("reversible_control",reversible_control)):
            rows.append({"dimensionless_pulse":t,"model":name,**model(t)})
    with (OUT/"washout-counterexample.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result={"kind":"constructed_counterexample_not_fitted","checks":checks,
            "conclusion":"An endpoint washout assay alone cannot distinguish these constructed mechanisms.",
            "distinguishing_observable":"Chemical retained after washing differs; endpoint does not.",
            "limits":["Assumes retained chemical has negligible loss over the readout window.",
                      "No biological experiment, parameter estimation, prediction, or historical reconstruction.",
                      "Other observations can distinguish models; equality is deliberately constructed."]}
    (OUT/"washout-checks.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
