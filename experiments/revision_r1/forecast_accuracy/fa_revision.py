#!/usr/bin/env python3
"""Corrected forecast-accuracy study for the revision (replaces SOTA/forecast_accuracy.py).

Runs INSIDE the container (Python 3.8, prophet 1.1.5).  It does not touch the simulator.

What changes with respect to the submitted study
  * Series: exactly what the simulator reads for each of the 100 VMs of each workload
      PlanetLab  10 daily folders, single integer column
      Alibaba    column index 2 (cpu_util_percent)      [the submitted study used mem_util_percent]
      Materna    ';'-separated, column index 4 (CPU usage [%]), decimal comma
      Azure      column index 3 (avg)
    and only the samples it uses: the first 288 after the header
    (UtilizationModelPlanetLabInMemory: data[i], i = 0..287, numData = 289).
  * Protocol A (as in the submitted table): one step ahead at every step, window of the
    last 30 samples.
  * Protocol B (as the method uses the forecast): at every decision instant t = 6, 12, ...
    (migrationInterval = 6), window = last min(t, 30) samples, horizon 6; the mean of the 6
    predicted values is compared with the mean of the next 6 observed values.
    Protocol B is also applied to the Bollinger-transformed window (upper band, N = 5,
    alpha = 0.5, sample standard deviation, back-filled, as pymodule/signalProcessing.py),
    against the same raw target: this is the series WBP gives to the forecaster.
  * Forecasters
      Prophet   same call as pymodule/forecastingTechniques.py::python_getFacebookProphet
                (Prophet(uncertainty_samples=None), fake daily dates from 1970-01-01).
                As in FBProphetForecastingTechnique.java, a ValueError falls back to the
                last value of the window (counted in the column `fallbacks`).
      LVP       last value of the window.
      EWMA0.8   exponential smoothing as the simulator runs it: statsmodels
                SimpleExpSmoothing(initialization_method="estimated").fit(smoothing_level=0.8),
                last value if the window has fewer than 10 samples
                (SimpleExpSmoothingForecastingTechnique.java).
      EWMA0.5   pandas ewm(alpha=0.5, adjust=False), as in the submitted table.
  * The series are per VM.  The consolidation loop forecasts host-level utilisation
    (sum of the VMs placed on a host), which only exists inside a simulation.

Output: one CSV row per (trace, vm, protocol, signal, forecaster) with the sums needed to
pool bias / MAE / RMSE / MAPE:  n, sum_err (prediction - actual), sum_abs, sum_sq, n_mape,
sum_ape, fallbacks.
MAPE excludes targets with |actual| < 1.0 (percent), as the submitted script did.

Usage:  python3.8 fa_revision.py --workloads /workspace/workloads --out /out/fa_raw.csv
                                 --procs 12 [--protocols A,B] [--no-prophet] [--limit-vms N]
Resumable: (trace, vm, protocol) blocks already present in the CSV are skipped.
"""
import argparse
import csv
import glob
import logging
import os
import sys
import time
import warnings
from multiprocessing import Pool

import numpy as np
import pandas as pd

WINDOW = 30
INTERVAL = 6
NSAMPLES = 288
BB_N, BB_ALPHA = 5, 0.5
MAPE_EPS = 1.0
DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]
TRACES = [(f"planetlab_{d}", "PlanetLab", f"planetlab/planetlab_{d}_100_mostDiff", "planetlab") for d in DAYS] + [
    ("alibaba", "Alibaba", "alibaba2018/alibaba2018_fixed_first_500_100_mostDiff", "alibaba"),
    ("materna", "Materna", "materna/materna_trace1_valid_0_288_100_mostDiff", "materna"),
    ("azure", "Azure", "azure/azure_azure2019_traces_100_mostDiff", "azure"),
]
FIELDS = ["trace", "workload", "vm", "protocol", "signal", "forecaster", "n", "sum_err", "sum_abs", "sum_sq",
          "n_mape", "sum_ape", "fallbacks", "seconds"]


def read_series(path, kind):
    """First 288 samples of the column the simulator reads, in percent."""
    vals = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    if kind != "planetlab":
        lines = lines[1:]                       # getJumpFirstLine() == true
    for ln in lines[:NSAMPLES]:
        if kind == "planetlab":
            vals.append(float(int(ln)))
        elif kind == "alibaba":
            vals.append(float(ln.split(",")[2]))
        elif kind == "azure":
            vals.append(float(ln.split(",")[3]))
        elif kind == "materna":
            vals.append(float(ln.split(";")[4].replace('"', "").replace(",", ".")))
    return np.asarray(vals, dtype=float)


def bollinger_upper(window):
    """pymodule/signalProcessing.py::get_bollinger_upper (pandas rolling, sample std, bfill)."""
    ser = pd.Series(np.asarray(window, dtype=float))
    ma = ser.rolling(BB_N).mean()
    std = ser.rolling(BB_N).std()
    return pd.Series(ma + BB_ALPHA * std).fillna(method="bfill").values


_PROPHET = None


def _prophet_cls():
    global _PROPHET
    if _PROPHET is None:
        logging.getLogger("prophet").setLevel(logging.CRITICAL)
        logging.getLogger("cmdstanpy").setLevel(logging.CRITICAL)
        logging.getLogger("cmdstanpy").disabled = True
        from prophet import Prophet
        _PROPHET = Prophet
    return _PROPHET


def f_prophet(hist, horizon):
    """Returns (scalar forecast, fallback flag)."""
    if len(hist) < INTERVAL:                      # FBProphetForecastingTechnique.java
        return float(hist[-1]), 0
    try:
        Prophet = _prophet_cls()
        m = Prophet(uncertainty_samples=None)
        df = pd.DataFrame({"ds": pd.date_range("1970-01-01 0:00:00", freq="1D", periods=len(hist)).tolist(),
                           "y": pd.Series(list(np.float_(hist)), dtype=float)})
        m.fit(df)
        future = m.make_future_dataframe(periods=horizon)
        fc = m.predict(future)
        return float(np.mean(fc["yhat"].iloc[-horizon:].values)), 0
    except ValueError:
        return float(hist[-1]), 1


def f_lvp(hist, horizon):
    return float(hist[-1]), 0


def f_ewma08(hist, horizon):
    if len(hist) < 10:                            # SimpleExpSmoothingForecastingTechnique.java
        return float(hist[-1]), 0
    from statsmodels.tsa.api import SimpleExpSmoothing
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SimpleExpSmoothing(pd.Series(list(np.float_(hist)), dtype=float),
                                 initialization_method="estimated").fit(smoothing_level=0.8)
        return float(np.mean(np.asarray(fit.forecast(horizon)))), 0


def f_ewma05(hist, horizon):
    return float(pd.Series(np.asarray(hist, dtype=float)).ewm(alpha=0.5, adjust=False).mean().iloc[-1]), 0


FORECASTERS = [("Prophet", f_prophet), ("LVP", f_lvp), ("EWMA0.8", f_ewma08), ("EWMA0.5", f_ewma05)]


class Acc:
    def __init__(self):
        self.n = 0
        self.se = self.sa = self.sq = self.sape = 0.0
        self.nm = 0
        self.fb = 0

    def add(self, pred, actual, fb):
        if not np.isfinite(pred):
            pred = 0.0                            # FutureTechnique.getForecasting: NaN -> 0
        e = pred - actual
        self.n += 1
        self.se += e
        self.sa += abs(e)
        self.sq += e * e
        if abs(actual) >= MAPE_EPS:
            self.nm += 1
            self.sape += abs(e / actual)
        self.fb += fb


def work(task):
    trace, wl, path, kind, protocols, use_prophet = task
    y = read_series(path, kind)
    vm = os.path.basename(path)
    rows = []
    fcs = [(n, f) for n, f in FORECASTERS if use_prophet or n != "Prophet"]
    t0 = time.time()
    if "A" in protocols:
        acc = {n: Acc() for n, _ in fcs}
        for t in range(WINDOW, len(y)):
            hist, actual = y[t - WINDOW:t], float(y[t])
            for n, f in fcs:
                p, fb = f(hist, 1)
                acc[n].add(p, actual, fb)
        dt = time.time() - t0
        rows += [dict(trace=trace, workload=wl, vm=vm, protocol="A", signal="raw", forecaster=n, n=a.n,
                      sum_err=a.se, sum_abs=a.sa, sum_sq=a.sq, n_mape=a.nm, sum_ape=a.sape, fallbacks=a.fb, seconds=round(dt, 2))
                 for n, a in acc.items()]
    if "B" in protocols:
        t1 = time.time()
        acc = {(s, n): Acc() for s in ("raw", "bollinger") for n, _ in fcs}
        for t in range(INTERVAL, len(y) - INTERVAL + 1, INTERVAL):
            hist = y[max(0, t - WINDOW):t]
            actual = float(np.mean(y[t:t + INTERVAL]))
            hb = bollinger_upper(hist)
            for n, f in fcs:
                p, fb = f(hist, INTERVAL)
                acc[("raw", n)].add(p, actual, fb)
                if np.isfinite(hb).all():
                    p, fb = f(hb, INTERVAL)
                else:
                    p, fb = float("nan"), 1
                acc[("bollinger", n)].add(p, actual, fb)
        dt = time.time() - t1
        rows += [dict(trace=trace, workload=wl, vm=vm, protocol="B", signal=s, forecaster=n, n=a.n,
                      sum_err=a.se, sum_abs=a.sa, sum_sq=a.sq, n_mape=a.nm, sum_ape=a.sape, fallbacks=a.fb, seconds=round(dt, 2))
                 for (s, n), a in acc.items()]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workloads", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--protocols", default="B,A")
    ap.add_argument("--no-prophet", action="store_true")
    ap.add_argument("--limit-vms", type=int, default=None)
    ap.add_argument("--traces", default=None, help="comma-separated trace ids (default: all 13)")
    a = ap.parse_args()
    protocols = [p for p in a.protocols.split(",") if p]
    done = set()
    if os.path.exists(a.out):
        with open(a.out, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                done.add((r["trace"], r["vm"], r["protocol"]))
    else:
        with open(a.out, "w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, FIELDS).writeheader()
    tasks = []
    sel = set(a.traces.split(",")) if a.traces else None
    for trace, wl, rel, kind in TRACES:
        if sel and trace not in sel:
            continue
        files = sorted(f for f in glob.glob(os.path.join(a.workloads, rel, "*")) if os.path.isfile(f))
        if a.limit_vms:
            files = files[:a.limit_vms]
        for proto in protocols:                  # one task per protocol so that B results arrive first
            for f in files:
                if (trace, os.path.basename(f), proto) not in done:
                    tasks.append((trace, wl, f, kind, [proto], not a.no_prophet))
    # protocol order as given on the command line; within a protocol the single-trace
    # workloads first, then the PlanetLab days (so partial results cover every workload early)
    tasks.sort(key=lambda t: (protocols.index(t[4][0]), t[0].startswith("planetlab"), t[0]))
    print(f"{len(tasks)} tasks to run ({len(done)} blocks already done), procs={a.procs}, "
          f"OMP={os.environ.get('OMP_NUM_THREADS')} STAN={os.environ.get('STAN_NUM_THREADS')}", flush=True)
    t0 = time.time()
    k = 0
    with Pool(a.procs) as pool, open(a.out, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, FIELDS)
        for rows in pool.imap_unordered(work, tasks, chunksize=1):
            for r in rows:
                w.writerow(r)
            fh.flush()
            k += 1
            if k % 50 == 0:
                print(f"[{time.strftime('%T')}] {k}/{len(tasks)} tasks, {time.time() - t0:.0f} s", flush=True)
    print(f"DONE {k} tasks in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
