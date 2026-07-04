#!/usr/bin/env python3
"""SOTA comparison across ALL 4 workloads (Guirado request): PlanetLab, Alibaba, Materna, Azure.
Per workload: WF / WBF (re-run) vs AMOVMC / EUQ-VMC (shared + native), same simulator/model.
Plus re-run-vs-paper reproducibility check. Metrics: Energy(kWh), SLA(%), #migr, ESV(=E*SLA), RAMbw(x1e5)."""
import glob, json, os, statistics as st

OUT = r"C:\Users\PcVIP\Desktop\_publish_vmcons\output"
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]

# Published paper values: E, SLA%, migr, ESV, RAMbw
# planetlab from tab:sota_reproduction (already the re-run env); others from tab:*_results
PAPER = {
    "planetlab": {"WF": (19.32, 3.93, 324, 75.87, 38.11), "WBF": (20.07, 3.18, 363, 63.87, 42.82)},
    "alibaba":   {"WF": (26.47, 5.14, 350, 135.12, 42.58), "WBF": (28.02, 3.02, 330, 85.21, 40.45)},
    "materna":   {"WF": (24.17, 3.48, 371, 84.55, 44.84), "WBF": (25.13, 2.41, 320, 60.68, 36.94)},
    "azure":     {"WF": (23.43, 2.26, 294, 51.98, 33.48), "WBF": (24.59, 1.63, 259, 39.50, 29.89)},
}


def m1(fp):
    j = json.load(open(fp)); cs = j["cloudsimResults"]; net = j["networkPhysicalResults"]
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)); ram = net.get("totalRAMInBW", 0)
    sla = cs.get("slaOverall", 0) * 100
    return (e, sla, cs.get("numberOfMigrations", 0), e * sla, ram / 1e5)


def agg(files):
    if not files:
        return None
    rows = [m1(f) for f in files]
    return (len(rows),) + tuple(st.mean(r[i] for r in rows) for i in range(5))


def globs(*folders):
    fs = []
    for fo in folders:
        fs += glob.glob(os.path.join(OUT, fo, "*_data.json"))
    return fs


def folder_wl(method, wl):
    """SOTA folder(s) for a method+workload. PlanetLab spans 10 day-folders."""
    if wl == "planetlab":
        return globs(*[f"{method}_pl_{d}" for d in DAYS])
    return globs(f"{method}_{wl}")


def wf_wbf(wl):
    if wl == "planetlab":
        pool = globs(*[f"p4_pl_{d}" for d in DAYS])
    else:
        pool = globs(f"paper4_full_{wl}_prophet")
    wf, wbf = [], []
    for f in pool:
        cfg = json.load(open(f)).get("experimentConfiguration", {})
        (wbf if "bollinger" in str(cfg.get("hostSignalProcessing")) else wf).append(f)
    return agg(wf), agg(wbf)


def line(label, v):
    if not v:
        return f"{label:22}{'(sin datos)':>14}"
    n, e, sla, mig, esv, ram = v
    return f"{label:22}{n:>4}{e:>9.2f}{sla:>8.2f}{mig:>9.1f}{esv:>9.2f}{ram:>9.2f}"


HDR = f"{'Technique':22}{'n':>4}{'Energy':>9}{'SLA%':>8}{'migr':>9}{'ESV':>9}{'RAMbw':>9}"

for wl in ["planetlab", "alibaba", "materna", "azure"]:
    print("=" * 70)
    print(f"  {wl.upper()}")
    print("=" * 70)
    print(HDR); print("-" * 70)
    wf, wbf = wf_wbf(wl)
    for lbl, v in [("WF (psp2)", wf), ("WBF (psp2+Boll)", wbf),
                   ("AMOVMC (shared)", agg(folder_wl("amovmc", wl))),
                   ("AMOVMC (native)", agg(folder_wl("amovmc_native", wl))),
                   ("EUQ-VMC (shared)", agg(folder_wl("euqvmc", wl))),
                   ("EUQ-VMC (native)", agg(folder_wl("euqvmc_native", wl)))]:
        print(line(lbl, v))
    print("-" * 70)
    print("  re-run vs paper:  E / SLA% / migr / ESV / RAMbw")
    for tech, v in [("WF", wf), ("WBF", wbf)]:
        if not v:
            continue
        _, e, sla, mig, esv, ram = v
        p = PAPER[wl][tech]
        print(f"   {tech:4} rerun {e:.2f}/{sla:.2f}/{mig:.0f}/{esv:.1f}/{ram:.1f}"
              f"   paper {p[0]}/{p[1]}/{p[2]}/{p[3]}/{p[4]}")
    print()
