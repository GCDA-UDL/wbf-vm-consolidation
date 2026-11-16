# Workload subsets shipped with the package

This folder holds the trace subsets that the experiments read. Sources and licenses are in
[DATA_LICENSES.md](DATA_LICENSES.md).

| Workload | Folder | Series | Column read by the simulator |
|---|---|---|---|
| PlanetLab | `planetlab/planetlab_<day>_100_mostDiff` (ten days, 20110303 … 20110420) | 100 per day | the single value of each line (CPU utilization, %) |
| Alibaba 2018 | `alibaba2018/alibaba2018_fixed_first_500_100_mostDiff` | 100 | `cpu_util_percent` |
| Materna | `materna/materna_trace1_valid_0_288_100_mostDiff` | 100 | `CPU usage [%]` |
| Microsoft Azure 2019 | `azure/azure_azure2019_traces_100_mostDiff` | 100 | `avg` (the files also hold `min` and `max`) |

Notes:

- The simulator uses the first 288 samples of each series (24 hours at 5-minute sampling), even
  when a file holds more.
- The folder names end in `mostDiff` (most different). For Azure, the 100 series are the candidates
  with the largest accumulated variation of the `max` column, whereas the simulations read the
  `avg` column.
- The statistics of the simulated series (median CPU utilization and accumulated absolute
  difference per workload) are computed by `analysis_revision/figures/workload_stats.py`.
