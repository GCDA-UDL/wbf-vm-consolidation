#!/bin/bash
# Resume of the BB+NeoPro campaign after power cut: only the 4 remaining experiments.
# Completed experiments (9x30 sims) are NOT touched.
export OMP_NUM_THREADS=1 STAN_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
EXPS="np_pl_20110409_st np_pl_20110411_st np_pl_20110412_st np_pl_20110420_st"
for e in $EXPS; do
  echo "===== $e  $(date +%H:%M:%S) ====="
  java -jar metacloud.jar testbed "$e" && java -jar metacloud.jar folder "$e" || { echo "FAIL $e"; exit 1; }
done
echo "NP_RESUME_DONE"
