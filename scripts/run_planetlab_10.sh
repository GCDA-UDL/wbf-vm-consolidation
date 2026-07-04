#!/bin/bash
# Full PlanetLab 10-trace reproduction (Table 6).
# Loops the 10 CloudSim days; each config runs 30 seeds x 2 signals (none=WF,
# bollinger=WBF) with Facebook Prophet. testbed expands -> folder executes.
# Usage (inside container):  bash scripts/run_planetlab_10.sh [day ...]
set -u
cd /workspace

DAYS=("20110303" "20110306" "20110309" "20110322" "20110325" \
      "20110403" "20110409" "20110411" "20110412" "20110420")
# optional: restrict to the days passed as arguments
if [ "$#" -gt 0 ]; then DAYS=("$@"); fi

ts() { date '+%Y-%m-%d %H:%M:%S'; }
echo "[$(ts)] START PlanetLab 10-trace: ${DAYS[*]}"

for day in "${DAYS[@]}"; do
  exp="p4_pl_${day}"
  mkdir -p "generatedExperiments/$exp" "output/$exp" "results/$exp"
  echo "[$(ts)] === $exp : testbed (expand) ==="
  java -jar metacloud.jar testbed "$exp"        || { echo "[$(ts)] FAIL testbed $exp"; exit 1; }
  echo "[$(ts)] === $exp : folder (execute 60 sims) ==="
  java -jar metacloud.jar folder "$exp"          || { echo "[$(ts)] FAIL folder $exp"; exit 1; }
  n=$(ls output/$exp/*_data.json 2>/dev/null | wc -l)
  echo "[$(ts)] === $exp DONE : $n result files ==="
done

echo "[$(ts)] ALL DONE"
