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
"""Regenerate the 16 per-workload boxplot figures (migrations / energy / ME / SLA
x 4 workloads) in EXACTLY Sergi's visual style (Plotly boxplots, plotly_white,
same per-technique colors, same y-labels, same 800x450 size, no title/legend),
but from the REPRODUCTION per-seed data (composite network-aware energy), so the
figures match the revised tables. Output filenames identical -> drop-in for LaTeX.
Techniques: MU MMT RS MC WPSP (static campaign) + WP/WBP (prophet_st runs).
PlanetLab pools the 10 daily traces x 30 seeds (consistent with the tables)."""
import glob, json, os
import plotly.graph_objects as go

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


def emig(r):
    return (4.096 * r + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics(fp):
    d = json.load(open(fp)); cs = d["cloudsimResults"]; net = d["networkPhysicalResults"]
    ram = net.get("totalRAMInBW", 0)
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)) + emig(ram)
    return dict(energy=e,
                migrations=cs.get("numberOfMigrations", 0),
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


YLAB = {"migrations": "# of migrations", "energy": "kWh",
        "ratio_me": "MIPS completed / Energy Consumption", "sla": "%"}
KEY = {"migrations": "migrations", "energy": "energy", "ratio_me": "me", "sla": "sla"}

for wl in ["planetlab", "alibaba", "materna", "azure"]:
    data = collect(wl)
    for suffix, ylab in YLAB.items():
        fig = go.Figure()
        for t in ORDER:
            vals = [m[KEY[suffix]] for m in data[t]]
            fig.add_trace(go.Box(y=vals, name=t, marker_color=COLORS[t],
                                 boxpoints="outliers", showlegend=False))
        fig.update_layout(template="plotly_white", width=800, height=450,
                          margin=dict(l=70, r=10, t=10, b=40),
                          yaxis_title=ylab, font=dict(size=15))
        dest = os.path.join(DEST, f"{wl}_{suffix}.png")
        fig.write_image(dest, scale=1)
        print("saved", os.path.basename(dest), f"(n per box: {len(data['WBP'])})")
print("done")
