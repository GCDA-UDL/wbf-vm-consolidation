#!/usr/bin/env python3
"""Configs and run lists of the robustness check on four additional traces (runs `mt_*`).

  python -B tools/mt_gen.py            (from experiments/revision_r1/)

1. Base configs, testbed/mt_<trace>_<family>.json: clones of the paper's configs of the same
   provider and technique family (paper4_full_<p>_static, paper4_full_<p>_prophet_st, amovmc_<p>,
   euqvmc_<p>, np_<p>_st), with ONLY `name`, `experimentOutputFolder` and `workloadTrace` changed
   (dataStartStep stays 0: see tables/mt_trace_check.md).  An existing file is never overwritten with
   different content.
2. Single-run configs, testbed/mt_<trace>__<tag>_sNN.json, written by
   tools/make_singles.py, the tool of the other revision experiments, with the same --set values it used (t0/h2 for the
   classical policies, gen_t1.sh for LVP = WPSP, WP and WBP; nothing for AMOVMC, EUQ-VMC and
   BB+NeoPro, whose configs already fix the technique).  4 traces x 10 techniques x 30 seeds = 1 200.
3. Run lists (lists/), seed-major so that an interrupted campaign leaves complete seed pairs:
   mt_fast.txt (MU, MMT, RS, MC, WPSP: 600), mt_prophet.txt (WP, WBP: 240), mt_sota.txt (AMOVMC,
   EUQ-VMC: 240), mt_neural.txt (BB+NeoPro: 120), mt_smoke.txt (seed 0, every technique except
   BB+NeoPro: 36) and mt_smoke_neural.txt (seed 0, BB+NeoPro: 4).
Proof that the configs differ from their templates only in those fields: tools/mt_diff_configs.py.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mt_common as M  # noqa: E402

os.chdir(M.EXP)


def write_new(path, text):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            if fh.read() == text:
                return "unchanged"
        raise SystemExit(f"refusing to overwrite an existing file with different content: {path}")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return "written"


# 1. base configs ---------------------------------------------------------------------------------
fams = sorted({t[2] for t in M.TECHS})
nb = {"written": 0, "unchanged": 0}
for tr in M.TRACES:
    for fam in fams:
        tpl = M.template_name(tr["provider"], fam)
        with open(os.path.join(M.TESTBED, tpl + ".json"), encoding="utf-8") as fh:
            d = json.load(fh)                       # key order of the template is kept
        new = M.base_name(tr, fam)
        d["name"] = [new]
        d["experimentOutputFolder"] = [new]
        d["workloadTrace"] = [M.workload_trace(tr)]
        nb[write_new(os.path.join(M.TESTBED, new + ".json"), json.dumps(d, indent=2) + "\n")] += 1
print(f"base configs: {nb}")

# 2. single-run configs with the November tool ------------------------------------------------------
n_single = 0
for tr in M.TRACES:
    for tag, label, fam, sets, _ in M.TECHS:
        cmd = [sys.executable, "-B", os.path.join("tools", "make_singles.py"), "--pkg", M.PKG,
               "--base", M.base_name(tr, fam), "--exp", tr["exp"], "--tag", tag,
               "--seeds", f"{M.SEEDS[0]}-{M.SEEDS[-1]}"]
        for k, v in sets.items():
            cmd += ["--set", f"{k}={json.dumps(v)}"]
        out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()
        n_single += len(M.SEEDS)
        print(f"  {tr['exp']:12} {tag:9} <- {M.base_name(tr, fam):26} {' '.join(cmd[13:]) or '(no --set)'} | {out}")
print(f"single-run configs: {n_single}")

# 3. lists ----------------------------------------------------------------------------------------
lists = {k: [] for k in M.LIST_FILES}
for s in M.SEEDS:
    for tr in M.TRACES:
        for tag, _, _, _, lst in M.TECHS:
            lists[lst].append(M.single_name(tr, tag, s))
smoke = [M.single_name(tr, tag, 0) for tag in ("wp", "wbp", "amovmc", "euqvmc", "mu", "mmt", "rs", "mc", "wpsp")
         for tr in M.TRACES]
smoke_np = [M.single_name(tr, "bbneopro", 0) for tr in M.TRACES]
out = {M.LIST_FILES[k]: v for k, v in lists.items()}
out[M.SMOKE_FILE] = smoke
out[M.SMOKE_NEURAL_FILE] = smoke_np
for fn, names in out.items():
    with open(os.path.join(M.LISTS, fn), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(names) + "\n")
    print(f"lists/{fn}: {len(names)} runs")
