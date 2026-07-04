#!/usr/bin/env python3
"""SOTA comparison extended to all workloads (Guirado request).
Per workload: WF / WBF (re-run here) vs AMOVMC / EUQ-VMC (shared + native placement),
all in the same simulator/energy/SLA/network model. Also compares the re-run WF/WBF
against the values published in the paper to check reproducibility drift.
Metrics: Energy(kWh), SLA(%), #migrations, ESV(=E*SLA), RAM-in-BW(x1e5). Lower is better."""
import glob, json, os, statistics as st

OUT = r"C:\Users\PcVIP\Desktop\_publish_vmcons\output"

# Published paper values (tab:materna_results, tab:azure_results_v2): E, SLA%, migr, ESV, RAMbw
PAPER = {
    "materna": {"WF": (24.17, 3.48, 371, 84.55, 44.84), "WBF": (25.13, 2.41, 320, 60.68, 36.94)},
    "azure":   {"WF": (23.43, 2.26, 294, 51.98, 33.48), "WBF": (24.59, 1.63, 259, 39.50, 29.89)},
}


def m1(fp):
    j = json.load(open(fp)); cs = j["cloudsimResults"]; net = j["networkPhysicalResults"]
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)); ram = net.get("totalRAMInBW", 0)
    sla = cs.get("slaOverall", 0) * 100
    # (energy, sla, migr, esv, ram) for display
    return (e, sla, cs.get("numberOfMigrations", 0), e * sla, ram / 1e5)


def agg(files):
    if not files:
        return None
    rows = [m1(f) for f in files]
    n = len(rows)
    return (n,) + tuple(st.mean(r[i] for r in rows) for i in range(5))


def folder(name):
    return agg(glob.glob(os.path.join(OUT, name, "*_data.json")))


def wf_wbf(wl):
    """Split the re-run paper4_full_<wl>_prophet folder into WF (none) and WBF (bollinger)."""
    wf, wbf = [], []
    for f in glob.glob(os.path.join(OUT, f"paper4_full_{wl}_prophet", "*_data.json")):
        cfg = json.load(open(f)).get("experimentConfiguration", {})
        (wbf if "bollinger" in str(cfg.get("hostSignalProcessing")) else wf).append(f)
    return agg(wf), agg(wbf)


def line(label, v):
    if not v:
        return f"{label:26}{'(sin datos)':>14}"
    n, e, sla, mig, esv, ram = v
    return f"{label:26}{n:>4}{e:>9.2f}{sla:>8.2f}{mig:>8.1f}{esv:>9.2f}{ram:>9.2f}"


HDR = f"{'Technique':26}{'n':>4}{'Energy':>9}{'SLA%':>8}{'migr':>8}{'ESV':>9}{'RAMbw':>9}"

for wl in ["materna", "azure"]:
    print("=" * 76)
    print(f"  {wl.upper()}  (re-run in our simulator, lower is better)")
    print("=" * 76)
    print(HDR); print("-" * 76)
    wf, wbf = wf_wbf(wl)
    rows = [("WF (psp2)", wf), ("WBF (psp2+Boll)", wbf),
            ("AMOVMC (shared)", folder(f"amovmc_{wl}")),
            ("AMOVMC (native)", folder(f"amovmc_native_{wl}")),
            ("EUQ-VMC (shared)", folder(f"euqvmc_{wl}")),
            ("EUQ-VMC (native)", folder(f"euqvmc_native_{wl}"))]
    for lbl, v in rows:
        print(line(lbl, v))
    print("-" * 76)
    # reproducibility check vs paper
    print("  Re-run vs paper (WF/WBF):  E / SLA% / migr / ESV / RAMbw")
    for tech, v in [("WF", wf), ("WBF", wbf)]:
        if not v:
            print(f"    {tech}: (sin datos re-ejecutados)"); continue
        _, e, sla, mig, esv, ram = v
        pe, psla, pmig, pesv, pram = PAPER[wl][tech]
        print(f"    {tech}:  rerun {e:.2f}/{sla:.2f}/{mig:.0f}/{esv:.2f}/{ram:.2f}"
              f"   paper {pe}/{psla}/{pmig}/{pesv}/{pram}")
    print()
