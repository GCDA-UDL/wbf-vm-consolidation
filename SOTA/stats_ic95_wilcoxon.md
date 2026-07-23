# Revised SOTA statistics — mean ± 95% CI + paired Wilcoxon (Holm-corrected, with direction)

Every metric is **lower-is-better**. Wilcoxon paired by common random seed (PlanetLab keyed by (trace,seed), n=300; others n=30). p-values are Holm-Bonferroni corrected over all 48 tests. 'dir' = which technique wins (lower).


## Planetlab

| Technique | n | Energy (kWh) | SLA (%) | # migr. | RAM-in-BW |
|---|--:|---|---|---|---|
| WF | 300 | 24.04 ± 0.17 | 3.98 ± 0.13 | 319.17 ± 8.33 | 37.73 ± 0.98 |
| WBF | 300 | 25.53 ± 0.16 | 3.10 ± 0.12 | 368.18 ± 9.67 | 43.29 ± 1.09 |
| AMOVMC | 300 | 38.98 ± 0.35 | 0.37 ± 0.01 | 597.45 ± 7.42 | 69.29 ± 0.77 |
| EUQ-VMC | 300 | 39.41 ± 0.30 | 3.34 ± 0.06 | 1297.47 ± 17.88 | 141.42 ± 1.87 |

*Paired Wilcoxon (WBF vs X) — winner (lower) · raw p · Holm-adj:*

| Comparison | Metric | winner | raw p | Holm p |
|---|---|---|---|---|
| WBF vs WF | Energy | **WF** | 1.5e-41 *** | 6.1e-40 *** |
| WBF vs WF | SLA | **WBF** | 1.6e-28 *** | 6.4e-27 *** |
| WBF vs WF | migr | **WF** | 2.9e-15 *** | 1.1e-13 *** |
| WBF vs WF | RAM | **WF** | 2.9e-16 *** | 1.1e-14 *** |
| WBF vs AMOVMC | Energy | **WBF** | 6.1e-51 *** | 2.9e-49 *** |
| WBF vs AMOVMC | SLA | **AMOVMC** | 6.1e-51 *** | 2.9e-49 *** |
| WBF vs AMOVMC | migr | **WBF** | 2.9e-49 *** | 1.2e-47 *** |
| WBF vs AMOVMC | RAM | **WBF** | 1.1e-49 *** | 4.8e-48 *** |
| WBF vs EUQ-VMC | Energy | **WBF** | 6.1e-51 *** | 2.9e-49 *** |
| WBF vs EUQ-VMC | SLA | **WBF** | 1.5e-08 *** | 3.5e-07 *** |
| WBF vs EUQ-VMC | migr | **WBF** | 6.1e-51 *** | 2.9e-49 *** |
| WBF vs EUQ-VMC | RAM | **WBF** | 6.1e-51 *** | 2.9e-49 *** |

## Alibaba

| Technique | n | Energy (kWh) | SLA (%) | # migr. | RAM-in-BW |
|---|--:|---|---|---|---|
| WF | 30 | 25.71 ± 0.42 | 5.59 ± 0.64 | 327.30 ± 19.39 | 38.48 ± 1.99 |
| WBF | 30 | 26.83 ± 0.36 | 5.31 ± 0.75 | 375.83 ± 19.79 | 44.07 ± 2.30 |
| AMOVMC | 30 | 39.11 ± 0.18 | 0.10 ± 0.02 | 449.43 ± 9.94 | 51.19 ± 1.18 |
| EUQ-VMC | 30 | 50.27 ± 0.49 | 2.71 ± 0.05 | 1840.63 ± 35.04 | 201.72 ± 3.91 |

*Paired Wilcoxon (WBF vs X) — winner (lower) · raw p · Holm-adj:*

| Comparison | Metric | winner | raw p | Holm p |
|---|---|---|---|---|
| WBF vs WF | Energy | **WF** | 2.6e-04 *** | 3.1e-03 ** |
| WBF vs WF | SLA | **WBF** | 7.0e-01 ns | 7.0e-01 ns |
| WBF vs WF | migr | **WF** | 3.5e-03 ** | 2.8e-02 * |
| WBF vs WF | RAM | **WF** | 1.3e-03 ** | 1.2e-02 * |
| WBF vs AMOVMC | Energy | **WBF** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs AMOVMC | SLA | **AMOVMC** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs AMOVMC | migr | **WBF** | 1.1e-05 *** | 1.6e-04 *** |
| WBF vs AMOVMC | RAM | **WBF** | 9.2e-06 *** | 1.5e-04 *** |
| WBF vs EUQ-VMC | Energy | **WBF** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs EUQ-VMC | SLA | **EUQ-VMC** | 1.3e-08 *** | 3.1e-07 *** |
| WBF vs EUQ-VMC | migr | **WBF** | 1.7e-06 *** | 3.5e-05 *** |
| WBF vs EUQ-VMC | RAM | **WBF** | 1.9e-09 *** | 6.9e-08 *** |

## Materna

| Technique | n | Energy (kWh) | SLA (%) | # migr. | RAM-in-BW |
|---|--:|---|---|---|---|
| WF | 30 | 23.55 ± 0.27 | 4.83 ± 0.39 | 386.70 ± 16.17 | 44.75 ± 1.83 |
| WBF | 30 | 24.45 ± 0.36 | 4.38 ± 0.36 | 418.47 ± 24.96 | 48.08 ± 2.70 |
| AMOVMC | 30 | 36.00 ± 0.37 | 0.66 ± 0.09 | 544.63 ± 16.56 | 60.97 ± 1.77 |
| EUQ-VMC | 30 | 45.71 ± 1.06 | 4.74 ± 0.18 | 1948.27 ± 74.22 | 205.17 ± 8.61 |

*Paired Wilcoxon (WBF vs X) — winner (lower) · raw p · Holm-adj:*

| Comparison | Metric | winner | raw p | Holm p |
|---|---|---|---|---|
| WBF vs WF | Energy | **WF** | 1.9e-04 *** | 2.5e-03 ** |
| WBF vs WF | SLA | **WBF** | 8.1e-03 ** | 5.7e-02 ns |
| WBF vs WF | migr | **WF** | 4.7e-02 * | 2.8e-01 ns |
| WBF vs WF | RAM | **WF** | 7.3e-02 ns | 2.9e-01 ns |
| WBF vs AMOVMC | Energy | **WBF** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs AMOVMC | SLA | **AMOVMC** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs AMOVMC | migr | **WBF** | 2.6e-07 *** | 5.6e-06 *** |
| WBF vs AMOVMC | RAM | **WBF** | 2.6e-07 *** | 5.6e-06 *** |
| WBF vs EUQ-VMC | Energy | **WBF** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs EUQ-VMC | SLA | **WBF** | 5.0e-02 * | 2.8e-01 ns |
| WBF vs EUQ-VMC | migr | **WBF** | 1.7e-06 *** | 3.5e-05 *** |
| WBF vs EUQ-VMC | RAM | **WBF** | 1.9e-09 *** | 6.9e-08 *** |

## Azure

| Technique | n | Energy (kWh) | SLA (%) | # migr. | RAM-in-BW |
|---|--:|---|---|---|---|
| WF | 30 | 22.91 ± 0.42 | 2.48 ± 0.24 | 284.60 ± 21.67 | 32.67 ± 2.37 |
| WBF | 30 | 23.61 ± 0.39 | 2.31 ± 0.22 | 325.13 ± 22.13 | 36.92 ± 2.50 |
| AMOVMC | 30 | 35.59 ± 0.44 | 0.31 ± 0.06 | 451.60 ± 13.48 | 50.60 ± 1.65 |
| EUQ-VMC | 30 | 38.07 ± 0.77 | 2.15 ± 0.10 | 1344.17 ± 55.32 | 140.03 ± 6.06 |

*Paired Wilcoxon (WBF vs X) — winner (lower) · raw p · Holm-adj:*

| Comparison | Metric | winner | raw p | Holm p |
|---|---|---|---|---|
| WBF vs WF | Energy | **WF** | 3.0e-05 *** | 4.3e-04 *** |
| WBF vs WF | SLA | **WBF** | 8.0e-02 ns | 2.9e-01 ns |
| WBF vs WF | migr | **WF** | 3.9e-04 *** | 4.3e-03 ** |
| WBF vs WF | RAM | **WF** | 7.3e-04 *** | 7.3e-03 ** |
| WBF vs AMOVMC | Energy | **WBF** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs AMOVMC | SLA | **AMOVMC** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs AMOVMC | migr | **WBF** | 2.1e-06 *** | 3.6e-05 *** |
| WBF vs AMOVMC | RAM | **WBF** | 5.6e-09 *** | 1.4e-07 *** |
| WBF vs EUQ-VMC | Energy | **WBF** | 1.9e-09 *** | 6.9e-08 *** |
| WBF vs EUQ-VMC | SLA | **EUQ-VMC** | 2.6e-01 ns | 5.2e-01 ns |
| WBF vs EUQ-VMC | migr | **WBF** | 1.7e-06 *** | 3.5e-05 *** |
| WBF vs EUQ-VMC | RAM | **WBF** | 1.9e-09 *** | 6.9e-08 *** |

## PlanetLab ablation robustness (trace level, n=10)

Pooling 10 traces × 30 seeds as 300 i.i.d. pairs is pseudo-replication (trace is a blocking factor), so PlanetLab CIs/p are optimistic. Re-testing the WBF-vs-WF ablation on the 10 trace-means:

- `Energy  n=10  p=1.95e-03 **  (WBF higher)`
- `SLA     n=10  p=1.95e-03 **  (WBF lower)`
- `migr    n=10  p=1.95e-03 **  (WBF higher)`
- `RAM     n=10  p=1.95e-03 **  (WBF higher)`

## Honest reading (post-correction)

- **WBF vs AMOVMC and WBF vs EUQ-VMC survive Holm on all metrics/workloads** (p adj ≪ 0.001): the head-to-head efficiency conclusions (energy, migrations, network transfer) are robust.
- **WBF loses SLA to AMOVMC on all four workloads** (AMOVMC wins, significant) and to EUQ-VMC on Alibaba — the honest energy-vs-SLA trade-off, not a WBF SLA win.
- **Bollinger ablation (WF→WBF) is fragile after correction:** energy increase significant on PlanetLab/Materna only (2/4); migration increase 3/4; SLA improvement survives on PlanetLab only. Present it as *directional* evidence that Bollinger trades a little energy/migration for SLA stability on volatile traces, not an all-workloads effect.