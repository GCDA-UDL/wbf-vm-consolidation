# Facebook Prophet vs. NeuralProphet — full metrics (4 workloads)

> **Status (revision of November 2026).** Exploratory runs made before the campaign of the manuscript; the energy column is the composite energy of the submitted version. Not the comparison reported in the revised manuscript: see the note at the top of `README.md` in this folder. The rows "WBP, NeuralProphet" are the WBP loop with the NeuralProphet forecaster in place of Prophet, which is what the manuscript calls BB+NeoPro; they are not the 2023 method as published. WP and WBP were called WF and WBF when this note was written.

FP = Facebook Prophet (our forecaster). NP = NeuralProphet. Energy is the **composite** energy
(host + network-routing of migrations). Lower is better, except ME (higher is better).

## PlanetLab
| Technique | Forecaster | Energy | SLA % | Migr | ESV | ME | RAM-BW |
|-----------|-----------|-------:|------:|-----:|----:|---:|-------:|
| WP  | **Facebook Prophet** | 25.5 | 4.44 | **281** | 112.4 | 9.91 | 34.0 |
| WP  | NeuralProphet | 26.7 | 6.00 | 353 | 160.7 | 9.45 | 44.9 |
| WBP | **Facebook Prophet** | 26.4 | 3.57 | **300** | 93.8 | 9.69 | 35.1 |
| WBP | NeuralProphet | 27.3 | 4.08 | 332 | 111.7 | 9.45 | 41.8 |

## Alibaba
| Technique | Forecaster | Energy | SLA % | Migr | ESV | ME | RAM-BW |
|-----------|-----------|-------:|------:|-----:|----:|---:|-------:|
| WP  | **Facebook Prophet** | 25.5 | 5.58 | **314** | 141.2 | 9.82 | 37.5 |
| WP  | NeuralProphet | 26.5 | 7.43 | 432 | 195.9 | 9.26 | 50.7 |
| WBP | **Facebook Prophet** | 26.5 | 5.97 | **369** | 157.3 | 9.41 | 42.7 |
| WBP | NeuralProphet | 27.4 | 5.38 | 434 | 145.4 | 9.18 | 49.8 |

## Materna
| Technique | Forecaster | Energy | SLA % | Migr | ESV | ME | RAM-BW |
|-----------|-----------|-------:|------:|-----:|----:|---:|-------:|
| WP  | **Facebook Prophet** | 23.1 | 5.02 | **354** | 115.7 | 9.25 | 41.7 |
| WP  | NeuralProphet | 23.4 | 6.10 | 385 | 142.9 | 9.11 | 45.5 |
| WBP | **Facebook Prophet** | 24.3 | 4.53 | **418** | 110.0 | 8.82 | 47.8 |
| WBP | NeuralProphet | 24.7 | 5.60 | 453 | 138.3 | 8.68 | 53.2 |

## Azure
| Technique | Forecaster | Energy | SLA % | Migr | ESV | ME | RAM-BW |
|-----------|-----------|-------:|------:|-----:|----:|---:|-------:|
| WP  | **Facebook Prophet** | 22.9 | 2.60 | **289** | 59.8 | 9.70 | 32.6 |
| WP  | NeuralProphet | 23.5 | 2.89 | 366 | 68.4 | 9.29 | 41.1 |
| WBP | **Facebook Prophet** | 23.6 | 2.33 | 323 | 55.1 | 9.43 | 36.5 |
| WBP | NeuralProphet | 22.7 | 3.13 | 290 | 71.1 | 9.60 | 33.3 |

## Conclusion
Facebook Prophet beats NeuralProphet in 7 of 8 cases (fewer migrations, and usually lower SLA and
energy). NeuralProphet struggles with the short 30-step decision windows; Facebook Prophet is robust
with little data, which is what the migration-decision task needs.
