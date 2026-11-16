#!/bin/bash
# Host side (Linux, macOS or Git Bash on Windows). Launches one campaign as a DETACHED container
# that survives the shell: the inputs are copied from the repository (mounted read-only) into the
# container filesystem (fast), results and logs are copied to the host through bind mounts as each
# run ends.
#   bash tools/start_campaign.sh <campaign> <list_file_name_in_lists/> <parallel> [xmx]
# Results: experiments/revision_r1/output/<exp>/   Logs: experiments/revision_r1/runlogs/<campaign>/
# Resume after an interruption: run the same command again (finished runs are skipped).
# Variables:
#   PKG    repository root (default: two levels above this folder); its testbed/ must hold the
#          single testbeds written by tools/gen_t1.sh and tools/gen_t3.sh
#   IMAGE  Docker image (default: metacloudsim, the tag built by `docker compose build`)
set -eu
export MSYS_NO_PATHCONV=1
# absolute path of a folder; on Git Bash in the Windows form that Docker expects
abspath() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }
E="$(abspath "$(dirname "$0")/..")"
PKG="$(abspath "${PKG:-$E/../..}")"
IMAGE="${IMAGE:-metacloudsim}"
CAMP="$1"; LIST="$2"; PAR="${3:-16}"; XMX="${4:-640m}"; EXTRA="${5:-}"   # 5th: extra JVM options (not used)
mkdir -p "$E/output" "$E/runlogs"
docker rm -f "mcs_$CAMP" >/dev/null 2>&1 || true
docker run -d --name "mcs_$CAMP" \
  -e OMP_NUM_THREADS=1 -e STAN_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 \
  -e JAVA_XMX="$XMX" -e JAVA_EXTRA="$EXTRA" \
  -v "$PKG:/pkgsrc:ro" -v "$E/lists:/lists:ro" -v "$E/tools:/tools:ro" \
  -v "$E/output:/hostout" -v "$E/runlogs:/hostlogs" \
  "$IMAGE" bash -c "cd /pkgsrc && cp -r environment hosts interactions launcher.json metacloud.jar pymodule scripts testbed topologies vms workloads /workspace/ && bash /tools/run_singles.sh /lists/$LIST $PAR $CAMP"
