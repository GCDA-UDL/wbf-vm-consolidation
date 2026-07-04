#!/usr/bin/env python3
"""
Full Facebook Prophet vs. NeuralProphet comparison on the four workloads.
All metrics (composite energy, SLA, migrations, ESV, ME, RAM in BW, hosts, CPU dispersion).

Reads the per-seed result files produced by the simulator:
  - Prophet (FP):  output/paper4_full_<wl>_prophet/*_data.json
  - NeuralProphet: output/exp_np_<wl>/*_data.json (and exp_neuralprophet/ for PlanetLab)

Usage (from the repository root, after running the experiments):
  python3 experiments/neuralprophet/compare_fp_np.py --out RESULTS_4WORKLOADS.md
"""
import argparse, glob, json, os, collections

OUT_DIR = os.environ.get("OUT_DIR", "output")
WL = ["planetlab", "alibaba", "materna", "azure"]


def emig_paths(trib):
    return (4.096 * trib + 20.165) * 1.1 / 3.6e6


def metrics(d):
    cs = d["cloudsimResults"]; net = d["networkPhysicalResults"]; cpu = d["cpuResults"]
    e = cs.get("energyWithExtraHost", cs.get("energy", 0)) + emig_paths(net.get("totalRAMInBW", 0))
    sla = cs.get("slaOverall", 0) * 100
    alloc = cs.get("vmTotalAllocatedMips", 0)
    return {"energy": e, "sla": sla, "mig": cs.get("numberOfMigrations", 0),
            "ramBw": net.get("totalRAMInBW", 0) / 1e5,
            "hosts": cpu.get("totalUsedHosts", 0),
            "disp": cpu.get("medianCPUDispersionOfActiveHosts", 0) * 100,
            "esv": e * sla, "me": (alloc / e / 1e7) if e else 0}


def variant(d):
    sig = str(d["experimentConfiguration"].get("hostSignalProcessing"))
    return "WBF" if "bollinger" in sig else "WF"


def collect(patterns):
    agg = collections.defaultdict(list)
    for pat in patterns:
        for fp in glob.glob(pat):
            try: d = json.load(open(fp))
            except Exception: continue
            agg[variant(d)].append(metrics(d))
    out = {}
    for k, rows in agg.items():
        out[k] = {m: sum(r[m] for r in rows) / len(rows) for m in rows[0]}
        out[k]["n"] = len(rows)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="RESULTS_4WORKLOADS.md")
    args = ap.parse_args()

    lines = ["# Facebook Prophet vs NeuralProphet — 4 workloads, full metrics\n\n"]
    lines.append("FP = Facebook Prophet (our forecaster). NP = NeuralProphet. ")
    lines.append("Energy = composite (host + network migration). Lower is better, except ME (higher).\n\n")

    print(f"{'workload':10} {'tech':4} {'forecaster':12} {'E':>6} {'SLA':>6} {'mig':>6} {'ESV':>7} {'ME':>5} {'RAMbw':>7}")
    for wl in WL:
        fp = collect([f"{OUT_DIR}/paper4_full_{wl}_prophet/*_data.json"])
        np_pats = [f"{OUT_DIR}/exp_np_{wl}/*_data.json"]
        if wl == "planetlab":
            np_pats.append(f"{OUT_DIR}/exp_neuralprophet/*_data.json")
        npr = collect(np_pats)
        lines.append(f"## {wl}\n\n")
        lines.append("| Technique | Forecaster | Energy | SLA % | Migr | ESV | ME | RAM in BW |\n")
        lines.append("|---------|-----------|--------|-------|------|-----|----|-----------|\n")
        for tech in ["WF", "WBF"]:
            for label, src in [("Facebook Prophet", fp), ("NeuralProphet", npr)]:
                m = src.get(tech)
                if not m:
                    continue
                print(f"{wl:10} {tech:4} {label:12} {m['energy']:6.1f} {m['sla']:6.2f} "
                      f"{m['mig']:6.0f} {m['esv']:7.1f} {m['me']:5.2f} {m['ramBw']:7.1f}")
                star = " **" if label == "Facebook Prophet" else ""
                lines.append(f"| {tech}{star} | {label}{star} | {m['energy']:.1f} | {m['sla']:.2f} | "
                             f"{m['mig']:.0f} | {m['esv']:.1f} | {m['me']:.2f} | {m['ramBw']:.1f} |\n")
        lines.append("\n")

    lines.append("## Conclusion\n\nFacebook Prophet vs NeuralProphet per workload: ")
    lines.append("FP generally wins (fewer migrations / SLA / energy). NeuralProphet struggles with the ")
    lines.append("short 30-step windows (its lr_range_test does not converge); FP is robust with little data.\n")
    with open(args.out, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
