# Re-run in one-JVM mode versus the stored campaign (same configurations and seeds)

Stored: runs behind the manuscript tables (batch mode). Re-run: this campaign. `identical` counts the runs whose four result sections are byte-identical (sha1). Difference = re-run − stored, paired by trace and seed.

| workload | technique | metric | stored mean ± CI | re-run mean ± CI | difference | p | n | identical runs |
|---|---|---|---|---|---|---|---|---|
| PlanetLab | WPSP | e_hosts | 18.81 ± 1.17 | 18.85 ± 1.17 | +0.03542 | 0.124 | 10 | 0/300 |
| PlanetLab | WPSP | e_total | 19.17 ± 1.14 | 19.21 ± 1.14 | +0.03597 | 0.13 | 10 | 0/300 |
| PlanetLab | WPSP | sla | 5.53 ± 0.47 | 5.45 ± 0.40 | -0.07889 | 0.353 | 10 | 0/300 |
| PlanetLab | WPSP | migr | 425 ± 33 | 425 ± 34 | +0.24 | 0.96 | 10 | 0/300 |
| PlanetLab | WPSP | traffic | 2540 ± 193 | 2544 ± 195 | +3.876 | 0.897 | 10 | 0/300 |
| PlanetLab | WP | e_hosts | 19.32 ± 1.19 | 19.33 ± 1.17 | +0.01239 | 0.692 | 10 | 7/300 |
| PlanetLab | WP | e_total | 19.59 ± 1.17 | 19.61 ± 1.16 | +0.01809 | 0.539 | 10 | 7/300 |
| PlanetLab | WP | sla | 3.98 ± 0.35 | 3.94 ± 0.38 | -0.04027 | 0.599 | 10 | 7/300 |
| PlanetLab | WP | migr | 319 ± 26 | 326 ± 27 | +6.367 | 0.234 | 10 | 7/300 |
| PlanetLab | WP | traffic | 1886 ± 157 | 1926 ± 154 | +39.85 | 0.193 | 10 | 7/300 |
| PlanetLab | WBP | e_hosts | 20.11 ± 1.18 | 20.03 ± 1.21 | -0.07516 | 0.0577 | 10 | 0/300 |
| PlanetLab | WBP | e_total | 20.42 ± 1.16 | 20.34 ± 1.19 | -0.08141 | 0.0415 | 10 | 0/300 |
| PlanetLab | WBP | sla | 3.10 ± 0.34 | 3.25 ± 0.28 | +0.1565 | 0.112 | 10 | 0/300 |
| PlanetLab | WBP | migr | 368 ± 39 | 362 ± 36 | -6.43 | 0.424 | 10 | 0/300 |
| PlanetLab | WBP | traffic | 2165 ± 218 | 2121 ± 205 | -43.7 | 0.271 | 10 | 0/300 |
| Alibaba | WPSP | e_hosts | 20.96 ± 0.28 | 20.88 ± 0.29 | -0.08007 | 0.44 | 30 | 0/30 |
| Alibaba | WPSP | e_total | 21.27 ± 0.28 | 21.19 ± 0.30 | -0.08334 | 0.465 | 30 | 0/30 |
| Alibaba | WPSP | sla | 4.98 ± 0.80 | 5.23 ± 0.85 | +0.2501 | 0.371 | 30 | 0/30 |
| Alibaba | WPSP | migr | 366 ± 14 | 356 ± 18 | -9.467 | 0.393 | 30 | 0/30 |
| Alibaba | WPSP | traffic | 2223 ± 92 | 2200 ± 124 | -22.64 | 0.824 | 30 | 0/30 |
| Alibaba | WP | e_hosts | 20.90 ± 0.28 | 20.85 ± 0.28 | -0.05302 | 0.428 | 30 | 0/30 |
| Alibaba | WP | e_total | 21.17 ± 0.28 | 21.12 ± 0.28 | -0.05555 | 0.382 | 30 | 0/30 |
| Alibaba | WP | sla | 5.59 ± 0.64 | 5.58 ± 0.73 | -0.01224 | 0.968 | 30 | 0/30 |
| Alibaba | WP | migr | 327 ± 19 | 323 ± 13 | -4.367 | 0.688 | 30 | 0/30 |
| Alibaba | WP | traffic | 1924 ± 99 | 1907 ± 65 | -17.59 | 0.887 | 30 | 0/30 |
| Alibaba | WBP | e_hosts | 21.32 ± 0.28 | 21.31 ± 0.27 | -0.006811 | 0.871 | 30 | 0/30 |
| Alibaba | WBP | e_total | 21.63 ± 0.28 | 21.62 ± 0.27 | -0.009501 | 0.903 | 30 | 0/30 |
| Alibaba | WBP | sla | 5.31 ± 0.75 | 5.63 ± 0.78 | +0.3282 | 0.57 | 30 | 0/30 |
| Alibaba | WBP | migr | 376 ± 20 | 374 ± 18 | -2.3 | 0.91 | 30 | 0/30 |
| Alibaba | WBP | traffic | 2203 ± 115 | 2185 ± 95 | -18.83 | 0.792 | 30 | 0/30 |
| Materna | WPSP | e_hosts | 17.43 ± 0.14 | 17.50 ± 0.16 | +0.06632 | 0.404 | 30 | 0/30 |
| Materna | WPSP | e_total | 17.73 ± 0.14 | 17.80 ± 0.16 | +0.07609 | 0.262 | 30 | 0/30 |
| Materna | WPSP | sla | 5.55 ± 0.30 | 5.37 ± 0.36 | -0.1792 | 0.0879 | 30 | 0/30 |
| Materna | WPSP | migr | 356 ± 26 | 366 ± 23 | +9.767 | 0.441 | 30 | 0/30 |
| Materna | WPSP | traffic | 2072 ± 136 | 2140 ± 126 | +68.37 | 0.339 | 30 | 0/30 |
| Materna | WP | e_hosts | 17.95 ± 0.15 | 17.86 ± 0.17 | -0.08927 | 0.198 | 30 | 0/30 |
| Materna | WP | e_total | 18.27 ± 0.15 | 18.17 ± 0.17 | -0.09669 | 0.191 | 30 | 0/30 |
| Materna | WP | sla | 4.83 ± 0.39 | 4.97 ± 0.42 | +0.1318 | 0.503 | 30 | 0/30 |
| Materna | WP | migr | 387 ± 16 | 375 ± 18 | -11.27 | 0.44 | 30 | 0/30 |
| Materna | WP | traffic | 2238 ± 92 | 2186 ± 117 | -51.69 | 0.503 | 30 | 0/30 |
| Materna | WBP | e_hosts | 18.44 ± 0.16 | 18.37 ± 0.16 | -0.06693 | 0.477 | 30 | 0/30 |
| Materna | WBP | e_total | 18.78 ± 0.16 | 18.72 ± 0.16 | -0.05991 | 0.543 | 30 | 0/30 |
| Materna | WBP | sla | 4.38 ± 0.36 | 4.41 ± 0.48 | +0.02462 | 0.73 | 30 | 0/30 |
| Materna | WBP | migr | 418 ± 25 | 420 ± 23 | +1.3 | 0.877 | 30 | 0/30 |
| Materna | WBP | traffic | 2404 ± 135 | 2453 ± 138 | +49.22 | 0.824 | 30 | 0/30 |
| Microsoft Azure | WPSP | e_hosts | 18.56 ± 0.21 | 18.64 ± 0.20 | +0.07876 | 0.393 | 30 | 0/30 |
| Microsoft Azure | WPSP | e_total | 18.82 ± 0.22 | 18.89 ± 0.20 | +0.06802 | 0.503 | 30 | 0/30 |
| Microsoft Azure | WPSP | sla | 2.87 ± 0.32 | 2.51 ± 0.27 | -0.3579 | 0.0803 | 30 | 0/30 |
| Microsoft Azure | WPSP | migr | 324 ± 18 | 311 ± 21 | -12.8 | 0.416 | 30 | 0/30 |
| Microsoft Azure | WPSP | traffic | 1849 ± 98 | 1774 ± 124 | -75.01 | 0.271 | 30 | 0/30 |
| Microsoft Azure | WP | e_hosts | 18.82 ± 0.19 | 18.80 ± 0.18 | -0.0194 | 0.754 | 30 | 1/30 |
| Microsoft Azure | WP | e_total | 19.05 ± 0.20 | 19.02 ± 0.17 | -0.03689 | 0.496 | 30 | 1/30 |
| Microsoft Azure | WP | sla | 2.48 ± 0.24 | 2.57 ± 0.33 | +0.09099 | 0.673 | 30 | 1/30 |
| Microsoft Azure | WP | migr | 285 ± 22 | 264 ± 18 | -20.23 | 0.147 | 30 | 1/30 |
| Microsoft Azure | WP | traffic | 1634 ± 119 | 1511 ± 106 | -122.2 | 0.0677 | 30 | 1/30 |
| Microsoft Azure | WBP | e_hosts | 18.98 ± 0.21 | 19.04 ± 0.19 | +0.0508 | 0.299 | 30 | 0/30 |
| Microsoft Azure | WBP | e_total | 19.25 ± 0.21 | 19.31 ± 0.19 | +0.06267 | 0.262 | 30 | 0/30 |
| Microsoft Azure | WBP | sla | 2.31 ± 0.22 | 2.28 ± 0.23 | -0.02564 | 0.328 | 30 | 0/30 |
| Microsoft Azure | WBP | migr | 325 ± 22 | 343 ± 20 | +17.67 | 0.195 | 30 | 0/30 |
| Microsoft Azure | WBP | traffic | 1846 ± 125 | 1929 ± 116 | +82.72 | 0.289 | 30 | 0/30 |
