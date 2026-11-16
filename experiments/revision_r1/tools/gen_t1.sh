#!/bin/bash
# Host side: writes the single testbeds and the lists of the closed-loop campaign.
#   bash tools/gen_t1.sh <seeds>            e.g. 0-29
# Variants (same selection psp2, same MAD rule, same placement ac; only the host forecaster
# and the Bollinger transform change):
#   lvp     last value, no Bollinger            (= WPSP of the paper, re-run)
#   lvpbb   last value + Bollinger(5, 0.5)
#   ewma    simpleExpSmoothing (level 0.8), no Bollinger
#   ewmabb  simpleExpSmoothing (level 0.8) + Bollinger(5, 0.5)
#   wp      fbProphet, no Bollinger             (= WP of the paper, re-run)
#   wbp     fbProphet + Bollinger(5, 0.5)       (= WBP of the paper, re-run)
# The single testbeds are written to <repository>/testbed/ (ignored by git); the repository root
# is taken from the location of this script and can be changed with the variable PKG.
set -eu
SEEDS="${1:-0-29}"
cd "$(dirname "$0")/.."
PKG="${PKG:-../..}"
: > lists/t1_fast.txt
: > lists/t1_prophet.txt
BASES=""
for d in 20110303 20110306 20110309 20110322 20110325 20110403 20110409 20110411 20110412 20110420; do BASES="$BASES pl_$d:p4_pl_${d}_st"; done
BASES="$BASES alibaba:paper4_full_alibaba_prophet_st materna:paper4_full_materna_prophet_st azure:paper4_full_azure_prophet_st"
for b in $BASES; do
  tr="${b%%:*}"; base="${b##*:}"
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "cl_$tr" --tag lvp    --seeds "$SEEDS" --set 'hostForecastingTechnique=["last"]' --set 'hostSignalProcessing=["none"]' --list lists/t1_fast.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "cl_$tr" --tag lvpbb  --seeds "$SEEDS" --set 'hostForecastingTechnique=["last"]' --set 'hostSignalProcessing=["bollinger", 5, 0.5]' --list lists/t1_fast.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "cl_$tr" --tag ewma   --seeds "$SEEDS" --set 'hostForecastingTechnique=["simpleExpSmoothing", 0.8]' --set 'hostSignalProcessing=["none"]' --list lists/t1_fast.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "cl_$tr" --tag ewmabb --seeds "$SEEDS" --set 'hostForecastingTechnique=["simpleExpSmoothing", 0.8]' --set 'hostSignalProcessing=["bollinger", 5, 0.5]' --list lists/t1_fast.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "cl_$tr" --tag wp     --seeds "$SEEDS" --set 'hostForecastingTechnique=["fbProphet"]' --set 'hostSignalProcessing=["none"]' --list lists/t1_prophet.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "cl_$tr" --tag wbp    --seeds "$SEEDS" --set 'hostForecastingTechnique=["fbProphet"]' --set 'hostSignalProcessing=["bollinger", 5, 0.5]' --list lists/t1_prophet.txt > /dev/null
done
wc -l lists/t1_fast.txt lists/t1_prophet.txt
