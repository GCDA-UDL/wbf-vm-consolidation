#!/usr/bin/env python3
"""Write one single-combination testbed JSON per simulation, so that every simulation
runs in its own JVM (`java -jar metacloud.jar folder <name>` regenerates and runs exactly
one configuration).

A base testbed (as shipped in testbed/) lists every swept parameter as a JSON array.  This
script fixes each array to one value: the seed, and the overrides given on the command line.

Usage:
  python -B make_singles.py --pkg <pkg> --base <base_testbed_name> --exp <output_folder_name>
         --tag <variant_tag> --seeds 0-29 [--set key=json_value ...] [--list <file_to_append>]

Example (EWMA + Bollinger on Materna, seeds 0-29):
  python -B make_singles.py --pkg pkg --base paper4_full_materna_prophet_st --exp cl_materna \
      --tag ewma_bb --seeds 0-29 \
      --set 'hostForecastingTechnique=["simpleExpSmoothing", 0.8]' \
      --set 'hostSignalProcessing=["bollinger", 5, 0.5]'

Each generated file is testbed/<exp>__<tag>_s<seed>.json; its output goes to
output/<exp>/<exp>__<tag>_s<seed>_00000_data.json.
"""
import argparse
import json
import os


def parse_seeds(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


ap = argparse.ArgumentParser()
ap.add_argument("--pkg", required=True)
ap.add_argument("--base", required=True)
ap.add_argument("--exp", required=True)
ap.add_argument("--tag", required=True)
ap.add_argument("--seeds", required=True)
ap.add_argument("--set", action="append", default=[])
ap.add_argument("--list", default=None)
a = ap.parse_args()

base = json.load(open(os.path.join(a.pkg, "testbed", a.base + ".json"), encoding="utf-8"))
over = {}
for kv in a.set:
    k, v = kv.split("=", 1)
    over[k] = json.loads(v)

names = []
for seed in parse_seeds(a.seeds):
    d = json.loads(json.dumps(base))
    name = f"{a.exp}__{a.tag}_s{seed:02d}"
    d["override"] = []
    d["name"] = [name]
    d["experimentOutputFolder"] = [a.exp]
    d["randomSeed"] = [seed]
    for k, v in over.items():
        d[k] = [v]
    # every swept array must have exactly one element
    multi = [k for k, v in d.items() if k != "override" and isinstance(v, list) and len(v) != 1]
    if multi:
        raise SystemExit(f"parameters still swept in {a.base}: {multi}; fix them with --set")
    with open(os.path.join(a.pkg, "testbed", name + ".json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=1)
    names.append(name)

if a.list:
    with open(a.list, "a", encoding="utf-8", newline="\n") as fh:
        for n in names:
            fh.write(n + "\n")
print(f"{len(names)} single testbeds written for {a.exp}/{a.tag}")
