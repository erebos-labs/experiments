"""Constructed observational equivalence with finite chemical loss.

NOT a seed model fit. All rates and times are dimensionless and invented.
At the end of a pulse p, a responsive fraction q=1-exp(-p) is created.
A: retained chemical-associated state R either germinates (rate a) or is
   lost without germination (rate b). R'=-(a+b)R; G'=aR; L'=bR.
B: chemical is absent after washing. A committed fraction M0=q*a/(a+b)
   germinates at rate a+b. M'=-(a+b)M; G'=(a+b)M.
Both have G(T)=q*a/(a+b)*(1-exp(-(a+b)*T)). This is deliberately
constructed, including the free responsive fraction in B; it does not
establish either mechanism in real seeds. Independent chemical or state
measurements could distinguish them. Inspired by Soos et al. 2012,
doi:10.1111/j.1469-8137.2012.04358.x; no paper data used.
"""
import csv
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data"

def validate(pulse, time, a, b):
    if any(not math.isfinite(x) or x < 0 for x in (pulse, time, a, b)):
        raise ValueError("inputs must be finite and nonnegative")
    if a+b == 0 or not math.isfinite(a+b):
        raise ValueError("finite positive total rate required")

def states(pulse, time, a, b):
    validate(pulse,time,a,b)
    q = -math.expm1(-pulse)
    total = a+b
    decay = math.exp(-total*time)
    emerged = q*(a/total)*(-math.expm1(-total*time))
    retained = {"germinated":emerged,"retained_state":q*decay,
                "lost":q*(b/total)*(-math.expm1(-total*time))}
    initial_committed = q*(a/total)
    committed = {"germinated":initial_committed*(-math.expm1(-total*time)),"committed_state":initial_committed*decay,
                 "initial_committed":q*(a/total),"retained_chemical":0.0}
    return q,retained,committed

def rk4_retention(pulse,time,a,b,steps=2000):
    # Independent integration of the ODE, not the closed-form G expression.
    validate(pulse,time,a,b)
    r,g,l = -math.expm1(-pulse),0.0,0.0
    h=time/steps
    def rhs(y):
        return (-(a+b)*y[0],a*y[0],b*y[0])
    def shift(y,k,scale):
        return tuple(v+scale*d for v,d in zip(y,k))
    for _ in range(steps):
        y=(r,g,l); k1=rhs(y); k2=rhs(shift(y,k1,h/2))
        k3=rhs(shift(y,k2,h/2)); k4=rhs(shift(y,k3,h))
        r,g,l=tuple(v+h*(d1+2*d2+2*d3+d4)/6
                    for v,d1,d2,d3,d4 in zip(y,k1,k2,k3,k4))
    return r,g,l

def rk4_commitment(pulse,time,a,b,steps=2000):
    # Different initial state and ODE from the retained-state model.
    validate(pulse,time,a,b)
    m,g = (-math.expm1(-pulse))*a/(a+b),0.0
    h=time/steps
    def rhs(y):
        return (-(a+b)*y[0],(a+b)*y[0])
    def shift(y,k,scale):
        return tuple(v+scale*d for v,d in zip(y,k))
    for _ in range(steps):
        y=(m,g); k1=rhs(y); k2=rhs(shift(y,k1,h/2))
        k3=rhs(shift(y,k2,h/2)); k4=rhs(shift(y,k3,h))
        m,g=tuple(v+h*(d1+2*d2+2*d3+d4)/6
                  for v,d1,d2,d3,d4 in zip(y,k1,k2,k3,k4))
    return m,g

def check():
    cases=0; max_mass_error=0.0; max_curve_difference=0.0
    for pulse in (0,0.1,1,5):
        for a,b in ((0,1),(1,0),(1,0.5),(0.2,3)):
            previous=-1.0
            for time in (0,0.01,0.1,1,5,10):
                q,r,m=states(pulse,time,a,b);cases+=1
                assert all(-1e-15 <= x <= 1+1e-15 for x in (*r.values(),*m.values()))
                error=abs(r["retained_state"]+r["germinated"]+r["lost"]-q)
                max_mass_error=max(max_mass_error,error)
                assert error < 5e-16
                assert abs(m["committed_state"]+m["germinated"]-m["initial_committed"]) < 5e-16
                max_curve_difference=max(max_curve_difference,abs(r["germinated"]-m["germinated"]))
                assert r["germinated"] >= previous;previous=r["germinated"]
                if time == 0: assert r["germinated"] == 0
                if a == 0: assert r["germinated"] == 0
                if b == 0: assert r["lost"] == 0
    q,r,m=states(1,1,1,0.5)
    assert r["retained_state"] > 0 and m["retained_chemical"] == 0
    numeric=rk4_retention(1,2,1,0.5)
    _,exact,_=states(1,2,1,0.5)
    integration_error=max(abs(x-y) for x,y in zip(numeric,(exact["retained_state"],exact["germinated"],exact["lost"])))
    assert integration_error < 1e-12
    numeric_m,numeric_g=rk4_commitment(1,2,1,0.5)
    _,_,exact_m=states(1,2,1,0.5)
    commitment_error=max(abs(numeric_m-exact_m["committed_state"]),abs(numeric_g-exact_m["germinated"]))
    assert commitment_error < 1e-12
    assert abs(numeric_g-numeric[1]) < 1e-12
    assert max_curve_difference < 1e-14
    rejected=0
    for bad in ((-1,1,1,1),(1,math.nan,1,1),(1,1,math.inf,1),(1,1,0,0)):
        try: states(*bad)
        except ValueError: rejected+=1
    assert rejected == 4
    return {"cases":cases,"max_mass_error":max_mass_error,
            "max_curve_difference":max_curve_difference,"rk4_steps":2000,
            "independent_retention_integration_max_error":integration_error,
            "independent_commitment_integration_max_error":commitment_error,
            "independent_numeric_curve_difference":abs(numeric_g-numeric[1]),"invalid_inputs_rejected":rejected}

def main():
    result={"kind":"constructed_equivalence_not_biological_data","checks":check(),
            "parameters":{"a":1,"b":0.5,"pulse":1,"time_units":"dimensionless"},
            "claim":"These constructed mechanisms give identical germination curves with nonzero chemical loss.",
            "limits":["Responsive fraction and rate in commitment model are assigned to match retention model.",
                      "No empirical model selection, seed data fitting, receptor model, or biological prediction.",
                      "Mass conservation and numerical agreement do not validate the biological assumptions."]}
    rows=[]
    for time in (0,0.1,0.5,1,2,5,10):
        q,r,m=states(1,time,1,0.5)
        rows.append({"dimensionless_time":time,"pulse_fraction":q,
                     "A_germinated":r["germinated"],"A_retained":r["retained_state"],"A_lost":r["lost"],
                     "B_germinated":m["germinated"],"B_committed":m["committed_state"],"B_chemical":0})
    with (OUT/"finite-loss-curves.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    (OUT/"finite-loss-checks.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__ == "__main__": main()
