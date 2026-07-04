# Additional experiments

Beyond the main comparison (classical baselines vs. WF/WBF on the four workloads), two extra studies
support the design choices of the method. Each has its own folder with a short report.

| Study | Question | Result |
|-------|----------|--------|
| [neuralprophet/](neuralprophet/) | Is a deep-learning forecaster (NeuralProphet) better than Facebook Prophet for the migration decision? | **No** — Facebook Prophet wins in 7 of 8 cases (fewer migrations). |
| [bollinger_tuning/](bollinger_tuning/) | How does the Bollinger filter (window, $\alpha$) affect WF → WBF? | The filter trades a small energy increase for fewer migrations and lower SLA; tuning shifts the operating point. |

The corresponding simulator configurations are in `../testbed/`
(`exp_neuralprophet.json`, `exp_bollinger_search.json`) and are run exactly like the main
experiments (see [../REPRODUCE.md](../REPRODUCE.md)).
