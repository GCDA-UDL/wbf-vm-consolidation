# How to reproduce the experiments

Everything runs inside Docker — no local Java/Python needed. The image provides
**Java 8 + Python 3.8 + Facebook Prophet + the `jpy` bridge**; your clone provides the
simulator (`metacloud.jar`), the experiment configs (`testbed/`), the workload traces
(`workloads/`) and the forecasting code (`pymodule/`). Results are written to `results/`.

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
docker compose run --rm sim          # default: PlanetLab Prophet/WBF (runs testbed + folder)
# another experiment:
docker compose run --rm sim bash -c "java -jar metacloud.jar testbed paper4_full_alibaba_prophet && java -jar metacloud.jar folder paper4_full_alibaba_prophet"
```

### Available experiments

| Experiment (config) | Techniques | Workload |
|---------------------|-----------|----------|
| `paper4_full_planetlab_prophet` | WF + **WBF** (Facebook Prophet ± Bollinger) | PlanetLab |
| `paper4_full_planetlab_static`  | MU / MMT / RS / MC / WPSP (classical) | PlanetLab |
| `paper4_full_alibaba_prophet` / `_static` | as above | Alibaba 2018 |
| `paper4_full_materna_prophet` / `_static` | as above | Materna |
| `paper4_full_azure_prophet` / `_static`   | as above | Microsoft Azure 2019 |
| `exp_bollinger_search` | Bollinger parameter sweep | Materna |
| `exp_neuralprophet` | NeuralProphet vs Facebook Prophet | PlanetLab (needs neural image, see §4) |

Each run sweeps **30 random seeds**; a full workload takes a while (minutes to ~1 h depending on
CPU). To reproduce all four workloads, run the eight `paper4_full_*` experiments.

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

The paper's reference values (Tables 6–9) are in `results/reference/` for comparison.

---

## 4. NeuralProphet comparison (optional)

NeuralProphet needs a separate image (torch 1.6 + neuralprophet 0.2.7):

```bash
docker build -f Dockerfile.neural -t metacloudsim-neural .
docker run --rm -v "$PWD":/workspace -w /workspace metacloudsim-neural \
  java -jar metacloud.jar testbed exp_neuralprophet
```

---

## Notes

- `LD_PRELOAD` (libpython) and the `jpy` config are set inside the image — you don't need to set
  anything.
- Energy reported is **composite** (host energy + network-routing energy of migrations).
- PlanetLab Table 6 in the paper averages 10 daily traces; `planetlab_20110303` and
  `planetlab_20110403` are shipped. Add the remaining traces from CloudSim for the exact average.
- Workload licensing and sources: see [workloads/DATA_LICENSES.md](workloads/DATA_LICENSES.md).
