# Workload statistics: published Table 2 against the simulated series

Statistic: per VM, median of the CPU utilization (%) and accumulated absolute difference between consecutive samples; cells give the median over the VMs ± the sample standard deviation over the VMs.

The simulator reads the first 288 samples of each file (`numData` = 289 in `UtilizationModelFactory.java`; the reader fills `numData − 1` elements and copies the last one).

## 1. Which column and window reproduce each published cell

| workload | candidate | samples | % CPU median | accumulated diff | sum of relative errors |
|---|---|---|---|---|---|
| PlanetLab | cpu, day 20110322 | 288 | 24.2 ± 17.1 | 4085 ± 1361 | 0.0782 |
| PlanetLab | cpu, day 20110322 | 289 | 24.2 ± 17.1 | 4085 ± 1361 | 0.0782 |
| PlanetLab | cpu, day 20110325 | 288 | 25.5 ± 17.7 | 4048 ± 1058 | 0.3002 |
| PlanetLab | cpu, day 20110325 | 289 | 25.5 ± 17.7 | 4048 ± 1058 | 0.3002 |
| PlanetLab | **published** | | 24.0 ± 17.2 | 3996 ± 1312 | |
| Alibaba | cpu_util_percent | 289 | 32.2 ± 5.3 | 1347 ± 132 | 0.0035 |
| Alibaba | cpu_util_percent | 288 | 32.3 ± 5.3 | 1343 ± 132 | 0.0081 |
| Alibaba | cpu_util_percent | 577 | 33.9 ± 5.0 | 2470 ± 203 | 1.4890 |
| Alibaba | net_out | 577 | 31.5 ± 3.8 | 30 ± 15 | 2.1607 |
| Alibaba | **published** | | 32.2 ± 5.3 | 1346 ± 132 | |
| Materna | CPU usage [%] | 288 | 5.3 ± 6.4 | 518 ± 631 | 0.0133 |
| Materna | CPU usage [%] | 289 | 5.3 ± 6.4 | 518 ± 631 | 0.0133 |
| Materna | Memory usage [%] | 288 | 14.0 ± 11.0 | 917 ± 771 | 3.3591 |
| Materna | Memory usage [%] | 289 | 14.0 ± 11.0 | 917 ± 771 | 3.3591 |
| Materna | **published** | | 5.3 ± 6.4 | 517 ± 630 | |
| Microsoft Azure | max | 289 | 16.9 ± 15.6 | 3148 ± 2342 | 0.0032 |
| Microsoft Azure | max | 288 | 17.0 ± 15.5 | 3132 ± 2338 | 0.0142 |
| Microsoft Azure | max | 387 | 17.4 ± 15.2 | 4081 ± 3138 | 0.6945 |
| Microsoft Azure | avg | 387 | 7.7 ± 9.1 | 774 ± 730 | 2.4074 |
| Microsoft Azure | avg | 288 | 7.7 ± 9.3 | 618 ± 575 | 2.5047 |
| Microsoft Azure | **published** | | 16.9 ± 15.6 | 3148 ± 2342 | |

## 2. Published and revised values

| workload | column read by the simulator | series | published | revised (simulated series) | published cell reproduced by |
|---|---|---|---|---|---|
| PlanetLab | `cpu` (org/cloudbus/cloudsim/UtilizationModelPlanetLabInMemory.java (one integer per line)) | 1000 × 288 samples | 24.0 ± 17.2; 3996 ± 1312 | 24.0 ± 20.1; 4702 ± 1271 | cpu, day 20110322, first 288 samples (sum of relative errors 0.0782) |
| Alibaba | `cpu_util_percent` (svila/workloads/UtilizationModelAlibaba2018InMemory.java, line.split(",")[2]) | 100 × 288 samples | 32.2 ± 5.3; 1346 ± 132 | 32.3 ± 5.3; 1343 ± 132 | cpu_util_percent, first 289 samples (sum of relative errors 0.0035) |
| Materna | `CPU usage [%]` (svila/workloads/UtilizationModelMaternaInMemory.java, line.split(";")[4]) | 100 × 288 samples | 5.3 ± 6.4; 517 ± 630 | 5.3 ± 6.4; 518 ± 631 | CPU usage [%], first 288 samples (sum of relative errors 0.0133) |
| Microsoft Azure | `avg` (svila/workloads/UtilizationModelAzureInMemory.java, line.split(",")[3]) | 100 × 288 samples | 16.9 ± 15.6; 3148 ± 2342 | 7.7 ± 9.3; 618 ± 575 | max, first 289 samples (sum of relative errors 0.0032) |

With the duplicated last element that the simulator appends, the medians are: PlanetLab 24.0 ± 20.1; Alibaba 32.2 ± 5.3; Materna 5.2 ± 6.4; Microsoft Azure 7.7 ± 9.3 (the accumulated difference does not change).

### PlanetLab, day by day (simulated window)

| day | % CPU median | accumulated diff |
|---|---|---|
| 20110303 | 30.8 ± 20.9 | 4869 ± 1386 |
| 20110306 | 22.0 ± 20.1 | 4346 ± 1476 |
| 20110309 | 20.5 ± 18.1 | 4511 ± 1213 |
| 20110322 | 24.2 ± 17.1 | 4085 ± 1361 |
| 20110325 | 25.5 ± 17.7 | 4048 ± 1058 |
| 20110403 | 27.5 ± 21.8 | 4977 ± 947 |
| 20110409 | 22.2 ± 22.9 | 4877 ± 1242 |
| 20110411 | 26.0 ± 22.2 | 4959 ± 1229 |
| 20110412 | 27.0 ± 19.7 | 4458 ± 1132 |
| 20110420 | 14.0 ± 17.1 | 5252 ± 1097 |

## 3. Figure `fig_workload_variability.pdf`

Boxplot over the VMs (PlanetLab: 1000 VM-days; others: 100 VMs) of the accumulated absolute difference of the simulated CPU series. Box: quartiles; line: median; diamond: mean; whiskers: 1.5 × IQR; dots: VMs beyond the whiskers.

| workload | min | Q1 | median | Q3 | max | mean |
|---|---|---|---|---|---|---|
| PlanetLab | 3221 | 4184 | 4702 | 5435 | 14974 | 5026 |
| Alibaba | 1251 | 1290 | 1343 | 1431 | 1824 | 1383 |
| Materna | 208 | 326 | 518 | 986 | 3366 | 747 |
| Microsoft Azure | 39 | 381 | 618 | 1070 | 3704 | 779 |

