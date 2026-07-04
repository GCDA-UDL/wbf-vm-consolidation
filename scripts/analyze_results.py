#!/usr/bin/env python3
"""
Aggregate the per-seed results (_data.json) of the Paper 4 experiments into per
(workload, technique) averages, compute the composite metrics and write a JSON summary.

Technique identification (from experimentConfiguration):
  selectionPolicy mu/mmt/rs/mc          -> MU/MMT/RS/MC
  psp2 + last                            -> WPSP
  psp2 + fbProphet + signal none         -> WF
  psp2 + fbProphet + signal bollinger    -> WBF

Metrics (paper Tables 6-9):
  energy (kWh)            composite (energyWithExtraHost + migration-path energy)
  sla (%)                 cloudsimResults.slaOverall * 100
  migrations              cloudsimResults.numberOfMigrations
  hosts                   cpuResults.totalUsedHosts
  allocMips               vmTotalAllocatedMips
  ramInBw (x10^5 MB)      networkPhysicalResults.totalRAMInBW / 1e5
  shutdowns               cloudsimResults.numberOfHostShutdowns
  dispersion (%)          cpuResults.medianCPUDispersionOfActiveHosts * 100
  ESV                     energy * sla(%)
  ME (x10^7)              allocMips / energy / 1e7

Usage (from the repository root, after running the experiments):
  python3 scripts/analyze_results.py --output-dir output --out summary.json
"""
import argparse
import glob
import json
import os
from collections import defaultdict

TECH_ORDER = ["MU", "MMT", "RS", "MC", "WPSP", "WF", "WBF"]
WL_ORDER = ["planetlab", "alibaba", "materna", "azure"]


def signal_is_bollinger(sig):
    if isinstance(sig, list):
        return any("bollinger" in str(x).lower() for x in sig)
    return "bollinger" in str(sig).lower()


def identify(cfg):
    sp = str(cfg.get("selectionPolicy", "")).lower()
    fc = str(cfg.get("hostForecastingTechnique", "")).lower()
    sig = cfg.get("hostSignalProcessing", "none")
    if sp in ("mu", "mmt", "rs", "mc"):
        return sp.upper()
    if sp == "psp2":
        if "fbprophet" in fc:
            return "WBF" if signal_is_bollinger(sig) else "WF"
        return "WPSP"
    return None


def workload_of(path, cfg):
    for wl in WL_ORDER:
        if f"paper4_full_{wl}_" in path:
            return wl
    tr = str(cfg.get("workloadTrace", "")).lower()
    for wl in WL_ORDER:
        if wl[:5] in tr:
            return wl
    return "unknown"


def energy_migrations_paths(total_ram_in_bw):
    """Network-routing energy of the migrations (composite-energy term).
    energyMigrationsPaths = (4.096 * totalRAMInBW + 20.165) * 1.1 / (3600*1000)  [kWh]."""
    return (4.096 * total_ram_in_bw + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics_of(d):
    cs = d.get("cloudsimResults", {})
    net = d.get("networkPhysicalResults", {})
    cpu = d.get("cpuResults", {})
    # Composite "Energy Consumption" = energyWithExtraHost + energyMigrationsPaths
    ewh = cs.get("energyWithExtraHost", cs.get("energy", 0.0))
    energy = ewh + energy_migrations_paths(net.get("totalRAMInBW", 0.0))
    sla_pct = cs.get("slaOverall", 0.0) * 100.0
    alloc = cs.get("vmTotalAllocatedMips", 0.0)  # scalar (cpu.totalAllocatedMIPS is a list)
    return {
        "energy": energy,
        "sla": sla_pct,
        "migrations": cs.get("numberOfMigrations", 0),
        "hosts": cpu.get("totalUsedHosts", 0.0),
        "allocMips": alloc,
        "ramInBw": net.get("totalRAMInBW", 0.0) / 1e5,
        "shutdowns": cs.get("numberOfHostShutdowns", 0),
        "dispersion": cpu.get("medianCPUDispersionOfActiveHosts", 0.0) * 100.0,
        "esv": energy * sla_pct,
        "me": (alloc / energy / 1e7) if energy else 0.0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="output")
    ap.add_argument("--out", default="summary.json")
    args = ap.parse_args()

    files = glob.glob(os.path.join(args.output_dir, "paper4_full_*",
                                   "*_data.json"))
    print(f"Found {len(files)} result files")

    # accumulate: (wl, tech) -> list of metric dicts
    acc = defaultdict(list)
    skipped = 0
    for fp in files:
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception:
            skipped += 1
            continue
        cfg = d.get("experimentConfiguration", {})
        tech = identify(cfg)
        wl = workload_of(fp, cfg)
        if tech is None or wl == "unknown":
            skipped += 1
            continue
        acc[(wl, tech)].append(metrics_of(d))

    # averages
    summary = {}
    for wl in WL_ORDER:
        summary[wl] = {}
        for tech in TECH_ORDER:
            rows = acc.get((wl, tech), [])
            if not rows:
                continue
            avg = {}
            for k in rows[0]:
                avg[k] = sum(r[k] for r in rows) / len(rows)
            avg["n"] = len(rows)
            summary[wl][tech] = avg

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # console summary
    print(f"Skipped: {skipped}")
    for wl in WL_ORDER:
        techs = summary.get(wl, {})
        ns = sum(t["n"] for t in techs.values())
        print(f"\n{wl}: {len(techs)} techniques, {ns} experiments")
        for tech in TECH_ORDER:
            if tech in techs:
                m = techs[tech]
                print(f"  {tech:5} (n={m['n']:2}): "
                      f"E={m['energy']:6.2f} SLA={m['sla']:5.2f}% "
                      f"mig={m['migrations']:6.1f} ESV={m['esv']:7.2f} "
                      f"ME={m['me']:5.2f}")
    print(f"\nSummary written to {args.out}")


if __name__ == "__main__":
    main()
