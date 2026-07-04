# Reference results — paper Tables 6–9 (ground truth)

These are the values published in the paper. Use them as the **ground truth** to compare any
re-run produced under `output/<experiment>/`.

## Metrics

| Metric | Description | Unit | Better |
|--------|-------------|------|--------|
| Energy | Total (composite) energy of the simulation | kWh | lower |
| SLA | Service-Level-Agreement violations | % | lower |
| Migrations | Number of VM migrations | # | lower |
| ESV | Energy–SLA Value (combined metric) | — | lower |

## Table 6 — PlanetLab (all techniques)

| Technique | Energy (kWh) | SLA (%) | Migrations | ESV |
|-----------|-------------:|--------:|-----------:|----:|
| MU | 38.71 | 5.43 | 1618 | 210.27 |
| MMT | 28.44 | 2.92 | 931 | 84.15 |
| RS | 28.70 | 3.00 | 776 | 85.79 |
| MC | 28.87 | 2.94 | 828 | 85.23 |
| WPSP | 24.74 | 4.02 | 454 | 99.77 |
| WF | 23.16 | 2.46 | 322 | 56.33 |
| **WBF** | **23.15** | **2.23** | **296** | **53.84** |

WBF = WF + Bollinger Bands signal processing → best in 3 of 4 metrics.

## Table 7 — Alibaba
| Technique | Energy (kWh) | SLA (%) | Migrations | ESV |
|-----------|-------------:|--------:|-----------:|----:|
| WF | 26.47 | 5.14 | 350 | 135.12 |
| **WBF** | 28.02 | **3.02** | **330** | **85.21** |

## Table 8 — Materna
| Technique | Energy (kWh) | SLA (%) | Migrations | ESV |
|-----------|-------------:|--------:|-----------:|----:|
| WF | 24.17 | 3.48 | 371 | 84.55 |
| **WBF** | 25.13 | **2.41** | **320** | **60.68** |

## Table 9 — Azure
| Technique | Energy (kWh) | SLA (%) | Migrations | ESV |
|-----------|-------------:|--------:|-----------:|----:|
| WF | 23.43 | 2.26 | 294 | 51.98 |
| **WBF** | 24.59 | **1.63** | **259** | **39.50** |

## How to compare a new run

1. Run the experiments (see [../../REPRODUCE.md](../../REPRODUCE.md)) — results land in `output/<experiment>/`.
2. Aggregate them: `python3 scripts/analyze_results.py --output-dir output --out summary.json`
   (or open `python/notebooks/statistics_paper4.ipynb`).
3. Compare the aggregated tables with the reference values above.

Note: PlanetLab Table 6 averages 10 daily traces; the shipped subset reproduces the trends, while
exact absolute values need the full set of traces.
