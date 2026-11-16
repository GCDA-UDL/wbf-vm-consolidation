#!/usr/bin/env python3
"""Tables of the revision experiments, from the per-run cache.

Run from experiments/revision_r1/ (paths are relative to that folder):

  python -B ../../analysis_revision/extract_runs.py --out output --cache cache      (first)
  python -B tools/build_tables.py [--stored-cache ../../analysis_revision/cache]
                                  [--timing-campaigns t1timing]

Read-only on the outputs.  Metric definitions: analysis_revision/revlib.py::metrics_rev
(migration traffic counted once, host energy = energyWithExtraHost, migration energy with
kappa = 0.512 J per MB and hop plus 20.165 J per migration).  Every run is labelled from its
own experimentConfiguration (forecaster, signal processing and its parameters, history
length, seed, trace), never from the folder name; the folder prefix only selects the family
(cl_ closed loop, bs_ Bollinger sensitivity, tm_ decision time).

--stored-cache is the per-run cache of the campaign behind the main tables (written by
analysis_revision/extract_runs.py); it is needed only for rerun_vs_stored.md.
The decision-time row is read from runlogs/<campaign>/_timing.log, written by the runner.

Writes tables/*.md and tables/*.tex.
"""
import argparse
import collections
import glob
import json
import math
import os
import re
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)                                  # experiments/revision_r1
REPO = os.path.dirname(os.path.dirname(EXP))                 # repository root
sys.path.insert(0, os.path.join(REPO, "analysis_revision"))
import revlib as L  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cache", default=os.path.join(EXP, "cache"))
ap.add_argument("--stored-cache", default=os.path.join(REPO, "analysis_revision", "cache"))
ap.add_argument("--timing-campaigns", default="t1timing",
                help="comma-separated campaigns under runlogs/ run without contention (decision time)")
a = ap.parse_args()
TAB = os.path.join(EXP, "tables")
os.makedirs(TAB, exist_ok=True)

runs, _ = L.load_cache(a.cache)
runs = [r for r in runs if L.complete(r)]

FC = {"last": "LVP", "simpleexpsmoothing": "EWMA", "fbprophet": "Prophet"}
WLN = {"planetlab": "PlanetLab", "alibaba": "Alibaba", "materna": "Materna", "azure": "Microsoft Azure"}


def sig(r):
    s = str(r.get("cfg_hostSignalProcessing") or "none").lower()
    if "bollinger" not in s:
        return None
    p = r.get("cfg_hostSignalProcessingParams")
    if isinstance(p, str):
        p = json.loads(p)
    return (int(float(p[0])), float(p[1]))


def variant(r):
    fc = FC.get(str(r.get("cfg_hostForecastingTechnique")).lower(), str(r.get("cfg_hostForecastingTechnique")))
    return fc + ("+BB" if sig(r) else "")


def unit_key(r):
    return (L.trace_day(r), int(r.get("cfg_randomSeed")))


def agg(wl, rs, key):
    """Mean and 95% CI half-width; PlanetLab: over the per-trace means."""
    vals = collections.defaultdict(list)
    for r in rs:
        v = r["_m"][key] if key in r["_m"] else r.get(key)
        if v is None:
            continue
        vals[L.trace_day(r)].append(v)
    if not vals:
        return None
    if wl == "planetlab":
        means = [float(np.mean(v)) for _, v in sorted(vals.items())]
        n, m, sd, ci = L.mean_ci(means)
        return dict(mean=m, ci=ci, n_units=n, n_runs=sum(len(v) for v in vals.values()))
    allv = [x for v in vals.values() for x in v]
    n, m, sd, ci = L.mean_ci(allv)
    return dict(mean=m, ci=ci, n_units=n, n_runs=len(allv))


def paired(wl, rs_a, rs_b, key):
    """a - b.  PlanetLab: paired t on the trace means; others: Wilcoxon on seed pairs."""
    A = {unit_key(r): r["_m"][key] for r in rs_a}
    B = {unit_key(r): r["_m"][key] for r in rs_b}
    ks = sorted(set(A) & set(B), key=lambda k: (str(k[0]), k[1]))
    if len(ks) < 5:
        return None
    xa = np.array([A[k] for k in ks], float)
    xb = np.array([B[k] for k in ks], float)
    if wl == "planetlab":
        days = sorted({k[0] for k in ks})
        ma = np.array([np.mean([A[k] for k in ks if k[0] == d]) for d in days])
        mb = np.array([np.mean([B[k] for k in ks if k[0] == d]) for d in days])
        d = ma - mb
        p = 1.0 if np.allclose(d, 0) else float(stats.ttest_rel(ma, mb).pvalue)
        return dict(n=len(days), diff=float(d.mean()), p=p, test="paired t, 10 trace means")
    d = xa - xb
    p = 1.0 if not np.any(d != 0) else float(stats.wilcoxon(xa, xb).pvalue)
    return dict(n=len(ks), diff=float(d.mean()), p=p, test="Wilcoxon, seed pairs")


# decision time per run, from the simulator's own log line
TIMING = {}
for camp in [c for c in a.timing_campaigns.split(",") if c]:
    p = os.path.join(EXP, "runlogs", camp, "_timing.log")
    if os.path.exists(p):
        bad = set()      # runs with a negative mean in any stage: the wall clock stepped back during the run
        for ln in open(p, encoding="utf-8", errors="replace"):
            m = re.match(r"^(\S+) \| Execution time - ([A-Za-z ]+) mean:\s*([0-9.eE+-]+)", ln)
            if m:
                if float(m.group(3)) < 0:
                    bad.add(m.group(1))
                if m.group(2).strip() == "total":
                    TIMING[m.group(1)] = float(m.group(3))
        for name in bad:
            if name in TIMING:
                TIMING[name] = -abs(TIMING[name]) if TIMING[name] else -1.0   # flagged: excluded below (<= 0)
for r in runs:
    r["_m"] = L.metrics_rev(r)
    name = r["file"].replace("_00000_data.json", "")
    r["_m"]["dec_time"] = TIMING.get(name)
    r["_name"] = name

fam = collections.defaultdict(list)
for r in runs:
    fam[r["folder"].split("_")[0]].append(r)

ROWS = [("e_hosts", "Host energy (kWh)", 2), ("e_total", "Total energy (kWh)", 2),
        ("sla", r"SLA violation (\%)", 2), ("migr", r"\# of migrations", 0),
        ("traffic", r"Migration traffic (GB$\cdot$hop)", 0), ("act_hosts", "Mean active hosts", 2)]


def cell(g, d, tex=True):
    if g is None:
        return "--" if tex else "-"
    pm = "\\,$\\pm$\\,".replace("\\\\", "\\") if tex else " ± "
    return f"{g['mean']:.{d}f}{pm}{g['ci']:.{d}f}"


out_md = []

# ============================================================================ closed loop
CL = fam.get("cl", [])
if CL:
    COLS = ["LVP", "LVP+BB", "EWMA", "EWMA+BB", "Prophet", "Prophet+BB"]
    by = collections.defaultdict(list)
    for r in CL:
        by[(L.workload(r), variant(r))].append(r)
    DT = collections.defaultdict(list)
    for r in fam.get("tm", []):
        DT[(L.workload(r), variant(r))].append(r)
    md = ["# Closed-loop forecaster replacement (new runs, one simulation per JVM)", "",
          "Same selection (WPSP, `psp2`), same MAD overload rule, same placement (`ac`); only the host "
          "forecaster and the Bollinger transform (5, 0.5) change. LVP = WPSP of the paper, Prophet = WP, "
          "Prophet+BB = WBP, all re-run here. EWMA = `simpleExpSmoothing`, smoothing level 0.8 (fixed in "
          "`pymodule`; last value while the history has fewer than 10 samples).", "",
          "Mean ± 95% CI (PlanetLab: over the 10 daily-trace means; others: over the seeds). "
          "Migration energy with kappa = 0.512 J per MB and hop.", ""]
    tex = [r"\begin{table*}[!ht]", r"\centering",
           r"\caption{Closed-loop replacement of the host forecaster: same selection (WPSP), overload rule and "
           r"placement; only the forecaster and the Bollinger transform change. LVP: last value (the WPSP column of "
           r"the per-workload tables); EWMA: exponential smoothing with level 0.8; Prophet and Prophet+BB are WP and "
           r"\textit{WBP}. All six variants re-run with one simulation per JVM. Mean $\pm$ 95\% CI (PlanetLab: over "
           r"the 10 daily traces; others: over the 30 seeds). Decision time: mean time of one consolidation "
           r"decision in dedicated runs without concurrent load (one trace per workload and two seeds per variant; "
           r"two runs in which the clock of the simulator stepped back are excluded).}",
           r"\label{tab:closed_loop}", r"\begin{adjustbox}{width=0.98\textwidth}",
           r"\begin{tabular}{llrrrrrr}", r"\hline",
           r"Workload & Metric & \textbf{LVP} & \textbf{LVP+BB} & \textbf{EWMA} & \textbf{EWMA+BB} & "
           r"\textbf{Prophet} & \textbf{Prophet+BB} \\", r"\hline"]
    for wl in L.WLS:
        if not any((wl, c) in by for c in COLS):
            continue
        md += [f"## {WLN[wl]}", "",
               "| metric | " + " | ".join(COLS) + " |", "|---|" + "---|" * len(COLS)]
        md.append("| runs (units) | " + " | ".join(
            (f"{len(by[(wl, c)])} ({len({unit_key(r)[0] for r in by[(wl, c)]}) if wl == 'planetlab' else len(by[(wl, c)])})"
             if (wl, c) in by else "-") for c in COLS) + " |")
        for i, (key, lab, d) in enumerate(ROWS):
            gs = {c: (agg(wl, by[(wl, c)], key) if (wl, c) in by else None) for c in COLS}
            md.append(f"| {lab} | " + " | ".join(cell(gs[c], d, tex=False) for c in COLS) + " |")
            if key != "act_hosts":
                first = WLN[wl] if i == 0 else ""
                tex.append(f"{first} & {lab} & " + " & ".join(cell(gs[c], d) for c in COLS) + r" \\")
        # decision time: dedicated runs without contention (family tm_), simulator's own timer
        dts = {c: [r["_m"]["dec_time"] for r in DT.get((wl, c), [])
                   if r["_m"]["dec_time"] is not None and r["_m"]["dec_time"] > 0] for c in COLS}
        nneg = sum(1 for c in COLS for r in DT.get((wl, c), [])
                   if r["_m"]["dec_time"] is not None and r["_m"]["dec_time"] <= 0)
        md.append("| Decision time (s), uncontended | " + " | ".join(
            (f"{np.mean(dts[c]):.4f} (n={len(dts[c])})" if dts[c] else "-") for c in COLS) + " |")
        tex.append(" & Decision time (s) & " + " & ".join(
            (f"{np.mean(dts[c]):.3f}" if dts[c] else "--") for c in COLS) + r" \\")
        tex.append(r"\hline")
        md.append("")
        if nneg:
            md += [f"Decision time: {nneg} run(s) with a negative logged mean in some stage excluded (the simulator "
                   "timer uses the wall clock and the virtual machine clock stepped back during the run).", ""]
        # paired contrasts useful for the text
        md += ["Paired contrasts (a − b; PlanetLab: paired t on trace means; others: Wilcoxon on seed pairs):", "",
               "| contrast | metric | n | mean difference | p |", "|---|---|---|---|---|"]
        for a_, b_ in [("Prophet", "LVP"), ("Prophet", "EWMA"), ("EWMA", "LVP"),
                       ("Prophet+BB", "LVP+BB"), ("Prophet+BB", "EWMA+BB"),
                       ("LVP+BB", "LVP"), ("EWMA+BB", "EWMA"), ("Prophet+BB", "Prophet")]:
            if (wl, a_) in by and (wl, b_) in by:
                for key, lab, d in ROWS[:5]:
                    t = paired(wl, by[(wl, a_)], by[(wl, b_)], key)
                    if t:
                        md.append(f"| {a_} − {b_} | {key} | {t['n']} | {t['diff']:+.4g} | {t['p']:.3g} |")
        md.append("")
    tex += [r"\end{tabular}", r"\end{adjustbox}", r"\end{table*}"]
    open(os.path.join(TAB, "closed_loop.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    open(os.path.join(TAB, "tab_closed_loop.tex"), "w", encoding="utf-8", newline="\n").write(
        "% Generated by experiments/tools/build_tables.py -- do not edit by hand.\n" + "\n".join(tex) + "\n")
    out_md.append("closed_loop.md")

    # ---- statistical reproduction of the stored campaign (LVP = WPSP, Prophet = WP, Prophet+BB = WBP)
    if os.path.exists(os.path.join(a.stored_cache, "runs.jsonl")):
        sruns, _ = L.load_cache(a.stored_cache)
        md = ["# Re-run in one-JVM mode versus the stored campaign (same configurations and seeds)", "",
              "Stored: runs behind the manuscript tables (batch mode). Re-run: this campaign. "
              "`identical` counts the runs whose four result sections are byte-identical (sha1). "
              "Difference = re-run − stored, paired by trace and seed.", "",
              "| workload | technique | metric | stored mean ± CI | re-run mean ± CI | difference | p | n | identical runs |",
              "|---|---|---|---|---|---|---|---|---|"]
        MAP = {"LVP": "WPSP", "Prophet": "WP", "Prophet+BB": "WBP"}
        for wl in L.WLS:
            st = L.collect_table_runs(sruns, wl)
            for v, t in MAP.items():
                if (wl, v) not in by:
                    continue
                new = by[(wl, v)]
                old = st[t]
                for r in old:
                    r["_m"] = L.metrics_rev(r)
                oh = {unit_key(r): r.get("result_sha1") for r in old}
                ident = sum(1 for r in new if oh.get(unit_key(r)) == r.get("result_sha1"))
                keys_new = {unit_key(r) for r in new}
                old_m = [r for r in old if unit_key(r) in keys_new]
                for key, lab, d in ROWS[:5]:
                    go, gn = agg(wl, old_m, key), agg(wl, new, key)
                    t_ = paired(wl, new, old_m, key)
                    md.append(f"| {WLN[wl]} | {t} | {key} | {cell(go, d, False)} | {cell(gn, d, False)} | "
                              f"{t_['diff']:+.4g} | {t_['p']:.3g} | {t_['n']} | {ident}/{len(new)} |")
        open(os.path.join(TAB, "rerun_vs_stored.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
        out_md.append("rerun_vs_stored.md")

# ============================================================================ Bollinger sensitivity
BS = fam.get("bs", [])
if BS:
    # baseline (5, 0.5): the Prophet+BB runs of the closed-loop campaign with the same seeds (same mode)
    bs_seeds = {int(r.get("cfg_randomSeed")) for r in BS}
    BS = BS + [r for r in fam.get("cl", []) if variant(r) == "Prophet+BB" and sig(r) == (5, 0.5)
               and int(r.get("cfg_randomSeed")) in bs_seeds]
    by = collections.defaultdict(list)
    for r in BS:
        by[(L.workload(r), sig(r))].append(r)
    cfgs = sorted({k[1] for k in by}, key=lambda s: (s[1] != 0.5, s[0], s[1]) if s else (0, 0, 0))
    order = [c for c in [(3, 0.5), (5, 0.5), (10, 0.5), (20, 0.5), (5, 1.0), (5, 1.5), (5, 2.0)] if c in cfgs]
    order += [c for c in cfgs if c not in order]
    md = ["# Bollinger sensitivity of WBP (new runs, one simulation per JVM)", "",
          f"Seeds {min(bs_seeds)}-{max(bs_seeds)}. The column (5, 0.5) is the Prophet+BB variant of the closed-loop "
          "campaign restricted to the same seeds. ",
          "One-at-a-time variations around (N = 5, alpha = 0.5). Mean ± 95% CI "
          "(PlanetLab: over the 10 daily-trace means; others: over the seeds).", ""]
    tex = [r"\begin{table*}[!ht]", r"\centering",
           r"\caption{Sensitivity of \textit{WBP} to the Bollinger parameters: window $N$ at $\alpha=0.5$ and width "
           r"$\alpha$ at $N=5$ (one-at-a-time around the setting used in the paper, $N=5$, $\alpha=0.5$). "
           r"Mean $\pm$ 95\% CI (PlanetLab: over the 10 daily traces; others: over the seeds).}",
           r"\label{tab:bollinger_sensitivity}", r"\begin{adjustbox}{width=0.98\textwidth}",
           r"\begin{tabular}{ll" + "r" * len(order) + "}", r"\hline",
           r"Workload & Metric & " + " & ".join(f"({n}, {al:g})" for n, al in order) + r" \\", r"\hline"]
    for wl in L.WLS:
        if not any((wl, c) in by for c in order):
            continue
        md += [f"## {WLN[wl]}", "", "| metric | " + " | ".join(f"N={n}, a={al:g}" for n, al in order) + " |",
               "|---|" + "---|" * len(order)]
        md.append("| runs | " + " | ".join(str(len(by[(wl, c)])) if (wl, c) in by else "-" for c in order) + " |")
        for i, (key, lab, d) in enumerate(ROWS):
            gs = {c: (agg(wl, by[(wl, c)], key) if (wl, c) in by else None) for c in order}
            md.append(f"| {lab} | " + " | ".join(cell(gs[c], d, False) for c in order) + " |")
            first = WLN[wl] if i == 0 else ""
            tex.append(f"{first} & {lab} & " + " & ".join(cell(gs[c], d) for c in order) + r" \\")
        tex.append(r"\hline")
        md.append("")
        if (wl, (5, 0.5)) in by:
            md += ["Paired contrasts against (5, 0.5):", "", "| setting | metric | n | mean difference | p |",
                   "|---|---|---|---|---|"]
            for c in order:
                if c == (5, 0.5) or (wl, c) not in by:
                    continue
                for key, lab, d in ROWS[:5]:
                    t = paired(wl, by[(wl, c)], by[(wl, (5, 0.5))], key)
                    if t:
                        md.append(f"| N={c[0]}, a={c[1]:g} | {key} | {t['n']} | {t['diff']:+.4g} | {t['p']:.3g} |")
            md.append("")
    tex += [r"\end{tabular}", r"\end{adjustbox}", r"\end{table*}"]
    open(os.path.join(TAB, "bollinger_sensitivity.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    open(os.path.join(TAB, "tab_bollinger_sensitivity.tex"), "w", encoding="utf-8", newline="\n").write(
        "% Generated by experiments/tools/build_tables.py -- do not edit by hand.\n" + "\n".join(tex) + "\n")
    out_md.append("bollinger_sensitivity.md")

# ============================================================================ inventory
inv = collections.Counter()
for r in runs:
    pol = str(r.get("cfg_selectionPolicy", "")).lower()
    inv[(r["folder"].split("_")[0], L.workload(r), (variant(r) if pol == "psp2" else pol.upper()), str(sig(r)),
         str(r.get("cfg_forecastingHistoryLength")))] += 1
md = ["# Inventory of the revision runs (complete runs only)", "",
      "| family | workload | variant | Bollinger (N, alpha) | history | runs |", "|---|---|---|---|---|---|"]
for k, n in sorted(inv.items()):
    md.append("| " + " | ".join(str(x) for x in k) + f" | {n} |")
md.append("")
md.append(f"Total complete runs: {len(runs)}")
open(os.path.join(TAB, "inventory.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
out_md.append("inventory.md")
print("written:", ", ".join(out_md), "| runs:", len(runs), "| timed runs:", len(TIMING))
