#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------------------------
# Analysis of the SUBMITTED version of the manuscript (24 September 2026): this script produced
# its per-workload tables / figures. It was missing from tag v0.2.3 and was added in the revision
# for traceability; the only change is that the hard-coded local paths were replaced by
# repository-relative defaults. Superseded by analysis_revision/ (see SOTA/README.md). It uses
# the composite energy of the submitted version: host energy + (4.096 * RAMinBW + 20.165) * 1.1
# / 3.6e6 kWh, with RAMinBW as registered by the simulator, which counts every migration twice.
# ------------------------------------------------------------------------------------------------
"""Regenerate the 16 per-workload boxplots in Sergi's exact visual style
(Plotly look: white bg, light horizontal grid, no spines, per-technique colors
with translucent fill, outlier dots, 800x450) — but with matplotlib (kaleido
hangs on this machine). Data: reproduction per-seed, composite energy.
Same output filenames -> drop-in replacement for the LaTeX."""
import glob, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

# Raw outputs: <repository>/output by default; override with the environment variable WBF_OUTPUT.
OUT = os.environ.get("WBF_OUTPUT", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"))
# Figures are written to <repository>/results/figures_submitted by default; override with WBF_FIGURES.
DEST = os.environ.get("WBF_FIGURES", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "figures_submitted"))
os.makedirs(DEST, exist_ok=True)
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]
COLORS = {"MU": "#00CC96", "MMT": "#EF553B", "RS": "#AB63FA", "MC": "#636EFA",
          "WPSP": "#FF6692", "WP": "#19D3F3", "WBP": "#FFA15A"}
ORDER = ["MU", "MMT", "RS", "MC", "WPSP", "WP", "WBP"]
PMAP = {"mu": "MU", "mmt": "MMT", "rs": "RS", "mc": "MC", "psp2": "WPSP"}
TICKCOL = "#2a3f5f"; GRIDCOL = "#EBF0F8"


def emig(r):
    return (4.096 * r + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics(fp):
    d = json.load(open(fp)); cs = d["cloudsimResults"]; net = d["networkPhysicalResults"]
    ram = net.get("totalRAMInBW", 0)
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)) + emig(ram)
    return dict(energy=e, migrations=cs.get("numberOfMigrations", 0),
                sla=cs.get("slaOverall", 0) * 100,
                me=cs.get("vmTotalAllocatedMips", 0) / e if e else 0)


def collect(wl):
    data = {t: [] for t in ORDER}
    static = [f"pl_static_{d}" for d in DAYS] if wl == "planetlab" else [f"paper4_full_{wl}_static"]
    proph = [f"p4_pl_{d}_st" for d in DAYS] if wl == "planetlab" else [f"paper4_full_{wl}_prophet_st"]
    for fld in static:
        for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
            c = json.load(open(f)).get("experimentConfiguration", {})
            lbl = PMAP.get(c.get("selectionPolicy"))
            if lbl:
                data[lbl].append(metrics(f))
    for fld in proph:
        for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
            c = json.load(open(f)).get("experimentConfiguration", {})
            lbl = "WBP" if "bollinger" in str(c.get("hostSignalProcessing")) else "WP"
            data[lbl].append(metrics(f))
    return data


def me_formatter(x, pos):
    return f"{x/1e6:.0f}M"


YLAB = {"migrations": "# of migrations", "energy": "kWh",
        "ratio_me": "MIPS completed / Energy Consumption", "sla": "%"}
KEY = {"migrations": "migrations", "energy": "energy", "ratio_me": "me", "sla": "sla"}

for wl in ["planetlab", "alibaba", "materna", "azure"]:
    data = collect(wl)
    for suffix, ylab in YLAB.items():
        fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=100)
        fig.patch.set_facecolor("white"); ax.set_facecolor("white")
        series = [[m[KEY[suffix]] for m in data[t]] for t in ORDER]
        bp = ax.boxplot(series, patch_artist=True, widths=0.55,
                        labels=ORDER, whis=1.5,
                        flierprops=dict(marker="o", markersize=3.5, linestyle="none"))
        for i, t in enumerate(ORDER):
            c = COLORS[t]
            bp["boxes"][i].set(facecolor=to_rgba(c, 0.5), edgecolor=c, linewidth=1.4)
            bp["medians"][i].set(color=c, linewidth=1.4)
            for w in (bp["whiskers"][2 * i], bp["whiskers"][2 * i + 1],
                      bp["caps"][2 * i], bp["caps"][2 * i + 1]):
                w.set(color=c, linewidth=1.4)
            bp["fliers"][i].set(markerfacecolor=c, markeredgecolor=c)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.yaxis.grid(True, color=GRIDCOL, linewidth=1.2)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", length=0, labelsize=13, colors=TICKCOL)
        ax.set_ylabel(ylab, fontsize=13, color=TICKCOL)
        if suffix == "ratio_me":
            ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(me_formatter))
        fig.tight_layout(pad=1.2)
        dest = os.path.join(DEST, f"{wl}_{suffix}.png")
        fig.savefig(dest, dpi=100, facecolor="white")
        plt.close(fig)
        print("saved", os.path.basename(dest), f"(n={len(data['WBP'])})")
print("done")
