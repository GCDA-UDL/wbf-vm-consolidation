#!/usr/bin/env python3
"""Block diagram of one consolidation decision of WBP as implemented in the simulator.

Sources of each step (simulator sources under svila/):
  1  GlobalRunner / migrationInterval = 6; history of at most 30 samples
  2  policiesVmOptimizer/future/FutureTechnique.java (signal processing before forecasting);
     pymodule/signalProcessing.py get_bollinger_upper (window 5, alpha 0.5)
  3  pymodule/forecastingTechniques.py python_getFacebookProphet; hostForecastingResume = mean
  4  policiesHostOverSaturation/future/FutureHostOverSaturationMAD.java, OverSaturationData.java
  5  policiesVmSelection/future/FutureVmSelectionBase.java (first-check loop),
     FuturePSP2VmSelection.java (score H, threshold 0.65)
  6  policiesVmMigration/future/FutureAbsoluteCapacityVmMigrationPolicy.java
  7  policiesHostUnderUtilisation/future/FutureHostUnderUtilisationBase.java
Usage: python -B fig_wbp_cycle.py --out <dir> [--preview <dir>]
"""
import argparse

import figstyle as S

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--preview", default=None)
a = ap.parse_args()

S.apply()
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.patches import FancyBboxPatch        # noqa: E402

W = 88.0                 # mm
LINE = 3.45              # mm per text line at 8 pt
PAD = 1.5                # mm, vertical padding inside a box
GAPY = 3.2               # mm between boxes (arrow)
X0, X1 = 6.5, W - 0.6    # box horizontal extent (step number on the left)

STEPS = [
    ("1", ["Every 6 samples (30 min), for each active host:",
           "CPU utilization history, last 30 samples at most"], False),
    ("2", ["Replace the history by its upper Bollinger band:",
           "moving average of 5 samples + 0.5 standard deviations"], True),
    ("3", ["Fit Prophet on that series, forecast the next 6 samples",
           "and take their mean: host forecast û"], False),
    ("4", ["Host overloaded if û > 1 − MAD(history)",
           "(threshold 1 if the history has fewer than 12 samples)"], False),
    ("5", ["Each overloaded host: WPSP removes VMs one at a time,",
           "lowest score H first (only if H ≤ 0.65), until the forecast",
           "falls under the threshold or no VM qualifies"], False),
    ("6", ["Placement, largest VM demand first: first host,",
           "by decreasing capacity, with room for the VM and",
           "not overloaded after receiving it"], False),
    ("7", ["Remaining hosts, least loaded first: all the VMs of the",
           "host are moved if every one fits elsewhere by the same",
           "rule, and the emptied host is switched off"], False),
    ("", ["Migrations issued"], False),
]

heights = [len(lines) * LINE + 2 * PAD for _, lines, _ in STEPS]
H = sum(heights) + GAPY * (len(STEPS) - 1) + 1.2
fig = plt.figure(figsize=(W * S.MM, H * S.MM))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

y = H - 0.6
centers = []
for (num, lines, wbp_only), h in zip(STEPS, heights):
    top, bot = y, y - h
    last = num == ""
    ax.add_patch(FancyBboxPatch((X0, bot), X1 - X0, h, boxstyle="round,pad=0,rounding_size=1.2",
                                facecolor="#e8f1fd" if wbp_only else ("#f1f0ec" if last else "white"),
                                edgecolor=S.C_FAMILY["WBP"] if wbp_only else S.INK2,
                                linewidth=0.9 if wbp_only else 0.7,
                                linestyle=(0, (3, 2)) if wbp_only else "solid"))
    for i, txt in enumerate(lines):
        ax.text((X0 + X1) / 2 if last else X0 + 2.0, top - PAD - (i + 0.5) * LINE, txt,
                ha="center" if last else "left", va="center", fontsize=8)
    if num:
        ax.text(X0 - 3.4, (top + bot) / 2, num, ha="center", va="center", fontsize=8, color=S.INK2,
                fontweight="bold")
    if wbp_only:
        ax.text(X1 - 1.6, top - PAD - 0.5 * LINE, "WBP only", ha="right", va="center", fontsize=8,
                fontweight="bold", color=S.C_FAMILY["WBP"])
    centers.append((top, bot))
    y = bot - GAPY
for (t0, b0), (t1, b1) in zip(centers, centers[1:]):
    ax.annotate("", xy=((X0 + X1) / 2, t1), xytext=((X0 + X1) / 2, b0),
                arrowprops=dict(arrowstyle="-|>", color=S.INK2, linewidth=0.8, mutation_scale=7,
                                shrinkA=0, shrinkB=0))
S.save(fig, a.out, a.preview, "fig_wbp_cycle")
print(f"size: {W:.0f} mm x {H:.1f} mm")
