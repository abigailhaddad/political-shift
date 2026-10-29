"""Offices where political headcount rose while non-political headcount fell, BASE -> END.

Input: data/subelement_headcount.parquet (pull_subelement_headcount.py), plus local accessions and
separations for the recode check: recode_gap = change in non-political headcount minus (hires - separations)
over the months after BASE through END. A large gap means people were moved in or out by reorganization, not hired or lost.
Non-political excludes series 1102. Writes output/political_shift_by_office.csv (all subelements).
"""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from common import BASE, DATA, END, OUT, POLITICAL_SQL, RAW, RAW_SEP


def main():
    c = duckdb.connect()
    h = c.sql(f"select * from '{DATA / 'subelement_headcount.parquet'}'").df()
    w = h.pivot_table(index=["agency_code", "agency_subelement_code"], columns="f",
                      values=["political", "sched_c", "sched_pc", "nonpol_ex1102"], fill_value=0)
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    names = h.sort_values("f").groupby(["agency_code", "agency_subelement_code"])[["agency", "agency_subelement"]].last()
    w = w.join(names).reset_index()

    nonpol = f"not coalesce({POLITICAL_SQL}, false) and coalesce(occupational_series_code, '') <> '1102'"
    month = "regexp_extract(filename, '_(\\d{6})_v', 1)"
    flows = c.sql(f"""
        with hi as (select agency_code, agency_subelement_code, count(*) hires
                    from read_parquet('{RAW}/*.parquet', filename=true, union_by_name=true)
                    where {nonpol} and {month} > '{BASE}' and {month} <= '{END}' group by all),
             se as (select agency_code, agency_subelement_code, count(*) seps
                    from read_parquet('{RAW_SEP}/*.parquet', filename=true, union_by_name=true)
                    where {nonpol} and {month} > '{BASE}' and {month} <= '{END}' group by all)
        select * from hi full join se using (agency_code, agency_subelement_code)""").df()
    w = w.merge(flows, on=["agency_code", "agency_subelement_code"], how="left").fillna({"hires": 0, "seps": 0})
    w["political_change"] = w[f"political_{END}"] - w[f"political_{BASE}"]
    w["nonpol_change"] = w[f"nonpol_ex1102_{END}"] - w[f"nonpol_ex1102_{BASE}"]
    w["nonpol_pct_change"] = (100 * w.nonpol_change / w[f"nonpol_ex1102_{BASE}"]).round(1)
    w["recode_gap"] = w.nonpol_change - (w.hires - w.seps)
    w["recode_gap_pct"] = (100 * w.recode_gap / w[f"nonpol_ex1102_{BASE}"]).round(1)
    w["political_up_nonpol_down"] = (w.political_change > 0) & (w.nonpol_change < 0)
    w.sort_values("political_change", ascending=False).to_csv(OUT / "political_shift_by_office.csv", index=False)
    print(w[w.political_up_nonpol_down].shape[0], "subelements with political up and non-political down")


if __name__ == "__main__":
    main()
