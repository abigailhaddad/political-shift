"""Headcount by agency subelement, split political / non-political, from the government-wide employment
snapshots for BASE and END. Reads only the needed columns over HTTP. Writes data/subelement_headcount.parquet."""
import sys
import time
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from common import BASE, DATA, END, POLITICAL_SQL
from download import REPO, list_tree

MONTHS = [BASE, END]


def main():
    latest = {}
    for e in list_tree("employment"):
        name = e["path"].split("/")[-1]
        month = name.split("_")[1]
        version = int(name.split("_v")[1].split(".")[0])
        if month in MONTHS and version > latest.get(month, (None, 0))[1]:
            latest[month] = (name, version)
    c = duckdb.connect()
    c.sql("install httpfs; load httpfs")
    parts = DATA / "subelement_parts"
    parts.mkdir(exist_ok=True)
    for month, (name, _) in sorted(latest.items()):
        dest = parts / f"{month}.parquet"
        if dest.exists():
            continue
        for attempt in range(5):
            try:
                c.sql(f"""copy (select '{month}' f, '{name}' file, agency_code, any_value(agency) agency,
                                       agency_subelement_code, any_value(agency_subelement) agency_subelement,
                                       count(*) total,
                                       count(*) filter (coalesce({POLITICAL_SQL}, false)) political,
                                       count(*) filter (appointment_type_code = '44') sched_c,
                                       count(*) filter (appointment_type_code = '67') sched_pc,
                                       count(*) filter (not coalesce({POLITICAL_SQL}, false)
                                                        and coalesce(occupational_series_code, '') <> '1102') nonpol_ex1102
                                from read_parquet('{REPO}/resolve/main/employment/{name}')
                                group by agency_code, agency_subelement_code)
                          to '{dest}' (format parquet)""")
                break
            except duckdb.Error as exc:
                print(f"{name}: {exc}; retrying", file=sys.stderr)
                time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError(f"could not read {name}")
    c.sql(f"copy (select * from read_parquet('{parts}/*.parquet')) to '{DATA / 'subelement_headcount.parquet'}' (format parquet)")
    print(c.sql(f"select f, file, sum(total) total, sum(political) political from '{DATA / 'subelement_headcount.parquet'}' group by all order by f"))


if __name__ == "__main__":
    main()
