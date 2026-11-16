#!/usr/bin/env python3
"""Regenerates every figure of the revision and the workload table.

Usage (from analysis_revision/figures):
  python -B make_all.py [--package ../..] [--cache ../cache] [--facts ../out/facts.json] \
         [--out ../out/figures] [--table-out ../out/tables] [--preview preview] \
         [--orig-workloads <workloads folder of the original project>]

--package is the root of this repository: only its workloads/ and topologies/ folders are read.
Nothing is written outside --out, --table-out, --preview and this folder.
The two notes written in this folder (WORKLOAD_STATS.md, TOPOLOGY.md) name their inputs by paths
relative to this folder, so they do not depend on where the repository is cloned.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--package", default=os.path.join(HERE, "..", ".."))
ap.add_argument("--cache", default=os.path.join(HERE, "..", "cache"))
ap.add_argument("--facts", default=os.path.join(HERE, "..", "out", "facts.json"))
ap.add_argument("--out", default=os.path.join(HERE, "..", "out", "figures"))
ap.add_argument("--table-out", default=os.path.join(HERE, "..", "out", "tables"))
ap.add_argument("--preview", default=os.path.join(HERE, "preview"))
ap.add_argument("--orig-workloads", default=None)
a = ap.parse_args()


def run(script, *args):
    cmd = [sys.executable, "-B", os.path.join(HERE, script)] + list(args)
    print(">>", script)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    subprocess.run(cmd, check=True, cwd=HERE, env=env)


def rel(path):
    """Path relative to this folder (the working directory of the scripts), with forward slashes."""
    try:
        return os.path.relpath(path, HERE).replace(os.sep, "/")
    except ValueError:                      # another drive (Windows): keep the path as given
        return os.path.abspath(path)


res = ["--cache", a.cache, "--out", a.out, "--preview", a.preview]
if os.path.exists(a.facts):
    res += ["--facts", a.facts]
run("fig_results.py", *res)
ws = ["--workloads", rel(os.path.join(a.package, "workloads")), "--table-out", a.table_out, "--fig-out", a.out,
      "--note-out", os.path.join(HERE, "WORKLOAD_STATS.md"), "--preview", a.preview]
if a.orig_workloads:
    ws += ["--orig-workloads", a.orig_workloads]
run("workload_stats.py", *ws)
run("fig_topology.py", "--topology",
    rel(os.path.join(a.package, "topologies", "fatTreeTopology_k-2_g-2_s-2_hs-2_h-16.json")),
    "--out", a.out, "--preview", a.preview, "--note", os.path.join(HERE, "TOPOLOGY.md"))
run("fig_wbp_cycle.py", "--out", a.out, "--preview", a.preview)
print("done")
