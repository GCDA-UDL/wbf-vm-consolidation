#!/bin/bash
# BB+NeoPro campaign: NeuralProphet + Bollinger, single-thread, same 30 seeds,
# to fill the BB+NeoPro rows Guirado added to the SOTA table.
export OMP_NUM_THREADS=1 STAN_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
EXPS="np_alibaba_st np_materna_st np_azure_st np_pl_20110303_st np_pl_20110306_st np_pl_20110309_st np_pl_20110322_st np_pl_20110325_st np_pl_20110403_st np_pl_20110409_st np_pl_20110411_st np_pl_20110412_st np_pl_20110420_st"
for e in $EXPS; do
  echo "===== $e  $(date +%H:%M:%S) ====="
  java -jar metacloud.jar testbed "$e" && java -jar metacloud.jar folder "$e" || { echo "FAIL $e"; exit 1; }
done
echo "NP_CAMPAIGN_DONE"
