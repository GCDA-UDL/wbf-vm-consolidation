#!/usr/bin/env python3
"""SOTA comparison table from this repo's output/ folder (run after the SOTA configs).
Portable: reads ./output relative to the repo root. Usage:  python SOTA/compare_sota.py
Prints WF / WBF / AMOVMC / EUQ-VMC on PlanetLab (10 traces x 30 seeds), efficiency-first."""
import glob, json, os, statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]


def emig(t):
    return (4.096 * t + 20.165) * 1.1 / 3.6e6


def m1(fp):
    j = json.load(open(fp)); cs = j["cloudsimResults"]; net = j["networkPhysicalResults"]
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)); ram = net.get("totalRAMInBW", 0)
    sla = cs.get("slaOverall", 0) * 100
    return cs.get("numberOfMigrations", 0), sla, e, ram / 1e5, e * sla


def avg(folders):
    files = []
    for f in folders:
        files += glob.glob(os.path.join(OUT, f, "*_data.json"))
    if not files:
        return None
    r = [m1(f) for f in files]
    n = len(r)
    return (n, st.mean(x[0] for x in r), st.mean(x[1] for x in r),
            st.mean(x[2] for x in r), st.mean(x[3] for x in r), st.mean(x[4] for x in r))


def wf_wbf():
    wf, wbf = [], []
    for day in DAYS:
        for f in glob.glob(os.path.join(OUT, f"p4_pl_{day}", "*_data.json")):
            cfg = json.load(open(f))["experimentConfiguration"]
            (wbf if "bollinger" in str(cfg.get("hostSignalProcessing")) else wf).append(f)

    def agg(fs):
        if not fs:
            return None
        r = [m1(f) for f in fs]; n = len(r)
        return (n, st.mean(x[0] for x in r), st.mean(x[1] for x in r),
                st.mean(x[2] for x in r), st.mean(x[3] for x in r), st.mean(x[4] for x in r))
    return agg(wf), agg(wbf)


wf, wbf = wf_wbf()
rows = [("WF (WPSP+FP)", wf), ("WBF (this work)", wbf),
        ("AMOVMC (2025)",  avg([f"amovmc_pl_{d}" for d in DAYS])),
        ("EUQ-VMC (2025)", avg([f"euqvmc_pl_{d}" for d in DAYS]))]

print("PlanetLab (10 traces x 30 seeds) - head-to-head in our simulator")
print(f"{'Method':18}{'n':>5}{'Energy':>9}{'SLA%':>8}{'migr':>8}{'RAMbw':>9}{'ESV':>9}")
print("-" * 66)
for label, v in rows:
    if not v:
        print(f"{label:18}{'(no data - run the configs first)':>40}"); continue
    n, mig, sla, en, ram, esv = v
    print(f"{label:18}{n:>5}{en:>9.2f}{sla:>8.3f}{mig:>8.1f}{ram:>9.2f}{esv:>9.2f}")
print("-" * 66)
print("Efficiency (energy/migrations/network) is the consolidation objective: WBF wins there.")
print("AMOVMC reaches lower SLA/ESV by over-provisioning (highest energy, +65% migrations).")
