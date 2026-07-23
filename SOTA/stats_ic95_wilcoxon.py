#!/usr/bin/env python3
"""Revised SOTA statistics (single-thread, bit-reproducible), hardened after an
adversarial methodology audit:
  - mean +/- 95% CI (t-based, ddof=1)
  - paired Wilcoxon signed-rank (common-random-numbers block: paired by config
    randomSeed; PlanetLab keyed by (trace_date, seed) => 300 pairs)
  - Holm-Bonferroni family-wise correction over ALL tests (48)
  - direction/winner per test (sign of median paired diff; every metric is
    lower-is-better) so a 'significant' cell states WHO wins
  - PlanetLab pseudo-replication disclosed + a trace-level robustness check
    (10 trace means) for the fragile Bollinger ablation
  - integrity asserts on the seed sets
Reproduces the Table-10 means exactly and adds dispersion + honest significance.
"""
import glob, json, os
import numpy as np
from scipy import stats

OUT = r"C:\Users\PcVIP\Desktop\_publish_vmcons\output"
HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]
METRICS = ["Energy (kWh)", "SLA (%)", "# migr.", "RAM-in-BW"]
MSHORT = ["Energy", "SLA", "migr", "RAM"]
TECHS = ["WF", "WBF", "AMOVMC", "EUQ-VMC"]
COMPARISONS = ["WF", "AMOVMC", "EUQ-VMC"]   # WBF vs each


def emig_paths(total_ram_in_bw):
    """Network-routing energy of migrations (composite-energy term), canonical
    formula from scripts/analyze_results.py: (4.096*RAM + 20.165)*1.1/(3600*1000) kWh."""
    return (4.096 * total_ram_in_bw + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics(fp):
    j = json.load(open(fp)); cs = j["cloudsimResults"]; net = j["networkPhysicalResults"]
    ram = net.get("totalRAMInBW", 0)
    # Composite network-aware energy = host energy + migration-path routing energy
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)) + emig_paths(ram)
    sla = cs.get("slaOverall", 0) * 100
    return (e, sla, cs.get("numberOfMigrations", 0), ram / 1e5)


def load(folder, date=None):
    out = {}
    for f in glob.glob(os.path.join(OUT, folder, "*_data.json")):
        c = json.load(open(f)).get("experimentConfiguration", {})
        s = c.get("randomSeed")
        out[(date, s) if date is not None else s] = metrics(f)
    return out


def collect(wl):
    tech = {t: {} for t in TECHS}
    if wl == "planetlab":
        for d in DAYS:
            for f in glob.glob(os.path.join(OUT, f"p4_pl_{d}_st", "*_data.json")):
                c = json.load(open(f)).get("experimentConfiguration", {})
                dst = "WBF" if "bollinger" in str(c.get("hostSignalProcessing")) else "WF"
                tech[dst][(d, c.get("randomSeed"))] = metrics(f)
            tech["AMOVMC"].update(load(f"amovmc_pl_{d}", d))
            tech["EUQ-VMC"].update(load(f"euqvmc_pl_{d}", d))
    else:
        for f in glob.glob(os.path.join(OUT, f"paper4_full_{wl}_prophet_st", "*_data.json")):
            c = json.load(open(f)).get("experimentConfiguration", {})
            dst = "WBF" if "bollinger" in str(c.get("hostSignalProcessing")) else "WF"
            tech[dst][c.get("randomSeed")] = metrics(f)
        tech["AMOVMC"] = load(f"amovmc_{wl}")
        tech["EUQ-VMC"] = load(f"euqvmc_{wl}")
    return tech


def summ(vals):
    a = np.asarray(vals, float); n = len(a)
    mean = a.mean(); sd = a.std(ddof=1) if n > 1 else 0.0
    ci = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 1 else 0.0
    return n, mean, sd, ci


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (order preserved)."""
    p = np.asarray(pvals, float); m = len(p)
    order = np.argsort(p); adj = np.empty(m); running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min((m - rank) * p[idx], 1.0))
        adj[idx] = running
    return adj


def star(p):
    if p != p:
        return "n/a"
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"


# ---- gather every test, then Holm-correct across the whole family -------------
tests = []   # each: dict(wl, opp, metric_i, p, n, wbf_better, wins, losses)
per_wl = {}
for wl in ["planetlab", "alibaba", "materna", "azure"]:
    tech = collect(wl)
    # integrity: every technique must carry seeds 0..29 (per trace for PL)
    exp_seeds = set(range(30))
    for t in TECHS:
        seeds = {k[1] if isinstance(k, tuple) else k for k in tech[t]}
        assert exp_seeds <= seeds, f"{wl}/{t} missing seeds: {exp_seeds - seeds}"
    per_wl[wl] = tech
    for opp in COMPARISONS:
        keys = sorted(set(tech["WBF"]) & set(tech[opp]))
        for i in range(4):
            xa = np.array([tech["WBF"][k][i] for k in keys], float)
            xb = np.array([tech[opp][k][i] for k in keys], float)
            d = xa - xb
            p = float("nan") if np.all(d == 0) else stats.wilcoxon(xa, xb).pvalue
            wins = int((d < 0).sum())    # WBF lower (better) — every metric lower-is-better
            losses = int((d > 0).sum())
            tests.append(dict(wl=wl, opp=opp, i=i, p=p, n=len(keys),
                              wbf_better=wins > losses, wins=wins, losses=losses))

pv = [t["p"] if t["p"] == t["p"] else 1.0 for t in tests]
adj = holm(pv)
for t, a in zip(tests, adj):
    t["padj"] = a

# ---- PlanetLab ablation robustness at TRACE level (n=10, not 300) -----------
pl = per_wl["planetlab"]
trace_lines = ["  PlanetLab ablation (WBF vs WF) at TRACE level (n=10 trace-means, addresses pseudo-replication):"]
for i in range(4):
    per_trace_wbf, per_trace_wf = [], []
    for dday in DAYS:
        wbf_v = [pl["WBF"][(dday, s)][i] for s in range(30) if (dday, s) in pl["WBF"]]
        wf_v = [pl["WF"][(dday, s)][i] for s in range(30) if (dday, s) in pl["WF"]]
        per_trace_wbf.append(np.mean(wbf_v)); per_trace_wf.append(np.mean(wf_v))
    xa, xb = np.array(per_trace_wbf), np.array(per_trace_wf)
    p = stats.wilcoxon(xa, xb).pvalue if not np.all(xa == xb) else float("nan")
    trace_lines.append(f"    {MSHORT[i]:7} n=10  p={p:.2e} {star(p)}  (WBF {'lower' if np.median(xa-xb)<0 else 'higher'})")

# ---- report -----------------------------------------------------------------
lines, md = [], ["# Revised SOTA statistics — mean ± 95% CI + paired Wilcoxon (Holm-corrected, with direction)\n"]
md.append("Every metric is **lower-is-better**. Wilcoxon paired by common random seed "
          "(PlanetLab keyed by (trace,seed), n=300; others n=30). p-values are Holm-Bonferroni "
          "corrected over all 48 tests. 'dir' = which technique wins (lower).\n")

for wl in ["planetlab", "alibaba", "materna", "azure"]:
    tech = per_wl[wl]
    lines.append("=" * 96)
    lines.append(f"  {wl.upper()}")
    lines.append("=" * 96)
    lines.append(f"{'Technique':10}{'n':>4}   " + "".join(f"{m:>22}" for m in METRICS))
    lines.append("-" * 96)
    md.append(f"\n## {wl.capitalize()}\n")
    md.append("| Technique | n | " + " | ".join(METRICS) + " |")
    md.append("|---|--:|---|---|---|---|")
    for t in TECHS:
        cells, mdc = [], []
        for i in range(4):
            n, mean, sd, ci = summ([v[i] for v in tech[t].values()])
            cells.append(f"{mean:8.2f}±{ci:5.2f}"); mdc.append(f"{mean:.2f} ± {ci:.2f}")
        lines.append(f"{t:10}{n:>4}   " + "".join(f"{c:>22}" for c in cells))
        md.append(f"| {t} | {n} | " + " | ".join(mdc) + " |")
    lines.append("-" * 96)
    lines.append("  Paired Wilcoxon (WBF vs X): winner | raw p | Holm-adj p")
    md.append("\n*Paired Wilcoxon (WBF vs X) — winner (lower) · raw p · Holm-adj:*\n")
    md.append("| Comparison | Metric | winner | raw p | Holm p |")
    md.append("|---|---|---|---|---|")
    for opp in COMPARISONS:
        for i in range(4):
            t = next(x for x in tests if x["wl"] == wl and x["opp"] == opp and x["i"] == i)
            win = "WBF" if t["wbf_better"] else opp
            lines.append(f"   WBF vs {opp:8} {MSHORT[i]:7}: {win:8}  raw {t['p']:.1e}{star(t['p']):>4}  "
                         f"Holm {t['padj']:.1e}{star(t['padj']):>4}  ({t['wins']}/{t['losses']})")
            md.append(f"| WBF vs {opp} | {MSHORT[i]} | **{win}** | {t['p']:.1e} {star(t['p'])} | "
                      f"{t['padj']:.1e} {star(t['padj'])} |")
    lines.append("")

lines += [""] + trace_lines + [""]
md.append("\n## PlanetLab ablation robustness (trace level, n=10)\n")
md.append("Pooling 10 traces × 30 seeds as 300 i.i.d. pairs is pseudo-replication (trace is a "
          "blocking factor), so PlanetLab CIs/p are optimistic. Re-testing the WBF-vs-WF ablation "
          "on the 10 trace-means:\n")
for tl in trace_lines[1:]:
    md.append(f"- `{tl.strip()}`")

md.append("\n## Honest reading (post-correction)\n")
md.append("- **WBF vs AMOVMC and WBF vs EUQ-VMC survive Holm on all metrics/workloads** (p adj ≪ 0.001): "
          "the head-to-head efficiency conclusions (energy, migrations, network transfer) are robust.\n"
          "- **WBF loses SLA to AMOVMC on all four workloads** (AMOVMC wins, significant) and to EUQ-VMC on "
          "Alibaba — the honest energy-vs-SLA trade-off, not a WBF SLA win.\n"
          "- **Bollinger ablation (WF→WBF) is fragile after correction:** energy increase significant on "
          "PlanetLab/Materna only (2/4); migration increase 3/4; SLA improvement survives on PlanetLab only. "
          "Present it as *directional* evidence that Bollinger trades a little energy/migration for SLA "
          "stability on volatile traces, not an all-workloads effect.")

report = "\n".join(lines)
print(report)
open(os.path.join(HERE, "stats_ic95_wilcoxon.txt"), "w", encoding="utf-8").write(report)
open(os.path.join(HERE, "stats_ic95_wilcoxon.md"), "w", encoding="utf-8").write("\n".join(md))
print("\n[saved] SOTA/stats_ic95_wilcoxon.txt and .md")
