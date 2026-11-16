#!/bin/bash
# Host side: single testbeds and list of the Bollinger sensitivity campaign.
#   bash tools/gen_t3.sh <seeds>            e.g. 0-9
# WBP (psp2 + fbProphet + Bollinger) with one-at-a-time variations around (5, 0.5).
# The baseline (5, 0.5) is the `wbp` variant of the closed-loop campaign (cl_*), same mode.
# The single testbeds are written to <repository>/testbed/ (ignored by git); the repository root
# is taken from the location of this script and can be changed with the variable PKG.
set -eu
SEEDS="${1:-0-9}"
cd "$(dirname "$0")/.."
PKG="${PKG:-../..}"
: > lists/t3.txt
BASES=""
for d in 20110303 20110306 20110309 20110322 20110325 20110403 20110409 20110411 20110412 20110420; do BASES="$BASES pl_$d:p4_pl_${d}_st"; done
BASES="alibaba:paper4_full_alibaba_prophet_st materna:paper4_full_materna_prophet_st azure:paper4_full_azure_prophet_st $BASES"
for cfg in "n3a05:3:0.5" "n10a05:10:0.5" "n20a05:20:0.5" "n5a10:5:1.0" "n5a20:5:2.0" "n5a15:5:1.5"; do
  tag="${cfg%%:*}"; rest="${cfg#*:}"; n="${rest%%:*}"; al="${rest##*:}"
  for b in $BASES; do
    tr="${b%%:*}"; base="${b##*:}"
    python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "bs_$tr" --tag "$tag" --seeds "$SEEDS" --set 'hostForecastingTechnique=["fbProphet"]' --set "hostSignalProcessing=[\"bollinger\", $n, $al]" --list lists/t3.txt > /dev/null
  done
done
wc -l lists/t3.txt
