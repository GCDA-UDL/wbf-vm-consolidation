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
"""Per-workload tables for the unified experimentation chapter: 9 metrics x
7 techniques (MU MMT RS MC WPSP WP WBP), mean +/- 95% CI, composite energy,
Sergi's table format (metrics as rows, techniques as columns). Emits LaTeX
(one table per workload) + a markdown mirror + the headline claim numbers
(WBP vs classicals ranges) recomputed from the new data."""
import glob, json, os
import numpy as np
from scipy import stats

# Raw outputs: <repository>/output by default; override with the environment variable WBF_OUTPUT.
OUT = os.environ.get("WBF_OUTPUT", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"))
HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]
T = ["MU", "MMT", "RS", "MC", "WPSP", "WP", "WBP"]
PMAP = {"mu": "MU", "mmt": "MMT", "rs": "RS", "mc": "MC", "psp2": "WPSP"}
WLS = [("planetlab", "PlanetLab"), ("alibaba", "Alibaba"),
       ("materna", "Materna"), ("azure", "Microsoft Azure")]
METRICS = [("Energy Consumption (kWh)", "energy", 2),
           ("Total used hosts", "hosts", 0),
           ("SLA Violation (\\%)", "sla", 2),
           ("\\# of migrations", "migr", 0),
           ("ME ratio ($\\times10^7$)", "me", 2),
           ("Avg.\\ available MIPS/active host", "avmips", 0),
           ("Median CPU dispersion (\\%)", "disp", 2),
           ("VM communications (MB $\\times10^5$)", "vmcomm", 2),
           ("RAM in BW (MB $\\times10^5$)", "rambw", 2)]
BETTER_HIGH = {"me", "avmips"}


def emig(r):
    return (4.096 * r + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics(fp):
    d = json.load(open(fp)); cs = d["cloudsimResults"]; cpu = d["cpuResults"]
    net = d["networkPhysicalResults"]
    ram = net.get("totalRAMInBW", 0)
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)) + emig(ram)
    return dict(energy=e, hosts=cpu.get("totalUsedHosts", 0),
                sla=cs.get("slaOverall", 0) * 100,
                migr=cs.get("numberOfMigrations", 0),
                me=cs.get("vmTotalAllocatedMips", 0) / e / 1e7 if e else 0,
                avmips=cpu.get("averageFreeMIPSActiveHosts", 0),
                disp=cpu.get("medianCPUDispersionOfActiveHosts", 0) * 100,
                vmcomm=net.get("totalBWUsed", 0) / 1e5,
                rambw=ram / 1e5)


def collect(wl):
    data = {t: [] for t in T}
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


def mci(vals, key):
    a = np.array([v[key] for v in vals], float); n = len(a)
    m = a.mean(); ci = stats.t.ppf(0.975, n - 1) * a.std(ddof=1) / np.sqrt(n)
    return m, ci


tex, md, claims = [], ["# Unified per-workload tables (9 metrics x 7 techniques, composite)\n"], []
means = {}
for wl, disp in WLS:
    data = collect(wl)
    means[wl] = {t: {k: mci(data[t], k)[0] for _, k, _ in METRICS} for t in T}
    tex.append(f"% ===== {disp} =====")
    tex.append(r"\begin{table*}[!ht]")
    tex.append(r"  \centering")
    tex.append(r"  \caption{\vitoradd{%s results: mean $\pm$ 95\%% CI over the %s runs, composite network-aware energy.}}"
               % (disp, "300 (10 traces $\\times$ 30 seeds)" if wl == "planetlab" else "30 seeds"))
    tex.append(r"  \label{tab:%s_results_unified}" % wl)
    tex.append(r"  \begin{adjustbox}{width=0.98\textwidth}")
    tex.append(r"  \begin{tabular}{l" + "r" * 7 + "}")
    tex.append(r"  \hline")
    tex.append("  " + " & ".join([r"\multicolumn{1}{r}{}"] + [r"\textbf{%s}" % (r"\textit{WBP}" if t == "WBP" else t) for t in T]) + r" \\")
    tex.append(r"  \hline")
    md.append(f"\n## {disp}\n")
    md.append("| Metric | " + " | ".join(T) + " |")
    md.append("|---|" + "---|" * 7)
    for label, key, dec in METRICS:
        cells_t, cells_m, best = [], [], None
        vals = [mci(data[t], key) for t in T]
        marr = [v[0] for v in vals]
        best = max(range(7), key=lambda i: marr[i]) if key in BETTER_HIGH else min(range(7), key=lambda i: marr[i])
        for i, (m, ci) in enumerate(vals):
            s = (f"{m:.0f}\\,$\\pm$\\,{ci:.0f}" if dec == 0 else f"{m:.2f}\\,$\\pm$\\,{ci:.2f}")
            if i == best:
                s = r"\textbf{" + s + "}"
            cells_t.append(s)
            cells_m.append((f"{m:.0f}±{ci:.0f}" if dec == 0 else f"{m:.2f}±{ci:.2f}") + ("*" if i == best else ""))
        tex.append("  " + " & ".join([label] + cells_t) + r" \\")
        md.append(f"| {label} | " + " | ".join(cells_m) + " |")
    tex.append(r"  \hline")
    tex.append(r"  \end{tabular}")
    tex.append(r"  \end{adjustbox}")
    tex.append(r"\end{table*}")
    tex.append("")

# headline claims recomputed (WBP vs classicals MU/MMT/RS/MC)
claims.append("\n# RECOMPUTED HEADLINE CLAIMS (WBP vs classical MU/MMT/RS/MC, composite)\n")
agg = {"e": [], "m": [], "s": []}
for wl, disp in WLS:
    mm = means[wl]
    cls_e = [mm[t]["energy"] for t in ["MU", "MMT", "RS", "MC"]]
    cls_m = [mm[t]["migr"] for t in ["MU", "MMT", "RS", "MC"]]
    cls_s = [mm[t]["sla"] for t in ["MU", "MMT", "RS", "MC"]]
    we, wm, ws = mm["WBP"]["energy"], mm["WBP"]["migr"], mm["WBP"]["sla"]
    de = [(1 - we / c) * 100 for c in cls_e]
    dm = [(1 - wm / c) * 100 for c in cls_m]
    ds = [(1 - ws / c) * 100 for c in cls_s]
    agg["e"] += de; agg["m"] += dm; agg["s"] += ds
    claims.append(f"{disp}: energy -{min(de):.0f}..-{max(de):.0f}% | migr -{min(dm):.0f}..-{max(dm):.0f}% | "
                  f"SLA {'-' if min(ds)>0 else '+'}{abs(min(ds)):.0f}..{'-' if max(ds)>0 else '+'}{abs(max(ds)):.0f}% "
                  f"| WBP vs WP migr: {mm['WBP']['migr']:.0f} vs {mm['WP']['migr']:.0f}")
claims.append(f"GLOBAL: energy -{min(agg['e']):.0f}%..-{max(agg['e']):.0f}% | migrations -{min(agg['m']):.0f}%..-{max(agg['m']):.0f}%")

open(os.path.join(HERE, "unified_workload_tables.tex"), "w", encoding="utf-8").write("\n".join(tex))
open(os.path.join(HERE, "unified_workload_tables.md"), "w", encoding="utf-8").write("\n".join(md + claims))
print("\n".join(claims))
print("\n[saved] SOTA/unified_workload_tables.tex and .md")
