#!/usr/bin/env python3
"""Builds every result table of the revised manuscript from the cached raw runs.

Read-only on the simulation outputs: it only reads <cache>/runs.jsonl (one record per
simulation, written by extract_runs.py) and writes under <out>.

Usage:
  python -B build_revision.py --cache cache --out out [--kappa 0.512] [--beta 20.165]

Outputs:
  <out>/tables/*.tex     tables \\input by the manuscript
  <out>/facts.json       every aggregate used in the text (means, CIs, derived percentages)
  <out>/facts.md         the same, readable
  <out>/stats.md         all paired tests with raw and Holm-adjusted p-values
"""
import argparse
import json
import math
import os

import numpy as np
from scipy import stats

import revlib as L

ap = argparse.ArgumentParser()
ap.add_argument("--cache", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--kappa", type=float, default=L.KAPPA_REF)
ap.add_argument("--beta", type=float, default=L.BETA)
ap.add_argument("--extra-cache", default=None,
                help="cache with the additional (revision) runs: closed-loop variants, sensitivity")
a = ap.parse_args()
KAPPA, BETA = a.kappa, a.beta
os.makedirs(os.path.join(a.out, "tables"), exist_ok=True)

# key, LaTeX label, decimals, direction of "better" (None = no ranking)
ROWS = [
    ("e_hosts", r"Host energy (kWh)", 2, "min"),
    ("e_mig", r"Migration energy (kWh)", 2, "min"),
    ("e_total", r"Total energy (kWh)", 2, "min"),
    ("act_hosts", r"Mean active hosts", 2, None),
    ("sla", r"SLA violation (\%)", 2, "min"),
    ("migr", r"\# of migrations", 0, "min"),
    ("traffic", r"Migration traffic (GB$\cdot$hop)", 0, "min"),
    ("me", r"ME ratio ($\times10^7$)", 2, "max"),
    ("avmips", r"Avg.\ available MIPS/active host", 0, None),
    ("vmcomm", r"Inter-VM link load ($\times10^5$)", 2, "min"),
]
ROWKEYS = [k for k, _, _, _ in ROWS]
CLASSICAL = ["MU", "MMT", "RS", "MC"]
MAIN_T = L.MAIN_T            # MU MMT RS MC WPSP WP WBP
SOTA_T = L.SOTA_T            # WBP BB+NeoPro AMOVMC EUQ-VMC
COMPETITORS = ["MU", "MMT", "RS", "MC", "WPSP", "WP", "BB+NeoPro", "AMOVMC", "EUQ-VMC"]

runs, _ = L.load_cache(a.cache)
TR = {wl: L.collect_table_runs(runs, wl) for wl in L.WLS}


def by_pair(rs):
    d = {}
    for r in rs:
        k = L.pair_key(r)
        assert k not in d, ("duplicate pair key", k)
        d[k] = r
    return d


def values(rs, key, kappa=None):
    kappa = KAPPA if kappa is None else kappa
    return [L.metrics_rev(r, kappa, BETA)[key] for r in rs]


def aggregate(wl, rs, key, kappa=None):
    """Mean and 95% CI half-width.  PlanetLab: the unit of replication is the daily trace
    (10 trace means, t with 9 d.o.f.); other workloads: the 30 seeds."""
    kappa = KAPPA if kappa is None else kappa
    if wl == "planetlab":
        per_day = {}
        for r in rs:
            per_day.setdefault(L.trace_day(r), []).append(L.metrics_rev(r, kappa, BETA)[key])
        means = [float(np.mean(v)) for _, v in sorted(per_day.items())]
        n, m, sd, ci = L.mean_ci(means)
        return dict(mean=m, ci=ci, n_units=n, n_runs=len(rs), unit="trace")
    n, m, sd, ci = L.mean_ci(values(rs, key, kappa))
    return dict(mean=m, ci=ci, n_units=n, n_runs=len(rs), unit="seed")


def paired_test(wl, rs_a, rs_b, key):
    """WBP (a) vs competitor (b).  PlanetLab: paired t-test on the 10 per-trace means
    (each the average of 30 seeds).  Other workloads: Wilcoxon signed-rank on the 30
    seed-paired runs."""
    A, B = by_pair(rs_a), by_pair(rs_b)
    keys = sorted(set(A) & set(B), key=lambda k: (str(k[0]), int(k[1])))
    xa = np.array([L.metrics_rev(A[k], KAPPA, BETA)[key] for k in keys], float)
    xb = np.array([L.metrics_rev(B[k], KAPPA, BETA)[key] for k in keys], float)
    if wl == "planetlab":
        days = sorted({k[0] for k in keys})
        ma = np.array([xa[[i for i, k in enumerate(keys) if k[0] == d]].mean() for d in days])
        mb = np.array([xb[[i for i, k in enumerate(keys) if k[0] == d]].mean() for d in days])
        d = ma - mb
        if np.allclose(d, 0):
            p = 1.0
        else:
            p = float(stats.ttest_rel(ma, mb).pvalue)
        # run-level Wilcoxon kept for reference only
        p_run = float(stats.wilcoxon(xa, xb).pvalue) if np.any(xa != xb) else 1.0
        return dict(test="paired t (10 trace means)", n=len(days), p=p, p_run_level=p_run,
                    mean_diff=float(d.mean()), same_sign=int(max((d < 0).sum(), (d > 0).sum())))
    d = xa - xb
    if not np.any(d != 0):
        p = 1.0
    else:
        p = float(stats.wilcoxon(xa, xb).pvalue)
    return dict(test="Wilcoxon signed-rank (30 seeds)", n=len(keys), p=p, p_run_level=p,
                mean_diff=float(d.mean()), same_sign=int(max((d < 0).sum(), (d > 0).sum())))


# ----------------------------------------------------------------------------- aggregates
AGG = {wl: {t: {k: aggregate(wl, TR[wl][t], k) for k in ROWKEYS + ["e_exec", "e_on", "e_off",
                                                                  "e_onoff", "ram_moved", "hops",
                                                                  "esv", "hosts_acc"]}
            for t in L.ALL_T} for wl in L.WLS}

# ----------------------------------------------------------------------------- tests
TESTS = []
for wl in L.WLS:
    for opp in COMPETITORS:
        for k in ROWKEYS:
            t = paired_test(wl, TR[wl]["WBP"], TR[wl][opp], k)
            t.update(wl=wl, opp=opp, key=k)
            TESTS.append(t)
adj = L.holm([t["p"] for t in TESTS])
for t, p_adj in zip(TESTS, adj):
    t["p_holm"] = float(p_adj)
SIG = {(t["wl"], t["opp"], t["key"]): t["p_holm"] < 0.05 for t in TESTS}
NTESTS = len(TESTS)


# ----------------------------------------------------------------------------- LaTeX cells
def fmt(x, d):
    return f"{x:.{d}f}"


def cell(wl, t, key, d, best, mark_ns):
    g = AGG[wl][t][key]
    body = f"{fmt(g['mean'], d)}\\,$\\pm$\\,{fmt(g['ci'], d)}"
    if best:
        body = "\\textbf{" + body + "}"
    if mark_ns:
        body += "$^{\\dagger}$"
    return body


def best_of(wl, techs, key, direction, d):
    """Techniques whose mean, at the printed precision, equals the best mean."""
    if direction is None:
        return set()
    vals = {t: round(AGG[wl][t][key]["mean"], d) for t in techs}
    target = min(vals.values()) if direction == "min" else max(vals.values())
    return {t for t, v in vals.items() if v == target}


def table_rows(wl, techs):
    out = []
    for key, label, d, direction in ROWS:
        b = best_of(wl, techs, key, direction, d)
        cells = []
        for t in techs:
            ns = (t != "WBP") and not SIG[(wl, t, key)]
            cells.append(cell(wl, t, key, d, t in b, ns))
        out.append(f"  {label} & " + " & ".join(cells) + r" \\")
    return out


NOTE = (r"Bold: best mean of the row (no ranking for rows without a single preferred direction). "
        r"$^{\dagger}$: difference with respect to \textit{WBP} not statistically significant "
        r"(Holm-adjusted $p\geq0.05$).")
WLCAP = {
    "planetlab": ("PlanetLab", "mean $\\pm$ 95\\% CI over the 10 daily traces (each the average of 30 seeds; 300 runs per technique)"),
    "alibaba": ("Alibaba", "mean $\\pm$ 95\\% CI over the 30 seeds"),
    "materna": ("Materna", "mean $\\pm$ 95\\% CI over the 30 seeds"),
    "azure": ("Microsoft Azure", "mean $\\pm$ 95\\% CI over the 30 seeds"),
}


def write(name, lines):
    p = os.path.join(a.out, "tables", name)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("% Generated by analysis/build_revision.py -- do not edit by hand.\n")
        fh.write(f"% kappa = {KAPPA} J/(MB.hop), beta = {BETA} J/migration, migration traffic counted once.\n")
        fh.write("\n".join(lines) + "\n")


for wl in L.WLS:
    name, how = WLCAP[wl]
    head = " & ".join("\\textbf{" + (("\\textit{WBP}") if t == "WBP" else t) + "}" for t in MAIN_T)
    lines = [r"\begin{table*}[!ht]", r"  \centering",
             f"  \\caption{{{name} results: {how}. Migration energy computed with "
             f"$\\kappa={KAPPA}$~J per MB and hop. {NOTE}}}",
             f"  \\label{{tab:{wl}_results_unified}}",
             r"  \begin{adjustbox}{width=0.98\textwidth}",
             r"  \begin{tabular}{lrrrrrrr}", r"  \hline",
             r"  \multicolumn{1}{r}{} & " + head + r" \\", r"  \hline"]
    lines += table_rows(wl, MAIN_T)
    lines += [r"  \hline", r"  \end{tabular}", r"  \end{adjustbox}", r"\end{table*}"]
    write(f"tab_{wl}.tex", lines)

# SOTA table
lines = [r"\begin{table*}[!ht]", r"\centering",
         r"\caption{Comparison with recent consolidation methods under the shared placement stage "
         r"(controlled component comparison). PlanetLab: mean $\pm$ 95\% CI over the 10 daily traces; "
         f"other workloads: over the 30 seeds. Migration energy computed with $\\kappa={KAPPA}$~J per MB and hop. "
         + NOTE + "}",
         r"\label{tab:sota_reproduction}",
         r"\begin{adjustbox}{width=0.98\textwidth}", r"\begin{tabular}{lrrrr}", r"\hline",
         r"\textbf{Metric} & \textbf{\textit{WBP} (this work)} & \textbf{BB+NeoPro~\cite{VILA2023321}} & "
         r"\textbf{AMOVMC~\cite{goyal2025amovmc}} & \textbf{EUQ-VMC~\cite{li2025euqvmc}} \\", r"\hline"]
for wl in L.WLS:
    lines.append(f"\\multicolumn{{5}}{{l}}{{\\textbf{{{WLCAP[wl][0]}}}}} \\\\")
    lines += [x.strip() for x in table_rows(wl, SOTA_T)]
    lines.append(r"\hline")
lines += [r"\end{tabular}", r"\end{adjustbox}", r"\end{table*}"]
write("tab_sota.tex", lines)

# ----------------------------------------------------------------------------- energy components
lines = [r"\begin{table*}[!ht]", r"\centering",
         r"\caption{Energy components (kWh, mean over the runs of each technique). Execution: energy of the "
         r"active hosts under load; switch-on/off: start-up and shutdown transitions; migration: "
         f"Eq.~\\eqref{{eq:e_mig3}} with $\\kappa={KAPPA}$~J per MB and hop. The last row of each block is the "
         r"share of the migration term in the total.}",
         r"\label{tab:energy_components}",
         r"\begin{adjustbox}{width=0.9\textwidth}", r"\begin{tabular}{llrrrrrrr}", r"\hline",
         r"Workload & Component & " + " & ".join("\\textbf{" + (("\\textit{WBP}") if t == "WBP" else t) + "}" for t in MAIN_T) + r" \\",
         r"\hline"]
for wl in L.WLS:
    for i, (key, lab) in enumerate([("e_exec", "Execution"), ("e_onoff", "Switch-on/off"),
                                    ("e_mig", "Migration"), ("e_total", "Total")]):
        first = WLCAP[wl][0] if i == 0 else ""
        lines.append(f"{first} & {lab} & " + " & ".join(fmt(AGG[wl][t][key]['mean'], 2) for t in MAIN_T) + r" \\")
    lines.append(" & Migration share (\\%) & " + " & ".join(
        fmt(100 * AGG[wl][t]["e_mig"]["mean"] / AGG[wl][t]["e_total"]["mean"], 1) for t in MAIN_T) + r" \\")
    lines.append(r"\hline")
lines += [r"\end{tabular}", r"\end{adjustbox}", r"\end{table*}"]
write("tab_energy_components.tex", lines)

# ----------------------------------------------------------------------------- kappa sensitivity
KAPPAS = [0.0, 0.512, 1.0, 2.0, L.KAPPA_SIMULATOR, L.KAPPA_SUBMITTED]


def mean_total(wl, t, kappa):
    return aggregate(wl, TR[wl][t], "e_total", kappa)["mean"]


SENS = {}
for wl in L.WLS:
    SENS[wl] = {}
    for kp in KAPPAS:
        w = mean_total(wl, "WBP", kp)
        sav = {t: 100.0 * (1 - w / mean_total(wl, t, kp)) for t in CLASSICAL}
        SENS[wl][kp] = dict(wbp=w, saving=sav, lo=min(sav.values()), hi=max(sav.values()),
                            wp=mean_total(wl, "WP", kp), wpsp=mean_total(wl, "WPSP", kp))
    # break-even kappa against each classical technique:
    # E_hosts(WBP) + (k*T_wbp + b*N_wbp)/3.6e6 = E_hosts(X) + (k*T_x + b*N_x)/3.6e6
    be = {}
    for t in CLASSICAL:
        eh_w, eh_x = AGG[wl]["WBP"]["e_hosts"]["mean"], AGG[wl][t]["e_hosts"]["mean"]
        tw = np.mean([L.traffic_single(r) for r in TR[wl]["WBP"]])
        tx = np.mean([L.traffic_single(r) for r in TR[wl][t]])
        nw = np.mean([L.n_mig_net(r) for r in TR[wl]["WBP"]])
        nx = np.mean([L.n_mig_net(r) for r in TR[wl][t]])
        if wl == "planetlab":   # same weighting as the trace-level means (balanced design)
            pass
        be[t] = ((eh_w - eh_x) * 3.6e6 - BETA * (nx - nw)) / (tx - tw)
    SENS[wl]["breakeven"] = be

lines = [r"\begin{table}[!ht]", r"\centering",
         r"\caption{Sensitivity of the total-energy difference between \textit{WBP} and the classical techniques "
         r"(MU, MMT, RS, MC) to the migration-energy coefficient $\kappa$ (J per MB and hop). Cells: range of the "
         r"saving of \textit{WBP}, in \%, over the four classical techniques (negative: \textit{WBP} consumes more). "
         r"Last rows: value of $\kappa$ above which \textit{WBP} consumes less than at least one classical technique "
         r"and less than the four of them.}",
         r"\label{tab:kappa_sensitivity}",
         r"\begin{adjustbox}{width=\columnwidth}", r"\begin{tabular}{lrrrr}", r"\hline",
         r"$\kappa$ & PlanetLab & Alibaba & Materna & Azure \\", r"\hline"]
KLAB = {0.0: r"0 (host energy only)", 0.512: r"0.512 (reference)", 1.0: "1.0", 2.0: "2.0",
        L.KAPPA_SIMULATOR: r"3.549 (Sarji et al.)", L.KAPPA_SUBMITTED: r"4.096 (previous version)"}
for kp in KAPPAS:
    lines.append(f"{KLAB[kp]} & " + " & ".join(
        f"{SENS[wl][kp]['lo']:.1f} to {SENS[wl][kp]['hi']:.1f}" for wl in L.WLS) + r" \\")
lines.append(r"\hline")
lines.append(r"Break-even (at least one) & " + " & ".join(
    (f"{max(0.0, min(SENS[wl]['breakeven'].values())):.2f}") for wl in L.WLS) + r" \\")
lines.append(r"Break-even (all four) & " + " & ".join(
    (f"{max(0.0, max(SENS[wl]['breakeven'].values())):.2f}") for wl in L.WLS) + r" \\")
lines += [r"\hline", r"\end{tabular}", r"\end{adjustbox}", r"\end{table}"]
write("tab_kappa_sensitivity.tex", lines)

# ----------------------------------------------------------------------------- run inventory
INV = {}
for wl in L.WLS:
    for t in L.ALL_T:
        rs = TR[wl][t]
        days = sorted({L.trace_day(r) for r in rs if L.trace_day(r)})
        seeds = sorted({int(r.get("cfg_randomSeed")) for r in rs})
        INV[(wl, t)] = dict(n=len(rs), traces=max(1, len(days)), seeds=len(seeds),
                            seed_range=L.compress(seeds))
lines = [r"\begin{table}[!ht]", r"\centering",
         r"\caption{Simulations behind each table: traces $\times$ seeds per technique and workload.}",
         r"\label{tab:runs}",
         r"\begin{adjustbox}{width=\columnwidth}", r"\begin{tabular}{lrrrrr}", r"\hline",
         r"Technique & PlanetLab & Alibaba & Materna & Azure & Runs \\", r"\hline"]
tot_main = tot_all = 0
for t in L.ALL_T:
    cells = []
    n_t = 0
    for wl in L.WLS:
        i = INV[(wl, t)]
        cells.append(f"{i['traces']}$\\times${i['seeds']}")
        n_t += i["n"]
    name = "\\textit{WBP}" if t == "WBP" else t
    lines.append(f"{name} & " + " & ".join(cells) + f" & {n_t} \\\\")
    tot_all += n_t
    if t in MAIN_T:
        tot_main += n_t
    if t == "WBP":
        lines.append(r"\hline")
        lines.append(f"\\multicolumn{{5}}{{l}}{{Tables~\\ref{{tab:planetlab_results_unified}}--\\ref{{tab:azure_results_unified}}}} & {tot_main} \\\\")
        lines.append(r"\hline")
lines.append(r"\hline")
lines.append(f"\\multicolumn{{5}}{{l}}{{All (with Table~\\ref{{tab:sota_reproduction}})}} & {tot_all} \\\\")
lines += [r"\hline", r"\end{tabular}", r"\end{adjustbox}", r"\end{table}"]
write("tab_runs.tex", lines)

# ----------------------------------------------------------------------------- native placement / tuning
byf = {}
for r in runs:
    byf.setdefault(r["folder"], []).append(r)


def folder_runs(prefix_list):
    out = []
    for f in prefix_list:
        out += byf.get(f, [])
    return out


NATIVE = {}
for wl in L.WLS:
    if wl == "planetlab":
        fa = [f"amovmc_native_pl_{d}" for d in L.DAYS]
        fe = [f"euqvmc_native_pl_{d}" for d in L.DAYS]
    else:
        fa, fe = [f"amovmc_native_{wl}"], [f"euqvmc_native_{wl}"]
    NATIVE[wl] = {"AMOVMC (native)": folder_runs(fa), "EUQ-VMC (native)": folder_runs(fe)}

NKEYS = [("e_total", "Total energy (kWh)", 2), ("sla", r"SLA (\%)", 2), ("migr", r"\# migr.", 0),
         ("traffic", r"Traffic (GB$\cdot$hop)", 0), ("esv", r"E$\times$SLA", 1)]
lines = [r"\begin{table*}[!ht]", r"\centering",
         r"\caption{AMOVMC and EUQ-VMC with the shared placement stage of Table~\ref{tab:sota_reproduction} and with "
         r"their own (native) placement stage, against \textit{WBP} and BB+NeoPro. E$\times$SLA is the product of total energy (kWh) "
         r"and SLA violation (\%), the combined criterion used by those methods (lower is better). Mean $\pm$ 95\% CI "
         r"(PlanetLab: over the 10 daily traces; others: over the 30 seeds).}",
         r"\label{tab:sota_native}",
         r"\begin{adjustbox}{width=0.9\textwidth}", r"\begin{tabular}{llrrrrr}", r"\hline",
         r"Workload & Method & " + " & ".join(lab for _, lab, _ in NKEYS) + r" \\", r"\hline"]
NAT_AGG = {}
for wl in L.WLS:
    rowsets = [("\\textit{WBP}", TR[wl]["WBP"]), ("BB+NeoPro", TR[wl]["BB+NeoPro"]),
               ("AMOVMC (shared)", TR[wl]["AMOVMC"]),
               ("AMOVMC (native)", NATIVE[wl]["AMOVMC (native)"]),
               ("EUQ-VMC (shared)", TR[wl]["EUQ-VMC"]),
               ("EUQ-VMC (native)", NATIVE[wl]["EUQ-VMC (native)"])]
    for i, (lab, rs) in enumerate(rowsets):
        first = WLCAP[wl][0] if i == 0 else ""
        cells = []
        for key, _, d in NKEYS:
            g = aggregate(wl, rs, key)
            NAT_AGG[(wl, lab, key)] = g
            cells.append(f"{fmt(g['mean'], d)}\\,$\\pm$\\,{fmt(g['ci'], d)}")
        lines.append(f"{first} & {lab} & " + " & ".join(cells) + r" \\")
    lines.append(r"\hline")
lines += [r"\end{tabular}", r"\end{adjustbox}", r"\end{table*}"]
write("tab_sota_native.tex", lines)

# tuning sweeps (one PlanetLab day)
TUNE = {}
for f in sorted(byf):
    if f.startswith("amovmc_tune_") or f.startswith("euqvmc_tune_"):
        rs = byf[f]
        r0 = rs[0]
        TUNE[f] = dict(n=len(rs), trace=r0.get("cfg_workloadTrace"), parameter=r0.get("cfg_parameter"),
                       hos=r0.get("cfg_hostOverSaturationPolicy"), mig=r0.get("cfg_vmMigrationPolicy"),
                       techcfg=r0.get("cfg_techniquesConfiguration"),
                       **{k: float(np.mean(values(rs, k))) for k in ["e_total", "e_hosts", "sla", "migr", "traffic", "esv"]})

# reference points on the same PlanetLab day as the sweeps (default parameters, shared placement)
TUNE_DAY = "20110303"
TUNE_REF = {}
for t in ["WBP", "WP", "AMOVMC", "EUQ-VMC"]:
    rs = [r for r in TR["planetlab"][t] if L.trace_day(r) == TUNE_DAY]
    TUNE_REF[t] = dict(n=len(rs), parameter=rs[0].get("cfg_parameter") if rs else None,
                       techcfg=rs[0].get("cfg_techniquesConfiguration") if rs else None,
                       **{k: float(np.mean(values(rs, k))) for k in ["e_total", "e_hosts", "sla", "migr", "traffic", "esv"]})

TKEYS = [("e_total", "Total energy (kWh)", 2), ("sla", r"SLA (\%)", 2), ("migr", r"\# migr.", 0),
         ("traffic", r"Traffic (GB$\cdot$hop)", 0), ("esv", r"E$\times$SLA", 1)]
lines = [r"\begin{table*}[!ht]", r"\centering",
         r"\caption{Parameter sweeps of AMOVMC and EUQ-VMC with the shared placement on one PlanetLab day "
         r"(3 March 2011, 30 seeds per value; mean). The rows marked \emph{table} are the settings used in "
         r"Table~\ref{tab:sota_reproduction}; \textit{WBP} on the same day is given for reference.}",
         r"\label{tab:sota_tuning}",
         r"\begin{adjustbox}{max width=0.8\textwidth}", r"\begin{tabular}{lrrrrr}", r"\hline",
         r"Method (parameter) & " + " & ".join(lab for _, lab, _ in TKEYS) + r" \\", r"\hline"]


def trow(label, v):
    return f"{label} & " + " & ".join(fmt(v[k], d) for k, _, d in TKEYS) + r" \\"


lines.append(trow("\\textit{WBP}", TUNE_REF["WBP"]))
lines.append(r"\hline")
# AMOVMC: the swept knob is the performance level gamma of its overload test; the table runs use
# the built-in gamma = 0.80 (their `parameter` field is not gamma).  EUQ-VMC: `parameter` is the
# "safe" factor of its overload threshold; the table runs use 1.5.
lines.append(trow("AMOVMC ($\\gamma=0.80$, \\emph{table})", TUNE_REF["AMOVMC"]))
for f in sorted(TUNE):
    if f.startswith("amovmc_tune_"):
        lines.append(trow(f"AMOVMC ($\\gamma={float(TUNE[f]['parameter']):.2f}$)", TUNE[f]))
lines.append(r"\hline")
assert float(TUNE_REF["EUQ-VMC"]["parameter"]) == 1.5
lines.append(trow("EUQ-VMC ($safe=1.5$, \\emph{table})", TUNE_REF["EUQ-VMC"]))
for f in sorted(TUNE, reverse=True):
    if f.startswith("euqvmc_tune_"):
        lines.append(trow(f"EUQ-VMC ($safe={float(TUNE[f]['parameter']):.2f}$)", TUNE[f]))
lines += [r"\hline", r"\end{tabular}", r"\end{adjustbox}", r"\end{table*}"]
write("tab_sota_tuning.tex", lines)


# ----------------------------------------------------------------------------- facts
def pct_red(a_, b_):
    """Reduction of a with respect to b, in %."""
    return 100.0 * (1 - a_ / b_)


FACTS = dict(kappa=KAPPA, beta=BETA, n_tests=NTESTS, agg={}, derived={}, sens={}, native={}, tune=TUNE,
             tune_ref=TUNE_REF, tune_day=TUNE_DAY,
             inventory={f"{wl}/{t}": v for (wl, t), v in INV.items()},
             totals=dict(main=tot_main, all=tot_all))
for wl in L.WLS:
    FACTS["agg"][wl] = {t: {k: dict(mean=AGG[wl][t][k]["mean"], ci=AGG[wl][t][k]["ci"]) for k in AGG[wl][t]}
                        for t in L.ALL_T}
    d = {}
    for key in ["migr", "traffic", "e_total", "e_hosts", "e_mig", "sla"]:
        w = AGG[wl]["WBP"][key]["mean"]
        red = {t: pct_red(w, AGG[wl][t][key]["mean"]) for t in CLASSICAL}
        d[f"WBP_vs_classical_{key}"] = dict(lo=min(red.values()), hi=max(red.values()), per=red)
        wp = AGG[wl]["WP"][key]["mean"]
        redp = {t: pct_red(wp, AGG[wl][t][key]["mean"]) for t in CLASSICAL}
        d[f"WP_vs_classical_{key}"] = dict(lo=min(redp.values()), hi=max(redp.values()), per=redp)
        for opp in ["WP", "WPSP", "BB+NeoPro", "AMOVMC", "EUQ-VMC"]:
            d[f"WBP_vs_{opp}_{key}"] = pct_red(w, AGG[wl][opp][key]["mean"])
    for key, _, dd, direction in ROWS:
        order = sorted(MAIN_T, key=lambda t: AGG[wl][t][key]["mean"])
        d[f"order_{key}"] = order
    FACTS["derived"][wl] = d
    FACTS["sens"][wl] = {str(kp): SENS[wl][kp] for kp in KAPPAS}
    FACTS["sens"][wl]["breakeven"] = SENS[wl]["breakeven"]
    FACTS["native"][wl] = {lab: {key: NAT_AGG[(wl, lab, key)]["mean"] for key, _, _ in NKEYS}
                           for lab in ["\\textit{WBP}", "BB+NeoPro", "AMOVMC (shared)", "AMOVMC (native)",
                                       "EUQ-VMC (shared)", "EUQ-VMC (native)"]}
FACTS["tests"] = TESTS
json.dump(FACTS, open(os.path.join(a.out, "facts.json"), "w", encoding="utf-8"), indent=1, default=float)

# ----------------------------------------------------------------------------- readable reports
md = [f"# Facts for the revised text (kappa = {KAPPA} J/(MB.hop), beta = {BETA} J/migration)", ""]
for wl in L.WLS:
    md.append(f"## {WLCAP[wl][0]}")
    md.append("| metric | " + " | ".join(L.ALL_T) + " |")
    md.append("|---|" + "---|" * len(L.ALL_T))
    for key, label, d, _ in ROWS + [("e_exec", "exec", 2, None), ("e_onoff", "on/off", 2, None),
                                    ("ram_moved", "RAM moved GB", 0, None), ("hops", "mean hops", 2, None),
                                    ("esv", "ExSLA", 1, None)]:
        md.append(f"| {key} | " + " | ".join(
            f"{AGG[wl][t][key]['mean']:.{d}f} ± {AGG[wl][t][key]['ci']:.{d}f}" for t in L.ALL_T) + " |")
    dv = FACTS["derived"][wl]
    md.append("")
    for key in ["migr", "traffic", "e_total", "e_hosts", "e_mig", "sla"]:
        x = dv[f"WBP_vs_classical_{key}"]
        y = dv[f"WP_vs_classical_{key}"]
        md.append(f"- WBP vs classical, {key}: {x['lo']:.1f} % to {x['hi']:.1f} % lower "
                  f"({', '.join(f'{t} {v:.1f}' for t, v in x['per'].items())}); WP: {y['lo']:.1f} to {y['hi']:.1f}")
    for opp in ["WP", "WPSP", "BB+NeoPro", "AMOVMC", "EUQ-VMC"]:
        md.append(f"- WBP vs {opp}: " + ", ".join(
            f"{key} {dv[f'WBP_vs_{opp}_{key}']:+.1f} %" for key in ["migr", "traffic", "e_total", "e_hosts", "sla"])
            + "  (positive = WBP lower)")
    for key, _, _, direction in ROWS:
        md.append(f"- order {key} (ascending): {' < '.join(dv[f'order_{key}'])}")
    md.append("- kappa sensitivity (saving of WBP vs classical, %): " + "; ".join(
        f"k={kp:g}: {SENS[wl][kp]['lo']:.1f}..{SENS[wl][kp]['hi']:.1f}" for kp in KAPPAS))
    md.append("- break-even kappa per classical: " + ", ".join(
        f"{t} {v:.3f}" for t, v in SENS[wl]["breakeven"].items()))
    md.append("")
md.append("## Tuning sweeps")
for f, v in TUNE.items():
    md.append(f"- {f}: n={v['n']} trace={v['trace']} param={v['parameter']} hos={v['hos']} mig={v['mig']} "
              f"cfg={v['techcfg']} | E_total={v['e_total']:.2f} E_hosts={v['e_hosts']:.2f} SLA={v['sla']:.2f} "
              f"migr={v['migr']:.0f} traffic={v['traffic']:.0f} ExSLA={v['esv']:.1f}")
md.append("")
md.append(f"## Reference points on PlanetLab day {TUNE_DAY} (default parameters, shared placement)")
for t, v in TUNE_REF.items():
    md.append(f"- {t}: n={v['n']} param={v['parameter']} cfg={v['techcfg']} | E_total={v['e_total']:.2f} "
              f"E_hosts={v['e_hosts']:.2f} SLA={v['sla']:.2f} migr={v['migr']:.0f} traffic={v['traffic']:.0f} "
              f"ExSLA={v['esv']:.1f}")
md.append("")
md.append("## Significance of WBP vs X after Holm (S = significant, - = not), metrics: "
          "e_hosts e_total sla migr traffic act_hosts")
for wl in L.WLS:
    for opp in COMPETITORS:
        flags = " ".join(("S" if SIG[(wl, opp, k)] else "-") for k in
                         ["e_hosts", "e_total", "sla", "migr", "traffic", "act_hosts"])
        md.append(f"- {wl:9} WBP vs {opp:9}: {flags}")
md.append("")
md.append(f"## Inventory: main tables {tot_main} runs; with SOTA table {tot_all} runs")
open(os.path.join(a.out, "facts.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")

st = [f"# Paired tests, WBP vs each competitor ({NTESTS} tests, Holm-adjusted over the whole family)", "",
      "PlanetLab: paired t-test on the 10 per-trace means (run-level Wilcoxon, n = 300, shown for reference). "
      "Other workloads: Wilcoxon signed-rank on the 30 seed-paired runs.", "",
      "| workload | competitor | metric | n | mean(WBP − X) | raw p | Holm p | significant | run-level p (ref.) |",
      "|---|---|---|---|---|---|---|---|---|"]
for t in TESTS:
    st.append(f"| {t['wl']} | {t['opp']} | {t['key']} | {t['n']} | {t['mean_diff']:.4g} | {t['p']:.3g} | "
              f"{t['p_holm']:.3g} | {'yes' if t['p_holm'] < 0.05 else 'no'} | {t['p_run_level']:.3g} |")
open(os.path.join(a.out, "stats.md"), "w", encoding="utf-8").write("\n".join(st) + "\n")

nsig = sum(1 for t in TESTS if t["p_holm"] < 0.05)
print(f"tables written to {os.path.join(a.out, 'tables')}; tests: {NTESTS}, significant after Holm: {nsig}")
print(f"runs: main tables {tot_main}, all {tot_all}")
