#!/usr/bin/env python3
"""Per-run cache of the robustness-check runs only (output folders mt_*), in the format of
../../analysis_revision/extract_runs.py: its record() function is imported, and the per-folder record is the one
its main() writes.  Read-only on output/; writes <cache>/runs.jsonl.  The shared cache/ of the other
experiments is not touched, so their tables (inventory.md included) do not change.

  python -B tools/mt_extract.py [--out output] [--cache cache_mt] [--folders mt_materna2,...]
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mt_common as M  # noqa: E402

sys.path.insert(0, M.ANALYSIS)
from extract_runs import record  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.join(M.EXP, "output"))
ap.add_argument("--cache", default=os.path.join(M.EXP, "cache_mt"))
ap.add_argument("--folders", default=",".join(t["exp"] for t in M.TRACES),
                help="comma-separated output folders (default: the four mt_ folders)")
a = ap.parse_args()
os.makedirs(a.cache, exist_ok=True)

recs = []
for name in [f for f in a.folders.split(",") if f]:
    fo = os.path.join(a.out, name)
    if not os.path.isdir(fo):
        print(f"{name}: no folder yet", file=sys.stderr)
        continue
    files = sorted(glob.glob(os.path.join(fo, "*_data.json")))
    for fp in files:
        recs.append(record(fp))
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
                                                     for ln in open(os.path.join(fo, x), encoding="utf-8", errors="replace")
                                                     if ln.strip()}))})
    print(f"{name}: {len(files)} data files", file=sys.stderr)
with open(os.path.join(a.cache, "runs.jsonl"), "w", encoding="utf-8") as fh:
    for r in recs:
        fh.write(json.dumps(r) + "\n")
print(f"wrote {len(recs)} records to {a.cache}", file=sys.stderr)
