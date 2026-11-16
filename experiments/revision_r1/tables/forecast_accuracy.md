# Forecast accuracy on the series the simulator reads (new analysis)

Per-VM CPU series, first 288 samples, columns as read by the simulator (Alibaba: `cpu_util_percent`; Azure: `avg`; Materna: `CPU usage [%]`; PlanetLab: the daily files). Errors in percentage points of VM CPU utilisation, pooled over all windows. bias = mean(prediction − actual). MAPE excludes targets below 1 %, as the submitted script did. `fallbacks`: Prophet calls that raised ValueError and returned the last value. EWMA0.8 = exponential smoothing as the simulator runs it (statsmodels, level 0.8, last value under 10 samples); EWMA0.5 = the pandas EWMA of the submitted table.

The consolidation loop forecasts host-level utilisation (sum of the VMs on a host), which only exists inside a simulation; these are per-VM series.

## Protocol A: one step ahead at every step, window of 30 samples, raw series

| workload | VMs (expected) | forecaster | n | bias | MAE | RMSE | MAPE (%) | fallbacks |
|---|---|---|---|---|---|---|---|---|
| PlanetLab | 100 (1000; A: PlanetLab day 20110303 = 100) | Prophet | 25800 | +0.02 | 16.47 | 21.79 | 131.1 | 0 |
| PlanetLab | 100 (1000; A: PlanetLab day 20110303 = 100) | LVP | 25800 | +0.02 | 18.44 | 25.86 | 139.4 | 0 |
| PlanetLab | 100 (1000; A: PlanetLab day 20110303 = 100) | EWMA0.8 | 25800 | +0.02 | 17.15 | 23.67 | 131.7 | 0 |
| PlanetLab | 100 (1000; A: PlanetLab day 20110303 = 100) | EWMA0.5 | 25800 | +0.04 | 15.82 | 21.23 | 124.4 | 0 |
| Alibaba | 100 (100; A: PlanetLab day 20110303 = 100) | Prophet | 25800 | +0.25 | 7.27 | 10.19 | 21.9 | 0 |
| Alibaba | 100 (100; A: PlanetLab day 20110303 = 100) | LVP | 25800 | +0.02 | 4.78 | 7.90 | 14.4 | 0 |
| Alibaba | 100 (100; A: PlanetLab day 20110303 = 100) | EWMA0.8 | 25800 | +0.02 | 4.67 | 7.57 | 14.1 | 0 |
| Alibaba | 100 (100; A: PlanetLab day 20110303 = 100) | EWMA0.5 | 25800 | +0.03 | 4.75 | 7.44 | 14.3 | 0 |
| Materna | 100 (100; A: PlanetLab day 20110303 = 100) | Prophet | 25800 | +0.00 | 3.54 | 7.18 | 52.1 | 0 |
| Materna | 100 (100; A: PlanetLab day 20110303 = 100) | LVP | 25800 | +0.01 | 2.55 | 5.90 | 31.8 | 0 |
| Materna | 100 (100; A: PlanetLab day 20110303 = 100) | EWMA0.8 | 25800 | +0.01 | 2.47 | 5.64 | 31.6 | 0 |
| Materna | 100 (100; A: PlanetLab day 20110303 = 100) | EWMA0.5 | 25800 | +0.02 | 2.46 | 5.45 | 32.7 | 0 |
| Azure | 100 (100; A: PlanetLab day 20110303 = 100) | Prophet | 25800 | -0.00 | 2.97 | 6.68 | 36.8 | 0 |
| Azure | 100 (100; A: PlanetLab day 20110303 = 100) | LVP | 25800 | -0.00 | 2.72 | 5.31 | 31.2 | 0 |
| Azure | 100 (100; A: PlanetLab day 20110303 = 100) | EWMA0.8 | 25800 | -0.00 | 2.61 | 5.09 | 30.3 | 0 |
| Azure | 100 (100; A: PlanetLab day 20110303 = 100) | EWMA0.5 | 25800 | -0.00 | 2.49 | 4.93 | 29.3 | 0 |

## Protocol B: at each decision instant (every 6 steps), window of the last min(t, 30) samples, mean of the 6-step forecast against the mean of the next 6 observed samples, raw series

| workload | VMs (expected) | forecaster | n | bias | MAE | RMSE | MAPE (%) | fallbacks |
|---|---|---|---|---|---|---|---|---|
| PlanetLab | 1000 (1000) | Prophet | 47000 | -0.03 | 8.70 | 11.63 | 51.7 | 0 |
| PlanetLab | 1000 (1000) | LVP | 47000 | -0.01 | 14.56 | 19.16 | 77.3 | 0 |
| PlanetLab | 1000 (1000) | EWMA0.8 | 47000 | -0.00 | 12.38 | 16.35 | 66.6 | 0 |
| PlanetLab | 1000 (1000) | EWMA0.5 | 47000 | +0.00 | 9.69 | 12.79 | 54.5 | 0 |
| Alibaba | 100 (100) | Prophet | 4700 | +0.21 | 6.74 | 9.57 | 20.7 | 0 |
| Alibaba | 100 (100) | LVP | 4700 | -1.27 | 5.39 | 8.20 | 16.1 | 0 |
| Alibaba | 100 (100) | EWMA0.8 | 4700 | -1.03 | 5.03 | 7.63 | 14.9 | 0 |
| Alibaba | 100 (100) | EWMA0.5 | 4700 | -0.68 | 4.70 | 7.07 | 14.1 | 0 |
| Materna | 100 (100) | Prophet | 4700 | +0.11 | 2.94 | 6.68 | 39.0 | 0 |
| Materna | 100 (100) | LVP | 4700 | +0.13 | 2.74 | 6.03 | 30.3 | 0 |
| Materna | 100 (100) | EWMA0.8 | 4700 | +0.10 | 2.50 | 5.63 | 28.1 | 0 |
| Materna | 100 (100) | EWMA0.5 | 4700 | +0.06 | 2.20 | 5.11 | 26.0 | 0 |
| Azure | 100 (100) | Prophet | 4700 | +0.08 | 2.10 | 6.20 | 23.2 | 0 |
| Azure | 100 (100) | LVP | 4700 | +0.24 | 2.40 | 5.32 | 25.8 | 0 |
| Azure | 100 (100) | EWMA0.8 | 4700 | +0.18 | 2.08 | 4.93 | 22.4 | 0 |
| Azure | 100 (100) | EWMA0.5 | 4700 | +0.08 | 1.74 | 4.43 | 18.8 | 0 |

## Protocol B with the Bollinger-transformed window (upper band, N = 5, alpha = 0.5) as input and the same raw target: what WBP gives to the forecaster

| workload | VMs (expected) | forecaster | n | bias | MAE | RMSE | MAPE (%) | fallbacks |
|---|---|---|---|---|---|---|---|---|
| PlanetLab | 1000 (1000) | Prophet | 47000 | +7.69 | 11.38 | 14.65 | 78.7 | 0 |
| PlanetLab | 1000 (1000) | LVP | 47000 | +7.69 | 11.73 | 15.25 | 80.2 | 0 |
| PlanetLab | 1000 (1000) | EWMA0.8 | 47000 | +7.70 | 11.52 | 14.97 | 79.0 | 0 |
| PlanetLab | 1000 (1000) | EWMA0.5 | 47000 | +7.71 | 11.06 | 14.31 | 76.7 | 0 |
| Alibaba | 100 (100) | Prophet | 4700 | +2.61 | 7.84 | 10.96 | 24.8 | 0 |
| Alibaba | 100 (100) | LVP | 4700 | +2.12 | 5.65 | 8.26 | 17.9 | 0 |
| Alibaba | 100 (100) | EWMA0.8 | 4700 | +2.16 | 5.70 | 8.30 | 18.1 | 0 |
| Alibaba | 100 (100) | EWMA0.5 | 4700 | +2.17 | 5.78 | 8.33 | 18.4 | 0 |
| Materna | 100 (100) | Prophet | 4700 | +1.45 | 3.70 | 7.77 | 55.5 | 0 |
| Materna | 100 (100) | LVP | 4700 | +1.46 | 2.98 | 6.33 | 42.7 | 0 |
| Materna | 100 (100) | EWMA0.8 | 4700 | +1.44 | 2.97 | 6.34 | 42.6 | 0 |
| Materna | 100 (100) | EWMA0.5 | 4700 | +1.41 | 2.95 | 6.31 | 42.6 | 0 |
| Azure | 100 (100) | Prophet | 4700 | +1.32 | 2.86 | 7.30 | 34.9 | 0 |
| Azure | 100 (100) | LVP | 4700 | +1.24 | 2.21 | 5.34 | 26.6 | 0 |
| Azure | 100 (100) | EWMA0.8 | 4700 | +1.23 | 2.21 | 5.37 | 26.6 | 0 |
| Azure | 100 (100) | EWMA0.5 | 4700 | +1.23 | 2.21 | 5.40 | 26.6 | 0 |

