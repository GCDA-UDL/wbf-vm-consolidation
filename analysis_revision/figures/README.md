# Figures of the revised manuscript

Every figure is a vector PDF written to `analysis_revision/out/figures/`, with a 200 dpi PNG preview in
`analysis_revision/figures/preview/` (both folders are ignored by git). Scripts are read-only on their
inputs.

## Regenerate everything

```bash
cd analysis_revision/figures
python -B make_all.py
```

- Defaults: repository root `../..` (only `workloads/` and `topologies/` are read), per-run cache
  `../cache`, cross-check file `../out/facts.json`, figures to `../out/figures`, workload table to
  `../out/tables`, previews to `preview/`. Each default has an option (`--package`, `--cache`, `--facts`,
  `--out`, `--table-out`, `--preview`).
- `fig_results.py` needs the per-run cache (`../cache/runs.jsonl`, written by `../extract_runs.py` from
  the raw outputs, which are not stored in git). `workload_stats.py`, `fig_topology.py` and
  `fig_wbp_cycle.py` need only files of this repository.
- `fig_results.py` stops with an assertion if its numbers differ from `facts.json` (176 values
  compared; largest difference 4e-14). Run `build_revision.py` first if the cache changes.
- `--orig-workloads <folder>` (optional): workloads folder of the original project, which is not part of
  this repository. It only adds a fourth section to `WORKLOAD_STATS.md` (PlanetLab subset behind the
  cell of the submitted version, column used to select the Azure VMs).

## Style

- Printed sizes: single column 88 mm, double column 180 mm. All text is 8 pt Arial at that size, so
  include the figures at their natural width (`width=\columnwidth` or `width=\textwidth`). At
  `0.9\columnwidth` the text is 7.2 pt.
- Fonts embedded as TrueType (Type 42).
- Colours: classical techniques (MU, MMT, RS, MC) in neutral grey; the proposed family in one blue hue,
  light to dark in the order WPSP, WP, WBP. Energy terms and compared methods use distinct hues, and
  each also carries a hatch or a marker shape, so the figures read in greyscale.
- Technique order everywhere: MU, MMT, RS, MC, WPSP, WP, WBP.

## Figures

| File | Size (mm) | Script | Data |
|---|---|---|---|
| `fig_<wl>_migrations.pdf`, `fig_<wl>_sla.pdf` (wl = planetlab, alibaba, materna, azure) | 88 × 56 | `fig_results.py` | `cache/runs.jsonl`, runs of the result tables (`revlib.collect_table_runs`) |
| `fig_energy_components.pdf` | 180 × 92 | `fig_results.py` | same runs, `revlib.metrics_rev` |
| `fig_energy_components_stacked.pdf` (alternative, not needed if the previous one is used) | 180 × 62 | `fig_results.py` | same |
| `fig_kappa_sensitivity.pdf` | 180 × 56 | `fig_results.py` | same |
| `fig_sota_tradeoff.pdf` | 88 × 100 | `fig_results.py` | same, plus folders `amovmc_native_*`, `euqvmc_native_*` |
| `fig_workload_variability.pdf` | 88 × 58 | `workload_stats.py` | trace files of the package |
| `fig_topology.pdf` | 88 × 54 | `fig_topology.py` | `topologies/fatTreeTopology_k-2_g-2_s-2_hs-2_h-16.json` |
| `fig_wbp_cycle.pdf` | 88 × 110 | `fig_wbp_cycle.py` | none (diagram of the implemented decision cycle) |

### What the marks mean

- **Boxplots (migrations, SLA, workload variability).** Box: first to third quartile; line: median;
  white diamond: mean (the value given in the tables); whiskers: most extreme run within 1.5 × IQR of
  the box; dots: runs beyond the whiskers. Result boxplots: over the runs of each technique, 300 for
  PlanetLab (10 daily traces × 30 seeds) and 30 for the other workloads. The PlanetLab box therefore
  mixes trace-to-trace and seed-to-seed variation; the confidence intervals of the tables are computed
  over the 10 trace means. Workload variability: over the VMs (1000 VM-days for PlanetLab, 100 VMs for
  the others).
- **`fig_energy_components.pdf`.** Top row: mean execution energy of each technique (dots; no error
  bars). Bottom row: mean switch-on/off energy (hatched) and mean migration energy stacked from zero,
  migration energy with κ = 0.512 J per MB and hop and each migration counted once. Every panel spans
  2 kWh, so 1 kWh has the same height in both rows; only the origin of the top row changes from
  workload to workload (18.0, 20.5, 17.0, 18.0 kWh). Values equal the means of
  `tab_energy_components.tex`.
- **`fig_energy_components_stacked.pdf`.** The three terms stacked from zero. Kept as an alternative:
  the differences between techniques are 1 to 3 % of the bar and are hard to see in it.
- **`fig_kappa_sensitivity.pdf`.** Saving in mean total energy of WBP (solid) and WP (dashed) with
  respect to the classical technique that consumes least at each κ, in %; negative means that the
  proposal consumes more. Mean total energy is exact for every κ because it is affine in κ:
  host energy + (κ × traffic + 20.165 J × migrations) / 3.6e6. Dotted vertical lines: a = 0.512
  (reference: coefficient of the model of Liu et al.), b = 3.549 (value measured by Sarji et al., which
  is the constant built into the simulator), c = 4.096 (value used in the submitted version). The
  reference technique changes along the curve, which gives the bend near the origin: MU up to
  κ ≈ 0.12 (PlanetLab), 0.18 (Alibaba), 0.10 (Materna), 0.20 (Azure), then MMT (in Azure MC between
  0.20 and 0.32). The WBP curve at the tabulated κ values equals the lower end of the ranges of
  `tab_kappa_sensitivity.tex`, and it crosses zero at the "break-even, all" value of that table.
- **`fig_sota_tradeoff.pdf`.** One panel per workload, common axes. Point: mean total energy
  (κ = 0.512) and mean SLA violation; bars: 95 % confidence intervals (PlanetLab over the 10 trace
  means, others over the 30 seeds). Filled markers: shared placement stage (the configuration of the
  comparison table); hollow markers: native placement stage of AMOVMC and EUQ-VMC. Lower left is better.
- **`fig_topology.pdf`.** Drawn from the topology file; see `TOPOLOGY.md` for the counts. Thick lines:
  switch-to-switch links (weight 1000 in the file); thin lines: host-to-edge links (weight 100). Hosts
  are not labelled small or large: the host type is drawn per seed.
- **`fig_wbp_cycle.pdf`.** One consolidation decision as implemented; the source file of each step is
  listed in the docstring of `fig_wbp_cycle.py`. Not shown in the diagram: the VM demand used in steps
  5 and 6 is the last observed value; step 6 can use switched-off hosts as targets, step 7 cannot; WP
  skips step 2; WPSP skips step 2 and uses the last host value in step 3.

## Notes written by the scripts

Both notes are rewritten by `make_all.py` and are kept in git as generated from the files of this
repository.

- `WORKLOAD_STATS.md`: values of the workload table in the submitted version and in the revised
  manuscript, and the column and window that reproduce each cell of the submitted version.
- `TOPOLOGY.md`: switches per layer, links and host-to-host path lengths.
