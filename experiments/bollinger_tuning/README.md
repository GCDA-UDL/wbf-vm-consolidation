# Bollinger step — effect and parameters (WP → WBP)

> **Revised in November 2026.** The earlier text of this file said that the Bollinger step reduces
> migrations and described it as a filter of the migration decision. The campaign of the manuscript
> shows the opposite effect on migrations, and the code applies the band before the forecast, not
> to the decision. WP and WBP were called WF and WBF when the package was created; config and
> folder names keep those labels.

## What the step does

WBP is WP plus the Bollinger step. Before the forecast, the recent load history of each host is
replaced by its upper Bollinger Band: moving average of N = 5 samples plus α = 0.5 sample standard
deviations (`pymodule/signalProcessing.py`, `get_bollinger_upper`; config key
`hostSignalProcessing` with the entry `["bollinger", 5, 0.5]`). Prophet then forecasts that series.
The band is not a threshold applied to the forecast: a host is classified as overloaded when the
forecast exceeds a capacity threshold derived from the median absolute deviation of its load
history (config key `hostOverSaturationPolicy` = `mad`), the same rule as for the classical
policies, WPSP and WP.

## Effect in the campaign of the manuscript

Configs `p4_pl_<day>_st` and `paper4_full_<workload>_prophet_st` (13 traces × 30 seeds; each seed
runs WP and WBP). Means, from `results/reference/README.md`:

| Workload | Migrations, WP → WBP | SLA violation (%), WP → WBP | Host energy (kWh), WP → WBP | Mean active hosts, WP → WBP |
|---|---|---|---|---|
| PlanetLab | 319 → 368 | 3.98 → 3.10 | 19.32 → 20.11 | 6.30 → 6.61 |
| Alibaba | 327 → 376 | 5.59 → 5.31 | 20.90 → 21.32 | 6.82 → 6.99 |
| Materna | 387 → 418 | 4.83 → 4.38 | 17.95 → 18.44 | 5.83 → 6.02 |
| Microsoft Azure | 285 → 325 | 2.48 → 2.31 | 18.82 → 18.98 | 6.17 → 6.20 |

The step lowers SLA violations and increases migrations, active hosts and host energy on the four
workloads. After the correction for multiple tests (`results/reference/stats.md`) the SLA
difference is significant on PlanetLab only; the differences in host energy and active hosts are
significant on PlanetLab and Materna; the differences in migrations are not significant on any
workload.

## Parameter sweep

`testbed/exp_bollinger_search.json` runs WBP on Materna with five seeds and the settings
(N, α) = (4, 1.5), (5, 2.0), (20, 2.0) and (4, 2.0). It does not include the setting used in the
manuscript, (5, 0.5), so it does not document how that setting was chosen.

The revision adds a sensitivity analysis around (5, 0.5) on the four workloads (N = 3, 10, 20 at
α = 0.5 and α = 1.0, 1.5, 2.0 at N = 5; 13 traces, seeds 0-9, 780 runs besides the reference
setting). Its table is reported in the revised manuscript; the run lists, tools and tables are in
[../revision_r1/](../revision_r1/README.md) (`tables/bollinger_sensitivity.md`).
