# Closed-loop forecaster replacement (new runs, one simulation per JVM)

Same selection (WPSP, `psp2`), same MAD overload rule, same placement (`ac`); only the host forecaster and the Bollinger transform (5, 0.5) change. LVP = WPSP of the paper, Prophet = WP, Prophet+BB = WBP, all re-run here. EWMA = `simpleExpSmoothing`, smoothing level 0.8 (fixed in `pymodule`; last value while the history has fewer than 10 samples).

Mean ± 95% CI (PlanetLab: over the 10 daily-trace means; others: over the seeds). Migration energy with kappa = 0.512 J per MB and hop.

## PlanetLab

| metric | LVP | LVP+BB | EWMA | EWMA+BB | Prophet | Prophet+BB |
|---|---|---|---|---|---|---|
| runs (units) | 300 (10) | 300 (10) | 300 (10) | 300 (10) | 300 (10) | 300 (10) |
| Host energy (kWh) | 18.85 ± 1.17 | 20.00 ± 1.20 | 18.97 ± 1.18 | 20.00 ± 1.20 | 19.33 ± 1.17 | 20.03 ± 1.21 |
| Total energy (kWh) | 19.21 ± 1.14 | 20.31 ± 1.17 | 19.32 ± 1.15 | 20.31 ± 1.17 | 19.61 ± 1.16 | 20.34 ± 1.19 |
| SLA violation (\%) | 5.45 ± 0.40 | 3.23 ± 0.29 | 5.01 ± 0.42 | 3.15 ± 0.36 | 3.94 ± 0.38 | 3.25 ± 0.28 |
| \# of migrations | 425 ± 34 | 376 ± 47 | 411 ± 26 | 369 ± 34 | 326 ± 27 | 362 ± 36 |
| Migration traffic (GB$\cdot$hop) | 2544 ± 195 | 2214 ± 269 | 2446 ± 152 | 2170 ± 202 | 1926 ± 154 | 2121 ± 205 |
| Mean active hosts | 6.10 ± 0.37 | 6.56 ± 0.39 | 6.15 ± 0.38 | 6.56 ± 0.39 | 6.30 ± 0.37 | 6.58 ± 0.39 |
| Decision time (s), uncontended | 0.0019 (n=2) | 0.0056 (n=2) | 0.0136 (n=2) | 0.0177 (n=1) | 0.4256 (n=2) | 0.5662 (n=2) |

Decision time: 1 run(s) with a negative logged mean in some stage excluded (the simulator timer uses the wall clock and the virtual machine clock stepped back during the run).

Paired contrasts (a − b; PlanetLab: paired t on trace means; others: Wilcoxon on seed pairs):

| contrast | metric | n | mean difference | p |
|---|---|---|---|---|
| Prophet − LVP | e_hosts | 10 | +0.4849 | 5.34e-07 |
| Prophet − LVP | e_total | 10 | +0.3965 | 4.4e-06 |
| Prophet − LVP | sla | 10 | -1.51 | 6.28e-09 |
| Prophet − LVP | migr | 10 | -99.59 | 3.84e-07 |
| Prophet − LVP | traffic | 10 | -617.4 | 1.85e-07 |
| Prophet − EWMA | e_hosts | 10 | +0.3598 | 1.23e-07 |
| Prophet − EWMA | e_total | 10 | +0.2853 | 5.09e-07 |
| Prophet − EWMA | sla | 10 | -1.065 | 2.7e-07 |
| Prophet − EWMA | migr | 10 | -85.03 | 1.15e-06 |
| Prophet − EWMA | traffic | 10 | -520.1 | 4.43e-07 |
| EWMA − LVP | e_hosts | 10 | +0.1251 | 0.00883 |
| EWMA − LVP | e_total | 10 | +0.1112 | 0.0175 |
| EWMA − LVP | sla | 10 | -0.4447 | 0.00412 |
| EWMA − LVP | migr | 10 | -14.56 | 0.0124 |
| EWMA − LVP | traffic | 10 | -97.26 | 0.00259 |
| Prophet+BB − LVP+BB | e_hosts | 10 | +0.03537 | 0.214 |
| Prophet+BB − LVP+BB | e_total | 10 | +0.02205 | 0.39 |
| Prophet+BB − LVP+BB | sla | 10 | +0.02058 | 0.781 |
| Prophet+BB − LVP+BB | migr | 10 | -13.79 | 0.0937 |
| Prophet+BB − LVP+BB | traffic | 10 | -93.13 | 0.0544 |
| Prophet+BB − EWMA+BB | e_hosts | 10 | +0.03677 | 0.447 |
| Prophet+BB − EWMA+BB | e_total | 10 | +0.02981 | 0.533 |
| Prophet+BB − EWMA+BB | sla | 10 | +0.1004 | 0.311 |
| Prophet+BB − EWMA+BB | migr | 10 | -7.47 | 0.223 |
| Prophet+BB − EWMA+BB | traffic | 10 | -48.65 | 0.199 |
| LVP+BB − LVP | e_hosts | 10 | +1.152 | 1.63e-09 |
| LVP+BB − LVP | e_total | 10 | +1.104 | 2.76e-09 |
| LVP+BB − LVP | sla | 10 | -2.219 | 2.19e-08 |
| LVP+BB − LVP | migr | 10 | -49.58 | 0.000279 |
| LVP+BB − LVP | traffic | 10 | -329.5 | 7.36e-05 |
| EWMA+BB − EWMA | e_hosts | 10 | +1.025 | 2.18e-11 |
| EWMA+BB − EWMA | e_total | 10 | +0.9855 | 3.61e-11 |
| EWMA+BB − EWMA | sla | 10 | -1.854 | 1.45e-09 |
| EWMA+BB − EWMA | migr | 10 | -41.34 | 0.000106 |
| EWMA+BB − EWMA | traffic | 10 | -276.7 | 5.2e-05 |
| Prophet+BB − Prophet | e_hosts | 10 | +0.7021 | 6.48e-07 |
| Prophet+BB − Prophet | e_total | 10 | +0.73 | 4.57e-07 |
| Prophet+BB − Prophet | sla | 10 | -0.6887 | 3.51e-05 |
| Prophet+BB − Prophet | migr | 10 | +36.21 | 0.00124 |
| Prophet+BB − Prophet | traffic | 10 | +194.7 | 0.00129 |

## Alibaba

| metric | LVP | LVP+BB | EWMA | EWMA+BB | Prophet | Prophet+BB |
|---|---|---|---|---|---|---|
| runs (units) | 30 (30) | 30 (30) | 30 (30) | 30 (30) | 30 (30) | 30 (30) |
| Host energy (kWh) | 20.88 ± 0.29 | 21.24 ± 0.31 | 20.93 ± 0.27 | 21.34 ± 0.29 | 20.85 ± 0.28 | 21.31 ± 0.27 |
| Total energy (kWh) | 21.19 ± 0.30 | 21.52 ± 0.31 | 21.23 ± 0.27 | 21.63 ± 0.29 | 21.12 ± 0.28 | 21.62 ± 0.27 |
| SLA violation (\%) | 5.23 ± 0.85 | 4.98 ± 0.85 | 5.15 ± 0.79 | 4.69 ± 0.70 | 5.58 ± 0.73 | 5.63 ± 0.78 |
| \# of migrations | 356 ± 18 | 339 ± 15 | 353 ± 19 | 343 ± 15 | 323 ± 13 | 374 ± 18 |
| Migration traffic (GB$\cdot$hop) | 2200 ± 124 | 2001 ± 92 | 2123 ± 97 | 2036 ± 80 | 1907 ± 65 | 2185 ± 95 |
| Mean active hosts | 6.78 ± 0.10 | 6.94 ± 0.11 | 6.81 ± 0.10 | 6.98 ± 0.11 | 6.79 ± 0.10 | 7.00 ± 0.10 |
| Decision time (s), uncontended | 0.0019 (n=2) | 0.0053 (n=2) | 0.0138 (n=2) | 0.0173 (n=2) | 0.4911 (n=2) | 0.5182 (n=2) |

Paired contrasts (a − b; PlanetLab: paired t on trace means; others: Wilcoxon on seed pairs):

| contrast | metric | n | mean difference | p |
|---|---|---|---|---|
| Prophet − LVP | e_hosts | 30 | -0.03125 | 0.584 |
| Prophet − LVP | e_total | 30 | -0.07322 | 0.428 |
| Prophet − LVP | sla | 30 | +0.3417 | 0.262 |
| Prophet − LVP | migr | 30 | -33.2 | 0.00976 |
| Prophet − LVP | traffic | 30 | -293.8 | 0.000209 |
| Prophet − EWMA | e_hosts | 30 | -0.08224 | 0.44 |
| Prophet − EWMA | e_total | 30 | -0.1132 | 0.404 |
| Prophet − EWMA | sla | 30 | +0.4253 | 0.371 |
| Prophet − EWMA | migr | 30 | -29.6 | 0.0154 |
| Prophet − EWMA | traffic | 30 | -216.5 | 0.00123 |
| EWMA − LVP | e_hosts | 30 | +0.05099 | 0.7 |
| EWMA − LVP | e_total | 30 | +0.03997 | 0.746 |
| EWMA − LVP | sla | 30 | -0.08358 | 0.984 |
| EWMA − LVP | migr | 30 | -3.6 | 0.853 |
| EWMA − LVP | traffic | 30 | -77.28 | 0.465 |
| Prophet+BB − LVP+BB | e_hosts | 30 | +0.07386 | 0.36 |
| Prophet+BB − LVP+BB | e_total | 30 | +0.1001 | 0.289 |
| Prophet+BB − LVP+BB | sla | 30 | +0.6512 | 0.428 |
| Prophet+BB − LVP+BB | migr | 30 | +34.4 | 0.0124 |
| Prophet+BB − LVP+BB | traffic | 30 | +183.1 | 0.00871 |
| Prophet+BB − EWMA+BB | e_hosts | 30 | -0.03084 | 0.839 |
| Prophet+BB − EWMA+BB | e_total | 30 | -0.0096 | 0.761 |
| Prophet+BB − EWMA+BB | sla | 30 | +0.9419 | 0.135 |
| Prophet+BB − EWMA+BB | migr | 30 | +30.13 | 0.0156 |
| Prophet+BB − EWMA+BB | traffic | 30 | +148.2 | 0.0197 |
| LVP+BB − LVP | e_hosts | 30 | +0.3597 | 0.0473 |
| LVP+BB − LVP | e_total | 30 | +0.3314 | 0.0919 |
| LVP+BB − LVP | sla | 30 | -0.2513 | 0.746 |
| LVP+BB − LVP | migr | 30 | -17 | 0.078 |
| LVP+BB − LVP | traffic | 30 | -198.9 | 0.0093 |
| EWMA+BB − EWMA | e_hosts | 30 | +0.4135 | 0.0164 |
| EWMA+BB − EWMA | e_total | 30 | +0.4011 | 0.0208 |
| EWMA+BB − EWMA | sla | 30 | -0.4584 | 0.262 |
| EWMA+BB − EWMA | migr | 30 | -9.133 | 0.504 |
| EWMA+BB − EWMA | traffic | 30 | -86.64 | 0.146 |
| Prophet+BB − Prophet | e_hosts | 30 | +0.4649 | 0.00761 |
| Prophet+BB − Prophet | e_total | 30 | +0.5047 | 0.00466 |
| Prophet+BB − Prophet | sla | 30 | +0.05817 | 0.984 |
| Prophet+BB − Prophet | migr | 30 | +50.6 | 0.000419 |
| Prophet+BB − Prophet | traffic | 30 | +278 | 5.59e-05 |

## Materna

| metric | LVP | LVP+BB | EWMA | EWMA+BB | Prophet | Prophet+BB |
|---|---|---|---|---|---|---|
| runs (units) | 30 (30) | 30 (30) | 30 (30) | 30 (30) | 30 (30) | 30 (30) |
| Host energy (kWh) | 17.50 ± 0.16 | 18.46 ± 0.14 | 17.62 ± 0.15 | 18.39 ± 0.18 | 17.86 ± 0.17 | 18.37 ± 0.16 |
| Total energy (kWh) | 17.80 ± 0.16 | 18.77 ± 0.14 | 17.94 ± 0.15 | 18.71 ± 0.18 | 18.17 ± 0.17 | 18.72 ± 0.16 |
| SLA violation (\%) | 5.37 ± 0.36 | 4.06 ± 0.33 | 5.29 ± 0.34 | 3.99 ± 0.35 | 4.97 ± 0.42 | 4.41 ± 0.48 |
| \# of migrations | 366 ± 23 | 373 ± 23 | 379 ± 25 | 387 ± 30 | 375 ± 18 | 420 ± 23 |
| Migration traffic (GB$\cdot$hop) | 2140 ± 126 | 2188 ± 131 | 2219 ± 137 | 2233 ± 161 | 2186 ± 117 | 2453 ± 138 |
| Mean active hosts | 5.65 ± 0.06 | 6.03 ± 0.06 | 5.69 ± 0.06 | 5.99 ± 0.07 | 5.79 ± 0.07 | 5.99 ± 0.06 |
| Decision time (s), uncontended | 0.0017 (n=2) | 0.0051 (n=2) | 0.0118 (n=2) | 0.0156 (n=2) | 0.3914 (n=2) | 0.4511 (n=2) |

Paired contrasts (a − b; PlanetLab: paired t on trace means; others: Wilcoxon on seed pairs):

| contrast | metric | n | mean difference | p |
|---|---|---|---|---|
| Prophet − LVP | e_hosts | 30 | +0.3585 | 7.99e-06 |
| Prophet − LVP | e_total | 30 | +0.3651 | 1.06e-05 |
| Prophet − LVP | sla | 30 | -0.4023 | 0.00466 |
| Prophet − LVP | migr | 30 | +9.767 | 0.271 |
| Prophet − LVP | traffic | 30 | +46.05 | 0.49 |
| Prophet − EWMA | e_hosts | 30 | +0.2382 | 0.000209 |
| Prophet − EWMA | e_total | 30 | +0.2334 | 0.000505 |
| Prophet − EWMA | sla | 30 | -0.3268 | 0.0145 |
| Prophet − EWMA | migr | 30 | -4 | 0.537 |
| Prophet − EWMA | traffic | 30 | -33.36 | 0.371 |
| EWMA − LVP | e_hosts | 30 | +0.1203 | 0.0384 |
| EWMA − LVP | e_total | 30 | +0.1317 | 0.0405 |
| EWMA − LVP | sla | 30 | -0.07548 | 0.516 |
| EWMA − LVP | migr | 30 | +13.77 | 0.313 |
| EWMA − LVP | traffic | 30 | +79.41 | 0.135 |
| Prophet+BB − LVP+BB | e_hosts | 30 | -0.09011 | 0.28 |
| Prophet+BB − LVP+BB | e_total | 30 | -0.05215 | 0.556 |
| Prophet+BB − LVP+BB | sla | 30 | +0.3508 | 0.00664 |
| Prophet+BB − LVP+BB | migr | 30 | +46.53 | 0.0136 |
| Prophet+BB − LVP+BB | traffic | 30 | +265.1 | 0.00871 |
| Prophet+BB − EWMA+BB | e_hosts | 30 | -0.02352 | 0.761 |
| Prophet+BB − EWMA+BB | e_total | 30 | +0.008029 | 0.44 |
| Prophet+BB − EWMA+BB | sla | 30 | +0.4192 | 0.0164 |
| Prophet+BB − EWMA+BB | migr | 30 | +32.37 | 0.103 |
| Prophet+BB − EWMA+BB | traffic | 30 | +220.5 | 0.031 |
| LVP+BB − LVP | e_hosts | 30 | +0.9615 | 1.86e-09 |
| LVP+BB − LVP | e_total | 30 | +0.9684 | 1.86e-09 |
| LVP+BB − LVP | sla | 30 | -1.313 | 3.73e-09 |
| LVP+BB − LVP | migr | 30 | +7.567 | 0.344 |
| LVP+BB − LVP | traffic | 30 | +48.24 | 0.44 |
| EWMA+BB − EWMA | e_hosts | 30 | +0.7746 | 1.86e-09 |
| EWMA+BB − EWMA | e_total | 30 | +0.7766 | 1.86e-09 |
| EWMA+BB − EWMA | sla | 30 | -1.305 | 1.86e-09 |
| EWMA+BB − EWMA | migr | 30 | +7.967 | 0.797 |
| EWMA+BB − EWMA | traffic | 30 | +13.38 | 0.984 |
| Prophet+BB − Prophet | e_hosts | 30 | +0.513 | 1.99e-06 |
| Prophet+BB − Prophet | e_total | 30 | +0.5512 | 5.72e-07 |
| Prophet+BB − Prophet | sla | 30 | -0.5594 | 0.000952 |
| Prophet+BB − Prophet | migr | 30 | +44.33 | 0.00203 |
| Prophet+BB − Prophet | traffic | 30 | +267.3 | 0.00237 |

## Microsoft Azure

| metric | LVP | LVP+BB | EWMA | EWMA+BB | Prophet | Prophet+BB |
|---|---|---|---|---|---|---|
| runs (units) | 30 (30) | 30 (30) | 30 (30) | 30 (30) | 30 (30) | 30 (30) |
| Host energy (kWh) | 18.64 ± 0.20 | 19.08 ± 0.21 | 18.65 ± 0.18 | 19.13 ± 0.16 | 18.80 ± 0.18 | 19.04 ± 0.19 |
| Total energy (kWh) | 18.89 ± 0.20 | 19.34 ± 0.21 | 18.92 ± 0.18 | 19.39 ± 0.17 | 19.02 ± 0.17 | 19.31 ± 0.19 |
| SLA violation (\%) | 2.51 ± 0.27 | 2.28 ± 0.38 | 2.67 ± 0.29 | 1.95 ± 0.21 | 2.57 ± 0.33 | 2.28 ± 0.23 |
| \# of migrations | 311 ± 21 | 325 ± 19 | 323 ± 25 | 316 ± 26 | 264 ± 18 | 343 ± 20 |
| Migration traffic (GB$\cdot$hop) | 1774 ± 124 | 1859 ± 107 | 1856 ± 132 | 1815 ± 147 | 1511 ± 106 | 1929 ± 116 |
| Mean active hosts | 6.06 ± 0.08 | 6.25 ± 0.08 | 6.07 ± 0.07 | 6.26 ± 0.06 | 6.17 ± 0.07 | 6.22 ± 0.07 |
| Decision time (s), uncontended | 0.0017 (n=2) | 0.0049 (n=1) | 0.0119 (n=2) | 0.0153 (n=2) | 0.4214 (n=2) | 0.4872 (n=2) |

Decision time: 1 run(s) with a negative logged mean in some stage excluded (the simulator timer uses the wall clock and the virtual machine clock stepped back during the run).

Paired contrasts (a − b; PlanetLab: paired t on trace means; others: Wilcoxon on seed pairs):

| contrast | metric | n | mean difference | p |
|---|---|---|---|---|
| Prophet − LVP | e_hosts | 30 | +0.1636 | 0.119 |
| Prophet − LVP | e_total | 30 | +0.126 | 0.146 |
| Prophet − LVP | sla | 30 | +0.06369 | 0.839 |
| Prophet − LVP | migr | 30 | -47.07 | 0.00683 |
| Prophet − LVP | traffic | 30 | -262.4 | 0.00348 |
| Prophet − EWMA | e_hosts | 30 | +0.1508 | 0.0577 |
| Prophet − EWMA | e_total | 30 | +0.1014 | 0.171 |
| Prophet − EWMA | sla | 30 | -0.09503 | 0.416 |
| Prophet − EWMA | migr | 30 | -58.3 | 0.00238 |
| Prophet − EWMA | traffic | 30 | -344.6 | 0.00202 |
| EWMA − LVP | e_hosts | 30 | +0.0128 | 0.887 |
| EWMA − LVP | e_total | 30 | +0.02455 | 0.73 |
| EWMA − LVP | sla | 30 | +0.1587 | 0.626 |
| EWMA − LVP | migr | 30 | +11.23 | 0.466 |
| EWMA − LVP | traffic | 30 | +82.19 | 0.339 |
| Prophet+BB − LVP+BB | e_hosts | 30 | -0.04001 | 0.808 |
| Prophet+BB − LVP+BB | e_total | 30 | -0.03002 | 0.887 |
| Prophet+BB − LVP+BB | sla | 30 | -0.0009559 | 0.641 |
| Prophet+BB − LVP+BB | migr | 30 | +17.8 | 0.168 |
| Prophet+BB − LVP+BB | traffic | 30 | +69.56 | 0.237 |
| Prophet+BB − EWMA+BB | e_hosts | 30 | -0.09005 | 0.452 |
| Prophet+BB − EWMA+BB | e_total | 30 | -0.07373 | 0.7 |
| Prophet+BB − EWMA+BB | sla | 30 | +0.3277 | 0.00993 |
| Prophet+BB − EWMA+BB | migr | 30 | +27.1 | 0.0936 |
| Prophet+BB − EWMA+BB | traffic | 30 | +113.7 | 0.198 |
| LVP+BB − LVP | e_hosts | 30 | +0.4381 | 6.15e-08 |
| LVP+BB − LVP | e_total | 30 | +0.4503 | 8.01e-08 |
| LVP+BB − LVP | sla | 30 | -0.2257 | 0.0699 |
| LVP+BB − LVP | migr | 30 | +13.57 | 0.153 |
| LVP+BB − LVP | traffic | 30 | +85.45 | 0.213 |
| EWMA+BB − EWMA | e_hosts | 30 | +0.4753 | 4.42e-06 |
| EWMA+BB − EWMA | e_total | 30 | +0.4695 | 6.92e-06 |
| EWMA+BB − EWMA | sla | 30 | -0.7131 | 7.06e-05 |
| EWMA+BB − EWMA | migr | 30 | -6.967 | 0.644 |
| EWMA+BB − EWMA | traffic | 30 | -40.85 | 0.73 |
| Prophet+BB − Prophet | e_hosts | 30 | +0.2345 | 0.0145 |
| Prophet+BB − Prophet | e_total | 30 | +0.2943 | 0.00277 |
| Prophet+BB − Prophet | sla | 30 | -0.2903 | 0.0879 |
| Prophet+BB − Prophet | migr | 30 | +78.43 | 3.25e-05 |
| Prophet+BB − Prophet | traffic | 30 | +417.4 | 1.22e-05 |

