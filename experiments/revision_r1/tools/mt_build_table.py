#!/usr/bin/env python3
"""Table of the robustness check on four additional traces (runs `mt_*`).

  python -B tools/mt_build_table.py [--cache cache_mt] [--outdir tables] [--competitors classical|all]
                                    [--columns auto|7|10] [--require-complete]

Input: the per-run cache written by tools/mt_extract.py (or by ../../analysis_revision/extract_runs.py: the records
are the same).  Runs are taken from the four output folders mt_materna2, mt_materna3, mt_alibaba5 and
mt_alibaba8.  Each run is labelled from its own experimentConfiguration (technique as in
../../analysis_revision/revlib.py::technique), its trace from its own workloadTrace, and it is excluded, with the
reason listed, if anything differs from the settings of the paper (workload folder, dataStartStep, VM
template, shared placement `ac`, MAD overload rule for the selection policies, Bollinger (5, 0.5) for
WBP and BB+NeoPro, AMOVMC with its built-in gamma = 0.80 (`amovmc`, not the tuning variant),
EUQ-VMC with safe = 1.5), or if the technique in the file name does not match the configuration.

Metrics: ../../analysis_revision/revlib.py::metrics_rev, the definitions of the revised paper (host energy =
energyWithExtraHost; migration traffic counted once; migration energy kappa = 0.512 J per MB and hop
plus beta = 20.165 J per migration; total = host + migration).  Per trace and technique: mean and 95%
CI (t, n - 1 d.o.f.) over the seeds.  Tests: Wilcoxon signed-rank on seed pairs, WBP against each of
MU, MMT, RS and MC (or every other column with --competitors all), per trace and metric; Holm
correction over all the tests of the table; a dagger marks a non-significant difference (Holm-adjusted
p >= 0.05), bold the best mean of the row at the printed precision, as in the per-workload tables.
Ten columns (BB+NeoPro, AMOVMC, EUQ-VMC added) when runs of those methods are present.

Writes <outdir>/more_traces.md, <outdir>/tab_more_traces.tex (label tab:more_traces) and
<outdir>/more_traces.json, and prints per trace the ranges of the reduction of migrations and
migration traffic of WBP with respect to the four classical policies and of the total-energy difference.
"""
import argparse
import collections
import json
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mt_common as M  # noqa: E402

sys.path.insert(0, M.ANALYSIS)
import revlib as L  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cache", default=os.path.join(M.EXP, "cache_mt"))
ap.add_argument("--outdir", default=os.path.join(M.EXP, "tables"))
ap.add_argument("--folders", default=",".join(t["exp"] for t in M.TRACES))
ap.add_argument("--competitors", choices=["classical", "all"], default="classical")
ap.add_argument("--columns", choices=["auto", "7", "10"], default="auto")
ap.add_argument("--require-complete", action="store_true", help="exit 3 if a cell has fewer than 30 seeds")
a = ap.parse_args()

ROWS = [("e_hosts", "Host energy (kWh)", 2), ("e_total", "Total energy (kWh)", 2),
        ("sla", r"SLA violation (\%)", 2), ("migr", r"\# of migrations", 0),
        ("traffic", r"Migration traffic (GB$\cdot$hop)", 0)]
MDLAB = {"e_hosts": "Host energy (kWh)", "e_total": "Total energy (kWh)", "sla": "SLA violation (%)",
         "migr": "Number of migrations", "traffic": "Migration traffic (GB·hop)"}
MAIN = ["MU", "MMT", "RS", "MC", "WPSP", "WP", "WBP"]
EXTRA = ["BB+NeoPro", "AMOVMC", "EUQ-VMC"]
CLASSICAL = ["MU", "MMT", "RS", "MC"]
CITE = {"BB+NeoPro": r"BB+NeoPro~\cite{VILA2023321}", "AMOVMC": r"AMOVMC~\cite{goyal2025amovmc}",
        "EUQ-VMC": r"EUQ-VMC~\cite{li2025euqvmc}"}
FOLDERS = [f for f in a.folders.split(",") if f]
TR = [M.TRACE_BY_EXP[f] for f in FOLDERS]


def sig(r):
    if "bollinger" not in str(r.get("cfg_hostSignalProcessing") or "none").lower():
        return None
    p = r.get("cfg_hostSignalProcessingParams")
    p = json.loads(p) if isinstance(p, str) else p
    return (int(float(p[0])), float(p[1]))


def mismatch(r, label, tr):
    """Reasons why a run is not the intended configuration (empty list = OK)."""
    prov = M.PROVIDERS[tr["provider"]]
    why = []
    if (r.get("cfg_workload"), r.get("cfg_workloadTrace")) != (prov["wtype"], tr["folder"]):
        why.append(f"workload {r.get('cfg_workload')}/{r.get('cfg_workloadTrace')}")
    if r.get("cfg_dataStartStep") != tr["start"]:
        why.append(f"dataStartStep {r.get('cfg_dataStartStep')}")
    if r.get("cfg_vms") != prov["vms"] or r.get("cfg_numCloudlets") != 100:
        why.append(f"vms {r.get('cfg_vms')} / numCloudlets {r.get('cfg_numCloudlets')}")
    if r.get("cfg_vmMigrationPolicy") != "ac":
        why.append(f"placement {r.get('cfg_vmMigrationPolicy')} (not the shared one)")
    hos = r.get("cfg_hostOverSaturationPolicy")
    want_hos = {"AMOVMC": "amovmc", "EUQ-VMC": "euqvmc"}.get(label, "mad")
    if hos != want_hos:
        why.append(f"overload rule {hos}")
    if label == "EUQ-VMC" and str(r.get("cfg_parameter")) != "1.5":
        why.append(f"EUQ-VMC safe = {r.get('cfg_parameter')}")
    if label in ("WBP", "BB+NeoPro") and sig(r) != (5, 0.5):
        why.append(f"Bollinger {sig(r)}")
    if label not in MAIN + EXTRA:
        why.append(f"technique {label}")
    tag = r["file"].split("__", 1)[1].rsplit("_s", 1)[0] if "__" in r["file"] else None
    if tag not in M.TECH_BY_TAG or M.TECH_BY_TAG[tag][1] != label:
        why.append(f"file name says {tag}, configuration says {label}")
    return why


# ------------------------------------------------------------------------------------------- runs
runs, _ = L.load_cache(a.cache)
R = collections.defaultdict(dict)          # (trace key, label) -> {seed: metrics}
excluded, incomplete_runs, dup = [], [], []
for r in runs:
    if r["folder"] not in FOLDERS:
        continue
    tr = M.TRACE_BY_EXP[r["folder"]]
    if not L.complete(r):
        incomplete_runs.append(r["file"])
        continue
    label = L.technique(r)
    why = mismatch(r, label, tr)
    if why:
        excluded.append((r["file"], why))
        continue
    seed = int(r["cfg_randomSeed"])
    if seed in R[(tr["key"], label)]:
        dup.append(r["file"])
    R[(tr["key"], label)][seed] = L.metrics_rev(r)
if dup:
    raise SystemExit(f"duplicate runs (same trace, technique and seed): {dup[:10]}")

has_extra = any(R.get((t["key"], c)) for t in TR for c in EXTRA)
COLS = MAIN + EXTRA if (a.columns == "10" or (a.columns == "auto" and has_extra)) else MAIN
COMP = CLASSICAL if a.competitors == "classical" else [c for c in COLS if c != "WBP"]

# ------------------------------------------------------------------------------------ aggregates
AGG = {}
for t in TR:
    for c in COLS:
        for key, _, _ in ROWS:
            vals = [m[key] for s, m in sorted(R.get((t["key"], c), {}).items())]
            if vals:
                n, mean, sd, ci = L.mean_ci(vals)
                AGG[(t["key"], c, key)] = dict(n=n, mean=mean, sd=sd, ci=ci)

# ------------------------------------------------------------------------------------------ tests
TESTS = []
for t in TR:
    W = R.get((t["key"], "WBP"), {})
    for c in COMP:
        X = R.get((t["key"], c), {})
        seeds = sorted(set(W) & set(X))
        for key, _, _ in ROWS:
            if len(seeds) < 5:
                continue
            xa = np.array([W[s][key] for s in seeds], float)
            xb = np.array([X[s][key] for s in seeds], float)
            d = xa - xb
            p = 1.0 if not np.any(d != 0) else float(stats.wilcoxon(xa, xb).pvalue)
            TESTS.append(dict(trace=t["key"], opp=c, key=key, n=len(seeds), mean_diff=float(d.mean()), p=p))
if TESTS:
    for tst, ph in zip(TESTS, L.holm([x["p"] for x in TESTS])):
        tst["p_holm"] = float(ph)
SIG = {(x["trace"], x["opp"], x["key"]): x["p_holm"] < 0.05 for x in TESTS}


# ------------------------------------------------------------------------------------------ cells
def best(t, key, d):
    vals = {c: round(AGG[(t, c, key)]["mean"], d) for c in COLS if (t, c, key) in AGG}
    if not vals:
        return set()
    m = min(vals.values())
    return {c for c, v in vals.items() if v == m}


def tex_cell(t, c, key, d, b):
    g = AGG.get((t, c, key))
    if g is None:
        return "--"
    body = f"{g['mean']:.{d}f}\\,$\\pm$\\,{g['ci']:.{d}f}"
    if c in b:
        body = "\\textbf{" + body + "}"
    if (t, c, key) in SIG and not SIG[(t, c, key)]:
        body += "$^{\\dagger}$"
    return body


def md_cell(t, c, key, d, b):
    g = AGG.get((t, c, key))
    if g is None:
        return "-"
    body = f"{g['mean']:.{d}f} ± {g['ci']:.{d}f}"
    if c in b:
        body = f"**{body}**"
    if (t, c, key) in SIG and not SIG[(t, c, key)]:
        body += " †"
    return body


def pct_red(w, x):
    return 100.0 * (1 - w / x)


# ----------------------------------------------------------------------------------------- ranges
RANGES = {}
for t in TR:
    k = t["key"]
    rg = {}
    if all((k, c, "migr") in AGG for c in CLASSICAL + ["WBP"]):
        for key in ("migr", "traffic", "e_total", "e_hosts", "sla"):
            w = AGG[(k, "WBP", key)]["mean"]
            per = {c: pct_red(w, AGG[(k, c, key)]["mean"]) for c in CLASSICAL}
            absd = {c: w - AGG[(k, c, key)]["mean"] for c in CLASSICAL}
            rg[key] = dict(lo=min(per.values()), hi=max(per.values()), per=per,
                           abs_lo=min(absd.values()), abs_hi=max(absd.values()), abs=absd)
    RANGES[k] = rg

# ------------------------------------------------------------------------------------------ write
complete = all(AGG.get((t["key"], c, "e_total"), {}).get("n") == len(M.SEEDS) for t in TR for c in COLS)
ntests = len(TESTS)
os.makedirs(a.outdir, exist_ok=True)
comp_txt = "MU, MMT, RS and MC" if a.competitors == "classical" else "every other column"

md = ["# Robustness check on four additional traces", "",
      f"Generated by `tools/mt_build_table.py` from `{os.path.relpath(a.cache, M.EXP) if a.cache.startswith(M.EXP) else a.cache}` "
      "(do not edit by hand). Metrics: `../../analysis_revision/revlib.py::metrics_rev` (kappa = 0.512 J per MB and hop, "
      "beta = 20.165 J per migration, migration traffic counted once). Mean ± 95% CI over the seeds. Tests: "
      f"Wilcoxon signed-rank on seed pairs, WBP against {comp_txt}, Holm over the {ntests} tests of the table; "
      "† = not significant (Holm-adjusted p ≥ 0.05); bold = best mean of the row.", ""]
if not complete:
    md += ["**INCOMPLETE: some cells have fewer than 30 seeds (see the counts below). Do not quote these numbers.**", ""]
md += ["## Runs per trace and technique (seeds)", "",
       "| trace | " + " | ".join(COLS) + " |", "|---|" + "---|" * len(COLS)]
for t in TR:
    md.append(f"| {t['label']} | " + " | ".join(
        (f"{len(R[(t['key'], c)])} ({L.compress(R[(t['key'], c)].keys())})" if R.get((t["key"], c)) else "0")
        for c in COLS) + " |")
if excluded or incomplete_runs:
    md += ["", f"Excluded runs: {len(excluded)} (not the intended configuration), {len(incomplete_runs)} "
           "(simulation did not reach 86 400 s or result unreadable):", ""]
    md += [f"- {f}: {'; '.join(w)}" for f, w in excluded[:40]] + [f"- {f}: incomplete" for f in incomplete_runs[:40]]
for t in TR:
    md += ["", f"## {t['label']} (`{t['folder']}`)", "", "| metric | " + " | ".join(COLS) + " |",
           "|---|" + "---|" * len(COLS)]
    for key, _, d in ROWS:
        b = best(t["key"], key, d)
        md.append(f"| {MDLAB[key]} | " + " | ".join(md_cell(t["key"], c, key, d, b) for c in COLS) + " |")
    rg = RANGES[t["key"]]
    if rg:
        md += ["", "WBP with respect to MU, MMT, RS and MC (reduction in %, positive = WBP lower; absolute "
               "difference WBP − X):", ""]
        for key in ("migr", "traffic", "e_total", "e_hosts", "sla"):
            x = rg[key]
            d = {k: dd for k, _, dd in ROWS}[key]
            md.append(f"- {MDLAB[key]}: {x['lo']:.1f} % to {x['hi']:.1f} % ("
                      + ", ".join(f"{c} {v:.1f}" for c, v in x["per"].items())
                      + f"); WBP − X from {x['abs_lo']:+.{d}f} to {x['abs_hi']:+.{d}f}")
md += ["", "## Paired tests", "", "| trace | WBP vs | metric | n | mean(WBP − X) | raw p | Holm p | significant |",
       "|---|---|---|---|---|---|---|---|"]
for x in TESTS:
    md.append(f"| {M.TRACE_BY_EXP['mt_' + x['trace']]['label']} | {x['opp']} | {x['key']} | {x['n']} | "
              f"{x['mean_diff']:.4g} | {x['p']:.3g} | {x['p_holm']:.3g} | {'yes' if x['p_holm'] < 0.05 else 'no'} |")
with open(os.path.join(a.outdir, "more_traces.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(md) + "\n")

head = " & ".join("\\textbf{" + ("\\textit{WBP}" if c == "WBP" else CITE.get(c, c)) + "}" for c in COLS)
cap = (r"Robustness check on four traces not used in the other experiments: the first day of Materna traces 2 "
       r"and 3 (4 December 2015 and 4 January 2016) and days 5 and 8 of the Alibaba trace. Each one is the "
       r"subset of 100 VMs with the largest accumulated absolute change of CPU utilization over the simulated "
       r"day, the rule that selected the Materna and Alibaba traces of "
       r"Tables~\ref{tab:materna_results_unified} and~\ref{tab:alibaba_results_unified}; every technique keeps "
       r"the configuration of those tables" + (r" and of Table~\ref{tab:sota_reproduction}" if "AMOVMC" in COLS else "")
       + r", and only the trace changes. Mean $\pm$ 95\% CI over the 30 seeds; migration "
       r"energy computed with $\kappa=0.512$~J per MB and hop. Bold: best mean of the row. $^{\dagger}$: "
       r"difference with respect to \textit{WBP} not statistically significant (Wilcoxon signed-rank test on the "
       r"30 seed-paired runs, Holm-adjusted $p\geq0.05$ over the " + f"{ntests}" + r" tests of this table"
       + (r"; only MU, MMT, RS and MC are tested)." if a.competitors == "classical" else r").") )
tex = ["% Generated by experiments/tools/mt_build_table.py -- do not edit by hand.",
       "% kappa = 0.512 J/(MB.hop), beta = 20.165 J/migration, migration traffic counted once."]
if not complete:
    tex.append("% WARNING: INCOMPLETE -- some cells have fewer than 30 seeds; do not use.")
tex += [r"\begin{table*}[!ht]", r"\centering", r"\caption{" + cap + "}", r"\label{tab:more_traces}",
        r"\begin{adjustbox}{width=0.98\textwidth}", r"\begin{tabular}{ll" + "r" * len(COLS) + "}", r"\hline",
        r"Trace & Metric & " + head + r" \\", r"\hline"]
for t in TR:
    for i, (key, lab, d) in enumerate(ROWS):
        b = best(t["key"], key, d)
        tex.append(f"{t['label'] if i == 0 else ''} & {lab} & "
                   + " & ".join(tex_cell(t["key"], c, key, d, b) for c in COLS) + r" \\")
    tex.append(r"\hline")
tex += [r"\end{tabular}", r"\end{adjustbox}", r"\end{table*}"]
with open(os.path.join(a.outdir, "tab_more_traces.tex"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(tex) + "\n")

with open(os.path.join(a.outdir, "more_traces.json"), "w", encoding="utf-8") as fh:
    json.dump(dict(columns=COLS, competitors=COMP, complete=complete, n_tests=ntests,
                   agg={f"{k[0]}/{k[1]}/{k[2]}": v for k, v in AGG.items()}, tests=TESTS, ranges=RANGES,
                   excluded=excluded, incomplete=incomplete_runs), fh, indent=1)

# ------------------------------------------------------------------------------------------ print
print(f"runs used: {sum(len(v) for v in R.values())}; columns: {len(COLS)}; tests: {ntests}, significant after Holm: "
      f"{sum(1 for x in TESTS if x['p_holm'] < 0.05)}; excluded: {len(excluded)}; incomplete: {len(incomplete_runs)}; "
      f"complete table: {complete}")
for t in TR:
    rg = RANGES[t["key"]]
    if not rg:
        print(f"{t['label']}: WBP or a classical policy missing, no ranges")
        continue
    print(f"{t['label']}: WBP vs MU/MMT/RS/MC: migrations {rg['migr']['lo']:.1f} % to {rg['migr']['hi']:.1f} % lower; "
          f"migration traffic {rg['traffic']['lo']:.1f} % to {rg['traffic']['hi']:.1f} % lower; total energy "
          f"{rg['e_total']['lo']:.1f} % to {rg['e_total']['hi']:.1f} % lower (WBP - X {rg['e_total']['abs_lo']:+.2f} to "
          f"{rg['e_total']['abs_hi']:+.2f} kWh)")
print("written:", ", ".join(os.path.join(a.outdir, f) for f in ("more_traces.md", "tab_more_traces.tex", "more_traces.json")))
if a.require_complete and not complete:
    sys.exit(3)
