"""Download accessions and separations (latest version of each month) from the HF mirror, for the months
after BASE. shift.py uses them to check whether a headcount change came from hires and departures."""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from common import BASE, DATA, RAW, RAW_SEP

REPO = "https://huggingface.co/datasets/impactproject/opm-ehri-data"
# dataset -> (output dir, month filter)
PULLS = {
    "accessions": (RAW, lambda m: m > BASE),
    "separations": (RAW_SEP, lambda m: m > BASE),
}


def list_tree(path):
    url = f"{REPO.replace('/datasets/', '/api/datasets/')}/tree/main/{path}?limit=1000"
    entries = []
    while url:
        with urllib.request.urlopen(url) as r:
            entries += json.load(r)
            link = r.headers.get("Link", "")
        url = link.split(";")[0].strip("<>") if 'rel="next"' in link else None
    return entries


def pull(dataset, out, keep):
    out.mkdir(parents=True, exist_ok=True)
    latest = {}
    for e in list_tree(dataset):
        name = e["path"].split("/")[-1]
        month = name.split("_")[1]
        version = int(name.split("_v")[1].split(".")[0])
        if keep(month) and version > latest.get(month, (None, 0))[1]:
            latest[month] = (name, version)
    print(f"{dataset}: {len(latest)} months, {min(latest)}..{max(latest)}")
    for month, (name, _) in sorted(latest.items()):
        dest = out / name
        if dest.exists():
            continue
        for attempt in range(5):
            try:
                urllib.request.urlretrieve(f"{REPO}/resolve/main/{dataset}/{name}", dest)
                break
            except Exception as exc:
                print(f"{name}: {exc}; retrying", file=sys.stderr)
                time.sleep(10 * (attempt + 1))
        time.sleep(0.5)
    return {m: n for m, (n, _) in sorted(latest.items())}


def main():
    used = {dataset: pull(dataset, out, keep) for dataset, (out, keep) in PULLS.items()}
    (DATA / "files_used.json").write_text(json.dumps(used, indent=1))


if __name__ == "__main__":
    main()
