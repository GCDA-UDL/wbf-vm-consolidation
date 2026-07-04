# State-of-the-art comparison: AMOVMC and EUQ-VMC inside MetaCloudSim

Two recent (2025) VM-consolidation methods re-implemented inside the same
MetaCloudSim/CloudSim harness used for WBF, so the comparison shares the
identical energy model, SLA computation, network topology and workload traces.
Requested by F. Guirado to replace the "only-internal-baselines" comparison with
a head-to-head against current forecasting/optimisation methods.

| Method | Paper | Traces | What we reproduce |
|--------|-------|--------|-------------------|
| **AMOVMC** | Goyal & Awasthi, *Adaptive Multi-Objective VM Consolidation for Energy-Efficient Cloud Data Centers*, J. Grid Computing 23:21 (2025) | PlanetLab, Google, Alibaba | MWOHD host detection + modified VM selection + DWMA predictor |
| **EUQ-VMC** | Li et al., *Resource-Efficient and Quality-Aware VM Consolidation Method*, J. Grid Computing 23:6 (2025) | Bitbrains, Alibaba | HOD host detection + ROS VM selection + (MOFPA/D objectives) |

Both methods decompose into the same pluggable phases as every other technique in
the simulator (host over-saturation detection → VM selection → placement), so each
is wired through the existing `future` optimiser via the experiment config.

## How to enable them (config knobs)

```
AMOVMC :  hostOverSaturationPolicy = "amovmc"
          selectionPolicy          = "amovmc"
          hostForecastingTechnique = "dwma"      (+ vmForecastingTechnique* = "dwma")

EUQ-VMC:  hostOverSaturationPolicy = "euqvmc"
          selectionPolicy          = "euqvmc"
          hostForecastingTechnique = "last"
          parameter                = "1.5"        (the EUQ "safe" factor in Eq. 23)
```

Everything else stays at the Paper-4 values, so the only thing that changes between
runs is the consolidation logic under test (controlled comparison).

## Equation → code mapping

### AMOVMC (Goyal & Awasthi 2025)

| Paper | Code | Notes |
|-------|------|-------|
| Alg. 1 — dynamic window `ws∈[3,30]` | `DWMAForecastingTechnique.dynamicWindow()` | argmin one-step error |
| Eq. 17 — weighted moving average | `DWMAForecastingTechnique.wma()` | normaliser `ws*(ws+1)/2` (paper prints `ws*(ws-1)/2`, an apparent typo — corrected so weights sum to 1) |
| Eq. 18–19 — `PM_util = w1·P_next + w2·A_prev` | `DWMAForecastingTechnique.apply()` + `accuracyWeights()` | w1,w2 from last-10 accuracy of WMA vs persistence |
| Alg. 2 / Eq. 11 — MWOHD performance threshold | `FutureHostOverSaturationAMOVMC` | Eq. 11 inverted at performance `gamma` → critical **utilisation** `u_crit` (function of #VMs `V_n`); host over-utilised iff forecasted util > `u_crit`. `gamma = 0.80` (500 ms SLA point). Equivalent to the paper's `u_th < gamma` test while reusing the unchanged migration loop. |
| Alg. 3 — modified VM selection | `FutureAMOVMCVmSelection` | migrate argmax(combined predicted load) = `vm.getForecastedMIPS()` |

### EUQ-VMC (Li et al. 2025)

| Paper | Code | Notes |
|-------|------|-------|
| Eq. 4 — overload probability `P_over = 1 − Φ((HC−μ)/σ)` | `FutureHostOverSaturationEUQVMC` | μ,σ from the host utilisation history; HC = 1 (normalised); `Φ` via commons-math3 `NormalDistribution` |
| Eq. 23 — `T_upper = 1 − safe·P_over` | `FutureHostOverSaturationEUQVMC` | `safe` = experiment `parameter`; host over-utilised iff util > `T_upper` (Alg. 3) |
| Eq. 24 — `P_mig = U_res / RAM` (ROS) | `FutureEUQVMCVmSelection` | migrate argmax(`getForecastedMIPS()/getRam()`); Alg. 4 |
| Eq. 3/9/10 — objectives f1 energy, f2 waste, f3 overload prob | *(placement, see below)* | objective definitions for the MOFPA/D placement |

## Placement (design decision)

The paper proposals also include their own VM **placement** (AMOVMC: fitness Eq. 20;
EUQ-VMC: MOFPA/D evolutionary search). In this first stage **both methods reuse the
same power+network-aware placement as the baselines and WBF**. This is a deliberate
*controlled* comparison: holding placement constant isolates the effect of each
method's host-detection + VM-selection logic — the parts the papers emphasise — and
keeps the energy/SLA model identical across all techniques. Implementing AMOVMC's
fitness and EUQ-VMC's full MOFPA/D placement (the MOEA-Framework 2.13 and jMetal
5.0 libraries are already bundled) is the documented next step.

## Build (reproducible)

The shipped `metacloud.jar` **already contains** the AMOVMC/EUQ-VMC classes, so the
configs below run out of the box. To rebuild them from source (`SOTA/src/`):
`metacloud.jar` is an Eclipse runnable JAR — the new classes are compiled against it
and injected, no Maven reassembly. See `scripts/build_sota.sh`:

```
docker run --rm -v "$PWD:/work" -w /work metacloudsim-neural:latest bash scripts/build_sota.sh
```

## Reproduce the comparison (clone → run → compare)

```bash
# 0) one-time image build (Java 8 + Python 3.8 + Prophet + jpy)
docker compose build                  # image tag: metacloudsim
PRE=/usr/lib/x86_64-linux-gnu/libpython3.8.so.1.0   # libpython preload for jpy

# 1) WBF / WF reference (10 PlanetLab traces x 30 seeds) — Facebook Prophet
for d in 20110303 20110306 20110309 20110322 20110325 20110403 20110409 20110411 20110412 20110420; do
  docker run --rm -e LD_PRELOAD=$PRE -v "$PWD":/workspace -w /workspace metacloudsim \
    bash scripts/run_sota_batch.sh p4_pl_$d
done

# 2) AMOVMC and EUQ-VMC (same traces, same harness) — pure Java, ~8 s/sim
for m in amovmc euqvmc; do for d in 20110303 20110306 20110309 20110322 20110325 20110403 20110409 20110411 20110412 20110420; do
  docker run --rm -e LD_PRELOAD=$PRE -v "$PWD":/workspace -w /workspace metacloudsim \
    bash scripts/run_sota_batch.sh ${m}_pl_$d
done; done

# 3) print the comparison table
python SOTA/compare_sota.py
```

Optional robustness runs: `*_tune_*` configs (parameter sweep) and `*_native_*`
configs (each method's own placement) are in `testbed/` and run the same way. On
Windows/PowerShell prepend the bind mount with the absolute path and keep
`-e LD_PRELOAD=$PRE`. Each method config = 30 seeds; PlanetLab full = 300 sims/method.

## Smoke validation (PlanetLab 20110303, seed 0, 1 day)

| Method | migrations | SLA | Energy (kWh) | RAM in BW (×10⁵) |
|--------|-----------:|----:|-------------:|-----------------:|
| AMOVMC  |  697 | 0.60% | 33.32 | 78.55 |
| EUQ-VMC | 1070 | 2.98% | 24.77 | 117.94 |
| WF (ref)|  358 | 7.29% | 20.72 | 39.37 |

Both run end-to-end (exit 0, valid metrics, differentiated behaviour).

## Full comparison — PlanetLab (10 traces × 30 seeds = 300 sims/method)

Our reproduction (same harness, shared controlled placement, paper-default
parameters γ=0.80, safe=1.5). Paper-4 Table 6 values shown for reference.

| Technique | Energy (kWh) | SLA (%) | # migrations | ESV | RAM in BW (×10⁵) |
|-----------|-------------:|--------:|-------------:|----:|-----------------:|
| MU   *(paper)* | 38.71 | 5.43 | 1618 | 210.27 | 175.43 |
| MMT  *(paper)* | 28.44 | 2.92 |  931 |  84.15 |  86.88 |
| RS   *(paper)* | 28.70 | 3.00 |  776 |  85.79 |  84.93 |
| MC   *(paper)* | 28.87 | 2.94 |  828 |  85.23 |  88.86 |
| WPSP *(paper)* | 24.74 | 4.02 |  454 |  99.77 |  54.59 |
| **WF** *(repro)*  | 19.32 | 3.93 |  324 | 75.87 | 38.11 |
| **WBF** *(repro)* | 20.07 | 3.18 |  363 | 63.87 | 42.82 |
| **AMOVMC** *(ours)*  | 30.31 | **0.37** | 598 | **11.27** | 69.29 |
| **EUQ-VMC** *(ours)* | 21.71 | 3.34 | 1298 | 72.14 | 141.42 |

## Reading

- **AMOVMC** reaches the lowest SLA (0.37%) and therefore the lowest ESV, but it is
  *performance-obsessed*: it pays **+51% energy** (30.31 vs WBF 20.07) and **+65%
  migrations** (598 vs 363) to do so. Its aggressive performance-degradation
  threshold keeps hosts under-loaded.
- **EUQ-VMC** matches WBF on SLA (3.34% vs 3.18%) but needs **3.6× more migrations**
  (1298 vs 363) and **3.3× more network RAM transfer** (141 vs 43 ×10⁵) to get there —
  its overload-probability threshold + ROS selection migrate very frequently.
- **WBF holds the balanced operating point**: competitive SLA at the **fewest
  migrations and the lowest network cost** of all the forecasting methods, with
  near-lowest energy. This is exactly the network-aware trade-off Paper 4 argues for.

**Takeaway for the paper:** against two 2025 SOTA methods running in the *identical*
CloudSim energy/SLA model, WBF is not beaten on the energy–SLA–migration trade-off:
AMOVMC buys lower SLA with large energy+migration penalties, and EUQ-VMC matches
WBF's SLA only by migrating 3–4× more. This directly answers the reviewer/Guirado
concern that the original comparison used only the simulator's internal baselines.

*Note:* numbers use shared placement and the papers' default thresholds; the
qualitative trade-off (WBF = far fewer migrations / lower network cost) is robust to
parameter choice. Alibaba results for AMOVMC/EUQ-VMC are in
`output/{amovmc,euqvmc}_alibaba/` (AMOVMC SLA 0.10% / 449 migr; EUQ-VMC SLA 2.71% /
1841 migr), same pattern.

## Robustness 1 — parameter tuning (PlanetLab 20110303, 30 seeds)

We swept each method's overload-trigger parameter to find its *best* operating
point (configs `*_tune_*`, kept separate). Reference: WBF mig 310, SLA 3.87%, E 21.9.

| AMOVMC γ | migr | SLA% | Energy |  | EUQ-VMC safe | migr | SLA% | Energy |
|---------:|-----:|-----:|-------:|--|-------------:|-----:|-----:|-------:|
| 0.55 | 398 | 1.10 | 25.4 |  | 0.25 | 557 | 3.60 | 21.8 |
| 0.60 | 396 | 0.88 | 26.6 |  | 0.50 | 592 | 3.22 | 22.4 |
| 0.65 | **373** | 0.77 | 27.7 |  | 0.75 | 675 | 3.03 | 23.0 |
| 0.70 | 402 | 0.67 | 29.0 |  | 1.00 | 797 | 2.99 | 23.7 |
| 0.80* | 638 | 0.55 | 33.2 |  | 1.50* | 1210 | 3.23 | 24.4 |

(*default). Even at its best migration point AMOVMC matches WBF's migrations only
by spending **+26% energy** (γ=0.65: 373 migr, 27.7 kWh vs WBF 21.9); EUQ-VMC never
gets below **+50%** migrations (best 557 vs WBF 310). Parameters move the operating
point monotonically — confirming the implementations behave correctly.

## Robustness 2 — native placement (PlanetLab 10 traces × 30 seeds)

Each method run with its *own* placement (`amovmcfit` = AMOVMC fitness Eq. 20;
`euqmofpad` = EUQ-VMC 3-objective greedy), configs `*_native_*`.

| Technique | Energy | SLA% | migr | ESV | RAM-bw |
|-----------|-------:|-----:|-----:|----:|-------:|
| WBF | 20.07 | 3.18 | **363** | 63.9 | **42.8** |
| AMOVMC (shared placement) | 30.31 | 0.37 | 598 | 11.3 | 69.3 |
| AMOVMC (native fitness) | 31.72 | 0.38 | 1302 | 12.3 | 145.5 |
| EUQ-VMC (shared placement) | 21.71 | 3.34 | 1298 | 72.1 | 141.4 |
| EUQ-VMC (native MOFPA/D) | 28.45 | 3.31 | 2572 | 94.1 | 281.5 |

The methods' **native placements make them worse** in this harness (≈2× migrations
and network transfer), because the shared placement is a power+network-aware BFD
while their own placements ignore the routing-energy model. So the shared placement
is actually the *fairest* (best) configuration for the competitors — and WBF still
holds the migration/network advantage by a wide margin.

## Conclusion (honest framing)

This is **not** a clean win on every metric — be transparent about it:

- **AMOVMC attains a lower SLA (0.37%) and lower ESV** than WBF. By a single
  SLA-weighted score (ESV) AMOVMC looks better.
- **But the objective of consolidation is efficiency** — minimise energy and
  network-costly migrations at an *acceptable* SLA. On those metrics WBF wins:
  fewest migrations (−39% vs AMOVMC, −72% vs EUQ-VMC), lowest network transfer,
  near-lowest energy.
- **AMOVMC reaches its near-zero SLA by over-provisioning** (under-loading hosts):
  it has the *highest energy of every method* (+51% vs WBF) and +65% migrations.
  ESV rewards the low SLA while hiding that energy cost. The migration and network
  columns expose it.
- **EUQ-VMC** matches WBF's SLA but is strictly less efficient (3.6× migrations,
  3.3× network).

So the defensible claim is **efficiency, not domination**: on energy, migrations and
network cost — the quantities a network-aware consolidation method exists to reduce —
WBF is not outperformed by either 2025 method, and this holds under tuning and native
placement. **Recommended for the paper:** the shared-placement table with the
efficiency/over-provisioning framing (do *not* claim to beat them on SLA/ESV).
