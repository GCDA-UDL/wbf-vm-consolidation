# SOTA/ — compared methods and analysis of the submitted version

This folder holds two different things.

1. **Sources of the compared methods** (`src/`): the Java classes of AMOVMC and EUQ-VMC that are
   compiled into `metacloud.jar`. The mapping from the equations of the original articles to the
   code is in [../SOTA_COMPARISON.md](../SOTA_COMPARISON.md); `scripts/build_sota.sh` rebuilds them.
2. **Analysis of the submitted version of the manuscript** (24 September 2026): the Python scripts
   and the Markdown tables of this folder. They are kept for traceability and are superseded by
   [../analysis_revision/](../analysis_revision/README.md) and
   [../results/reference/](../results/reference/README.md), which follow the revised manuscript.

## What changed in the revision

- **Energy.** The scripts of this folder compute the composite energy of the submitted version:
  host energy + (4.096 × RAM-in-BW + 20.165) × 1.1 / 3.6e6 kWh, where RAM-in-BW is the field
  `totalRAMInBW` as registered by the simulator, which counts every migration twice. The revised
  manuscript reports host energy and migration energy separately, counts each migration once,
  uses 0.512 J per MB and hop, charges 20.165 J per migration and does not use the 1.1 factor.
  0.512 J/MB and 20.165 J are the coefficients of the model of Liu et al. (HPDC 2011, Eq. 17);
  4.096 J/MB is eight times that coefficient and is not a measurement.
- **Compared methods.** The original AMOVMC and EUQ-VMC articles do not report a value for gamma
  or for the safety factor `safe`; gamma = 0.80 and safe = 1.5 were set by the authors of this
  package. The re-implementation of AMOVMC in `src/` is partial (details in
  [../SOTA_COMPARISON.md](../SOTA_COMPARISON.md), section "What the AMOVMC re-implementation does
  not reproduce"):
  - the one-layer neural predictor that the article combines with its weighted moving average is
    not implemented; the forecast is the weighted moving average combined with the last observed
    value, on the aggregate utilisation history of the host (`DWMAForecastingTechnique.java`);
  - the overload test (`FutureHostOverSaturationAMOVMC.java`) inverts Eq. (11) of the article,
    which is discontinuous at a utilisation of 0.80, so for hosts with one or two VMs at
    gamma = 0.80 the threshold is 0.64 instead of 0.80; in the gamma sweep the difference affects
    many more host sizes;
  - under-utilised hosts are handled by the policy of the simulator, not by the 30 % threshold of
    the article;
  - the native placement (`FutureAMOVMCPlacement.java`) uses equal weights for the six terms of its
    fitness function, not the weights of Table 3 of the article, computes the cycle term as the
    variance of the history and includes switched-off hosts among the candidates.
- **Statistics.** `stats_ic95_wilcoxon.*` tests PlanetLab on 300 runs as if they were independent
  and uses a family of 48 tests. The revision uses the ten daily means and one family of 360 tests.
- **Forecast accuracy.** `forecast_accuracy.*` has the defects listed at the top of
  `forecast_accuracy.md`.
- **Latency.** `forecaster_latency.py` times one isolated forecast call outside the simulator. The
  revised manuscript reports the time of a complete consolidation decision measured inside the
  simulation loop.
- **Names.** In these files `WF` is WP and `WBF` is WBP.

## Files

| File | What it produced for the submitted version |
|---|---|
| `emit_workload_tables.py` | per-workload tables (seven techniques) |
| `build_tables_6_9.py`, `tables_6_9_rebuilt.md` | earlier form of the per-workload tables |
| `emit_transposed.py`, `transposed_table.md` | table of recent methods |
| `emit_latex.py` | LaTeX tables of an earlier draft |
| `stats_ic95_wilcoxon.py`, `stats_ic95_wilcoxon.md` | confidence intervals and paired tests |
| `fair_sota.py`, `fair_sota.md` | AMOVMC and EUQ-VMC with shared and native placement |
| `forecast_accuracy.py`, `forecast_accuracy.md` | forecast-accuracy table |
| `forecaster_latency.py` | latency of one forecast call |
| `regen_figures.py`, `regen_figures_mpl.py` | box plots |
| `compare_sota.py`, `compare_4_workloads.py`, `compare_4_workloads_st.py`, `compare_all_workloads.py` | comparison tables printed during development |

`emit_workload_tables.py`, `forecaster_latency.py`, `regen_figures.py` and `regen_figures_mpl.py`
were not part of tag v0.2.3 and were added afterwards.

The scripts read the raw outputs from `<repository>/output`; those that define `OUT` from the
environment accept the variable `WBF_OUTPUT` to use another folder. Until this revision several of
them pointed to a folder of the authors' machine. Individual run values change between executions of the
campaign (see `../results/reference/README.md`), so a re-execution does not regenerate these tables
value by value.
