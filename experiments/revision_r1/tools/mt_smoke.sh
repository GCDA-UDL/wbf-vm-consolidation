#!/bin/bash
# Host side (Git Bash). Stage 1 of the robustness check: smoke test, seed 0 of every technique and trace.
#   bash tools/mt_smoke.sh
# - mt_smoke:   lists/mt_smoke.txt (36 runs: MU, MMT, RS, MC, WPSP, WP, WBP, AMOVMC, EUQ-VMC), image
#               metacloudsim, 9 in parallel (MT_PAR_SMOKE);
# - mt_smokenp: lists/mt_smoke_neural.txt (4 BB+NeoPro runs), image metacloudsim-neural, 4 in
#               parallel (MT_PAR_SMOKENP).
# Samples the memory of both containers every 15 s (runlogs/mt_smoke/_mem.log), waits for both, then
# verifies the runs (runlogs/mt_smoke/_verify.md; tables/mt_verify_runs.md is the check of the 1,200 runs,
# written by tools/mt_collect.sh). The smoke results are seed 0 of the campaign; the campaign lists skip
# them later.
set -eu
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/.."
bash tools/mt_start_campaign.sh mt_smoke mt_smoke.txt "${MT_PAR_SMOKE:-9}" "${IMAGE:-metacloudsim}"
bash tools/mt_start_campaign.sh mt_smokenp mt_smoke_neural.txt "${MT_PAR_SMOKENP:-4}" "${IMAGE_NEURAL:-metacloudsim-neural}"
mkdir -p runlogs/mt_smoke
running() { docker inspect -f '{{.State.Running}}' "$@" 2>/dev/null | grep -q true; }
while running mcs_mt_smoke mcs_mt_smokenp; do
  docker stats --no-stream --format '{{.Name}} {{.MemUsage}} {{.CPUPerc}}' mcs_mt_smoke mcs_mt_smokenp 2>/dev/null \
    | sed "s/^/$(date '+%F %T') /" >> runlogs/mt_smoke/_mem.log || true
  sleep 15
done
echo "container exit codes: mcs_mt_smoke $(docker wait mcs_mt_smoke), mcs_mt_smokenp $(docker wait mcs_mt_smokenp)"
tail -n 3 runlogs/mt_smoke/_campaign.log runlogs/mt_smokenp/_campaign.log
PYTHONIOENCODING=utf-8 python -B tools/mt_verify_runs.py --lists mt_smoke.txt,mt_smoke_neural.txt \
  --out runlogs/mt_smoke/_verify.md
