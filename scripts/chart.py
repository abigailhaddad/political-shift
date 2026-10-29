"""Chart: political appointees and career staff partway into each new administration, against the level
the previous administration left. Reads output/compare_periods.csv. Writes output/political_shift.png."""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from common import OUT

INK, MUTED, GRID, SURFACE = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"
CURRENT, EARLIER = "#2a78d6", "#b4b2a9"


def month_name(yyyymm):
    return pd.Timestamp(f"{yyyymm[:4]}-{yyyymm[4:]}-01").strftime("%b %Y")


def main():
    d = pd.read_csv(OUT / "compare_periods.csv", dtype={"base": str, "end": str})
    labels = [f"{r.period.replace(' -> ', ' → ')}\n{month_name(r.base)} → {month_name(r.end)}" for r in d.itertuples()]
    pol = 100 * d.political_end / d.political_base
    car = d.career_pct_change
    colors = [EARLIER] * (len(d) - 1) + [CURRENT]
    y = range(len(d))[::-1]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=SURFACE,
                                 gridspec_kw={"wspace": 0.12, "width_ratios": [1.15, 1]})
    a1.barh(y, pol, color=colors, height=0.55, zorder=2)
    a1.vlines(100, -0.5, len(d) - 0.5, color=INK, lw=1, zorder=1)  # behind the bars, ends above its label
    a1.text(100, -0.62, "100% = what they inherited", ha="center", va="top", fontsize=8.5, color=MUTED)
    for yi, v, c in zip(y, pol, colors):
        a1.text(v - 2, yi, f"{v:.0f}%", va="center", ha="right", fontsize=10,
                color="white" if c == CURRENT else INK)
    a1.set_xlim(0, max(pol) * 1.08)
    a1.set_ylim(-0.95, len(d) - 0.5)
    a1.set_title("Political appointees, as % of the level\nthe previous administration left",
                 loc="left", fontsize=10, color=INK)

    a2.barh(y, car, color=colors, height=0.55, zorder=2)
    a2.vlines(0, -0.5, len(d) - 0.5, color=INK, lw=1, zorder=1)
    for yi, v in zip(y, car):
        a2.text(v + (0.4 if v >= 0 else -0.4), yi, f"{v:+.1f}%".replace("-", "−"), va="center",
                ha="left" if v >= 0 else "right", fontsize=10, color=INK)
    a2.set_ylim(-0.95, len(d) - 0.5)
    lo = min(car.min(), 0)
    a2.set_xlim(lo * 1.35, max(car.max(), 0) + abs(lo) * 0.35)
    a2.set_title("Career staff, change over\nthe same period", loc="left", fontsize=10, color=INK)

    for ax in (a1, a2):
        ax.set_facecolor(SURFACE)
        ax.set_yticks(list(y), labels if ax is a1 else [""] * len(d), fontsize=9.5, color=INK)
        ax.tick_params(length=0)
        ax.set_xticks([])
        for s in ax.spines.values():
            s.set_visible(False)

    fig.suptitle("This administration has more political appointees than it inherited",
                 x=0.01, ha="left", fontsize=14, fontweight="bold", color=INK)
    fig.text(0.01, 0.875, "Federal workforce about 19 months into each new administration",
             fontsize=10, color=MUTED)
    fig.text(0.01, 0.01,
             "Each transition compares October of the election year with August of the new term's second year. "
             "Political = Schedule C,\nnoncareer SES, presidential and Executive Schedule appointees. Career = everyone "
             "else, excluding contracting staff (series 1102).\nSource: OPM federal workforce data (EHRI), monthly "
             "employment snapshots.", fontsize=7.5, color=MUTED, va="bottom")
    fig.subplots_adjust(left=0.2, right=0.98, top=0.72, bottom=0.2)
    fig.savefig(OUT / "political_shift.png", dpi=160, facecolor=SURFACE)
    print(d[["period", "political_base", "political_end", "career_pct_change"]].assign(pol_pct=pol.round(1)).to_string(index=False))


if __name__ == "__main__":
    main()
