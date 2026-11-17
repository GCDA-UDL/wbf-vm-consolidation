#!/bin/bash
# Runs inside the container, before run_singles.sh (called by mt_start_campaign.sh). Writes one PREFLIGHT
# line to runlogs/<campaign>/_campaign.log with the image, the versions of the forecasting packages and of
# Java and the thread variables, and stops the campaign (exit 1, nothing is simulated) if the list has
# BB+NeoPro runs and neuralprophet cannot be imported in this image.
#   bash /tools/mt_preflight.sh <list_file> <campaign_name> <image>
set -u
LIST="$1"; CAMP="$2"; IMAGE="$3"
LOGDIR="/hostlogs/$CAMP"
mkdir -p "$LOGDIR"
VERS=$(python3.8 - 2>/dev/null <<'EOF'
import importlib
import importlib.metadata as md
out = []
for m in ("prophet", "neuralprophet", "torch", "pandas", "numpy"):
    try:
        mod = importlib.import_module(m)   # the module must import, not only be installed
    except Exception:
        out.append(f"{m}=MISSING")
        continue
    v = getattr(mod, "__version__", None)
    if not v:                               # neuralprophet 0.2.7 has no __version__
        try:
            v = md.version(m)
        except Exception:
            v = "?"
    out.append(f"{m}={v}")
print(" ".join(out))
EOF
)
JV=$(java -version 2>&1 | head -1 | tr -d '"')
echo "[$(date '+%F %T')] PREFLIGHT image=$IMAGE list=$LIST $VERS java=[$JV] OMP=${OMP_NUM_THREADS:-unset} STAN=${STAN_NUM_THREADS:-unset} MKL=${MKL_NUM_THREADS:-unset} OPENBLAS=${OPENBLAS_NUM_THREADS:-unset}" >> "$LOGDIR/_campaign.log"
if grep -q '__bbneopro_' "$LIST" && ! echo "$VERS" | grep -q 'neuralprophet=[0-9]'; then
  echo "[$(date '+%F %T')] ABORT list=$LIST has BB+NeoPro runs but neuralprophet is not importable in $IMAGE" >> "$LOGDIR/_campaign.log"
  exit 1
fi
exit 0
