# Changelog

Changes of the reproduction package from one version to the next. Versions are the git tags of the
repository. For the versions up to v0.2.3 see the tags and the section "What's new in v0.2.0" of
`README.md`.

## v0.3.0 (2026-11-17)

Changes with respect to v0.2.3. This version follows the manuscript as revised after peer review.

- **Energy accounting and tables.** Migration traffic is counted once per migration (the simulator
  registers every migration twice in its network accounting). Host energy, migration energy and
  total energy are reported separately. Migration energy uses 0.512 J per MB and hop and 20.165 J
  per migration (model of Liu et al., HPDC 2011, Eq. 17), without the 1.1 factor of the submitted
  version. `results/reference/` is regenerated with the tables of the revised manuscript,
  `facts.json` and `stats.md` (360 paired tests, Holm-corrected; PlanetLab tested on the ten daily
  means), including the sensitivity of the energy comparison to the coefficient (0 to 4.096 J per
  MB and hop).
- **Analysis scripts of the revision.** New folder `analysis_revision/`: the scripts that produce
  every table and figure of the revised manuscript from the raw outputs, and the generator of
  `results/reference/README.md`. The scripts and notes under `SOTA/`, `scripts/analyze_results.py`
  and `experiments/neuralprophet/` are marked as the analysis of the submitted version; four
  scripts of that analysis that were missing are added.
- **Experiments of the revision.** New folder `experiments/revision_r1/`: run lists, tools and
  resulting tables of the closed-loop replacement of the forecaster (2,340 runs), the sensitivity
  to the Bollinger parameters N and alpha (780 runs besides the reference setting), the forecast
  accuracy under the protocol of the method, and the ten techniques on two further traces of Alibaba
  (days 5 and 8) and two of Materna (traces 2 and 3), 1,200 runs (`mt_` tools, table
  `tab_more_traces.tex`). The four new workload subsets are in `workloads/` and their 20 base
  testbeds in `testbed/mt_*.json`.
- **Per-run caches.** `experiments/revision_r1/caches/` holds, compressed, the per-run records of the
  3,900 simulations of the main tables and of the 4,368 simulations of the revision experiments, and
  the timing log of the decision time; every table of the revised manuscript can be rebuilt from them
  (`experiments/revision_r1/README.md`, "Per-run caches"). The raw outputs are not shipped.
- **Documentation of the compared methods.** gamma = 0.80 (AMOVMC) and safe = 1.5 (EUQ-VMC) are
  settings chosen by the authors of this package; the original articles do not report them. The
  re-implementation of AMOVMC is documented as partial: its neural predictor is not implemented,
  the inverted overload test differs from Eq. (11) of its article for some host sizes, under-utilised
  hosts are handled by the simulator, and its native placement uses equal weights for the six terms
  of its fitness function (not those of Table 3 of its article), computes the cycle term as a
  variance and includes switched-off hosts among the candidates. The code comments of the AMOVMC
  classes that called the re-implementation faithful or the inverted test equivalent are corrected.
  BB+NeoPro is the WBP loop with the NeuralProphet forecaster,
  not the 2023 method as published. The description of the Bollinger step and of the workload
  subsets follows the code.
- **Documentation of reproducibility.** Individual runs are not reproducible bit for bit: ties
  between equivalent candidates are resolved by the iteration order of hash-based collections, and
  the results are distributions over seeds and traces. The earlier statement that the results were
  bit-reproducible is withdrawn. The runs of WPSP, WP and WBP were executed again (1,170 runs) and
  the means of the two campaigns agree (one of 60 paired comparisons with p < 0.05 before
  correction).
- **Environment.** `Dockerfile` and `Dockerfile.neural` set `OMP_NUM_THREADS`, `STAN_NUM_THREADS`,
  `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS` to 1. Paths of the developers' machines are replaced
  by repository-relative paths or environment variables (`WBF_OUTPUT`, `WBF_FIGURES`,
  `WBF_WORKLOADS`) in the analysis scripts of `SOTA/`, in one notebook and in four files of
  `pymodule/`, where the path is a variable used only by helper functions that the simulator does
  not call. The simulator (`metacloud.jar`), the experiment configurations and the workload subsets
  are unchanged; the Java sources under `SOTA/src/` change in comments only.
- **Metadata.** `CITATION.cff`: affiliation `SEMBAC, Universitat de Lleida` for every author and
  preferred citation marked as under review. This changelog is added.
