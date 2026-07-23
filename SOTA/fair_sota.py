#!/usr/bin/env python3
"""FAIR SOTA comparison (for review, NOT yet in the paper).
Addresses the JGC/ICC concern that the head-to-head is biased in our favour:
  - runs AMOVMC / EUQ-VMC under BOTH the shared placement AND their NATIVE
    configuration (amovmc_native / euqvmc_native), and
  - also reports ESV = Energy x SLA Violation. NOTE: ESV is the STANDARD
    Beloglazov metric that OUR original paper reported; it is NOT the private
    objective of AMOVMC or EUQ-VMC. To be fully fair we still need each
    competitor's OWN evaluation metric from its paper (goyal2025amovmc,
    li2025euqvmc) -- TODO, requires their papers.
Composite network-aware energy; mean +/- 95% CI over 30 seeds (PlanetLab 10x30)."""
import glob, json, os
import numpy as np
from scipy import stats

OUT = r"C:\Users\PcVIP\Desktop\_publish_vmcons\output"
HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]


def emig(r):
    return (4.096 * r + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics(fp):
    d = json.load(open(fp)); cs = d["cloudsimResults"]; net = d["networkPhysicalResults"]
    ram = net.get("totalRAMInBW", 0)
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)) + emig(ram)
    sla = cs.get("slaOverall", 0) * 100
    return (e, sla, cs.get("numberOfMigrations", 0), ram / 1e5, e * sla)  # last = ESV


def agg(folders):
    vals = []
    for fld in folders:
        for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
            vals.append(metrics(f))
    if not vals:
        return None
    a = np.array(vals, float); n = len(a)
    out = []
    for i in range(5):
        m = a[:, i].mean(); ci = stats.t.ppf(0.975, n - 1) * a[:, i].std(ddof=1) / np.sqrt(n)
        out.append((m, ci))
    return n, out


def folders(method, wl, native=False):
    suf = "_native" if native else ""
    if wl == "planetlab":
        if method == "wbf":
            return [f"p4_pl_{d}_st" for d in DAYS]  # split later
        return [f"{method}{suf}_pl_{d}" for d in DAYS]
    if method == "wbf":
        return [f"paper4_full_{wl}_prophet_st"]
    return [f"{method}{suf}_{wl}"]


def wbf_only(wl):
    vals = []
    for fld in folders("wbf", wl):
        for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
            c = json.load(open(f))["experimentConfiguration"]
            if "bollinger" in str(c.get("hostSignalProcessing")):
                vals.append(metrics(f))
    a = np.array(vals, float); n = len(a); out = []
    for i in range(5):
        m = a[:, i].mean(); ci = stats.t.ppf(0.975, n - 1) * a[:, i].std(ddof=1) / np.sqrt(n)
        out.append((m, ci))
    return n, out


LAB = ["Energy (kWh)", "SLA (%)", "# migr.", "RAM-in-BW", "ESV"]
lines = ["# FAIR SOTA comparison (composite energy) — FOR REVIEW, not yet in the paper\n",
         "Competitors under their NATIVE configuration vs. the shared placement. ESV = Energy x SLA "
         "Violation is the STANDARD Beloglazov metric that OUR original paper reported (NOT the "
         "competitors' own objective). Mean $\\pm$ 95% CI. Lower is better on all columns.\n"]
for wl, disp in [("planetlab", "PlanetLab"), ("alibaba", "Alibaba"),
                 ("materna", "Materna"), ("azure", "Azure")]:
    lines.append(f"\n## {disp}\n")
    lines.append("| Method | " + " | ".join(LAB) + " |")
    lines.append("|---|---|---|---|---|---|")
    rows = [("WBF (this work)", wbf_only(wl)),
            ("AMOVMC (shared)", agg(folders("amovmc", wl))),
            ("AMOVMC (native)", agg(folders("amovmc", wl, native=True))),
            ("EUQ-VMC (shared)", agg(folders("euqvmc", wl))),
            ("EUQ-VMC (native)", agg(folders("euqvmc", wl, native=True)))]
    for name, r in rows:
        if r is None:
            lines.append(f"| {name} | " + " | ".join("n/a" for _ in LAB) + " |")
            continue
        n, cells = r
        lines.append(f"| {name} | " + " | ".join(f"{m:.2f} ± {ci:.2f}" for m, ci in cells) + " |")

report = "\n".join(lines)
open(os.path.join(HERE, "fair_sota.md"), "w", encoding="utf-8").write(report)
print(report)
print("\n[saved] SOTA/fair_sota.md")
