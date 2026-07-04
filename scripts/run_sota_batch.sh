#!/bin/bash
# Run a list of experiments (testbed expand -> folder execute) for the SOTA comparison.
# Usage (inside container):  bash scripts/run_sota_batch.sh exp1 exp2 ...
set -u
cd /workspace
ts() { date '+%H:%M:%S'; }
echo "[$(ts)] START: $*"
for exp in "$@"; do
  mkdir -p "generatedExperiments/$exp" "output/$exp" "results/$exp"
  echo "[$(ts)] === $exp : testbed ==="
  java -jar metacloud.jar testbed "$exp" || { echo "[$(ts)] FAIL testbed $exp"; exit 1; }
  echo "[$(ts)] === $exp : folder ==="
  java -jar metacloud.jar folder "$exp"   || { echo "[$(ts)] FAIL folder $exp"; exit 1; }
  n=$(ls output/$exp/*_data.json 2>/dev/null | wc -l)
  echo "[$(ts)] === $exp DONE ($n results) ==="
done
echo "[$(ts)] ALL DONE"
