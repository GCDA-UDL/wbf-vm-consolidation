#!/bin/bash
# Host side (Linux, macOS or Git Bash on Windows). Launches (or resumes) the forecast-accuracy
# study as a detached container.
#   bash tools/start_fa.sh <procs> [protocols, default B,A] [traces, comma-separated, default all 13]
# Raw results: forecast_accuracy/$FA_OUT (appended as each VM finishes; resumable: the blocks
# already present in the file are skipped). Log: forecast_accuracy/fa_run.log
# Variables:
#   PKG     repository root (default: two levels above this folder); only workloads/ is read
#   IMAGE   Docker image (default: metacloudsim, the tag built by `docker compose build`)
#   FA_OUT  name of the raw CSV inside forecast_accuracy/ (default: fa_raw_v2.csv, the shipped
#           file, which is complete; give another name to compute everything again)
set -eu
export MSYS_NO_PATHCONV=1
# absolute path of a folder; on Git Bash in the Windows form that Docker expects
abspath() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }
E="$(abspath "$(dirname "$0")/..")"
PKG="$(abspath "${PKG:-$E/../..}")"
IMAGE="${IMAGE:-metacloudsim}"
FA_OUT="${FA_OUT:-fa_raw_v2.csv}"
PROCS="${1:-6}"; PROT="${2:-B,A}"; TRACES="${3:-}"
TR=""; if [ -n "$TRACES" ]; then TR="--traces $TRACES"; fi
docker rm -f mcs_fa >/dev/null 2>&1 || true
docker run -d --name mcs_fa \
  -e OMP_NUM_THREADS=1 -e STAN_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 \
  -v "$PKG/workloads:/workspace/workloads:ro" -v "$E/forecast_accuracy:/fa" \
  "$IMAGE" bash -c "python3.8 /fa/fa_revision.py --workloads /workspace/workloads --out /fa/$FA_OUT --procs $PROCS --protocols $PROT $TR >> /fa/fa_run.log 2>&1"
