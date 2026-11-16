# Additional experiments

## Experiments added by the revision of the manuscript

[revision_r1/](revision_r1/README.md) holds the run lists, the tools and the resulting tables of the
three experiments that the revised manuscript adds to the campaign of the main tables:

| Experiment | Table of the manuscript | Runs |
|---|---|---|
| Closed-loop replacement of the forecaster (last value, EWMA, Prophet, each with and without the Bollinger step) | `tab:closed_loop` | 13 traces × 6 variants × 30 seeds = 2,340, plus 48 runs for the decision time |
| Sensitivity to the Bollinger parameters N and alpha | `tab:bollinger_sensitivity` | 13 traces × 6 settings × seeds 0-9 = 780, besides the reference setting (N = 5, alpha = 0.5) |
| Forecast accuracy under the protocol of the method | `tab:forecast_val_u` | no simulation |

Their raw outputs are not shipped in this version of the package; see that README.

## Exploratory studies

Two exploratory studies made during the development of the method. Their notes were written for
the submitted version of the manuscript and were revised in November 2026; the statements in the
table below are the ones supported by the campaign of the revised manuscript
(`results/reference/README.md`, `results/reference/stats.md`).

| Study | Question | What the campaign of the manuscript shows |
|-------|----------|-------------------------------------------|
| [neuralprophet/](neuralprophet/) | Does NeuralProphet change the consolidation with respect to Prophet? | With the Bollinger step, the two forecasters give results that are statistically indistinguishable on Alibaba, Materna and Azure; on PlanetLab the NeuralProphet variant (BB+NeoPro) uses less total energy with higher SLA violations. BB+NeoPro is the WBP loop with the NeuralProphet forecaster, not the 2023 method as published. The notes in the folder describe an earlier exploratory run. |
| [bollinger_tuning/](bollinger_tuning/) | What does the Bollinger step (window N, width α) change between WP and WBP? | It lowers SLA violations and increases migrations, active hosts and host energy on the four workloads; the SLA difference is significant on PlanetLab only. |

The simulator configurations of the two exploratory studies are in `../testbed/`
(`exp_neuralprophet.json`, `exp_bollinger_search.json`) and are run like the main experiments
(see [../REPRODUCE.md](../REPRODUCE.md)).

WP and WBP were called WF and WBF when the package was created; config and folder names keep those
labels.
