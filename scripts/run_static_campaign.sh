#!/bin/bash
# Reconciliation campaign: classical baselines (MU/MMT/RS/MC/WPSP) under the
# single reproduction environment, to rebuild Tables 6-9 consistent with Table 10.
EXPS="paper4_full_alibaba_static paper4_full_materna_static paper4_full_azure_static \
pl_static_20110303 pl_static_20110306 pl_static_20110309 pl_static_20110322 pl_static_20110325 \
pl_static_20110403 pl_static_20110409 pl_static_20110411 pl_static_20110412 pl_static_20110420"
for e in $EXPS; do
  echo "===== $e ====="
  java -jar metacloud.jar testbed "$e" && java -jar metacloud.jar folder "$e" || { echo "FAIL $e"; exit 1; }
done
echo "CAMPAIGN_DONE"
