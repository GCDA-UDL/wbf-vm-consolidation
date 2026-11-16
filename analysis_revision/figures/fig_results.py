#!/usr/bin/env python3
"""Result figures of the revised manuscript, drawn from the cached raw runs.

  fig_<wl>_migrations.pdf, fig_<wl>_sla.pdf   boxplots over the runs of each technique
  fig_energy_components.pdf                    execution energy (dots) and the two small
                                               terms (stacked bars) on the same kWh scale
  fig_energy_components_stacked.pdf            the three terms stacked from zero
  fig_kappa_sensitivity.pdf                    total-energy saving of WBP and WP against the
                                               most frugal classical technique, vs kappa
  fig_sota_tradeoff.pdf                        energy-SLA operating points, shared and
                                               native placement

Metric definitions come from revlib.metrics_rev (migration traffic counted once; reference
kappa = 0.512 J per MB and hop).  Read-only on the cache.  Usage:
  python -B fig_results.py --cache ../cache --out ../../manuscript/figures_rev \
         [--preview preview] [--facts ../out/facts.json]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import revlib as L          # noqa: E402
import figstyle as S        # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cache", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--preview", default=None)
ap.add_argument("--facts", default=None, help="facts.json of build_revision.py, for the cross-check")
a = ap.parse_args()

S.apply()
import matplotlib.pyplot as plt                     # noqa: E402
from matplotlib.lines import Line2D                 # noqa: E402
from matplotlib.patches import Patch                # noqa: E402

KAPPA, BETA = L.KAPPA_REF, L.BETA
runs, _ = L.load_cache(a.cache)
TR = {wl: L.collect_table_runs(runs, wl) for wl in S.WLS}
byf = {}
for r in runs:
    byf.setdefault(r["folder"], []).append(r)


def vals(rs, key, kappa=KAPPA):
    return [L.metrics_rev(r, kappa, BETA)[key] for r in rs]


def aggregate(wl, rs, key, kappa=KAPPA):
    """Same rule as build_revision.aggregate: PlanetLab over the 10 trace means, the other
    workloads over the 30 seeds.  Returns (mean, 95% CI half-width)."""
    if wl == "planetlab":
        per_day = {}
        for r in rs:
            per_day.setdefault(L.trace_day(r), []).append(L.metrics_rev(r, kappa, BETA)[key])
        means = [float(np.mean(v)) for _, v in sorted(per_day.items())]
        _, m, _, ci = L.mean_ci(means)
        return m, ci
    _, m, _, ci = L.mean_ci(vals(rs, key, kappa))
    return m, ci


# ----------------------------------------------------------------------------- 1. boxplots
def boxplot(wl, key, ylabel, name):
    fig, ax = plt.subplots(figsize=(S.COL1, 56 * S.MM))
    data = [vals(TR[wl][t], key) for t in S.MAIN_T]
    bp = ax.boxplot(data, widths=0.58, patch_artist=True, showmeans=True,
                    medianprops=dict(color=S.INK, linewidth=1.0),
                    meanprops=dict(marker="D", markerfacecolor="white", markeredgecolor=S.INK,
                                   markersize=3.2, markeredgewidth=0.6),
                    flierprops=dict(marker="o", markersize=2.0, markerfacecolor=S.INK2,
                                    markeredgecolor="none", alpha=0.7),
                    whiskerprops=dict(color=S.INK2, linewidth=0.8),
                    capprops=dict(color=S.INK2, linewidth=0.8),
                    boxprops=dict(edgecolor=S.INK2, linewidth=0.8))
    for patch, med, t in zip(bp["boxes"], bp["medians"], S.MAIN_T):
        patch.set_facecolor(S.tech_color(t))
        if t == "WBP":                       # dark fill: the median line needs a light stroke
            med.set_color("white")
    ax.set_xticks(range(1, len(S.MAIN_T) + 1))
    ax.set_xticklabels(S.MAIN_T)
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    S.hgrid(ax)
    fig.subplots_adjust(left=0.15, right=0.985, top=0.97, bottom=0.11)
    S.save(fig, a.out, a.preview, name)


for wl in S.WLS:
    boxplot(wl, "migr", "Number of migrations", f"fig_{wl}_migrations")
    boxplot(wl, "sla", "SLA violation (%)", f"fig_{wl}_sla")

# ----------------------------------------------------------------------------- 2. energy components
MEAN = {wl: {t: {k: aggregate(wl, TR[wl][t], k)[0] for k in ["e_exec", "e_onoff", "e_mig", "e_total", "e_hosts"]}
             for t in S.MAIN_T} for wl in S.WLS}
SPAN = 2.0   # kWh shown in every panel of both rows, so that 1 kWh has the same height everywhere
x = np.arange(len(S.MAIN_T))

fig, axes = plt.subplots(2, 4, figsize=(S.COL2, 92 * S.MM), sharex=True)
for j, wl in enumerate(S.WLS):
    ex = [MEAN[wl][t]["e_exec"] for t in S.MAIN_T]
    lo = np.floor((min(ex) - 0.1) * 2) / 2
    assert max(ex) < lo + SPAN - 0.05, (wl, min(ex), max(ex))
    ax = axes[0, j]
    for xi, t in zip(x, S.MAIN_T):
        ax.plot([xi], [MEAN[wl][t]["e_exec"]], marker="o", markersize=5.5, markerfacecolor=S.tech_color(t),
                markeredgecolor=S.INK2, markeredgewidth=0.7, linestyle="none", clip_on=False, zorder=3)
    ax.set_ylim(lo, lo + SPAN)
    ax.set_yticks(np.arange(lo, lo + SPAN + 1e-9, 0.5))
    ax.set_title(S.WLNAME[wl])
    S.hgrid(ax)
    ax = axes[1, j]
    on = [MEAN[wl][t]["e_onoff"] for t in S.MAIN_T]
    mg = [MEAN[wl][t]["e_mig"] for t in S.MAIN_T]
    ax.bar(x, on, width=0.62, color=S.C_ONOFF, edgecolor="white", linewidth=0.6, hatch="////")
    ax.bar(x, mg, width=0.62, bottom=on, color=S.C_MIG, edgecolor="white", linewidth=0.6)
    ax.set_ylim(0, SPAN)
    ax.set_yticks(np.arange(0, SPAN + 1e-9, 0.5))
    ax.set_xticks(x)
    ax.set_xticklabels(S.MAIN_T, rotation=90)
    ax.set_xlim(-0.6, len(S.MAIN_T) - 0.4)
    S.hgrid(ax)
axes[0, 0].set_ylabel("Execution energy (kWh)")
axes[1, 0].set_ylabel("Switch-on/off and\nmigration energy (kWh)")
axes[1, 3].legend(handles=[Patch(facecolor=S.C_MIG, edgecolor="white", label="Migration"),
                           Patch(facecolor=S.C_ONOFF, edgecolor="white", hatch="////", label="Switch-on/off")],
                  loc="upper right", handlelength=1.4, borderaxespad=0.2, labelspacing=0.3)
fig.subplots_adjust(left=0.085, right=0.995, top=0.94, bottom=0.14, wspace=0.28, hspace=0.12)
S.save(fig, a.out, a.preview, "fig_energy_components")

fig, axes = plt.subplots(1, 4, figsize=(S.COL2, 62 * S.MM), sharey=True)
for j, wl in enumerate(S.WLS):
    ax = axes[j]
    ex = np.array([MEAN[wl][t]["e_exec"] for t in S.MAIN_T])
    on = np.array([MEAN[wl][t]["e_onoff"] for t in S.MAIN_T])
    mg = np.array([MEAN[wl][t]["e_mig"] for t in S.MAIN_T])
    ax.bar(x, ex, width=0.62, color=S.C_EXEC, edgecolor="white", linewidth=0.6)
    ax.bar(x, on, width=0.62, bottom=ex, color=S.C_ONOFF, edgecolor="white", linewidth=0.6, hatch="////")
    ax.bar(x, mg, width=0.62, bottom=ex + on, color=S.C_MIG, edgecolor="white", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(S.MAIN_T, rotation=90)
    ax.set_title(S.WLNAME[wl])
    S.hgrid(ax)
axes[0].set_ylabel("Energy (kWh)")
fig.legend(handles=[Patch(facecolor=S.C_EXEC, label="Execution"),
                    Patch(facecolor=S.C_ONOFF, hatch="////", edgecolor="white", label="Switch-on/off"),
                    Patch(facecolor=S.C_MIG, label="Migration")],
           loc="lower center", ncol=3, handlelength=1.4, bbox_to_anchor=(0.5, 0.0))
fig.subplots_adjust(left=0.07, right=0.995, top=0.92, bottom=0.30, wspace=0.08)
S.save(fig, a.out, a.preview, "fig_energy_components_stacked")

# ----------------------------------------------------------------------------- 3. kappa sensitivity
# Mean total energy is affine in kappa: E(k) = Eh + (k * T + beta * N) / 3.6e6, with the means
# of host energy Eh, single-count traffic T [MB.hop] and registered migrations N.
COEF = {}
for wl in S.WLS:
    COEF[wl] = {}
    for t in S.MAIN_T:
        rs = TR[wl][t]
        if wl == "planetlab":       # mean of the 10 trace means (balanced: equals the grand mean)
            def tm(f):
                d = {}
                for r in rs:
                    d.setdefault(L.trace_day(r), []).append(f(r))
                return float(np.mean([np.mean(v) for v in d.values()]))
        else:
            def tm(f):
                return float(np.mean([f(r) for r in rs]))
        COEF[wl][t] = (tm(lambda r: L.metrics_rev(r)["e_hosts"]), tm(L.traffic_single), tm(L.n_mig_net))


def total(wl, t, k):
    eh, tr, n = COEF[wl][t]
    return eh + (k * tr + BETA * n) / 3.6e6


def saving_vs_best_classical(wl, t, k):
    """Saving (%) of technique t with respect to the classical technique with the lowest total
    energy at this kappa (= the minimum of the four savings, SENS[...]['lo'] in build_revision)."""
    return min(100.0 * (1 - total(wl, t, k) / total(wl, c, k)) for c in S.CLASSICAL)


KS = np.linspace(0, 4.2, 211)
MARK = [(0.512, "a"), (L.KAPPA_SIMULATOR, "b"), (L.KAPPA_SUBMITTED, "c")]
fig, axes = plt.subplots(1, 4, figsize=(S.COL2, 56 * S.MM), sharey=True)
for j, wl in enumerate(S.WLS):
    ax = axes[j]
    ax.axhline(0, color=S.INK2, linewidth=0.7)
    for kv, lab in MARK:
        ax.axvline(kv, color=S.INK2, linewidth=0.6, linestyle=(0, (1, 2)))
        ax.annotate(lab, xy=(kv, 1.0), xycoords=("data", "axes fraction"), xytext=(0, 2),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8, color=S.INK2)
    ax.plot(KS, [saving_vs_best_classical(wl, "WBP", k) for k in KS], color=S.C_FAMILY["WBP"],
            linewidth=1.6, label="WBP")
    ax.plot(KS, [saving_vs_best_classical(wl, "WP", k) for k in KS], color=S.C_FAMILY["WP"],
            linewidth=1.4, linestyle=(0, (4, 2)), label="WP")
    ax.set_title(S.WLNAME[wl], pad=12)
    ax.set_xlim(0, 4.2)
    ax.set_xticks([0, 1, 2, 3, 4])
    S.hgrid(ax)
axes[0].set_ylabel("Total-energy saving (%)")
axes[0].legend(loc="upper left", handlelength=2.2, borderaxespad=0.3)
fig.supxlabel("Migration-energy coefficient κ (J per MB and hop)", fontsize=8, y=0.02)
fig.subplots_adjust(left=0.065, right=0.99, top=0.83, bottom=0.21, wspace=0.08)
S.save(fig, a.out, a.preview, "fig_kappa_sensitivity")

# ----------------------------------------------------------------------------- 4. SOTA trade-off
def native(wl, tag):
    fs = [f"{tag}_native_pl_{d}" for d in L.DAYS] if wl == "planetlab" else [f"{tag}_native_{wl}"]
    out = []
    for f in fs:
        out += byf.get(f, [])
    return out


POINTS = [("WBP", "WBP", lambda wl: TR[wl]["WBP"], True),
          ("AMOVMC", "AMOVMC (shared)", lambda wl: TR[wl]["AMOVMC"], True),
          ("EUQ-VMC", "EUQ-VMC (shared)", lambda wl: TR[wl]["EUQ-VMC"], True),
          ("BB+NeoPro", "BB+NeoPro", lambda wl: TR[wl]["BB+NeoPro"], True),
          ("AMOVMC", "AMOVMC (native)", lambda wl: native(wl, "amovmc"), False),
          ("EUQ-VMC", "EUQ-VMC (native)", lambda wl: native(wl, "euqvmc"), False)]
SOTA = {}
fig, axes = plt.subplots(2, 2, figsize=(S.COL1, 100 * S.MM), sharex=True, sharey=True)
for ax, wl in zip(axes.ravel(), S.WLS):
    for meth, lab, get, filled in POINTS:
        rs = get(wl)
        assert len(rs) == (300 if wl == "planetlab" else 30), (wl, lab, len(rs))
        e, eci = aggregate(wl, rs, "e_total")
        s, sci = aggregate(wl, rs, "sla")
        SOTA[(wl, lab)] = (e, eci, s, sci)
        c = S.C_METHOD[meth]
        ax.errorbar([e], [s], xerr=[eci], yerr=[sci], fmt="none", ecolor=c, elinewidth=0.9, capsize=1.5)
        ax.plot([e], [s], marker=S.M_METHOD[meth], markersize=5.2, linestyle="none",
                markerfacecolor=c if filled else "white", markeredgecolor=c, markeredgewidth=1.1)
    ax.text(0.97, 0.95, S.WLNAME[wl], transform=ax.transAxes, ha="right", va="top")
    ax.set_xlim(16, 37)
    ax.set_ylim(0, 7.2)
    ax.set_xticks([20, 25, 30, 35])
    ax.set_yticks([0, 2, 4, 6])
    S.hgrid(ax)
    ax.xaxis.grid(True)
for ax in axes[1]:
    ax.set_xlabel("Total energy (kWh)")
for ax in axes[:, 0]:
    ax.set_ylabel("SLA violation (%)")
handles = [Line2D([], [], marker=S.M_METHOD[m], linestyle="none", markersize=5.2,
                  markerfacecolor=S.C_METHOD[m] if filled else "white", markeredgecolor=S.C_METHOD[m],
                  markeredgewidth=1.1, label=lab) for m, lab, _, filled in POINTS]
fig.legend(handles=handles, loc="lower center", ncol=2, handletextpad=0.3, columnspacing=1.6,
           labelspacing=0.35, bbox_to_anchor=(0.55, 0.0))
fig.subplots_adjust(left=0.13, right=0.985, top=0.985, bottom=0.25, wspace=0.08, hspace=0.08)
S.save(fig, a.out, a.preview, "fig_sota_tradeoff")

# ----------------------------------------------------------------------------- cross-checks
print("\nkappa sensitivity, saving of WBP against the most frugal classical technique (%):")
for wl in S.WLS:
    print(f"  {wl:10} " + "  ".join(f"k={k:g}: {saving_vs_best_classical(wl, 'WBP', k):6.2f}"
                                    for k in [0.0, 0.512, 1.0, 2.0, L.KAPPA_SIMULATOR, L.KAPPA_SUBMITTED]))
print("\nmost frugal classical technique along kappa (reference of the saving):")
for wl in S.WLS:
    prev, seg = None, []
    for k in KS:
        best = min(S.CLASSICAL, key=lambda c: total(wl, c, k))
        if best != prev:
            seg.append(f"{best} from kappa = {k:.2f}")
            prev = best
    print(f"  {wl:10} " + "; ".join(seg))
if a.facts:
    F = json.load(open(a.facts, encoding="utf-8"))
    worst = 0.0
    n = 0
    for wl in S.WLS:
        for k in [0.0, 0.512, 1.0, 2.0, L.KAPPA_SIMULATOR, L.KAPPA_SUBMITTED]:
            ref = F["sens"][wl][str(k)]["lo"]
            worst = max(worst, abs(ref - saving_vs_best_classical(wl, "WBP", k)))
            n += 1
        for t in S.MAIN_T:
            for key in ["e_exec", "e_onoff", "e_mig", "e_total"]:
                worst = max(worst, abs(F["agg"][wl][t][key]["mean"] - MEAN[wl][t][key]))
                n += 1
        for lab in ["\\textit{WBP}", "AMOVMC (shared)", "AMOVMC (native)", "EUQ-VMC (shared)", "EUQ-VMC (native)"]:
            lab_p = "WBP" if "WBP" in lab else lab
            worst = max(worst, abs(F["native"][wl][lab]["e_total"] - SOTA[(wl, lab_p)][0]),
                        abs(F["native"][wl][lab]["sla"] - SOTA[(wl, lab_p)][2]))
            n += 2
    print(f"cross-check against {a.facts}: {n} values, largest absolute difference {worst:.2e}")
    assert worst < 1e-6, "figures and build_revision.py disagree"
print("\nSOTA operating points (total energy kWh ± CI, SLA % ± CI):")
for (wl, lab), (e, eci, s, sci) in SOTA.items():
    print(f"  {wl:10} {lab:28} {e:6.2f} ± {eci:4.2f}   {s:5.2f} ± {sci:4.2f}")
