#!/usr/bin/env python3
"""Checks, run by run, that the simulations of the robustness check read the intended workload and
ran the intended technique.  Read-only on output/, runlogs/, pkg/; writes a Markdown report.

  python -B tools/mt_verify_runs.py                            all mt_ runs that have a result
  python -B tools/mt_verify_runs.py --lists mt_smoke.txt,mt_smoke_neural.txt
  python -B tools/mt_verify_runs.py --names cl_alibaba__lvp_s00 \
         --expect cl_alibaba=alibaba2018/alibaba2018_fixed_first_500_100_mostDiff:0 --out <file>   (test on old runs)

Per run (result output/<exp>/<name>_00000_data.json, log runlogs/<campaign>/<name>.log.gz):
  1. the configuration stored in the result: workload type, workloadTrace (folder), dataStartStep, seed,
     lastClock = 86400, and the technique fields equal to those of testbed/<name>.json;
  2. the log: the reader's "UtilizationModelPlanetLabInMemory path:" lines name exactly the 100 files of
     /workspace/workloads/<type>/<folder>; no "Exception in", "Python runtime exception", "OutOfMemory"
     or "Traceback" line;
  3. Alibaba only: the reader prints every row it reads; the 288 rows printed after each path line must be
     rows dataStartStep..dataStartStep+287 of that file in workloads, byte for byte (for the
     additional traces: index column 1150..1437 for day 5 and 2014..2301 for day 8);
  4. the campaign that ran it: image and package versions (PREFLIGHT line of mt_start_campaign.sh) and the
     wall time.  BB+NeoPro must have run in an image where neuralprophet is importable.
Exit code 1 if any checked run fails a check (runs without a result are reported as pending).
"""
import argparse
import glob
import gzip
import json
import os
import re
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mt_common as M  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--lists", default=",".join(list(M.LIST_FILES.values()) + [M.SMOKE_FILE, M.SMOKE_NEURAL_FILE]))
ap.add_argument("--names", default=None, help="comma-separated run names (instead of --lists)")
ap.add_argument("--expect", action="append", default=[],
                help="EXP=TYPE/FOLDER[:dataStartStep] for folders that are not mt_ traces (tests)")
ap.add_argument("--out", default=os.path.join(M.EXP, "tables", "mt_verify_runs.md"))
a = ap.parse_args()

EXPECT = {t["exp"]: (M.PROVIDERS[t["provider"]]["wtype"], t["folder"], t["start"]) for t in M.TRACES}
for e in a.expect:
    exp, rest = e.split("=", 1)
    path, _, start = rest.partition(":")
    wtype, folder = path.split("/", 1)
    EXPECT[exp] = (wtype, folder, int(start or 0))

if a.names:
    names = [n for n in a.names.split(",") if n]
else:
    names = []
    for fn in a.lists.split(","):
        with open(os.path.join(M.LISTS, fn), encoding="utf-8") as fh:
            names += [ln.strip() for ln in fh if ln.strip()]
names = list(dict.fromkeys(names))

# campaign logs: preflight (image, versions) and wall time per run
CAMP = {}
WALL = {}
for p in glob.glob(os.path.join(M.EXP, "runlogs", "*", "_campaign.log")):
    camp = os.path.basename(os.path.dirname(p))
    for ln in open(p, encoding="utf-8", errors="replace"):
        m = re.match(r"^\[[^\]]+\] PREFLIGHT image=(\S+) list=\S+ (.*)$", ln)
        if m:
            CAMP[camp] = dict(image=m.group(1), versions=m.group(2).strip())
        m = re.match(r"^(OK|FAIL) (\S+) rc=(\S+) wall_ms=(\d+)", ln)
        if m:
            WALL.setdefault(m.group(2), []).append((camp, m.group(1), int(m.group(4)) / 1000.0))
LOGS = defaultdict(list)
for p in glob.glob(os.path.join(M.EXP, "runlogs", "*", "*.log.gz")):
    LOGS[os.path.basename(p)[:-7]].append(p)

ERR = re.compile(r"Exception in|Python runtime exception|OutOfMemory|Traceback")
PATH = re.compile(r"^UtilizationModelPlanetLabInMemory path: (.+)$")


_ROWS = {}


def data_rows(path):
    if path not in _ROWS:
        with open(path, "rb") as fh:
            _ROWS[path] = re.split(r"\r\n|\r|\n", fh.read().decode("utf-8"))[1:]
    return _ROWS[path]


def tb_sig(d):
    """Technique fields of a testbed single, in the form stored in the result's experimentConfiguration."""
    v = lambda k: d[k][0]  # noqa: E731
    return dict(selectionPolicy=v("selectionPolicy"), hostForecastingTechnique=v("hostForecastingTechnique")[0],
                hostSignalProcessing=v("hostSignalProcessing")[0],
                hostSignalProcessingParams=list(v("hostSignalProcessing")[1:]),
                hostOverSaturationPolicy=v("hostOverSaturationPolicy"), vmMigrationPolicy=v("vmMigrationPolicy"),
                parameter=v("parameter"), vms=v("vms"), numCloudlets=v("numCloudlets"))


rows = []
problems = []
pending = []
for name in names:
    exp, rest = name.split("__", 1)
    tag, seed = rest.rsplit("_s", 1)
    seed = int(seed)
    res = os.path.join(M.EXP, "output", exp, name + "_00000_data.json")
    if not os.path.exists(res):
        pending.append(name)
        continue
    wtype, folder, start = EXPECT[exp]
    issues = []
    # 1. stored configuration
    with open(res, encoding="utf-8") as fh:
        d = json.load(fh)
    c = d.get("experimentConfiguration", {})
    if (c.get("workload"), c.get("workloadTrace"), c.get("dataStartStep"), c.get("randomSeed"), c.get("name")) != \
            (wtype, folder, start, seed, name + "_00000"):
        issues.append(f"config: workload {c.get('workload')}/{c.get('workloadTrace')} start {c.get('dataStartStep')} "
                      f"seed {c.get('randomSeed')} name {c.get('name')}")
    if d.get("timeResults", {}).get("lastClock") != 86400:
        issues.append(f"lastClock {d.get('timeResults', {}).get('lastClock')}")
    with open(os.path.join(M.TESTBED, name + ".json"), encoding="utf-8") as fh:
        want = tb_sig(json.load(fh))
    got = {k: c.get(k) for k in want}
    if got != want:
        issues.append("technique fields differ: " + ", ".join(f"{k} {got[k]!r} != {want[k]!r}" for k in want if got[k] != want[k]))
    # 2-3. log
    logs = sorted(LOGS.get(name, []), key=os.path.getmtime)
    rows_ok = "n/a"
    nfiles = 0
    nerr = 0
    if not logs:
        issues.append("no log")
    else:
        with gzip.open(logs[-1], "rt", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        nerr = sum(1 for ln in lines if ERR.search(ln))
        if nerr:
            issues.append(f"{nerr} error line(s) in the log")
        want_dir = f"/workspace/workloads/{wtype}/{folder}"
        pkg_dir = os.path.join(M.PKG, "workloads", wtype, folder)
        want_files = sorted(os.listdir(pkg_dir))
        seen = []
        bad_rows = 0
        for i, ln in enumerate(lines):
            m = PATH.match(ln)
            if not m:
                continue
            p = m.group(1).strip()
            seen.append(p)
            if wtype == "alibaba2018" and os.path.dirname(p) == want_dir:
                exp_rows = data_rows(os.path.join(pkg_dir, os.path.basename(p)))[start:start + M.NUM_SAMPLES]
                if lines[i + 1:i + 1 + M.NUM_SAMPLES] != exp_rows:
                    bad_rows += 1
        nfiles = len(set(seen))
        if {os.path.dirname(p) for p in seen} != {want_dir} or sorted({os.path.basename(p) for p in seen}) != want_files:
            issues.append(f"reader paths: {nfiles} distinct, folders {sorted({os.path.dirname(p) for p in seen})[:3]}")
        if wtype == "alibaba2018":
            rows_ok = f"{nfiles - bad_rows}/{nfiles}"
            if bad_rows:
                issues.append(f"{bad_rows} file(s) with rows other than {start}..{start + 287}")
    # 4. campaign
    w = WALL.get(name, [])
    camp = w[-1][0] if w else (os.path.basename(os.path.dirname(logs[-1])) if logs else "?")
    info = CAMP.get(camp, {})
    image = info.get("image", "(no PREFLIGHT line)")
    if tag == "bbneopro" and not re.search(r"neuralprophet=[0-9]", info.get("versions", "")):
        issues.append(f"BB+NeoPro run without a neuralprophet preflight (campaign {camp}, image {image})")
    wall = w[-1][2] if w else None
    rows.append(dict(name=name, exp=exp, tag=tag, ok=not issues, files=nfiles, rows=rows_ok, err=nerr,
                     camp=camp, image=image, wall=wall, nlogs=len(logs), issues=issues))
    if issues:
        problems.append((name, issues))

# report --------------------------------------------------------------------------------------------
md = ["# Verification of the runs of the robustness check", "",
      "Generated by `tools/mt_verify_runs.py` (read-only). Checks per run: configuration stored in the result "
      "(workload folder, dataStartStep, seed, technique fields equal to the testbed file, lastClock = 86400); "
      "reader paths in the log (the 100 files of the intended folder); Alibaba: the 288 rows printed by the "
      "reader equal rows dataStartStep..dataStartStep+287 of each file; no error line; image of the campaign.", "",
      f"Runs requested: {len(names)}; with a result: {len(rows)}; verified OK: {sum(r['ok'] for r in rows)}; "
      f"with problems: {len(problems)}; pending (no result yet): {len(pending)}.", ""]
by = defaultdict(list)
for r in rows:
    by[(r["exp"], r["tag"])].append(r)
md += ["| folder | technique | runs | OK | wall time mean (s) | image(s) |", "|---|---|---|---|---|---|"]
for (exp, tag), rs in sorted(by.items()):
    walls = [r["wall"] for r in rs if r["wall"] is not None]
    lab = M.TECH_BY_TAG[tag][1] if tag in M.TECH_BY_TAG else tag
    md.append(f"| {exp} | {lab} | {len(rs)} | {sum(r['ok'] for r in rs)} | "
              f"{(f'{st.mean(walls):.1f}' if walls else '-')} | {', '.join(sorted({r['image'] for r in rs}))} |")
if len(rows) <= 60:
    md += ["", "| run | OK | reader files | Alibaba rows as expected | error lines | campaign | wall (s) | logs |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['name']} | {r['ok']} | {r['files']} | {r['rows']} | {r['err']} | {r['camp']} | "
                  f"{r['wall'] if r['wall'] is not None else '-'} | {r['nlogs']} |")
md += ["", "Campaigns (PREFLIGHT line of `tools/mt_start_campaign.sh`):", ""]
for camp in sorted({r["camp"] for r in rows}):
    md.append(f"- {camp}: {CAMP.get(camp, {}).get('image', '(none)')} {CAMP.get(camp, {}).get('versions', '')}")
for camp in sorted({r["camp"] for r in rows}):
    p = os.path.join(M.EXP, "runlogs", camp, "_mem.log")
    if os.path.exists(p):
        peak = defaultdict(float)
        for ln in open(p, encoding="utf-8", errors="replace"):
            m = re.search(r"(mcs_\S+) ([0-9.]+)(GiB|MiB)", ln)
            if m:
                v = float(m.group(2)) * (1.0 if m.group(3) == "GiB" else 1 / 1024)
                peak[m.group(1)] = max(peak[m.group(1)], v)
        md.append(f"- memory peaks in `runlogs/{camp}/_mem.log`: " + ", ".join(f"{k} {v:.2f} GiB" for k, v in peak.items()))
if problems:
    md += ["", "## Problems", ""] + [f"- {n}: " + "; ".join(i) for n, i in problems]
if pending and len(pending) <= 60:
    md += ["", "Pending: " + ", ".join(pending)]
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(md) + "\n")
print("\n".join(md[:8 + len(by) + 2]))
if problems:
    print("\n".join(md[md.index("## Problems"):][:40]))
print(f"written {a.out}")
sys.exit(1 if problems else 0)
