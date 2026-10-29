"""Line chart: government-wide political appointee headcount by month. Reads output/political_monthly.csv
(pull_political_monthly.py). Writes output/political_appointees.png."""
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from common import OUT

INK, MUTED, GRID, SURFACE, LINE = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb", "#2a78d6"
# Months left out of the line, with the reason given in the footnote.
EXCLUDE = {"202606": "June 2026 is left out: OPM's file for that month shows Defense Department political appointees "
                     "nearly doubling for one month, and OPM's release notes\nsay the same file is missing records "
                     "from Defense components."}
INAUGURATIONS = [("2017-01-20", "Trump"), ("2021-01-20", "Biden"), ("2025-01-20", "Trump")]


def main():
    d = pd.read_csv(OUT / "political_monthly.csv", dtype={"month": str})
    d["date"] = pd.to_datetime(d.month, format="%Y%m")
    d.loc[d.month.isin(EXCLUDE), "political"] = float("nan")  # breaks the line at those months
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.plot(d.date, d.political, color=LINE, lw=2, zorder=3)

    top = d.political.max() * 1.18
    for day, name in INAUGURATIONS:
        t = pd.Timestamp(day)
        ax.axvline(t, color=MUTED, lw=1, ls=(0, (3, 3)), zorder=1)
        ax.text(t + pd.Timedelta(days=25), top * 0.97, f"{name}\ntakes office", fontsize=9, color=MUTED, va="top")

    # The highest count before the latest inauguration, as a reference line.
    before = d[d.date < pd.Timestamp(INAUGURATIONS[-1][0])]
    peak = before.loc[before.political.idxmax()]
    ax.hlines(peak.political, peak.date, d.date.max(), color=MUTED, lw=1, ls=(0, (1, 2)), zorder=2)
    ax.text(pd.Timestamp(INAUGURATIONS[-1][0]) - pd.Timedelta(days=20), peak.political + top * 0.015,
            f"Previous high: {peak.political:,.0f} ({peak.date:%b %Y})", fontsize=9, color=MUTED,
            va="bottom", ha="right")

    last = d.iloc[-1]
    ax.plot(last.date, last.political, "o", color=LINE, ms=6, zorder=4)
    ax.annotate(f"{last.political:,.0f}\n{last.date:%b %Y}", (last.date, last.political), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=10, color=INK)

    ax.set_ylim(0, top)
    ax.set_xlim(d.date.min(), d.date.max() + pd.Timedelta(days=330))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.suptitle(f"More political appointees than at any point since {d.date.min():%Y}", x=0.02, ha="left",
                 fontsize=14, fontweight="bold", color=INK)
    fig.text(0.02, 0.885, "Federal employees on political appointments, by month", fontsize=10, color=MUTED)
    fig.text(0.02, 0.01, "Political = Schedule C, noncareer SES, presidential and Executive Schedule appointees. "
             "Source: OPM federal workforce data (EHRI), monthly employment snapshots.\n"
             + "\n".join(EXCLUDE.values()),
             fontsize=7.5, color=MUTED, va="bottom")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.82, bottom=0.15)
    fig.savefig(OUT / "political_appointees.png", dpi=160, facecolor=SURFACE)


if __name__ == "__main__":
    main()
