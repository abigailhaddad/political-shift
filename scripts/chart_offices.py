"""Chart of the offices where political headcount rose most while non-political headcount fell.

Reads output/political_shift_by_office.csv (shift.py). Rows: the TOP_N subelements with the largest
political gain among those with political up, non-political down, at least MIN_BASE non-political staff
in Oct 2024, and a recode gap within MAX_GAP_PCT (so reorganizations don't read as cuts).
Writes output/political_shift_offices.png.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from common import BASE, END, OUT
TOP_N = 12
MIN_BASE = 50
MAX_GAP_PCT = 10
INK, MUTED, SURFACE = "#1f1f1e", "#6b6a64", "#fcfcfb"
# Flat fills: direction only. The size of the change is written in each cell.
GREW, SHRANK, GREW_TEXT, SHRANK_TEXT = "#cde2fb", "#fbdcdc", "#0d366b", "#8f1f1e"

# Short department names for row labels; anything else falls back to the subelement name alone.
SHORT = {"HE": "HHS", "HS": "DHS", "DD": "DoD", "DJ": "DOJ", "DN": "Energy", "DL": "Labor",
         "TR": "Treasury", "ED": "Education", "AG": "USDA", "VA": "VA", "AF": "Air Force",
         "NV": "Navy", "HU": "HUD", "IN": "Interior", "CM": "Commerce", "AR": "Army", "TD": "DOT"}


def label(r):
    sub = r.agency_subelement.title()
    for a, b in [(" And ", " and "), (" Of ", " of "), (" The ", " the "), (" For ", " for "), ("Dhs ", "DHS ")]:
        sub = sub.replace(a, b)
    if sub.startswith("Office of the Secretary of"):
        sub = "Office of the Secretary"
    if len(sub) > 30:
        sub = sub.replace(" and ", " & ").replace("Administration", "Admin.")
    if r.agency_subelement == r.agency or r.agency_code not in SHORT or sub.startswith(SHORT[r.agency_code]):
        return sub
    return f"{SHORT[r.agency_code]}: {sub}"


def month_name(yyyymm):
    return pd.Timestamp(f"{yyyymm[:4]}-{yyyymm[4:]}-01").strftime("%B %Y")


def main():
    d = pd.read_csv(OUT / "political_shift_by_office.csv", dtype={"agency_code": str})
    pick = d[d.political_up_nonpol_down & (d[f"nonpol_ex1102_{BASE}"] >= MIN_BASE)
             & (d.recode_gap_pct.abs() <= MAX_GAP_PCT)].nlargest(TOP_N, "political_change")
    cols = [("Political appointees", "political"), ("Career staff", "nonpol_ex1102")]
    before = pick[[f"{c}_{BASE}" for _, c in cols]].to_numpy()
    after = pick[[f"{c}_{END}" for _, c in cols]].to_numpy()
    pct = 100 * (after - before) / before

    fig, ax = plt.subplots(figsize=(8, 0.42 * len(pick) + 1.8), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for i in range(len(pick)):
        for j in range(len(cols)):
            up = after[i, j] >= before[i, j]
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, color=GREW if up else SHRANK, ec=SURFACE, lw=2))
            sign = "+" if up else "\u2212"
            ax.text(j, i, f"{before[i, j]:,.0f} \u2192 {after[i, j]:,.0f}  ({sign}{abs(pct[i, j]):.0f}%)",
                    ha="center", va="center", fontsize=10, color=GREW_TEXT if up else SHRANK_TEXT)
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(len(pick) - 0.5, -0.5)
    ax.set_xticks([0, 1], [name for name, _ in cols])
    ax.xaxis.tick_top()
    ax.tick_params(length=0, labelsize=10, colors=INK)
    ax.set_yticks(range(len(pick)), [label(r) for r in pick.itertuples()], fontsize=10, color=INK)
    for sp in ax.spines.values():
        sp.set_visible(False)

    fig.suptitle("Political appointees up, career staff down", x=0.02, ha="left",
                 fontsize=14, fontweight="bold", color=INK)
    fig.text(0.02, 0.895, f"Headcount in federal offices, {month_name(BASE)} \u2192 {month_name(END)}", fontsize=10, color=MUTED)
    fig.text(0.02, 0.01, "Political = Schedule C, noncareer SES, presidential and Executive Schedule appointees. Career = everyone\n"
             "else, excluding contracting staff (series 1102). "
             "Source: OPM federal workforce data (EHRI), monthly employment snapshots.",
             fontsize=7.5, color=MUTED, va="bottom")
    fig.subplots_adjust(left=0.45, right=0.98, top=0.80, bottom=0.09)
    fig.savefig(OUT / "political_shift_offices.png", dpi=160, facecolor=SURFACE)
    print(pick[["agency_code", "agency_subelement", f"political_{BASE}", f"political_{END}",
                "nonpol_pct_change", "recode_gap_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
