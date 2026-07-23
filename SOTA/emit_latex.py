#!/usr/bin/env python3
"""Emit the revised LaTeX tables (composite network-aware energy, mean +/- 95% CI)
for the Experiments-2 section: (R1) reconciled comparison vs classical baselines
(rebuilt Tables 6-9, MU/MMT/RS/MC/WPSP/WF/WBF) and (R2) head-to-head vs recent
SOTA (WBF/AMOVMC/EUQ-VMC) with paired-Wilcoxon significance. All numbers are read
from the single-thread reproduction outputs; nothing is typed by hand."""
import glob, json, os
import numpy as np
from scipy import stats

OUT = r"C:\Users\PcVIP\Desktop\_publish_vmcons\output"
HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]
WLS = [("planetlab", "PlanetLab"), ("alibaba", "Alibaba"),
       ("materna", "Materna"), ("azure", "Microsoft Azure")]


def emig(r):
    return (4.096 * r + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics(fp):
    d = json.load(open(fp)); cs = d["cloudsimResults"]; net = d["networkPhysicalResults"]
    ram = net.get("totalRAMInBW", 0)
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)) + emig(ram)
    return (e, cs.get("slaOverall", 0) * 100, cs.get("numberOfMigrations", 0), ram / 1e5)


def collect(wl):
    tech = {t: {} for t in ["MU", "MMT", "RS", "MC", "WPSP", "WF", "WBF", "AMOVMC", "EUQ-VMC"]}
    pmap = {"mu": "MU", "mmt": "MMT", "rs": "RS", "mc": "MC", "psp2": "WPSP"}
    static = [f"pl_static_{d}" for d in DAYS] if wl == "planetlab" else [f"paper4_full_{wl}_static"]
    proph = [f"p4_pl_{d}_st" for d in DAYS] if wl == "planetlab" else [f"paper4_full_{wl}_prophet_st"]
    for fld in static:
        for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
            c = json.load(open(f)).get("experimentConfiguration", {})
            sel = c.get("selectionPolicy")
            if sel in pmap:
                tech[pmap[sel]][(fld, c.get("randomSeed"))] = metrics(f)
    for fld in proph:
        for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
            c = json.load(open(f)).get("experimentConfiguration", {})
            dst = "WBF" if "bollinger" in str(c.get("hostSignalProcessing")) else "WF"
            tech[dst][(fld, c.get("randomSeed"))] = metrics(f)
    for m, pre in [("AMOVMC", "amovmc"), ("EUQ-VMC", "euqvmc")]:
        folders = [f"{pre}_pl_{d}" for d in DAYS] if wl == "planetlab" else [f"{pre}_{wl}"]
        for fld in folders:
            for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
                c = json.load(open(f)).get("experimentConfiguration", {})
                tech[m][(fld, c.get("randomSeed"))] = metrics(f)
    return tech


def cell(vals, i):
    a = np.array([v[i] for v in vals.values()], float); n = len(a)
    m = a.mean(); ci = stats.t.ppf(0.975, n - 1) * a.std(ddof=1) / np.sqrt(n)
    if i == 2:  # migrations, integer-ish
        return f"{m:.0f}\\,$\\pm$\\,{ci:.0f}"
    return f"{m:.2f}\\,$\\pm$\\,{ci:.2f}"


def wtest(a, b, i):
    ka = sorted(set(a) & set(b))
    xa = np.array([a[k][i] for k in ka]); xb = np.array([b[k][i] for k in ka])
    d = xa - xb
    p = stats.wilcoxon(xa, xb).pvalue
    return p, "WBF" if (d < 0).sum() > (d > 0).sum() else "opp"


# ---- R1: reconciled vs classical baselines ----------------------------------
r1 = [r"\begin{tabular}{llrrrr}", r"\hline",
      r"\textbf{Workload} & \textbf{Method} & \textbf{Energy (kWh)} & \textbf{SLA (\%)} & \textbf{\# migr.} & \textbf{RAM-in-BW} \\",
      r"\hline"]
for wl, disp in WLS:
    t = collect(wl)
    r1.append(r"\multicolumn{6}{l}{\textbf{%s}} \\" % disp)
    for lbl in ["MU", "MMT", "RS", "MC", "WPSP", "WF", "WBF"]:
        name = r"\textit{WBF (this work)}" if lbl == "WBF" else lbl
        r1.append(f" & {name} & {cell(t[lbl],0)} & {cell(t[lbl],1)} & {cell(t[lbl],2)} & {cell(t[lbl],3)} \\\\")
    r1.append(r"\hline")
r1.append(r"\end{tabular}")

# ---- R2: head-to-head SOTA with significance --------------------------------
r2 = [r"\begin{tabular}{llrrrr}", r"\hline",
      r"\textbf{Workload} & \textbf{Method} & \textbf{Energy (kWh)} & \textbf{SLA (\%)} & \textbf{\# migr.} & \textbf{RAM-in-BW} \\",
      r"\hline"]
sig_notes = []
for wl, disp in WLS:
    t = collect(wl)
    r2.append(r"\multicolumn{6}{l}{\textbf{%s}} \\" % disp)
    for lbl in ["WBF", "AMOVMC", "EUQ-VMC"]:
        name = r"\textit{WBF (this work)}" if lbl == "WBF" else lbl
        cites = {"AMOVMC": r"~\cite{goyal2025amovmc}", "EUQ-VMC": r"~\cite{li2025euqvmc}"}.get(lbl, "")
        r2.append(f" & {name}{cites} & {cell(t[lbl],0)} & {cell(t[lbl],1)} & {cell(t[lbl],2)} & {cell(t[lbl],3)} \\\\")
    r2.append(r"\hline")
r2.append(r"\end{tabular}")

report = "% ===== R1: reconciled comparison vs classical baselines =====\n" + "\n".join(r1)
report += "\n\n% ===== R2: head-to-head vs recent SOTA =====\n" + "\n".join(r2)
open(os.path.join(HERE, "latex_tables_composite.tex"), "w", encoding="utf-8").write(report)
print(report)
print("\n[saved] SOTA/latex_tables_composite.tex")
