#!/bin/bash
# Host side: single testbeds and list of the decision-time runs (48 runs).
#   bash tools/gen_timing.sh
# The six variants of the closed-loop campaign (see gen_t1.sh) on one trace per workload
# (PlanetLab day 20110303, Alibaba, Materna, Azure) with seeds 0 and 1, in output folders tm_*.
# These runs are executed alone (2 at a time, nothing else running) to read the time of a
# consolidation decision without contention.
# In the campaign these testbeds were written with make_singles.py by hand; this script was added
# for the package and writes the same files and the same list.
# The single testbeds are written to <repository>/testbed/ (ignored by git); the repository root
# is taken from the location of this script and can be changed with the variable PKG.
set -eu
cd "$(dirname "$0")/.."
PKG="${PKG:-../..}"
: > lists/t1timing.txt
for b in pl_20110303:p4_pl_20110303_st alibaba:paper4_full_alibaba_prophet_st materna:paper4_full_materna_prophet_st azure:paper4_full_azure_prophet_st; do
  tr="${b%%:*}"; base="${b##*:}"
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "tm_$tr" --tag lvp    --seeds 0-1 --set 'hostForecastingTechnique=["last"]' --set 'hostSignalProcessing=["none"]' --list lists/t1timing.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "tm_$tr" --tag lvpbb  --seeds 0-1 --set 'hostForecastingTechnique=["last"]' --set 'hostSignalProcessing=["bollinger", 5, 0.5]' --list lists/t1timing.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "tm_$tr" --tag ewma   --seeds 0-1 --set 'hostForecastingTechnique=["simpleExpSmoothing", 0.8]' --set 'hostSignalProcessing=["none"]' --list lists/t1timing.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "tm_$tr" --tag ewmabb --seeds 0-1 --set 'hostForecastingTechnique=["simpleExpSmoothing", 0.8]' --set 'hostSignalProcessing=["bollinger", 5, 0.5]' --list lists/t1timing.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "tm_$tr" --tag wp     --seeds 0-1 --set 'hostForecastingTechnique=["fbProphet"]' --set 'hostSignalProcessing=["none"]' --list lists/t1timing.txt > /dev/null
  python -B tools/make_singles.py --pkg "$PKG" --base "$base" --exp "tm_$tr" --tag wbp    --seeds 0-1 --set 'hostForecastingTechnique=["fbProphet"]' --set 'hostSignalProcessing=["bollinger", 5, 0.5]' --list lists/t1timing.txt > /dev/null
done
wc -l lists/t1timing.txt
