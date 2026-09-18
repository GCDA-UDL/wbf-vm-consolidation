# Virtual Machine Consolidation in Cloud Computing Using Prophet's Forecasting Tool — reproduction package

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21197524.svg)](https://doi.org/10.5281/zenodo.21197524)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Reproducible with Docker](https://img.shields.io/badge/reproducible-Docker-2496ED.svg)

Reproducible code, configurations and analysis for the paper:

> **Virtual Machine Consolidation in Cloud Computing Using Prophet's Forecasting Tool**.

**Authors:** Vitor L. da Silva, Sergi Vila, Rosa Ana Tomás, Concepció Roig, Francesc Giné,
Fernando Cores, Josep L. Lérida, Fernando Guirado — SEMBAC, University of Lleida (UdL), Spain.

The proposed method, **WBP = WPSP + Bollinger Bands + Prophet** (formerly named WBF; the
repository keeps its original name), performs proactive VM consolidation: it forecasts host/VM
load with Prophet, filters transient peaks with Bollinger Bands, and selects which VMs to migrate
with a Weighted Pearson Selection Policy (WPSP), under an energy model that includes the
**network-routing cost** of migrations. It is compared, in the same simulator, against classical
baselines (MU/MMT/RS/MC/WPSP), two recent (2025) methods, **AMOVMC** and **EUQ-VMC**, and our
previous method **BB+NeoPro** (Bollinger + NeuralProphet).

This repository contains everything needed to **reproduce the experiments** in a self-contained
Docker environment — no local Java or Python required.

---

## Quick start (clone → build → run)

Only **Docker** is required. The simulator (`metacloud.jar`), configs, workload subsets and
forecasting code are all in the repository (the jar is committed directly — no Git LFS).

```bash
git clone https://github.com/GCDA-UDL/wbf-vm-consolidation.git
cd wbf-vm-consolidation
docker compose build                         # build the image (~10 min, first time)
docker compose run --rm sim                  # run PlanetLab (WBF + Prophet)
docker compose up jupyter                    # analysis at http://localhost:8888
```

Run any experiment by name (a file in `testbed/` without `.json`). Two steps: `testbed` expands
the config into per-seed runs, `folder` executes them → `output/<exp>/`.

**Linux / macOS**
```bash
EXP=paper4_full_alibaba_prophet
docker run --rm -v "$PWD":/workspace -w /workspace metacloudsim \
  bash -c "java -jar metacloud.jar testbed $EXP && java -jar metacloud.jar folder $EXP"
```
**Windows (PowerShell)**
```powershell
$EXP = "paper4_full_alibaba_prophet"
docker run --rm -v "${PWD}:/workspace" -w /workspace metacloudsim `
  bash -c "java -jar metacloud.jar testbed $EXP && java -jar metacloud.jar folder $EXP"
```

➡ **Full step-by-step for every experiment: [REPRODUCE.md](REPRODUCE.md)** (Linux + Windows).

---

## Workloads (data)

Four public cloud workloads — **PlanetLab, Alibaba 2018, Materna, Microsoft Azure 2019**. Small
**100-VM processed subsets** (`*_100_mostDiff`, ~14 MB) are **included** under `workloads/` so
everything reproduces from a single clone. Each dataset keeps its original license — see
**[workloads/DATA_LICENSES.md](workloads/DATA_LICENSES.md)**. The paper's reference values
(Tables 6–9) are in `results/reference/`.

## Heavy run artifacts

The raw per-seed simulation outputs and logs of the full campaign (~3 GB) are **not** in git; they
are archived separately (shared cloud + Zenodo). See **[ARTIFACTS.md](ARTIFACTS.md)**. You do not
need them to reproduce — the runs above regenerate the outputs from scratch.

---

## Repository structure

```
.
├── metacloud.jar             # the CloudSim-based simulator (committed directly)
├── launcher.json             # paths used inside the container (baseFolder=/workspace)
├── pymodule/                 # Python forecasting (Prophet, Bollinger, ...) loaded via jpy
├── testbed/                  # experiment configs (paper4_full_*, amovmc_*, euqvmc_*, exp_*)
├── workloads/                # 100-VM trace subsets + DATA_LICENSES.md
├── topologies/ hosts/ vms/   # network topology and host/VM definitions
├── interactions/             # VM-to-VM communication patterns
├── results/reference/        # paper Tables 6–9 (ground truth)
├── SOTA/                     # AMOVMC & EUQ-VMC comparison scripts + SOTA_COMPARISON.md
├── experiments/              # additional studies (NeuralProphet vs Prophet, Bollinger tuning)
├── scripts/                  # analysis helpers + container entrypoint
├── python/notebooks/         # analysis notebooks (tables and figures)
├── Dockerfile                # toolchain: Java 8 + Python 3.8 + Prophet + jpy
├── Dockerfile.neural         # variant with NeuralProphet (forecaster comparison)
├── docker-compose.yml        # services: sim + jupyter
├── CITATION.cff              # how to cite this software (read by Zenodo/GitHub)
└── REPRODUCE.md              # how to run each experiment (Linux + Windows)
```

---

## What's new in v0.2.0 (major-review revision)

- **Single energy definition everywhere**: all comparisons now use the composite network-aware
  energy (host + migration-routing). `SOTA/emit_transposed.py` regenerates the paper's
  full-metric SOTA table (9 metrics x 4 methods x 4 workloads).
- **Statistics**: `SOTA/stats_ic95_wilcoxon.py` — mean ± 95% CI, paired Wilcoxon signed-rank
  (common random seeds), Holm–Bonferroni correction, per-test winner.
- **BB+NeoPro campaign**: `testbed/np_*.json` + `scripts/run_np_campaign.sh` — NeuralProphet
  under the same 30 seeds / single-thread environment (390 simulations).
- **Classical-baseline reconciliation campaign**: `testbed/pl_static_*.json`,
  `paper4_full_*_static.json` + `scripts/run_static_campaign.sh` (1,950 simulations).
- **Forecaster validation**: `SOTA/forecast_accuracy.py` — one-step-ahead MAE/RMSE/MAPE of
  Prophet vs naive-last vs EWMA on the full VM population (141k windows).
- **Fairness analysis**: `SOTA/fair_sota.py` — AMOVMC/EUQ-VMC under shared vs their native
  placement. Result summaries in `SOTA/*.md`.

## Reproducibility notes

- The classical baselines (MU/MMT/RS/MC/WPSP) reproduce the original output within < 5 %.
- Energy is **composite** (host energy + network-routing energy of migrations), as in the paper.
- Results are **bit-reproducible**: the Facebook Prophet / Stan back-end is pinned to a single
  thread (`OMP/STAN/MKL/OPENBLAS_NUM_THREADS=1`) inside the image, so two independent runs match.
- The full 30-seed campaign over the four workloads has been executed (0 errors).

---

## Citation

If you use this software, please cite **both** the paper (above) and this reproduction package,
archived on Zenodo: **DOI [10.5281/zenodo.21197524](https://doi.org/10.5281/zenodo.21197524)**.
Machine-readable metadata is in [CITATION.cff](CITATION.cff).

## Funding

This work has been granted by the Ministerio de Ciencia, Innovación y Universidades (MICIU)
AEI/10.13039/501100011033 under contract PID2023-146193OB-I00.

## License

The original code, configurations and documentation in this repository are released under the
**MIT License** ([LICENSE](LICENSE)). Bundled third-party components (CloudSim, `jpy`, Facebook
Prophet and other dependencies inside `metacloud.jar` and the Docker image) retain their own
licenses — see [THIRD_PARTY.md](THIRD_PARTY.md).

**Contact:** Dr. Vitor L. da Silva — vitor.dasilva@udl.cat
