#!/bin/bash
# Host side (Git Bash). Stages 2-4 of the robustness check, one after the other, then the collection.
# Run it after the smoke test (tools/mt_smoke.sh) has passed, detached so that it survives the terminal:
#   nohup bash tools/mt_run_all.sh > runlogs/mt_run_all.log 2>&1 &
# Stages (image, parallel JVMs; change with MT_PAR_FAST, MT_PAR_PROPHET, MT_PAR_SOTA, MT_PAR_NEURAL):
#   2) mt_fast    lists/mt_fast.txt    600 runs MU MMT RS MC WPSP  metacloudsim           5
#      mt_prophet lists/mt_prophet.txt 240 runs WP WBP              metacloudsim          13
#   3) mt_sota    lists/mt_sota.txt    240 runs AMOVMC EUQ-VMC      metacloudsim          18
#   4) mt_neural  lists/mt_neural.txt  120 runs BB+NeoPro           metacloudsim-neural  8
#   then bash tools/mt_collect.sh (cache_mt/, tables/more_traces.md, tables/tab_more_traces.tex)
# Keep the JVMs running at the same time at 18 or less (about 0.65 GB each, STATE.md).
# A stage ends when its containers exit; the next one starts only if every run of the stage has a result.
# Otherwise the script stops: look at runlogs/<campaign>/_campaign.log and relaunch (finished runs are skipped).
set -eu
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/.."
ts() { date '+%F %T'; }
missing() {   # number of runs of lists/<file> without a result in output/
  local n=0 name exp
  while read -r name; do
    [ -z "$name" ] && continue
    exp="${name%%__*}"
    [ -s "output/$exp/${name}_00000_data.json" ] || n=$((n + 1))
  done < "lists/$1"
  echo "$n"
}
require_complete() {
  for l in "$@"; do
    m=$(missing "$l")
    echo "[$(ts)] lists/$l: $m run(s) without a result"
    if [ "$m" != "0" ]; then echo "[$(ts)] STOP"; exit 1; fi
  done
}
if [ "${MT_SKIP_SMOKE_CHECK:-0}" != "1" ]; then require_complete mt_smoke.txt mt_smoke_neural.txt; fi

echo "[$(ts)] stage 2: mt_fast + mt_prophet"
bash tools/mt_start_campaign.sh mt_fast mt_fast.txt "${MT_PAR_FAST:-5}" "${IMAGE:-metacloudsim}"
bash tools/mt_start_campaign.sh mt_prophet mt_prophet.txt "${MT_PAR_PROPHET:-13}" "${IMAGE:-metacloudsim}"
echo "[$(ts)] exit codes: $(docker wait mcs_mt_fast) $(docker wait mcs_mt_prophet)"
require_complete mt_fast.txt mt_prophet.txt

echo "[$(ts)] stage 3: mt_sota"
bash tools/mt_start_campaign.sh mt_sota mt_sota.txt "${MT_PAR_SOTA:-18}" "${IMAGE:-metacloudsim}"
echo "[$(ts)] exit code: $(docker wait mcs_mt_sota)"
require_complete mt_sota.txt

echo "[$(ts)] stage 4: mt_neural"
bash tools/mt_start_campaign.sh mt_neural mt_neural.txt "${MT_PAR_NEURAL:-8}" "${IMAGE_NEURAL:-metacloudsim-neural}"
echo "[$(ts)] exit code: $(docker wait mcs_mt_neural)"
require_complete mt_neural.txt

echo "[$(ts)] collection"
bash tools/mt_collect.sh
echo "[$(ts)] done"
