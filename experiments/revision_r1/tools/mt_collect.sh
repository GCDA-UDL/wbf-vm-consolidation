#!/bin/bash
# Host side (Git Bash). Collection of the robustness check, separate from collect.sh so that the shared
# cache/ and the tables of the other experiments do not change:
#   1. tools/mt_extract.py      -> cache_mt/runs.jsonl (only the four mt_ output folders)
#   2. tools/mt_verify_runs.py  -> tables/mt_verify_runs.md (workload folder and rows read, technique, image)
#   3. tools/mt_build_table.py  -> tables/more_traces.md, tables/tab_more_traces.tex, tables/more_traces.json
#   bash tools/mt_collect.sh [options of mt_build_table.py, e.g. --competitors all]
set -eu
cd "$(dirname "$0")/.."
# Python with numpy and scipy (the table needs them); set MT_PYTHON to choose another interpreter.
PY="${MT_PYTHON:-python}"
mkdir -p cache_mt
PYTHONIOENCODING=utf-8 "$PY" -B tools/mt_extract.py --out output --cache cache_mt 2> cache_mt/extract.log
PYTHONIOENCODING=utf-8 "$PY" -B tools/mt_verify_runs.py > cache_mt/verify.log \
  || echo "WARNING: some runs failed the verification, see tables/mt_verify_runs.md"
tail -n 1 cache_mt/verify.log
PYTHONIOENCODING=utf-8 "$PY" -B tools/mt_build_table.py --cache cache_mt "$@"
