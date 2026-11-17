# Experiments added by the revision of the manuscript

Run lists, tools and resulting tables of the four experiments that the revised manuscript adds to
the campaign of the main tables. They use the simulator, the configurations and the workload subsets
of this repository without any change; only the experiment configuration differs from run to run.

This folder holds what defines the runs (lists and generators), the scripts that launch them and
build the tables, the tables themselves and, in `caches/`, the per-run records from which every
table is computed. **The raw outputs of the simulations are not shipped.** See "Per-run caches" and
"What is not shipped" below.

## The four experiments

| Experiment | Table of the manuscript | Runs | Lists | Output folders |
|---|---|---|---|---|
| Closed-loop replacement of the forecaster | `tab:closed_loop` (`tables/tab_closed_loop.tex`) | 13 traces × 6 variants × 30 seeds = 2,340, plus 48 runs for the decision time | `t1_fast.txt`, `t1_prophet.txt`, `t1timing.txt` | `cl_<trace>`, `tm_<trace>` |
| Sensitivity to the Bollinger parameters N and alpha | `tab:bollinger_sensitivity` (`tables/tab_bollinger_sensitivity.tex`) | 13 traces × 6 settings × seeds 0-9 = 780, besides the reference setting | `t3.txt` | `bs_<trace>` |
| Forecast accuracy under the protocol of the method | `tab:forecast_val_u` (`tables/tab_forecast_accuracy.tex`) | no simulation; 1,700 VM blocks | none | none (`forecast_accuracy/fa_raw_v2.csv`) |
| Additional traces of Alibaba and Materna | `tab:more_traces` (`tables/tab_more_traces.tex`) | 4 traces × 10 techniques × 30 seeds = 1,200 | `mt_fast.txt`, `mt_prophet.txt`, `mt_sota.txt`, `mt_neural.txt` | `mt_materna2`, `mt_materna3`, `mt_alibaba5`, `mt_alibaba8` |

The 13 traces of the first three experiments are the ten PlanetLab days and the Alibaba, Materna and
Azure subsets of `workloads/`. The fourth experiment uses four further subsets, described in
"Additional traces" below.

**Closed loop.** The consolidation loop is run with six host forecasters and everything else equal:
selection WPSP (`psp2`), overload rule `mad`, placement `ac`. The forecaster is the last value (LVP),
exponential smoothing with level 0.8 (EWMA, `simpleExpSmoothing`) or Prophet (`fbProphet`), each
without and with the Bollinger step (N = 5, alpha = 0.5). LVP is WPSP, Prophet is WP and Prophet+BB is
WBP, so the three techniques of the main tables are executed again here. The decision time of the
table comes from 48 separate runs (the six variants on PlanetLab day 20110303, Alibaba, Materna and
Azure, seeds 0 and 1) executed two at a time with nothing else running.

**Bollinger sensitivity.** WBP with one parameter changed at a time around the setting used in the
manuscript (N = 5, alpha = 0.5): N = 3, 10, 20 at alpha = 0.5 and alpha = 1.0, 1.5, 2.0 at N = 5. The
column of the reference setting is the Prophet+BB variant of the closed-loop campaign restricted to
seeds 0-9 (130 runs), executed in the same way.

**Forecast accuracy.** Error of Prophet, the last value and exponential smoothing on the per-VM CPU
series that the simulator reads (first 288 samples of the column it uses). Protocol A: one step ahead
at every step with a window of 30 samples (PlanetLab day 20110303, Alibaba, Materna, Azure; 400 VM
blocks). Protocol B, the one of the method: at each decision instant (every 6 steps), window of the
last min(t, 30) samples, mean of the 6-step forecast against the mean of the next 6 observations, on
the raw window and on its upper Bollinger band (N = 5, alpha = 0.5); 13 traces, 1,300 VM blocks. It
does not run the simulator.

## Files

| Path | Content |
|---|---|
| `lists/t1_fast.txt`, `lists/t1_prophet.txt` | closed loop: the 1,560 runs without Prophet and the 780 runs with Prophet (written by `tools/gen_t1.sh 0-29`) |
| `lists/t3.txt` | Bollinger sensitivity: 780 runs (written by `tools/gen_t3.sh 0-9`) |
| `lists/t1timing.txt` | decision time: 48 runs (written by `tools/gen_timing.sh`) |
| `lists/t1_smoke.txt` | smoke test: one run of each new variant on Materna (3 runs of the closed loop) |
| `lists/q_fast.txt`, `lists/q_fast_rest.txt`, `lists/q_fast_rest_rev.txt`, `lists/q_prophet.txt`, `lists/q_prophet2.txt` | the same runs in the order in which the campaign executed them (see "How the campaign was executed") |
| `tools/make_singles.py` | writes one single-configuration testbed per simulation from a testbed of `testbed/` |
| `tools/gen_t1.sh`, `tools/gen_t3.sh`, `tools/gen_timing.sh` | write the single testbeds and the lists of each experiment |
| `tools/start_campaign.sh` | host side: starts a detached container that executes a list |
| `tools/run_singles.sh` | container side: executes each run of a list in its own JVM, several at a time; resumable |
| `tools/start_fa.sh` | host side: starts the forecast-accuracy computation in a container |
| `tools/collect.sh`, `tools/build_tables.py` | per-run cache and tables of the closed loop and of the sensitivity |
| `forecast_accuracy/fa_revision.py` | forecast-accuracy computation (runs inside the container) |
| `forecast_accuracy/fa_raw_v2.csv` | its result: one row per trace, VM, protocol, input and forecaster (12,000 rows) |
| `forecast_accuracy/fa_tables.py` | forecast-accuracy tables from that CSV |
| `lists/mt_fast.txt`, `lists/mt_prophet.txt`, `lists/mt_sota.txt`, `lists/mt_neural.txt` | additional traces: MU, MMT, RS, MC and WPSP (600 runs); WP and WBP (240); AMOVMC and EUQ-VMC (240); BB+NeoPro (120) (written by `tools/mt_gen.py`) |
| `lists/mt_smoke.txt`, `lists/mt_smoke_neural.txt` | additional traces, smoke test: seed 0 of every technique and trace (36 runs, and 4 runs of BB+NeoPro) |
| `../../testbed/mt_<trace>_<family>.json` | additional traces: the 20 base testbeds, copies of the testbeds of the main tables with only `name`, `experimentOutputFolder` and `workloadTrace` changed (`tables/mt_config_diff.md`) |
| `tools/mt_common.py`, `tools/mt_gen.py` | additional traces: definitions (traces, techniques, templates) and the generator of the single testbeds and lists |
| `tools/mt_start_campaign.sh`, `tools/mt_preflight.sh`, `tools/mt_smoke.sh`, `tools/mt_run_all.sh` | additional traces: launch (image as a parameter; preflight line with the package versions), smoke test and the three stages one after the other |
| `tools/mt_collect.sh`, `tools/mt_extract.py`, `tools/mt_verify_runs.py`, `tools/mt_build_table.py` | additional traces: per-run cache, check of the folder and rows each run read, and the table |
| `tools/mt_check_traces.py`, `tools/mt_diff_configs.py` | additional traces: proof of how the four subsets were cut and selected (needs the full original traces, not shipped) and of what the configurations change |
| `caches/` | per-run records of the main tables and of the four experiments, and the timing log of the decision time (see "Per-run caches") |
| `tables/` | the resulting tables, Markdown and LaTeX; index in `tables/INDEX.md` |

Each name in a list is a single testbed, `<folder>__<variant>_s<seed>`; its result is
`output/<folder>/<name>_00000_data.json`.

## Execution environment

- Docker image of this repository (`Dockerfile`: Java 8, Python 3.8, Prophet). The campaign used an
  image built from it with OpenJDK 1.8.0_452, prophet 1.1.5, pandas 1.3.5 and numpy 1.21.6, and the
  `metacloud.jar` of this repository (sha1 `a448d97a884acd7ea0d4d4a0a278d99e9ba789df`).
- `OMP_NUM_THREADS`, `STAN_NUM_THREADS`, `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS` set to 1 in every
  container (the launch scripts pass them).
- One simulation per JVM. The campaign of the main tables executed all the runs of a testbed in one
  JVM; here every run has its own single-configuration testbed and its own `java -jar metacloud.jar
  folder <name>`.
- JVM heap capped at 640 MB (`-Xmx640m`, set by `run_singles.sh`) so that several JVMs fit in memory:
  about 0.65 GB per JVM with the cap and about 1.5 GB without it. The cap does not enter the
  simulation logic.

## How to launch

From the repository root, with Docker and, on the host, Python 3 and bash (Git Bash on Windows):

```bash
docker compose build                       # image `metacloudsim` (first time)
cd experiments/revision_r1

# 1. single testbeds (written to ../../testbed/, ignored by git) and lists
bash tools/gen_t1.sh 0-29                  # closed loop: 2,340 testbeds
bash tools/gen_t3.sh 0-9                   # Bollinger sensitivity: 780 testbeds
bash tools/gen_timing.sh                   # decision time: 48 testbeds

# 2. campaigns: bash tools/start_campaign.sh <campaign> <list> <simulations at a time>
bash tools/start_campaign.sh clfast    t1_fast.txt    5
bash tools/start_campaign.sh clprophet t1_prophet.txt 8
bash tools/start_campaign.sh bs        t3.txt         5
# when the three have finished, with nothing else running (the name t1timing is the one that
# tools/collect.sh expects):
bash tools/start_campaign.sh t1timing  t1timing.txt   2

# 3. forecast accuracy, one command after the other has finished (about one hour each with 5 processes)
FA_OUT=fa_raw_rerun.csv bash tools/start_fa.sh 5 B
FA_OUT=fa_raw_rerun.csv bash tools/start_fa.sh 5 A planetlab_20110303,alibaba,materna,azure
```

- Each campaign is a detached container named `mcs_<campaign>`. The repository is mounted read-only
  and its inputs are copied into the container; results are copied to `output/<folder>/` and logs to
  `runlogs/<campaign>/` as each run ends (`_campaign.log`: one line per run with status and wall
  time; `_timing.log`: the timing lines of the simulator; `<name>.log.gz`: its standard output).
- Progress: `tail runlogs/<campaign>/_campaign.log`. Stop: `docker rm -f mcs_<campaign>`. Resume:
  the same `start_campaign.sh` command; finished runs are skipped.
- Keep the total number of simulations running at the same time within the memory of the Docker
  host (about 0.65 GB each). On the machine of the campaign (28 logical CPUs in use) the throughput
  was about 14 runs per minute without Prophet and 5 with Prophet.
- `PKG=<repository root>` and `IMAGE=<image>` change the defaults of the launch scripts.
- `start_fa.sh` writes to `forecast_accuracy/fa_raw_v2.csv` by default. That file is shipped complete,
  so without `FA_OUT` the script finds nothing left to compute.

## Additional traces of Alibaba and Materna

The ten techniques of the manuscript (MU, MMT, RS, MC, WPSP, WP, WBP, BB+NeoPro, AMOVMC, EUQ-VMC) on
four subsets not used in the other experiments, with the configurations of the main tables and of the
comparison with recent methods; only the trace changes (`tables/mt_config_diff.md`).

| Trace | Folder in `workloads/` | Rows read | Mean CPU of the VMs |
|---|---|---|---|
| Materna trace 2, 4 December 2015 | `materna/materna_trace2_valid_0_288_100_mostDiff` | the 288 rows of each file | 7.45 % |
| Materna trace 3, 4 January 2016 | `materna/materna_trace3_valid_0_288_100_mostDiff` | the 288 rows of each file | 7.86 % |
| Alibaba day 5 | `alibaba2018/alibaba2018_fixed_first_500_100_mostDiff_day5_final` | first 288 rows (index 1150-1437 of the trace) | 40.30 % |
| Alibaba day 8 | `alibaba2018/alibaba2018_fixed_first_500_100_mostDiff_day8_final` | first 288 rows (index 2014-2301 of the trace) | 40.86 % |

Each subset holds the 100 series with the largest accumulated absolute change of CPU utilization over
the day, the rule that selected the Materna and Alibaba subsets of the main tables (9.89 % and
33.61 % mean CPU). The two Alibaba windows start two samples (10 minutes) before the calendar day,
as cut by the script that produced them. `tables/mt_trace_check.md` documents the rows and column the
simulator reads and the selection.

```bash
cd experiments/revision_r1
python -B tools/mt_gen.py                  # 1,200 single testbeds (../../testbed/, ignored by git) and the lists
docker build -f ../../Dockerfile.neural -t metacloudsim-neural ../..   # image for BB+NeoPro
bash tools/mt_smoke.sh                     # seed 0 of each technique and trace (40 runs) and its check
bash tools/mt_run_all.sh                   # the 1,200 runs in three stages, then tools/mt_collect.sh
```

- `IMAGE` and `IMAGE_NEURAL` change the images (defaults `metacloudsim` and `metacloudsim-neural`);
  `MT_PAR_FAST`, `MT_PAR_PROPHET`, `MT_PAR_SOTA` and `MT_PAR_NEURAL` the simulations at a time of
  each stage (5 + 13, 18 and 8). With NeuralProphet a simulation took about 0.63 GB, as the others.
- `tools/mt_collect.sh` writes the per-run cache (`cache_mt/`), `tables/mt_verify_runs.md` (the
  folder and rows that each run read, from its log) and the table (`tables/more_traces.md`,
  `tab_more_traces.tex`, `more_traces.json`). Tests: Wilcoxon signed-rank on the 30 seed pairs, WBP
  against MU, MMT, RS and MC, Holm over the 80 tests of the table (`--competitors all` tests WBP
  against every other column).

## How to rebuild the tables

With the raw outputs in `output/` and the logs in `runlogs/` (host Python 3 with `numpy` and `scipy`):

```bash
bash tools/collect.sh
```

It runs `../../analysis_revision/extract_runs.py` (per-run cache in `cache/`), then
`tools/build_tables.py` and `forecast_accuracy/fa_tables.py`, and writes the files of `tables/`.
Metric definitions are those of `analysis_revision/revlib.py` (migration traffic counted once per
migration, migration energy with 0.512 J per MB and hop and 20.165 J per migration).

| Table | Needs |
|---|---|
| `closed_loop.md`, `tab_closed_loop.tex` | `output/cl_*`, `output/tm_*` and `runlogs/t1timing/_timing.log` (decision time) |
| `bollinger_sensitivity.md`, `tab_bollinger_sensitivity.tex` | `output/bs_*` and `output/cl_*` (reference setting) |
| `rerun_vs_stored.md` | `output/cl_*` and the per-run cache of the campaign of the main tables, `analysis_revision/cache/runs.jsonl` (see `analysis_revision/README.md`) |
| `inventory.md` | `output/` |
| `forecast_accuracy.md`, `tab_forecast_accuracy.tex` | `forecast_accuracy/fa_raw_v2.csv` (shipped) |

The forecast-accuracy tables can be rebuilt from what is shipped:

```bash
python -B forecast_accuracy/fa_tables.py                                  # shipped CSV
python -B forecast_accuracy/fa_tables.py --raw forecast_accuracy/fa_raw_rerun.csv   # a new computation
```

## Per-run caches

`caches/` holds the per-run records from which the tables are computed: one JSON line per simulation
with its configuration and the metrics read from its output (written by
`../../analysis_revision/extract_runs.py`), compressed with gzip.

| File | Runs | Tables |
|---|---|---|
| `main_runs.jsonl.gz` | the 3,900 simulations of the main tables and of the comparison with recent methods | per-workload tables, energy components, sensitivity to the coefficient, comparison with recent methods (`analysis_revision/build_revision.py`) |
| `revision_runs.jsonl.gz` | the 3,168 simulations of the closed loop, the Bollinger sensitivity and the decision time (`cl_`, `bs_`, `tm_`) | `closed_loop.md`, `bollinger_sensitivity.md`, `rerun_vs_stored.md`, `inventory.md` |
| `t1timing_timing.log` | the timing lines of the 48 decision-time runs | decision time of `tab_closed_loop.tex` |
| `more_traces_runs.jsonl.gz` | the 1,200 simulations of the additional traces | `more_traces.md`, `tab_more_traces.tex` |

To rebuild every table from them (host Python 3 with `numpy` and `scipy`; from the repository root):

```bash
mkdir -p analysis_revision/cache experiments/revision_r1/cache experiments/revision_r1/cache_mt \
         experiments/revision_r1/runlogs/t1timing
gunzip -c experiments/revision_r1/caches/main_runs.jsonl.gz > analysis_revision/cache/runs.jsonl
gunzip -c experiments/revision_r1/caches/revision_runs.jsonl.gz > experiments/revision_r1/cache/runs.jsonl
gunzip -c experiments/revision_r1/caches/more_traces_runs.jsonl.gz > experiments/revision_r1/cache_mt/runs.jsonl
cp experiments/revision_r1/caches/t1timing_timing.log experiments/revision_r1/runlogs/t1timing/_timing.log
python -B analysis_revision/build_revision.py --cache analysis_revision/cache --out analysis_revision/out
cd experiments/revision_r1
python -B tools/build_tables.py
python -B tools/mt_build_table.py --cache cache_mt
```

Run in this way, `build_revision.py` reproduces the ten tables of the main results of the manuscript,
and `build_tables.py` and `mt_build_table.py` the files of `tables/` byte for byte (checked on
17 November 2026).

## What is not shipped

- The raw outputs of the 4,368 simulations of these experiments (`output/`) and their campaign logs
  (`runlogs/`), except the timing log of the decision time (in `caches/`). The tables can be rebuilt
  from the per-run caches; the check of the folder and rows that each run of the additional traces
  read (`tables/mt_verify_runs.md`) needs the logs.
- The single testbeds: the generators write them again, identical to those of the campaigns.

A new execution does not reproduce the individual runs. Ties between equivalent candidates are
resolved by the iteration order of hash-based collections, so individual runs are not
reproducible bit for bit; results are distributions over seeds and traces, and a new execution has
to be compared on means and confidence intervals. `tables/rerun_vs_stored.md` is that comparison for
WPSP, WP and WBP:
the 1,170 runs of these three techniques in this campaign against the same traces and seeds of the
campaign behind the main tables. The means of the two campaigns agree: one of the 60 paired comparisons
has p < 0.05 before correction for multiple tests.

## How the campaign was executed

The runs were executed on 14 and 15 November 2026 with these tools; no run failed. The lists
`q_*.txt` record the order of execution, which does not affect the results because every run has its
own JVM.

- `q_fast.txt` holds the runs of `t1_fast.txt` with seeds 0-9 first; `q_fast_rest.txt` and
  `q_fast_rest_rev.txt` hold its seeds 10-29 in forward and reverse order, for two containers that
  worked from both ends.
- `q_prophet.txt` holds the runs of `t1_prophet.txt` and `t3.txt`: closed loop with seeds 0-9, then
  the sensitivity, then closed loop with seeds 10-29. `q_prophet2.txt` holds the runs of `t3.txt` in
  another order, for a second container.
- A first launch with `t1_fast.txt` and `t1_prophet.txt` was stopped to reorder the queue; the runs it
  had finished were kept.
- Three of the containers used a second copy of `run_singles.sh` that also copied one more output
  file of each run to the host and wrote the checksum of the jar in the log. The jar and the
  simulation command were the same; only the first copy is shipped.

The additional traces were executed on 17 November 2026 with the `mt_` tools, one simulation per JVM:
the 1,080 runs of the image `metacloudsim` and then the 120 runs of BB+NeoPro in the image with
NeuralProphet; all 1,200 runs passed the check of `tables/mt_verify_runs.md`. The first launch of
BB+NeoPro failed before simulating (the NeuralProphet image had been built before the `LD_PRELOAD`
line of the `Dockerfile`, and the bridge to Python could not load); `mt_start_campaign.sh` now passes
that variable, and the runs were executed again from the start.

## State of the scripts in this folder layout

The scripts are those of the campaign with the paths of the machine where it ran replaced by paths
relative to the repository (`PKG`, `IMAGE`, `FA_OUT`); `gen_timing.sh` was added for the package.

- Executed in this layout: `gen_t1.sh`, `gen_t3.sh` and `gen_timing.sh` write lists and single testbeds
  identical to those of the campaign (3,168 files), and `mt_gen.py` those of the additional traces
  (1,200 files and the six lists); `build_revision.py`, `build_tables.py`, `mt_build_table.py` and
  `fa_tables.py`, run on the per-run caches of `caches/`, reproduce the tables byte for byte.
- Not yet executed in this layout: `start_campaign.sh`, `mt_start_campaign.sh`, `run_singles.sh`,
  `start_fa.sh`, `collect.sh` and `mt_collect.sh` (they need Docker or the raw outputs).
  `mt_check_traces.py` needs the full original traces, which are not shipped.
