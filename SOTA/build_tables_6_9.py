#!/usr/bin/env python3
"""Rebuild the per-workload Tables 6-9 (MU/MMT/RS/MC/WPSP/WF/WBF) under the SINGLE
reproduction environment, so they are internally consistent with Table 10 (same
WBF numbers). Classical baselines come from the *_static reconciliation campaign;
WF/WBF from the prophet single-thread runs. Reports mean +/- 95% CI.
Runs partially: workloads with no *_static data yet are skipped with a note."""
import glob, json, os
import numpy as np
from scipy import stats

OUT = r"C:\Users\PcVIP\Desktop\_publish_vmcons\output"
HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]
METRICS = ["Energy (kWh)", "SLA (%)", "# migr.", "RAM-in-BW"]
POL = [("mu", "MU"), ("mmt", "MMT"), ("rs", "RS"), ("mc", "MC"), ("psp2", "WPSP")]


def emig_paths(total_ram_in_bw):
    """Network-routing energy of migrations (composite-energy term), canonical
    formula from scripts/analyze_results.py."""
    return (4.096 * total_ram_in_bw + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics(fp):
    j = json.load(open(fp)); cs = j["cloudsimResults"]; net = j["networkPhysicalResults"]
    ram = net.get("totalRAMInBW", 0)
    # Composite network-aware energy = host energy + migration-path routing energy
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)) + emig_paths(ram)
    sla = cs.get("slaOverall", 0) * 100
    return (e, sla, cs.get("numberOfMigrations", 0), ram / 1e5)


def summ(vals):
    a = np.asarray(vals, float); n = len(a)
    if n == 0:
        return 0, 0.0, 0.0
    mean = a.mean(); sd = a.std(ddof=1) if n > 1 else 0.0
    ci = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 1 else 0.0
    return n, mean, ci


def static_folders(wl):
    return [f"pl_static_{d}" for d in DAYS] if wl == "planetlab" else [f"paper4_full_{wl}_static"]


def load_classicals(wl):
    """Return {policy_label: [metric_tuples]} for the classical baselines."""
    by = {lbl: [] for _, lbl in POL}
    pmap = dict(POL)
    for fld in static_folders(wl):
        for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
            c = json.load(open(f)).get("experimentConfiguration", {})
            sel = c.get("selectionPolicy")
            if sel in pmap:
                by[pmap[sel]].append(metrics(f))
    return by


def load_wf_wbf(wl):
    wf, wbf = [], []
    pool = [f"p4_pl_{d}_st" for d in DAYS] if wl == "planetlab" else [f"paper4_full_{wl}_prophet_st"]
    for fld in pool:
        for f in glob.glob(os.path.join(OUT, fld, "*_data.json")):
            c = json.load(open(f)).get("experimentConfiguration", {})
            (wbf if "bollinger" in str(c.get("hostSignalProcessing")) else wf).append(metrics(f))
    return wf, wbf


lines, md = [], ["# Rebuilt Tables 6-9 (single reproduction environment) — mean ± 95% CI\n"]
for wl in ["planetlab", "alibaba", "materna", "azure"]:
    cls = load_classicals(wl)
    wf, wbf = load_wf_wbf(wl)
    have_cls = any(cls[lbl] for _, lbl in POL)
    rows = [(lbl, cls[lbl]) for _, lbl in POL] + [("WF", wf), ("WBF", wbf)]
    lines.append("=" * 88)
    lines.append(f"  TABLE — {wl.upper()}" + ("" if have_cls else "   [classicals PENDING — campaign not finished]"))
    lines.append("=" * 88)
    lines.append(f"{'Technique':10}{'n':>4}   " + "".join(f"{m:>20}" for m in METRICS))
    lines.append("-" * 88)
    md.append(f"\n## {wl.capitalize()}\n")
    md.append("| Technique | " + " | ".join(METRICS) + " |")
    md.append("|---|---|---|---|---|")
    for lbl, data in rows:
        if not data:
            lines.append(f"{lbl:10}{'--':>4}   " + "".join(f"{'(pending)':>20}" for _ in METRICS))
            md.append(f"| {lbl} | " + " | ".join("(pending)" for _ in METRICS) + " |")
            continue
        cells, mdc = [], []
        for i in range(4):
            n, mean, ci = summ([d[i] for d in data])
            cells.append(f"{mean:8.2f}±{ci:5.2f}")
            mdc.append(f"{mean:.2f} ± {ci:.2f}")
        lines.append(f"{lbl:10}{n:>4}   " + "".join(f"{c:>20}" for c in cells))
        md.append(f"| {lbl} | " + " | ".join(mdc) + " |")
    lines.append("")

report = "\n".join(lines)
print(report)
open(os.path.join(HERE, "tables_6_9_rebuilt.txt"), "w", encoding="utf-8").write(report)
open(os.path.join(HERE, "tables_6_9_rebuilt.md"), "w", encoding="utf-8").write("\n".join(md))
print("\n[saved] SOTA/tables_6_9_rebuilt.txt and .md")
