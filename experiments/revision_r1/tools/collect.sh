#!/bin/bash
# Host side: rebuild the per-run cache and every table from what is on disk now.
#   bash tools/collect.sh
# Inputs: output/ (raw outputs of the campaigns), runlogs/t1timing/_timing.log (decision time),
# ../../analysis_revision/cache/runs.jsonl (cache of the campaign behind the main tables; only for
# rerun_vs_stored.md) and forecast_accuracy/fa_raw_v2.csv.
set -eu
cd "$(dirname "$0")/.."
mkdir -p cache
PYTHONIOENCODING=utf-8 python -B ../../analysis_revision/extract_runs.py --out output --cache cache 2> cache/extract.log
PYTHONIOENCODING=utf-8 python -B tools/build_tables.py --timing-campaigns t1timing
if [ -s forecast_accuracy/fa_raw_v2.csv ]; then
  PYTHONIOENCODING=utf-8 python -B forecast_accuracy/fa_tables.py > /dev/null
  cp forecast_accuracy/forecast_accuracy.md forecast_accuracy/tab_forecast_accuracy.tex tables/
fi
ls tables
