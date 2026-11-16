# Analysis of the revised manuscript

Scripts that produce every result table and figure of the revised manuscript from the raw simulation
outputs. They are read-only on their inputs and need only Python 3 with `numpy`, `scipy` and
`matplotlib`. They were developed and run with Python 3.12 (numpy 1.26, scipy 1.15, matplotlib 3.10);
they have not yet been run with the Python 3.8 of the Docker image of this repository.

| File | What it does |
|---|---|
| `extract_runs.py` | One pass over `output/<experiment>/*_data.json`; writes one compact record per simulation (`runs.jsonl`). |
| `revlib.py` | Metric definitions and the map from experiment folders to techniques. |
| `build_revision.py` | Result tables (LaTeX), `facts.json` (every aggregate), `facts.md`, `stats.md` (paired tests). |
| `derived_checks.py` | Derived quantities quoted in the text (ranges, ratios, shares), from `facts.json`. |
| `make_reference_readme.py` | Writes `results/reference/README.md` from `results/reference/facts.json`. |
| `figures/` | Vector figures (results, energy components, sensitivity, topology, decision cycle) and the workload table; see `figures/README.md`. |

The tables of the three experiments added by the revision (closed-loop replacement of the forecaster,
sensitivity to the Bollinger parameters, forecast accuracy) are produced by the scripts of
[../experiments/revision_r1/](../experiments/revision_r1/README.md), which import `revlib.py` from this
folder.

## Metric definitions used by the revised manuscript

- Migration traffic is counted once per migration. The simulator registers every migration twice in its
  network accounting, so `revlib.py` halves `totalRAMInBW` and `totalMigratedRAM`.
- Host energy = `energyWithExtraHost` (execution + start-up + shutdown).
- Migration energy = (0.512 J per MB and hop × migration traffic + 20.165 J per migration) / 3.6e6 kWh.
  The coefficient 0.512 J/MB and the fixed term come from the model of Liu et al. (HPDC 2011, Eq. 17:
  E = 0.512·V + 20.165, V in megabytes, E in joules). No coefficient was measured by the authors.
- PlanetLab confidence intervals and tests use the ten daily means; the other workloads use the 30 seeds.

The scripts under `SOTA/` implement the energy expression of the submitted version and are kept for
traceability; see `SOTA/README.md`.

## Commands

The raw outputs are not stored in git (see `ARTIFACTS.md`). Either run the experiments (see
`REPRODUCE.md`; outputs go to `output/<experiment>/`) or unpack the archive of run outputs at the
repository root, so that `output/` exists. Then, from this folder:

```bash
# 1. per-run cache (reads output/, writes cache/runs.jsonl)
python -B extract_runs.py --out ../output --cache cache

# 2. tables, facts and tests (writes out/tables/*.tex, out/facts.json, out/facts.md, out/stats.md)
python -B build_revision.py --cache cache --out out

# 3. derived quantities quoted in the text
python -B derived_checks.py out/facts.json

# 4. figures and workload table (writes out/figures/*.pdf, out/tables/tab_workload_stats.tex)
cd figures && python -B make_all.py && cd ..

# 5. reference tables of the package
cp out/facts.json out/stats.md ../results/reference/
python -B make_reference_readme.py
```

`build_revision.py` accepts `--kappa` and `--beta` to rebuild every table with another
migration-energy coefficient; the sensitivity table covers the values 0, 0.512, 1, 2, 3.549 and 4.096
J per MB and hop. 0.512 is the reference (model of Liu et al.), 3.549 is the value measured by Sarji et
al. (2011), which is the constant built into the simulator, and 4.096 is the value used in the submitted
version (eight times the reference; it is not a measurement).

## What a re-execution reproduces

See the section "Comparing a re-execution with these tables" of `results/reference/README.md`: individual
runs of the stored campaign are not reproduced value by value; compare aggregates.
