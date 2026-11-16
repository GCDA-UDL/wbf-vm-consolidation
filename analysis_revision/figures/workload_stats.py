#!/usr/bin/env python3
"""Workload characterisation (Table 2 of the manuscript and its figure).

1. Recomputes the two statistics of the submitted Table 2 for every candidate column and
   window of each trace, to find which column reproduces each published cell.
2. Computes the same statistics on the series the simulator reads (column and samples
   taken from the UtilizationModel*InMemory classes) and writes the revised table, the
   figure and a note with old and new values.

Statistic (the recipe that reproduces the table of the submitted version): for every VM, the median of
its CPU utilization (%) and the accumulated absolute difference between consecutive
samples; the table gives the median over the VMs of each quantity +- the sample standard
deviation over the VMs.

Read-only on the traces.  Usage:
  python -B workload_stats.py --workloads <package>/workloads --table-out <dir> \
         --fig-out <dir> --note-out <file.md> [--preview <dir>]
"""
import argparse
import csv
import glob
import os
import statistics as st

import figstyle as S

ap = argparse.ArgumentParser()
ap.add_argument("--workloads", required=True)
ap.add_argument("--table-out", required=True)
ap.add_argument("--fig-out", required=True)
ap.add_argument("--note-out", required=True)
ap.add_argument("--preview", default=None)
ap.add_argument("--orig-workloads", default=None,
                help="optional: workloads folder of the original project (networkExperiments/workloads), "
                     "to look for the PlanetLab subset behind the published cell and to check with which "
                     "column the Azure mostDiff VMs were selected")
a = ap.parse_args()

SIM_SAMPLES = 288   # UtilizationModelPlanetLabInMemory reads numData - 1 = 288 lines
                    # (numData = 289; the last element duplicates sample 288)
PUBLISHED = {       # submitted manuscript, Table 2 (3_background.tex:249-250)
    "planetlab": (24.0, 17.2, 3996.0, 1312.0),
    "alibaba": (32.2, 5.3, 1346.0, 132.0),
    "materna": (5.3, 6.4, 517.0, 630.0),
    "azure": (16.9, 15.6, 3148.0, 2342.0),
}
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]


def fnum(x):
    return float(x.strip().strip('"').replace(",", "."))


def load_planetlab(folder):
    out = []
    for f in sorted(glob.glob(os.path.join(folder, "*"))):
        with open(f) as fh:
            out.append({"cpu": [float(x) for x in fh.read().split()]})
    return out


def load_csv(folder, sep, cols):
    """cols: {name: column index}.  Returns one dict of series per VM file."""
    out = []
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        with open(f, newline="", encoding="utf-8", errors="replace") as fh:
            rows = [r for r in csv.reader(fh, delimiter=sep) if r]
        body = rows[1:]
        out.append({name: [fnum(r[i]) for r in body] for name, i in cols.items()})
    return out


W = a.workloads
DATA = {
    "planetlab": {d: load_planetlab(os.path.join(W, "planetlab", f"planetlab_{d}_100_mostDiff")) for d in DAYS},
    "alibaba": load_csv(os.path.join(W, "alibaba2018", "alibaba2018_fixed_first_500_100_mostDiff"), ",",
                        {"cpu_util_percent": 2, "mem_util_percent": 3, "mem_gps": 4, "mkpi": 5,
                         "net_in": 6, "net_out": 7, "disk_io_percent": 8}),
    "materna": load_csv(os.path.join(W, "materna", "materna_trace1_valid_0_288_100_mostDiff"), ";",
                        {"CPU usage [MHZ]": 3, "CPU usage [%]": 4, "Memory usage [%]": 7}),
    "azure": load_csv(os.path.join(W, "azure", "azure_azure2019_traces_100_mostDiff"), ",",
                      {"min": 1, "max": 2, "avg": 3}),
}
# column the simulator reads (UtilizationModel*InMemory.readData) for each workload
SIM_COL = {"planetlab": "cpu", "alibaba": "cpu_util_percent", "materna": "CPU usage [%]", "azure": "avg"}
SIM_SRC = {
    "planetlab": "org/cloudbus/cloudsim/UtilizationModelPlanetLabInMemory.java (one integer per line)",
    "alibaba": "svila/workloads/UtilizationModelAlibaba2018InMemory.java, line.split(\",\")[2]",
    "materna": "svila/workloads/UtilizationModelMaternaInMemory.java, line.split(\";\")[4]",
    "azure": "svila/workloads/UtilizationModelAzureInMemory.java, line.split(\",\")[3]",
}


def per_vm(series_list, col, n):
    med = [st.median(d[col][:n]) for d in series_list]
    acc = [sum(abs(y - x) for x, y in zip(d[col][:n], d[col][1:n])) for d in series_list]
    return med, acc


def summary(med, acc):
    return st.median(med), st.stdev(med), st.median(acc), st.stdev(acc)


def relerr(s, target):
    return sum(abs(x - t) / t for x, t in zip(s, target))


def fmt(s):
    return f"{s[0]:.1f} ± {s[1]:.1f} | {s[2]:.0f} ± {s[3]:.0f}"


note = ["# Workload statistics: published Table 2 against the simulated series", "",
        "Statistic: per VM, median of the CPU utilization (%) and accumulated absolute difference between "
        "consecutive samples; cells give the median over the VMs ± the sample standard deviation over the VMs.",
        "",
        f"The simulator reads the first {SIM_SAMPLES} samples of each file (`numData` = 289 in "
        "`UtilizationModelFactory.java`; the reader fills `numData − 1` elements and copies the last one).",
        ""]

# ----------------------------------------------------------------------------- 1. reproduction
note += ["## 1. Which column and window reproduce each published cell", "",
         "| workload | candidate | samples | % CPU median | accumulated diff | sum of relative errors |",
         "|---|---|---|---|---|---|"]
BEST = {}
for wl in S.WLS:
    cands = []
    if wl == "planetlab":
        sets = {f"day {d}": DATA[wl][d] for d in DAYS}
        sets["ten days pooled (1000 VM-days)"] = [v for d in DAYS for v in DATA[wl][d]]
        for name, ser in sets.items():
            for n in (288, 289):
                s = summary(*per_vm(ser, "cpu", n))
                cands.append((relerr(s, PUBLISHED[wl]), f"cpu, {name}", n, s))
    else:
        ser = DATA[wl]
        nmax = max(len(next(iter(d.values()))) for d in ser)
        for col in ser[0]:
            for n in sorted({288, 289, nmax}):
                s = summary(*per_vm(ser, col, n))
                cands.append((relerr(s, PUBLISHED[wl]), col, n, s))
    cands.sort(key=lambda c: c[0])
    BEST[wl] = cands[0]
    shown = cands[:4]
    # always show the simulated column at the simulated window
    for c in cands:
        if (wl == "planetlab" or c[1] == SIM_COL[wl]) and c[2] == SIM_SAMPLES and c not in shown:
            if wl != "planetlab":
                shown.append(c)
    for err, col, n, s in shown:
        a1, a2 = fmt(s).split(" | ")
        note.append(f"| {S.WLNAME[wl]} | {col} | {n} | {a1} | {a2} | {err:.4f} |")
    p = PUBLISHED[wl]
    note.append(f"| {S.WLNAME[wl]} | **published** | | {p[0]:.1f} ± {p[1]:.1f} | {p[2]:.0f} ± {p[3]:.0f} | |")
note.append("")

# ----------------------------------------------------------------------------- 2. simulated series
NEW, ACC = {}, {}
for wl in S.WLS:
    if wl == "planetlab":
        ser = [v for d in DAYS for v in DATA[wl][d]]
    else:
        ser = DATA[wl]
    med, acc = per_vm(ser, SIM_COL[wl], SIM_SAMPLES)
    NEW[wl] = summary(med, acc)
    ACC[wl] = acc
    # same statistics on the 289-element array held by the simulator (last sample duplicated)
    med2 = [st.median(d[SIM_COL[wl]][:SIM_SAMPLES] + [d[SIM_COL[wl]][SIM_SAMPLES - 1]]) for d in ser]
    NEW[wl + "_dup"] = (st.median(med2), st.stdev(med2), NEW[wl][2], NEW[wl][3])

PL_DAY = {d: summary(*per_vm(DATA["planetlab"][d], "cpu", SIM_SAMPLES)) for d in DAYS}

note += ["## 2. Published and revised values", "",
         "| workload | column read by the simulator | series | published | revised (simulated series) | "
         "published cell reproduced by |",
         "|---|---|---|---|---|---|"]
for wl in S.WLS:
    p = PUBLISHED[wl]
    b = BEST[wl]
    nser = 1000 if wl == "planetlab" else len(DATA[wl])
    note.append(f"| {S.WLNAME[wl]} | `{SIM_COL[wl]}` ({SIM_SRC[wl]}) | {nser} × {SIM_SAMPLES} samples | "
                f"{p[0]:.1f} ± {p[1]:.1f}; {p[2]:.0f} ± {p[3]:.0f} | "
                f"{NEW[wl][0]:.1f} ± {NEW[wl][1]:.1f}; {NEW[wl][2]:.0f} ± {NEW[wl][3]:.0f} | "
                f"{b[1]}, first {b[2]} samples (sum of relative errors {b[0]:.4f}) |")
note += ["", "With the duplicated last element that the simulator appends, the medians are: " + "; ".join(
    f"{S.WLNAME[wl]} {NEW[wl + '_dup'][0]:.1f} ± {NEW[wl + '_dup'][1]:.1f}" for wl in S.WLS) +
    " (the accumulated difference does not change).", "",
    "### PlanetLab, day by day (simulated window)", "",
    "| day | % CPU median | accumulated diff |", "|---|---|---|"]
for d in DAYS:
    s = PL_DAY[d]
    note.append(f"| {d} | {s[0]:.1f} ± {s[1]:.1f} | {s[2]:.0f} ± {s[3]:.0f} |")
note.append("")

# ----------------------------------------------------------------------------- table
os.makedirs(a.table_out, exist_ok=True)
tex = [
    "% Generated by analysis/figures/workload_stats.py -- do not edit by hand.",
    "% Statistics of the series read by the simulator: first 288 samples of each VM;",
    "% PlanetLab: the ten daily traces pooled (1000 VM-days); Alibaba: cpu_util_percent;",
    "% Materna: CPU usage [%]; Azure: avg.",
    r"\begin{table*}[btph]",
    r"  \centering",
    r"  \caption{CPU statistics of the simulated VM traces, computed on the column that the simulator reads "
    r"(PlanetLab: CPU utilization; Alibaba: \texttt{cpu\_util\_percent}; Materna: \texttt{CPU usage [\%]}; "
    r"Azure: \texttt{avg}) and on its first 288 samples (24~h at 5-minute sampling). Cells: median over the "
    r"VMs of the per-VM median utilization and of the per-VM accumulated absolute difference between "
    r"consecutive samples, $\pm$ standard deviation over the VMs. PlanetLab: the ten simulated days pooled "
    r"(1000 VM-days); Alibaba, Materna and Azure: 100 VMs each.}",
    r"  \begin{adjustbox}{width=0.7\textwidth}",
    r"    \begin{tabular}{lrrrr}",
    r"    \hline",
    r"        Metric & PlanetLab & Alibaba & Materna & MS Azure \\",
    r"    \hline",
    r"    \% CPU median & " + " & ".join(
        f"{NEW[wl][0]:.1f}$\\pm${NEW[wl][1]:.1f}" for wl in S.WLS) + r" \\",
    r"    \% CPU accumulated difference & " + " & ".join(
        f"{NEW[wl][2]:.0f}$\\pm${NEW[wl][3]:.0f}" for wl in S.WLS) + r" \\",
    r"    \hline",
    r"    \end{tabular}%",
    r"    \end{adjustbox}",
    r"  \label{tab:workload_statistics}%",
    r"\end{table*}%",
]
with open(os.path.join(a.table_out, "tab_workload_stats.tex"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(tex) + "\n")
print("written tab_workload_stats.tex")

# ----------------------------------------------------------------------------- figure
S.apply()
import matplotlib.pyplot as plt  # noqa: E402

fig, ax = plt.subplots(figsize=(S.COL1, 58 * S.MM))
data = [ACC[wl] for wl in S.WLS]
bp = ax.boxplot(data, widths=0.55, patch_artist=True, showmeans=True,
                medianprops=dict(color=S.INK, linewidth=1.0),
                meanprops=dict(marker="D", markerfacecolor="white", markeredgecolor=S.INK,
                               markersize=3.2, markeredgewidth=0.6),
                flierprops=dict(marker="o", markersize=2.2, markerfacecolor=S.INK2,
                                markeredgecolor="none", alpha=0.7),
                whiskerprops=dict(color=S.INK2, linewidth=0.8), capprops=dict(color=S.INK2, linewidth=0.8),
                boxprops=dict(edgecolor=S.INK2, linewidth=0.8))
for patch in bp["boxes"]:
    patch.set_facecolor(S.C_FAMILY["WPSP"])
ax.set_xticks(range(1, 5))
ax.set_xticklabels(["PlanetLab", "Alibaba", "Materna", "Azure"])
ax.set_ylabel("Accumulated CPU difference (%)")
ax.set_ylim(bottom=0)
S.hgrid(ax)
fig.subplots_adjust(left=0.17, right=0.985, top=0.97, bottom=0.11)
S.save(fig, a.fig_out, a.preview, "fig_workload_variability")

box = {wl: (min(ACC[wl]), st.quantiles(ACC[wl], n=4)[0], st.median(ACC[wl]),
            st.quantiles(ACC[wl], n=4)[2], max(ACC[wl]), st.mean(ACC[wl])) for wl in S.WLS}
note += ["## 3. Figure `fig_workload_variability.pdf`", "",
         "Boxplot over the VMs (PlanetLab: 1000 VM-days; others: 100 VMs) of the accumulated absolute "
         "difference of the simulated CPU series. Box: quartiles; line: median; diamond: mean; whiskers: "
         "1.5 × IQR; dots: VMs beyond the whiskers.", "",
         "| workload | min | Q1 | median | Q3 | max | mean |", "|---|---|---|---|---|---|---|"]
for wl in S.WLS:
    b = box[wl]
    note.append(f"| {S.WLNAME[wl]} | " + " | ".join(f"{x:.0f}" for x in b) + " |")
note.append("")

# ----------------------------------------------------------------------------- 4. original project
if a.orig_workloads:
    OW = a.orig_workloads
    note += ["## 4. Checks against the workloads folder of the original project", "",
             f"Folder: `{OW}` (not part of the reproduction package).", ""]
    # 4a. PlanetLab subset behind the published cell
    cands = []
    for dname in sorted(os.listdir(os.path.join(OW, "planetlab"))):
        full = os.path.join(OW, "planetlab", dname)
        if not (os.path.isdir(full) and dname.startswith("planetlab_") and dname.endswith("_mostDiff")):
            continue
        ser = load_planetlab(full)
        if len(ser) < 20:
            continue
        s = summary(*per_vm(ser, "cpu", 288))
        cands.append((relerr(s, PUBLISHED["planetlab"]), dname, len(ser), s))
    cands.sort(key=lambda c: c[0])
    note += ["### 4a. PlanetLab subset that reproduces the published cell (24.0 ± 17.2; 3996 ± 1312)", "",
             "| subset folder | VMs | % CPU median | accumulated diff | sum of relative errors |",
             "|---|---|---|---|---|"]
    for err, dname, nvm, s in cands[:4]:
        a1, a2 = fmt(s).split(" | ")
        note.append(f"| `{dname}` | {nvm} | {a1} | {a2} | {err:.4f} |")
    note.append("")
    print("PlanetLab published cell, best subset of the original project:", cands[0][1], cands[0][2],
          "VMs ->", fmt(cands[0][3]), f"(err {cands[0][0]:.4f})")
    # 4b. column used to select the Azure mostDiff VMs
    pool = sorted(glob.glob(os.path.join(OW, "azure", "azure2019_traces", "*.csv")))
    chosen = {os.path.basename(f) for f in glob.glob(os.path.join(
        W, "azure", "azure_azure2019_traces_100_mostDiff", "*.csv"))}
    if pool:
        score = {c: {} for c in ("min", "max", "avg")}
        for f in pool:
            with open(f, newline="") as fh:
                rows = [r for r in csv.reader(fh) if r]
            head, body = rows[0], rows[1:290]
            for c in score:
                x = [float(r[head.index(c)]) for r in body]
                score[c][os.path.basename(f)] = sum(abs(q - p) for p, q in zip(x, x[1:]))
        note += ["### 4b. Column with which the 100 Azure `mostDiff` VMs were selected", "",
                 f"Candidate pool: {len(pool)} VMs in `azure/azure2019_traces`. Ranking by the accumulated "
                 "absolute difference over the first 289 rows and keeping the first 100:", "",
                 "| ranking column | VMs of the simulated subset among the first 100 |", "|---|---|"]
        for c in ("min", "max", "avg"):
            top = sorted(score[c], key=score[c].get, reverse=True)[:100]
            hit = len(set(top) & chosen)
            note.append(f"| `{c}` | {hit} of 100 |")
            print(f"Azure selection, ranking by {c}: {hit} of 100")
        note += ["", "The selection notebook of the original project (`networkExperiments/azure_wl_filter.ipynb`, "
                 "first code cell) ranks with `data = data[0:289]` and `data['max'].diff().abs().sum()`.", ""]

with open(a.note_out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(note) + "\n")
print("written", a.note_out)
for wl in S.WLS:
    print(f"{wl:10} published {PUBLISHED[wl]}  best: {BEST[wl][1]} n={BEST[wl][2]} -> {fmt(BEST[wl][3])} "
          f"(err {BEST[wl][0]:.4f})  simulated: {fmt(NEW[wl])}")
