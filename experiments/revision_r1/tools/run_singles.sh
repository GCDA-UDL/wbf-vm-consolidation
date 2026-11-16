#!/bin/bash
# Runs inside the container. Executes every testbed named in a list file, each one in its
# own JVM, P at a time.
#   bash /tools/run_singles.sh <list_file> <parallel> <campaign_name>
# - Results are written by the simulator to /workspace/output/<exp>/ (container filesystem)
#   and copied to /hostout/<exp>/ (host bind mount) when the run ends.
# - Resumable: a run whose result already exists in /hostout is skipped.
# - The thread variables (OMP/STAN/MKL/OPENBLAS_NUM_THREADS) must be 1 in the container
#   environment; their values are written to the campaign log.
# - JVM heap capped with JAVA_XMX (default 640m) so that several JVMs fit in memory; the cap
#   does not enter the simulation logic.
# - Per run it keeps in /hostlogs/<campaign>/: one line in _campaign.log (status, wall time),
#   the simulator's own timing lines in _timing.log, and the full stdout gzipped.
set -u
LIST="$1"; PAR="${2:-8}"; CAMP="${3:-default}"
export LOGDIR="/hostlogs/$CAMP"
export JAVA_XMX="${JAVA_XMX:-640m}"
export JAVA_EXTRA="${JAVA_EXTRA:-}"   # extra JVM options (empty in the campaigns of the article)
cd /workspace
mkdir -p "$LOGDIR" generatedExperiments output results
echo "[$(date '+%F %T')] START list=$LIST parallel=$PAR Xmx=$JAVA_XMX extra=[$JAVA_EXTRA] OMP=${OMP_NUM_THREADS:-unset} STAN=${STAN_NUM_THREADS:-unset} MKL=${MKL_NUM_THREADS:-unset} OPENBLAS=${OPENBLAS_NUM_THREADS:-unset} host=$(hostname)" >> "$LOGDIR/_campaign.log"
run_one() {
  name="$1"
  exp="${name%%__*}"
  res="${name}_00000_data.json"
  if [ -s "/hostout/$exp/$res" ]; then echo "SKIP $name" >> "$LOGDIR/_campaign.log"; return 0; fi
  mkdir -p "generatedExperiments/$name" "output/$exp" "results/$name" "/hostout/$exp"
  t0=$(date +%s%N)
  java $JAVA_EXTRA "-Xmx$JAVA_XMX" -jar metacloud.jar folder "$name" 2>&1 | gzip -c > "$LOGDIR/$name.log.gz"
  rc=${PIPESTATUS[0]}
  t1=$(date +%s%N)
  wall=$(( (t1 - t0) / 1000000 ))
  if [ -s "output/$exp/$res" ]; then cp "output/$exp/$res" "/hostout/$exp/$res.part" && mv "/hostout/$exp/$res.part" "/hostout/$exp/$res"; st=OK; else st=FAIL; fi
  echo "$st $name rc=$rc wall_ms=$wall" >> "$LOGDIR/_campaign.log"
  zcat "$LOGDIR/$name.log.gz" | grep -a -E "Execution time|Python runtime exception|OutOfMemory|Exception in" | sed "s/^/$name | /" >> "$LOGDIR/_timing.log"
}
export -f run_one
grep -v '^\s*$' "$LIST" | xargs -P "$PAR" -I{} bash -c 'run_one "$@"' _ {}
echo "[$(date '+%F %T')] END list=$LIST ok=$(grep -c '^OK' "$LOGDIR/_campaign.log") fail=$(grep -c '^FAIL' "$LOGDIR/_campaign.log") skip=$(grep -c '^SKIP' "$LOGDIR/_campaign.log")" >> "$LOGDIR/_campaign.log"
