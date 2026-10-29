"""Government-wide political appointee headcount for every monthly employment snapshot from START on.
Reads only the columns that decide political status, over HTTP. Writes output/political_monthly.csv."""
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from common import DATA, OUT, POLITICAL_SQL
from download import REPO, list_tree

START = "201601"


def main():
    latest = {}
    for e in list_tree("employment"):
        name = e["path"].split("/")[-1]
        month = name.split("_")[1]
        version = int(name.split("_v")[1].split(".")[0])
        if month >= START and version > latest.get(month, (None, 0))[1]:
            latest[month] = (name, version)
    cache = DATA / "political_monthly_parts"
    cache.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect()
    c.sql("install httpfs; load httpfs")
    for month, (name, _) in sorted(latest.items()):
        dest = cache / f"{month}.csv"
        if dest.exists():
            continue
        for attempt in range(5):
            try:
                c.sql(f"""copy (select '{month}' "month", '{name}' "file", count(*) total,
                                       count(*) filter (coalesce({POLITICAL_SQL}, false)) political,
                                       count(*) filter (appointment_type_code = '44') sched_c
                                from read_parquet('{REPO}/resolve/main/employment/{name}'))
                          to '{dest}' (header)""")
                break
            except duckdb.Error as exc:
                print(f"{name}: {exc}; retrying", file=sys.stderr)
                time.sleep(15 * (attempt + 1))
        else:
            raise RuntimeError(f"could not read {name}")
        time.sleep(1)
    out = pd.concat([pd.read_csv(p, dtype={"month": str}) for p in sorted(cache.glob("*.csv"))])
    out = out[out.month >= START].sort_values("month")
    out.to_csv(OUT / "political_monthly.csv", index=False)
    print(f"{len(out)} months, {out.month.min()}..{out.month.max()}")


if __name__ == "__main__":
    main()
