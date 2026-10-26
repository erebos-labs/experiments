"""Reconcile reported KAR1 concentrations; no biological model or new data.
Source: Sella Rolando et al. (2026), doi:10.1038/s41598-025-30823-7,
KAR1 preparation and UHPLC-MS/MS results/discussion.
Run: python3 dose_check.py
"""
from decimal import Decimal as D
import json
from pathlib import Path

SOURCE = "https://www.nature.com/articles/s41598-025-30823-7"
STOCK_NM = D("5.5")
REPORTED_PLUS_MINUS_NM = D("0.23")  # Do not interpret as a CI or assumed SD.
PURE_TESTED_UM = tuple(map(D, ("0.001", "0.01", "0.1", "1", "10")))

def um_to_nm(value):
    return value * D("1000")

def dilute(concentration, dilution):
    if dilution <= 0:
        raise ValueError("dilution must be positive")
    return concentration / dilution

def main():
    rows = []
    for factor in (1, 10, 100, 1000):
        rows.append({"dilution_factor": factor,
                     "KAR1_nM": str(dilute(STOCK_NM, D(factor))),
                     "reported_plus_minus_scaled_nM": str(dilute(REPORTED_PLUS_MINUS_NM, D(factor)))})
    # Checks use independent exact reference values rather than rounded display.
    assert um_to_nm(D("0.001")) == D("1")
    assert um_to_nm(D("1")) == D("1000")
    assert dilute(STOCK_NM, D("100")) == D("0.055")
    assert dilute(STOCK_NM, D("1000")) == D("0.0055")
    try:
        dilute(STOCK_NM, D("0"))
    except ValueError:
        pass
    else:
        raise AssertionError("zero dilution must fail")
    result = {"source": SOURCE, "kind": "unit_conversion_only",
              "smoke_water": rows,
              "pure_tested_nM": [str(um_to_nm(x)) for x in PURE_TESTED_UM],
              "one_uM_divided_by_smoke_stock": str(um_to_nm(D("1"))/STOCK_NM),
              "checks_passed": 5,
              "limits": ["Reported plus/minus is scaled, not a confidence interval.",
                         "Dilution assumes ideal mixing and no chemical loss.",
                         "No fitted threshold, dose-response, significance test or replication of germination.",
                         "Whole smoke contains other compounds; KAR1-equivalent is not biological equivalence."]}
    out = Path(__file__).resolve().parent / "data/dose-check.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
