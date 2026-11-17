#!/bin/bash
# Host side (Linux, macOS or Git Bash on Windows). As tools/start_campaign.sh, with the Docker image as a
# parameter (BB+NeoPro needs the image with NeuralProphet) and a preflight line in the campaign log
# (tools/mt_preflight.sh: image, versions of the forecasting packages and of Java; the campaign stops if a
# list with BB+NeoPro runs is started in an image where neuralprophet cannot be imported).
#   bash tools/mt_start_campaign.sh <campaign> <list_file_name_in_lists/> <parallel> [image] [xmx]
# image: 4th argument, else the variable IMAGE, else metacloudsim (the tag built by `docker compose build`);
#        BB+NeoPro: metacloudsim-neural (docker build -f Dockerfile.neural -t metacloudsim-neural .).
# Results: experiments/revision_r1/output/<exp>/   Logs: experiments/revision_r1/runlogs/<campaign>/
# Resume after an interruption: run the same command again (finished runs are skipped).
# PKG: repository root (default: two levels above this folder); its testbed/ must hold the single
#      testbeds written by tools/mt_gen.py.
# Working directory: /workspace (writable) before the preflight, because neuralprophet 0.2.7 opens
# logs.log in the current directory when it is imported and /pkgsrc is mounted read-only.
# LD_PRELOAD: the Dockerfile sets it; it is passed again for images built before that line, in which
# jpy fails to load ("undefined symbol: PyFloat_Type").
set -eu
export MSYS_NO_PATHCONV=1
abspath() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }
E="$(abspath "$(dirname "$0")/..")"
PKG="$(abspath "${PKG:-$E/../..}")"
CAMP="$1"; LIST="$2"; PAR="${3:-16}"; IMAGE="${4:-${IMAGE:-metacloudsim}}"; XMX="${5:-640m}"; EXTRA=""
[ -s "$E/lists/$LIST" ] || { echo "no such list: $E/lists/$LIST" >&2; exit 1; }
mkdir -p "$E/output" "$E/runlogs"
docker rm -f "mcs_$CAMP" >/dev/null 2>&1 || true
docker run -d --name "mcs_$CAMP" \
  -e OMP_NUM_THREADS=1 -e STAN_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 \
  -e JAVA_XMX="$XMX" -e JAVA_EXTRA="$EXTRA" \
  -e LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libpython3.8.so.1.0 \
  -v "$PKG:/pkgsrc:ro" -v "$E/lists:/lists:ro" -v "$E/tools:/tools:ro" \
  -v "$E/output:/hostout" -v "$E/runlogs:/hostlogs" \
  "$IMAGE" bash -c "cd /pkgsrc && cp -r environment hosts interactions launcher.json metacloud.jar pymodule scripts testbed topologies vms workloads /workspace/ && cd /workspace && bash /tools/mt_preflight.sh /lists/$LIST $CAMP $IMAGE && bash /tools/run_singles.sh /lists/$LIST $PAR $CAMP"
