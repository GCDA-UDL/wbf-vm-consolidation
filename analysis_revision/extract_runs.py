#!/usr/bin/env python3
"""Read-only single pass over every <folder>/*_data.json under OUT and write one
compact record per run (CSV + JSONL) to the cache folder. Nothing is written
under OUT.  Usage:
    python -B extract_runs.py --out <output_dir> --cache <cache_dir>
"""
import argparse, glob, hashlib, json, os, re, sys

CFG_KEYS = ["name", "experimentOutputFolder", "workload", "workloadTrace", "selectionPolicy",
            "hostForecastingTechnique", "hostForecastingTechniqueParams",
            "hostSignalProcessing", "hostSignalProcessingParams", "hostOverSaturationPolicy",
            "hostUnderUtilisationPolicy", "vmMigrationPolicy", "vmOptimizerPolicy",
            "allocationPolicy", "selectionMode", "techniqueLoader", "hosts", "hostsDistribution",
            "vms", "vmsDistribution", "topology", "interactions", "interactionsDistribution",
            "randomSeed", "simulationTimeLimit", "migrationInterval", "forecastingHistoryLength",
            "defaultHistoryLength", "techniquesConfiguration", "isTunning", "tunningValue",
            "parameter", "utilizationThreshold", "minRatio", "maxRatio", "offsetRatio",
            "hostAllocationUtilization", "numCloudlets", "internalClusterRate",
            "externalClusterRate", "network", "dataSource", "dataStartStep",
            "limitAdjustment", "hostForecastingResume", "vmForecastingTechniqueBasic",
            "vmForecastingTechniqueAccurate", "signalProcessing", "forecastingTechnique",
            "defaultWeight", "defaultWeightInterconnected", "logicLinkWeight",
            "overrideLinkWeight", "adjustLoadRatio", "onlyInitialHosts", "usedHostRatio",
            "mipsStatsInterpolation"]


def mean(a):
    return sum(a) / len(a) if a else float("nan")


def record(fp):
    rec = {"folder": os.path.basename(os.path.dirname(fp)), "file": os.path.basename(fp)}
    m = re.search(r"_(\d{5})_data\.json$", fp)
    rec["fileIndex"] = int(m.group(1)) if m else None
    rec["bytes"] = os.path.getsize(fp)
    try:
        with open(fp, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as ex:  # unreadable / truncated file
        rec["parse_ok"] = False
        rec["parse_error"] = repr(ex)[:200]
        return rec
    rec["parse_ok"] = True
    c = d.get("experimentConfiguration", {})
    for k in CFG_KEYS:
        v = c.get(k)
        rec["cfg_" + k] = json.dumps(v) if isinstance(v, (list, dict)) else v
    cs = d.get("cloudsimResults", {})
    for k in ["energy", "energyWithExtraHost", "energyOpenHosts", "energyCloseHosts",
              "energyOpenCloseHosts", "slaOverall", "sla", "slaAverage", "slaTimePerActiveHost",
              "slaDegradationDueToMigration", "numberOfMigrations", "numberOfDelayedMigrations",
              "numberOfHostShutdowns", "vmTotalAllocatedMips", "vmTotalRequestedMips",
              "vmTotalUnderAllocatedDueToMigrationMips", "numberOfHosts", "numberOfVms"]:
        rec["cs_" + k] = cs.get(k)
    rec["cs_len_timeBeforeHostShutdown"] = len(cs.get("timeBeforeHostShutdown", []) or [])
    rec["cs_len_timeBeforeVmMigration"] = len(cs.get("timeBeforeVmMigration", []) or [])
    for sec, pre in [("networkPhysicalResults", "np_"), ("networkResults", "nl_")]:
        n = d.get(sec, {})
        for k in ["totalRAMInBW", "totalBWUsed", "totalMigratedRAM", "energyMigrationsPaths",
                  "energyMigrations", "averageMigrationDistances", "totalTimeMigrating",
                  "numInteractions", "numLinks"]:
            rec[pre + k] = n.get(k)
        rec[pre + "len_migrationDistances"] = len(n.get("migrationDistances", []) or [])
        rec[pre + "sum_numMigrationsPerSnapshot"] = sum(n.get("numMigrationsPerSnapshot", []) or [])
        rec[pre + "sum_RAMInBWPerSnapshot"] = sum(n.get("RAMInBWPerSnapshot", []) or [])
        rec[pre + "sum_migratedRAMPerSnapshot"] = sum(n.get("migratedRAMPerSnapshot", []) or [])
    cpu = d.get("cpuResults", {})
    for k in ["totalUsedHosts", "averageFreeMIPSActiveHosts", "medianCPUDispersionOfActiveHosts",
              "averageCPUDispersionOfActiveHosts", "totalSaturatedHosts",
              "averageCPUPercAllocatedOfVms"]:
        rec["cpu_" + k] = cpu.get(k)
    for k in ["totalAvailableMIPS", "totalRequestedMIPS", "totalAllocatedMIPS", "totalUsedMIPS",
              "usedHostsPerSnapshot", "averageFreeMIPSActiveHostsPerSnapshot"]:
        arr = cpu.get(k, []) or []
        rec["cpu_mean_" + k] = mean(arr)
        rec["cpu_len_" + k] = len(arr)
        rec["cpu_sum_" + k] = sum(arr) if arr else float("nan")
    av = cpu.get("totalAvailableMIPS", []) or []
    rec["cpu_min_totalAvailableMIPS"] = min(av) if av else None
    rec["cpu_max_totalAvailableMIPS"] = max(av) if av else None
    ram = d.get("ramResults", {})
    ar = ram.get("totalAllocatedRAM", []) or []
    rec["ram_alloc_first"] = ar[0] if ar else None
    rec["ram_alloc_min"] = min(ar) if ar else None
    rec["ram_alloc_max"] = max(ar) if ar else None
    tar = ram.get("totalAvailableRAM", []) or []
    rec["ram_avail_first"] = tar[0] if tar else None
    sl = d.get("slaResults", {})
    for k in ["totalRequestedMipsPerTime", "totalAllocatedMipsPerTime",
              "totalNonSatisfiedMipsPerTime", "totalRequestedMips", "totalAllocatedMips",
              "totalNonSatisfiedMips"]:
        rec["sla_" + k] = sl.get(k)
    snap = d.get("snapshotResults", {})
    es = snap.get("energySnapshots", []) or []
    rec["snap_sum_energy"] = sum(es) if es else None
    rec["snap_len"] = len(es)
    nv = snap.get("numVmsInDatacenter", []) or []
    rec["snap_min_numVmsInDatacenter"] = min(nv) if nv else None
    t = d.get("timeResults", {})
    rec["t_lastClock"] = t.get("lastClock")
    rec["t_timeElapsed"] = t.get("timeElapsed")
    # fingerprint of the result sections (to detect bit-identical runs across folders)
    h = hashlib.sha1()
    for sec in ["cloudsimResults", "networkPhysicalResults", "cpuResults", "slaResults"]:
        h.update(json.dumps(d.get(sec, {}), sort_keys=True).encode())
    rec["result_sha1"] = h.hexdigest()
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="simulation output folder (read-only)")
    ap.add_argument("--cache", required=True, help="where to write runs.jsonl / runs.csv")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    folders = sorted(p for p in glob.glob(os.path.join(a.out, "*")) if os.path.isdir(p))
    recs = []
    for i, fo in enumerate(folders):
        files = sorted(glob.glob(os.path.join(fo, "*_data.json")))
        for fp in files:
            recs.append(record(fp))
        # other files in the folder
        allf = os.listdir(fo)
        recs.append({"folder": os.path.basename(fo), "file": "__FOLDER__",
                     "n_data": len(files), "n_files": len(allf),
                     "n_status": sum(1 for x in allf if x.startswith("status_")),
                     "n_migr_csv": sum(1 for x in allf if x.endswith("_migrations.csv")),
                     "n_corr_csv": sum(1 for x in allf if x.endswith("_correlations.csv")),
                     "status_lines": sum(sum(1 for _ in open(os.path.join(fo, x), encoding="utf-8", errors="replace"))
                                         for x in allf if x.startswith("status_")),
                     "status_values": json.dumps(sorted({ln.strip().split(",")[-1]
                                                         for x in allf if x.startswith("status_")
                                                         for ln in open(os.path.join(fo, x), encoding="utf-8", errors="replace") if ln.strip()}))})
        print(f"[{i+1}/{len(folders)}] {os.path.basename(fo)}: {len(files)} data files", file=sys.stderr)
    with open(os.path.join(a.cache, "runs.jsonl"), "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    print(f"wrote {len(recs)} records to {a.cache}", file=sys.stderr)


if __name__ == "__main__":
    main()
