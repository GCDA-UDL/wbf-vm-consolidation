# Virtual Machine Consolidation in Cloud Computing Using Prophet's Forecasting Tool — reproduction package

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21197524.svg)](https://doi.org/10.5281/zenodo.21197524)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Reproducible with Docker](https://img.shields.io/badge/reproducible-Docker-2496ED.svg)

Reproducible code, configurations and analysis for the paper:

> **Virtual Machine Consolidation in Cloud Computing Using Prophet's Forecasting Tool**.

**Authors:** Vitor L. da Silva, Sergi Vila, Rosa Ana Tomás, Concepció Roig, Francesc Giné,
Fernando Cores, Josep L. Lérida, Fernando Guirado — SEMBAC, University of Lleida (UdL), Spain.

The proposed method, **WBP = WPSP + Bollinger Bands + Prophet** (formerly named WBF; the
repository, the experiment configs and the output folders keep the original names, in which `WF`
is WP and `WBF` is WBP), performs proactive VM consolidation. At every decision it replaces the
recent load history of each host by its upper Bollinger Band, forecasts the host load with
Prophet, compares the forecast with an adaptive capacity threshold, and selects the VMs that
leave an overloaded host with the Weighted Pearson Selection Policy (WPSP). The energy model adds
host start-up and shutdown and the data moved by migrations along the network path to the energy
of the active hosts. WBP is compared, in the same simulator, against the classical selection
policies (MU/MMT/RS/MC), its own variants without the Bollinger step (WP) and without the
forecast (WPSP), two recent (2025) methods, **AMOVMC** and **EUQ-VMC**, and **BB+NeoPro**, the
WBP loop with the NeuralProphet forecaster in place of Prophet (it is not our 2023 method as
published).

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
docker compose run --rm sim                  # run PlanetLab (WP and WBP)
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
**[workloads/DATA_LICENSES.md](workloads/DATA_LICENSES.md)**. The reference values of the revised
manuscript (per-workload tables and comparison with recent methods) are in
[results/reference/README.md](results/reference/README.md).

## Heavy run artifacts

The raw per-seed simulation outputs and logs of the full campaign (~3 GB) are **not** in git; they
are archived separately (shared cloud + Zenodo). See **[ARTIFACTS.md](ARTIFACTS.md)**. The runs
above regenerate outputs of the same kind from scratch; the individual values of a re-execution
differ from the stored ones, so compare aggregates (see
[results/reference/README.md](results/reference/README.md)).

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
├── results/reference/        # reference tables of the revised manuscript (generated)
├── analysis_revision/        # scripts behind the tables and figures of the revised manuscript
├── SOTA/                     # AMOVMC & EUQ-VMC sources and the analysis of the submitted version
├── experiments/              # experiments of the revision (revision_r1/) and exploratory studies
├── scripts/                  # analysis helpers + container entrypoint
├── python/notebooks/         # analysis notebooks (tables and figures)
├── Dockerfile                # toolchain: Java 8 + Python 3.8 + Prophet + jpy
├── Dockerfile.neural         # variant with NeuralProphet (forecaster comparison)
├── docker-compose.yml        # services: sim + jupyter
├── CITATION.cff              # how to cite this software (read by Zenodo/GitHub)
├── CHANGELOG.md              # what changes from one version to the next
└── REPRODUCE.md              # how to run each experiment (Linux + Windows)
```

---

## Revision of the manuscript (November 2026, not yet released)

The manuscript was revised after peer review, and the analysis changed with it. This branch of the
package follows the revised manuscript.

- **Energy.** The revised manuscript reports host energy, migration energy and their sum. Migration
  traffic is counted once per migration (the simulator registers each migration twice in its network
  accounting), and the 1.1 factor of the submitted version is not used. The migration-energy
  coefficient is 0.512 J per MB and hop, the coefficient of the model of Liu et al. (HPDC 2011,
  Eq. 17: E = 0.512·V + 20.165, V in megabytes, E in joules). The comparison of total energy is
  repeated for coefficients between 0 and 4.096 J per MB and hop, among them 3.549 J/MB, the value
  measured by Sarji et al. (2011) and the constant built into the simulator, and 4.096 J/MB, the
  value used in the submitted version (eight times the reference; it is not a measurement). No
  coefficient was measured by the authors.
- **Statistics.** PlanetLab confidence intervals and tests use the ten daily traces as the unit of
  replication. One family of 360 paired tests, Holm-corrected.
- **Analysis scripts.** `analysis_revision/` produces every table and figure of the revised
  manuscript; `results/reference/` holds the resulting reference tables, `facts.json` and `stats.md`.
- **Threads.** The `Dockerfile` now sets the single-thread variables (see the notes below).
- **Documentation.** Files that describe the submitted version (24 September 2026) are marked as
  such: `SOTA_COMPARISON.md`, `SOTA/*.md`, `experiments/neuralprophet/`.
- **Compared methods.** The original AMOVMC and EUQ-VMC articles do not report a value for gamma
  (AMOVMC overload test) or for the safety factor `safe` (EUQ-VMC): gamma = 0.80 and safe = 1.5 were
  set by the authors of this package. The re-implementation of AMOVMC is partial: its neural
  predictor is not implemented, the inverted overload test differs from Eq. (11) of its article
  for some host sizes, under-utilised hosts are handled by the simulator, and its native placement
  uses equal weights for the six terms of its fitness function. The list is in
  [SOTA_COMPARISON.md](SOTA_COMPARISON.md).
- **Added by the revision, reported in the revised manuscript:** a closed-loop replacement of the
  forecaster (last value, EWMA, Prophet, each with and without the Bollinger step; 2,340 runs), a
  sensitivity analysis of the Bollinger parameters N and alpha (780 runs besides the reference
  setting N = 5, alpha = 0.5) and the forecast accuracy under the protocol of the method. Run lists,
  tools and tables are in [experiments/revision_r1/](experiments/revision_r1/README.md); their raw
  outputs are not shipped in this version.

The list of changes with respect to v0.2.3 is in [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.2.0 (version of the submitted manuscript)

The items below describe the analysis of the submitted version. Its energy definition and its
statistics were replaced in the revision (see above), and its forecaster validation had errors
that are listed in `SOTA/forecast_accuracy.md`.


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

- **Energy.** The revised manuscript uses the definitions of
  [results/reference/README.md](results/reference/README.md). The scripts under `SOTA/`,
  `scripts/analyze_results.py` and `python/notebooks/statisticsSource.ipynb` compute the composite
  energy of the submitted version.
- **Threads.** Images built from this version of the `Dockerfile` set
  `OMP/STAN/MKL/OPENBLAS_NUM_THREADS=1`. In v0.2.3 and earlier only `scripts/run_np_campaign.sh` and
  `scripts/run_np_resume.sh` exported these variables, so the commands of `REPRODUCE.md` did not set
  them for the Prophet campaign.
- **Individual runs are not reproducible bit for bit.** Ties between equivalent candidates are
  resolved by the iteration order of hash-based collections, so the results are distributions over
  seeds and traces: compare aggregates. The runs of WPSP, WP and WBP were executed again
  (1,170 runs) and the means of the two campaigns agree: one of 60 paired comparisons has p < 0.05
  before correction for multiple tests
  ([results/reference/README.md](results/reference/README.md),
  [experiments/revision_r1/tables/rerun_vs_stored.md](experiments/revision_r1/tables/rerun_vs_stored.md)).
  Earlier versions of this file stated that the results were bit-reproducible; that statement was
  wrong.
- **Size of the campaign.** The tables of the revised manuscript rest on 3,900 simulations
  (13 traces × 10 techniques × 30 seeds); the native-placement and parameter-sweep tables use the
  additional configs `*_native_*` and `*_tune_*`.

---

## Citation

If you use this software, please cite **both** the paper (above) and this reproduction package,
archived on Zenodo: **DOI [10.5281/zenodo.21197524](https://doi.org/10.5281/zenodo.21197524)**.
Machine-readable metadata is in [CITATION.cff](CITATION.cff).

## Funding

This work has been granted by the Ministerio de Ciencia, Innovación y Universidades (MICIU) AEI/10.13039/501100011033 under contract PID2023-146193OB-I00.

## License

The original code, configurations and documentation in this repository are released under the
**MIT License** ([LICENSE](LICENSE)). Bundled third-party components (CloudSim, `jpy`, Facebook
Prophet and other dependencies inside `metacloud.jar` and the Docker image) retain their own
licenses — see [THIRD_PARTY.md](THIRD_PARTY.md).

**Contact:** Dr. Vitor L. da Silva — vitor.dasilva@udl.cat
