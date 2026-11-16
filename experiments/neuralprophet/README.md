# Facebook Prophet vs. NeuralProphet

> **Status (revision of November 2026).** Exploratory run made before the campaign of the manuscript. It is not the comparison reported in the revised manuscript. That comparison is the BB+NeoPro campaign (`testbed/np_*_st.json`, `scripts/run_np_campaign.sh`; 13 traces × 30 seeds); BB+NeoPro is the WBP loop with the NeuralProphet forecaster in place of Prophet, not the 2023 method as published. In that campaign none of the differences between WBP and BB+NeoPro is statistically significant on Alibaba, Materna and Azure, and on PlanetLab BB+NeoPro uses less total energy with higher SLA violations (`results/reference/README.md`, `results/reference/stats.md`). The statements and the explanation below were not re-verified. WP and WBP were called WF and WBF when this note was written.

## Question
Would a deep-learning forecaster — **NeuralProphet** (Triebe et al., 2021), which augments the
Prophet decomposition with auto-regressive neural modules — improve the consolidation over standard
**Facebook Prophet**?

## Design
Keeping everything else fixed (same workloads, seeds, policies), only the host forecaster is
replaced (`fbProphet` → `neuralProphet`) and WP and WBP are re-run on the four workloads:
- WP  = WPSP + forecaster, **without** Bollinger
- WBP = WPSP + forecaster, **with** Bollinger (5, 0.5)

Config: `../../testbed/exp_neuralprophet.json` · image: `Dockerfile.neural` (torch 1.6 +
neuralprophet 0.2.7). Analysis: `compare_fp_np.py`.

## Result — number of migrations (lower is better)

| Workload | WP · FP | WP · NP | WBP · FP | WBP · NP |
|----------|--------:|--------:|---------:|---------:|
| PlanetLab | **281** | 353 | **300** | 332 |
| Alibaba   | **314** | 432 | **369** | 434 |
| Materna   | **354** | 385 | **418** | 453 |
| Azure     | **289** | 366 | 323 | **290** |

Facebook Prophet produces fewer migrations than NeuralProphet in **7 of 8** cases, and also lower
SLA violations and energy in almost all of them.

## Why
With the short decision window (a sliding history of 30 steps), NeuralProphet's learning-rate range
test does not converge and falls back to a sub-optimal default, whereas Facebook Prophet is robust
with little data and missing values. This empirically justifies the choice of Facebook Prophet for
the migration-decision task over a heavier neural model (it is also reported in the paper).
