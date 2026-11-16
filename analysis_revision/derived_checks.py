#!/usr/bin/env python3
"""Derived quantities quoted in the prose of the revised manuscript, recomputed from out/facts.json.
Usage: python -B derived_checks.py out/facts.json
"""
import json
import sys

F = json.load(open(sys.argv[1], encoding="utf-8"))
WLS = ["planetlab", "alibaba", "materna", "azure"]
MAIN = ["MU", "MMT", "RS", "MC", "WPSP", "WP", "WBP"]
CLAS = ["MU", "MMT", "RS", "MC"]
A = F["agg"]


def m(wl, t, k):
    return A[wl][t][k]["mean"]


print("== energy component shares over the 7 main techniques and 4 workloads (% of total)")
ex, oo, mg, hs = [], [], [], []
for wl in WLS:
    for t in MAIN:
        tot = m(wl, t, "e_total")
        ex.append(100 * m(wl, t, "e_exec") / tot)
        oo.append(100 * m(wl, t, "e_onoff") / tot)
        mg.append(100 * m(wl, t, "e_mig") / tot)
        hs.append(100 * m(wl, t, "e_hosts") / tot)
print(f"execution  : {min(ex):.1f} .. {max(ex):.1f}")
print(f"on/off     : {min(oo):.2f} .. {max(oo):.2f}")
print(f"migration  : {min(mg):.2f} .. {max(mg):.2f}")
print(f"hosts total: {min(hs):.1f} .. {max(hs):.1f}")

print("\n== WBP vs classical, ranges over the 4 workloads")
for k in ["migr", "traffic", "e_total", "e_hosts", "sla"]:
    lo = min(F["derived"][wl][f"WBP_vs_classical_{k}"]["lo"] for wl in WLS)
    hi = max(F["derived"][wl][f"WBP_vs_classical_{k}"]["hi"] for wl in WLS)
    print(f"{k:8}: {lo:.1f} .. {hi:.1f} % lower")
    for wl in WLS:
        d = F["derived"][wl][f"WBP_vs_classical_{k}"]
        print(f"   {wl:9} {d['lo']:.1f} .. {d['hi']:.1f}")

print("\n== WP vs classical total energy")
for wl in WLS:
    d = F["derived"][wl]["WP_vs_classical_e_total"]
    print(f"   {wl:9} {d['lo']:.1f} .. {d['hi']:.1f}")

print("\n== WBP vs WP (Bollinger step): relative change of WBP with respect to WP, %")
for wl in WLS:
    print(f"   {wl:9} " + "  ".join(
        f"{k} {100 * (m(wl, 'WBP', k) / m(wl, 'WP', k) - 1):+.1f}" for k in
        ["migr", "traffic", "e_hosts", "e_total", "sla", "act_hosts"]))

print("\n== host energy of WBP relative to classical (% above = positive)")
for wl in WLS:
    vals = [100 * (m(wl, "WBP", "e_hosts") / m(wl, t, "e_hosts") - 1) for t in CLAS]
    print(f"   {wl:9} {min(vals):+.1f} .. {max(vals):+.1f}")

print("\n== spread of host energy and total energy among the 7 techniques (max/min - 1, %)")
for wl in WLS:
    for k in ["e_hosts", "e_total"]:
        v = [m(wl, t, k) for t in MAIN]
        print(f"   {wl:9} {k:8} {min(v):.2f} .. {max(v):.2f}  spread {100 * (max(v) / min(v) - 1):.1f}")

print("\n== break-even kappa (J per MB and hop) and multiples of the reference 0.512")
for wl in WLS:
    be = F["sens"][wl]["breakeven"]
    print(f"   {wl:9} first {max(0, min(be.values())):.2f}  all {max(0, max(be.values())):.2f}  "
          f"(x{max(0, max(be.values())) / 0.512:.2f})")

print("\n== SOTA: WBP vs competitors (positive = WBP lower), %")
for wl in WLS:
    for opp in ["BB+NeoPro", "AMOVMC", "EUQ-VMC"]:
        print(f"   {wl:9} vs {opp:9} " + "  ".join(
            f"{k} {F['derived'][wl][f'WBP_vs_{opp}_{k}']:+.1f}" for k in ["migr", "traffic", "e_total", "e_hosts", "sla"]))
print("   SLA ratios WBP/AMOVMC:", "  ".join(f"{wl} {m(wl, 'WBP', 'sla') / m(wl, 'AMOVMC', 'sla'):.1f}" for wl in WLS))
print("   active hosts AMOVMC/WBP:", "  ".join(f"{wl} {m(wl, 'AMOVMC', 'act_hosts') / m(wl, 'WBP', 'act_hosts'):.2f}" for wl in WLS))
print("   traffic EUQ/WBP:", "  ".join(f"{wl} {m(wl, 'EUQ-VMC', 'traffic') / m(wl, 'WBP', 'traffic'):.1f}" for wl in WLS))

print("\n== native placement vs shared (ratio native/shared)")
N = F["native"]
for wl in WLS:
    for meth in ["AMOVMC", "EUQ-VMC"]:
        s, n = N[wl][f"{meth} (shared)"], N[wl][f"{meth} (native)"]
        print(f"   {wl:9} {meth:8} " + "  ".join(f"{k} {n[k] / s[k]:.2f}" for k in ["e_total", "sla", "migr", "traffic", "esv"]))
print("   ExSLA WBP / AMOVMC(shared):", "  ".join(
    f"{wl} {N[wl][chr(92) + 'textit{WBP}']['esv'] / N[wl]['AMOVMC (shared)']['esv']:.1f}" for wl in WLS))

print("\n== family SLA relative to classical on Alibaba (ratio)")
fam = [m("alibaba", t, "sla") for t in ["WPSP", "WP", "WBP"]]
cl = [m("alibaba", t, "sla") for t in CLAS]
print(f"   family {min(fam):.2f}..{max(fam):.2f}; classical {min(cl):.2f}..{max(cl):.2f}; "
      f"ratios {min(fam) / max(cl):.2f} .. {max(fam) / min(cl):.2f}")
