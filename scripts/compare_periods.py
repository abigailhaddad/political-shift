"""Compare transitions: political and career headcount change from October of the election year to August
of the new term's second year. Run the pipeline for each period first (PERIOD_BASE / PERIOD_END).
Writes output/compare_periods.csv."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from common import DEFAULT_BASE, DEFAULT_END, OUT

PERIODS = [("201610", "201808", "Obama -> Trump 1"), ("202010", "202208", "Trump 1 -> Biden"),
           (DEFAULT_BASE, DEFAULT_END, "Biden -> Trump 2")]
MIN_BASE, MAX_GAP_PCT = 50, 10  # same office filters as chart.py


def main():
    rows = []
    for b, e, name in PERIODS:
        tag = "" if (b, e) == (DEFAULT_BASE, DEFAULT_END) else f"_{b}_{e}"
        d = pd.read_csv(OUT / f"political_shift_by_office{tag}.csv", dtype={"agency_code": str})
        ok = d[(d[f"nonpol_ex1102_{b}"] >= MIN_BASE) & (d.recode_gap_pct.abs() <= MAX_GAP_PCT)]
        both = ok[ok.political_up_nonpol_down]
        hhs = d[d.agency_subelement_code == "HE10"].iloc[0]
        rows.append({
            "period": name, "base": b, "end": e,
            "political_base": d[f"political_{b}"].sum(), "political_end": d[f"political_{e}"].sum(),
            "sched_c_base": d[f"sched_c_{b}"].sum(), "sched_c_end": d[f"sched_c_{e}"].sum(),
            "career_base": d[f"nonpol_ex1102_{b}"].sum(), "career_end": d[f"nonpol_ex1102_{e}"].sum(),
            "offices_political_up_career_down": len(both),
            "offices_political_up5_career_down": int((both.political_change >= 5).sum()),
            "hhs_os_political_base": hhs[f"political_{b}"], "hhs_os_political_end": hhs[f"political_{e}"],
            "hhs_os_career_pct_change": hhs.nonpol_pct_change, "hhs_os_recode_gap_pct": hhs.recode_gap_pct,
        })
    out = pd.DataFrame(rows)
    for col in ["political", "sched_c", "career"]:
        out[f"{col}_pct_change"] = (100 * (out[f"{col}_end"] / out[f"{col}_base"] - 1)).round(1)
    out.to_csv(OUT / "compare_periods.csv", index=False)
    print(out.T.to_string())


if __name__ == "__main__":
    main()
