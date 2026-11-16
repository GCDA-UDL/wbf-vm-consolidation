# How to reproduce the experiments

Everything runs inside Docker — no local Java/Python needed. The image provides
**Java 8 + Python 3.8 + Facebook Prophet + the `jpy` bridge**; your clone provides the
simulator (`metacloud.jar`), the experiment configs (`testbed/`), the workload traces
(`workloads/`) and the forecasting code (`pymodule/`). Outputs are written to `output/`.

> Requirement: **Docker** (Desktop on Windows/macOS, Engine on Linux). ~6 GB free disk.

---

## 0. Clone

The simulator jar is committed directly — a plain clone fetches everything (no Git LFS needed).

```bash
git clone https://github.com/GCDA-UDL/wbf-vm-consolidation.git
cd wbf-vm-consolidation
```

## 1. Build the image (first time, ~10 min)

```bash
docker compose build           # or:  docker build -t metacloudsim .
```

---

## 2. Run an experiment

Each experiment is a file in `testbed/` (use the name **without** `.json`). Running it has **two
steps**: `testbed` expands the config into per-seed runs, and `folder` executes them. Output (the
per-seed `*_data.json`) goes to `output/<experiment>/`.

### Linux / macOS (bash)

```bash
EXP=paper4_full_planetlab_prophet
docker run --rm -v "$PWD":/workspace -w /workspace metacloudsim \
  bash -c "java -jar metacloud.jar testbed $EXP && java -jar metacloud.jar folder $EXP"
```

### Windows (PowerShell)

```powershell
$EXP = "paper4_full_planetlab_prophet"
docker run --rm -v "${PWD}:/workspace" -w /workspace metacloudsim `
  bash -c "java -jar metacloud.jar testbed $EXP && java -jar metacloud.jar folder $EXP"
```

### Or with docker compose (any OS)

```bash
docker compose run --rm sim          # default: PlanetLab, WP and WBP (runs testbed + folder)
# another experiment:
docker compose run --rm sim bash -c "java -jar metacloud.jar testbed paper4_full_alibaba_prophet && java -jar metacloud.jar folder paper4_full_alibaba_prophet"
```

### Available experiments

| Experiment (config) | Techniques | Workload |
|---------------------|-----------|----------|
| `paper4_full_planetlab_prophet` | WP + **WBP** (Prophet without and with the Bollinger step; `WF`/`WBF` in older notes) | PlanetLab |
| `paper4_full_planetlab_static`  | MU / MMT / RS / MC / WPSP (classical) | PlanetLab |
| `paper4_full_alibaba_prophet` / `_static` | as above | Alibaba 2018 |
| `paper4_full_materna_prophet` / `_static` | as above | Materna |
| `paper4_full_azure_prophet` / `_static`   | as above | Microsoft Azure 2019 |
| `exp_bollinger_search` | Bollinger parameter sweep | Materna |
| `exp_neuralprophet` | NeuralProphet vs Facebook Prophet | PlanetLab (needs neural image, see §4) |

Each run sweeps **30 random seeds**; a full workload takes a while (minutes to ~1 h depending on
CPU).

### Experiments behind the tables of the revised manuscript

The tables are computed from the output folders below (`<day>` is one of the ten PlanetLab days:
20110303, 20110306, 20110309, 20110322, 20110325, 20110403, 20110409, 20110411, 20110412, 20110420).
The `_st` configs are identical to the configs without the suffix except for their name.

| Techniques | Experiment configs | Runner |
|---|---|---|
| MU, MMT, RS, MC, WPSP | `pl_static_<day>`, `paper4_full_<workload>_static` | `scripts/run_static_campaign.sh` |
| WP, WBP | `p4_pl_<day>_st`, `paper4_full_<workload>_prophet_st` | `scripts/run_sota_batch.sh <config> ...` |
| BB+NeoPro | `np_pl_<day>_st`, `np_<workload>_st` (neural image, see §4) | `scripts/run_np_campaign.sh` |
| AMOVMC, EUQ-VMC (shared placement) | `amovmc_pl_<day>`, `amovmc_<workload>`, `euqvmc_pl_<day>`, `euqvmc_<workload>` | `scripts/run_sota_batch.sh <config> ...` |
| AMOVMC, EUQ-VMC (own placement) | `amovmc_native_*`, `euqvmc_native_*` | `scripts/run_sota_batch.sh <config> ...` |
| Parameter sweeps (one PlanetLab day) | `amovmc_tune_g*`, `euqvmc_tune_s*` | `scripts/run_sota_batch.sh <config> ...` |

`<workload>` is `alibaba`, `materna` or `azure`. The runners are meant to be started inside the
container, for example:

```bash
docker run --rm -v "$PWD":/workspace -w /workspace metacloudsim \
  bash scripts/run_sota_batch.sh paper4_full_materna_prophet_st
```

For AMOVMC and EUQ-VMC, gamma = 0.80 (AMOVMC overload test; fixed in the `amovmc` policy) and
safe = 1.5 (EUQ-VMC safety factor; the `parameter` of its configs) were set by the authors of this
package; the original articles do not report these values. The `*_tune_*` configs sweep them.

### Experiments added by the revision

The closed-loop replacement of the forecaster, the sensitivity to the Bollinger parameters and the
forecast accuracy under the protocol of the method have their own run lists and launch scripts,
which execute one simulation per JVM from single-configuration testbeds derived from
`p4_pl_<day>_st` and `paper4_full_<workload>_prophet_st`. See
[experiments/revision_r1/README.md](experiments/revision_r1/README.md).

---

## 3. Analyse the results (tables and figures)

After the runs, the per-simulation JSON files are in `output/<experiment>/`. Analyse them with
the bundled script or the notebooks.

```bash
# inside the image (no local Python needed)
docker run --rm -v "$PWD":/workspace -w /workspace metacloudsim \
  python3.8 scripts/analyze_results.py

# or interactive notebooks at http://localhost:8888
docker compose up jupyter
```

`scripts/analyze_results.py` and the notebooks belong to the analysis of the submitted version
(`analyze_results.py` computes its composite energy). The tables and figures of the revised manuscript are produced by the scripts of
[analysis_revision/](analysis_revision/README.md), and its reference values are in
[results/reference/README.md](results/reference/README.md). Compare aggregates, not individual
runs: individual runs are not reproducible bit for bit, because ties between equivalent candidates
are resolved by the iteration order of hash-based collections, and the results are distributions
over seeds and traces (see that file).

---

## 4. NeuralProphet comparison (optional)

NeuralProphet needs a separate image (torch 1.6 + neuralprophet 0.2.7):

```bash
docker build -f Dockerfile.neural -t metacloudsim-neural .
docker run --rm -v "$PWD":/workspace -w /workspace metacloudsim-neural \
  java -jar metacloud.jar testbed exp_neuralprophet
```

The BB+NeoPro columns of the manuscript come from the `np_*_st` configs, run with
`scripts/run_np_campaign.sh` inside the neural image; `exp_neuralprophet` is an earlier exploratory
config. BB+NeoPro is the WBP loop with the NeuralProphet forecaster in place of Prophet; it is not
the 2023 method as published.

---

## Notes

- `LD_PRELOAD` (libpython) and the `jpy` config are set inside the image — you don't need to set
  anything.
- Threads: images built from this version of the `Dockerfile` set
  `OMP/STAN/MKL/OPENBLAS_NUM_THREADS=1`. With an image built from v0.2.3 or earlier, add
  `-e OMP_NUM_THREADS=1 -e STAN_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1` to
  `docker run`.
- Energy: the revised manuscript reports host energy, migration energy and total energy, as
  defined in [results/reference/README.md](results/reference/README.md). The migration-energy
  coefficient is 0.512 J per MB and hop, from the model of Liu et al. (HPDC 2011, Eq. 17); the
  4.096 J/MB of the submitted version is eight times that value and is not a measurement. No
  coefficient was measured by the authors.
- The PlanetLab table of the manuscript averages ten daily traces; the ten subsets are shipped
  under `workloads/planetlab/`.
- Workload licensing and sources: see [workloads/DATA_LICENSES.md](workloads/DATA_LICENSES.md).
