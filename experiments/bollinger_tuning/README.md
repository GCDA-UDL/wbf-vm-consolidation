# Bollinger filter — effect and tuning (WF → WBF)

## Question
The Bollinger Bands filter is the component that turns **WF** (WPSP + Facebook Prophet) into
**WBF**. How does adding the filter — and tuning its window $N$ and width $\alpha$ — change the
trade-off between energy, SLA and migrations?

## Design
Same configuration on a representative workload, comparing WF (no bands) with WBF (with bands), and
sweeping the Bollinger parameters $(N, \alpha)$.
Config: `../../testbed/exp_bollinger_search.json`. Run as in [../../REPRODUCE.md](../../REPRODUCE.md).

## Result
- Adding the Bollinger filter (WF → WBF) **reduces migrations and SLA violations** for a small
  energy increase ($<5\%$): the filter suppresses migrations triggered by transient peaks.
  On PlanetLab, for example, migrations drop from $358$ (WF) to $320$ (WBF) and SLA from
  $7.29\%$ to $3.55\%$ — the same direction reported in the paper.
- A wider band (larger $\alpha$, e.g. $(4, 1.5)$ vs $(5, 0.5)$) provisions more head-room and
  filters more transients, shifting the operating point towards fewer migrations at a slightly
  higher energy. The window $N$ controls how reactive the band is to recent load.
- The benefit is largest on **variable** workloads (PlanetLab, Azure) and marginal on **stable**
  ones (Alibaba, Materna), where the band rarely triggers and WBF behaves close to WPSP.

## Takeaway
The Bollinger filter is an effective, low-cost volatility filter for the migration decision; its
parameters tune the energy-vs-migrations operating point rather than changing the qualitative
behaviour.
