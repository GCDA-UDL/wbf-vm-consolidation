#!/usr/bin/env python3
"""FINAL bit-reproducible SOTA comparison (single-thread Stan) across the 4 workloads.
WF/WBF read from the _st (single-thread) re-run; AMOVMC/EUQ-VMC use dwma (already deterministic).
Also reports WF/WBF single-thread vs the earlier multi-thread run, to quantify the change."""
import glob, json, os, statistics as st

OUT = r"C:\Users\PcVIP\Desktop\_publish_vmcons\output"
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]


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
    if wl == "planetlab":
        return globs(*[f"{method}_pl_{d}" for d in DAYS])
    return globs(f"{method}_{wl}")


def wf_wbf(wl, suffix=""):
    if wl == "planetlab":
        pool = globs(*[f"p4_pl_{d}{suffix}" for d in DAYS])
    else:
        pool = globs(f"paper4_full_{wl}_prophet{suffix}")
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
    print(f"  {wl.upper()}  (WF/WBF single-thread = bit-reproducible)")
    print("=" * 70)
    print(HDR); print("-" * 70)
    wf, wbf = wf_wbf(wl, "_st")
    for lbl, v in [("WF (psp2)", wf), ("WBF (psp2+Boll)", wbf),
                   ("AMOVMC (shared)", agg(folder_wl("amovmc", wl))),
                   ("AMOVMC (native)", agg(folder_wl("amovmc_native", wl))),
                   ("EUQ-VMC (shared)", agg(folder_wl("euqvmc", wl))),
                   ("EUQ-VMC (native)", agg(folder_wl("euqvmc_native", wl)))]:
        print(line(lbl, v))
    print("-" * 70)
    wf_mt, wbf_mt = wf_wbf(wl, "")  # multi-thread run for comparison
    print("  single-thread vs multi-thread (E / SLA% / migr):")
    for tech, s, mt in [("WF", wf, wf_mt), ("WBF", wbf, wbf_mt)]:
        if not s or not mt:
            continue
        print(f"   {tech:4} ST {s[1]:.2f}/{s[2]:.2f}/{s[3]:.0f}   MT {mt[1]:.2f}/{mt[2]:.2f}/{mt[3]:.0f}")
    print()
