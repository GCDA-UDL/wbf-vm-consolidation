# Workload data — sources, licenses and attribution

This folder ships **small processed 100-VM subsets** (`*_100_mostDiff`, the most-different VMs used
by the paper) of four public cloud workloads, included **only to enable reproduction** of the
experiments. Each remains under its **original license**; please consult and cite the original
sources below. If you need the full traces, download them from the official repositories.

| Workload | Subset included | Original source | License / terms |
|----------|-----------------|-----------------|-----------------|
| **PlanetLab** | `planetlab/planetlab_20110303_100_mostDiff` | PlanetLab CoMon CPU traces, as distributed with **CloudSim** (Beloglazov & Buyya) | Academic use; bundled with CloudSim examples |
| **Alibaba 2018** | `alibaba2018/alibaba2018_fixed_first_500_100_mostDiff` | **Alibaba Cluster Trace v2018** — https://github.com/alibaba/clusterdata | Per Alibaba terms (academic use + citation) |
| **Materna** | `materna/materna_trace1_valid_0_288_100_mostDiff` | **Materna / GWA-T-13** (Grid Workloads Archive) — http://gwa.ewi.tudelft.nl | Per GWA terms (academic use + citation) |
| **Azure 2019** | `azure/azure_azure2019_traces_100_mostDiff` | **Microsoft Azure Public Dataset v2** — https://github.com/Azure/AzurePublicDataset | Per Microsoft Azure dataset license |

## Notes
- These are **derived subsets** (100 VMs each, ~8 MB total), not the full datasets.
- PlanetLab Table 6 in the paper averages **10 daily traces** (20110303 … 20110420); only the
  `20110303` trace is shipped here. Add the remaining PlanetLab traces from CloudSim for the exact
  PlanetLab averages.
- If any rights holder objects to the redistribution of a subset, open an issue and it will be
  replaced by a download script.

## How to cite
Please cite the original dataset papers/repositories (above) **and** the paper this package
reproduces (see the top-level `README.md`).
