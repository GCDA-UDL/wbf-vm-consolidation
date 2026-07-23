#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
forecast_accuracy.py
====================
Standalone forecast-accuracy analysis for Paper 4 (WBF: WPSP + Bollinger + Prophet).

This script DOES NOT touch the CloudSim/MetaCloudSim simulator. It answers the
reviewer request "the forecaster is never validated (no MAE/RMSE/MAPE)" by
measuring, on the *same CPU time series* the simulator forecasts, how well
Facebook Prophet predicts the next step compared with two trivial baselines
(naive-last and EWMA).

--------------------------------------------------------------------------------
PAPER / SIMULATOR CONVENTIONS (reverse-engineered, do not change silently)
--------------------------------------------------------------------------------
Reconstructed from:
  * pymodule/forecastingTechniques.py  -> ForecastingTechniques.python_getFacebookProphet
  * pymodule/traceImporter.py          -> per-workload CPU-series loaders
  * testbed/paper4_full_*_prophet_st.json (the WBF run descriptors), which set:
        "forecastingHistoryLength": 30      -> history window = 30 steps
        "defaultHistoryLength":     30
        "hostForecastingTechnique": "fbProphet"
        "hostForecastingResume":    "mean"  -> collapse the horizon to a scalar by MEAN
        "vmForecastingResume*":     "mean"
        "hostSignalProcessing":  ["bollinger", 5, 0.5]  (winma=5, alpha=0.5)
        "migrationInterval":        6       -> consolidation cadence (6 steps = 30 min)
        "selectionPolicy":          "psp2"  (Weighted Pearson Selection, WPSP)
        "techniquesConfiguration":  {"pearson": 0.45}

Prophet is invoked EXACTLY as in pymodule/forecastingTechniques.py:
    m = Prophet(uncertainty_samples=None)
    ds = daily date range from 1970-01-01, one row per history sample
    m.fit(df); future = m.make_future_dataframe(periods=HORIZON); m.predict(future)
    forecast = yhat.iloc[-HORIZON:]           # last HORIZON predictions
Then "resume=mean" collapses those HORIZON predictions to a single scalar.

Window / horizon:
  * HISTORY_WINDOW = 30 steps. All four workloads are sampled every 5 minutes,
    so 30 steps = 150 minutes -- this is the "~30-step / 150-min window" the paper
    refers to.
  * HORIZON = 1 by default (predict the next step, the natural MAE/RMSE/MAPE target).
    The simulator consolidates every migrationInterval=6 steps; set HORIZON=6 (with
    RESUME="mean") to mirror the "mean CPU over the next migration interval" reading.

Signal processing (Bollinger, winma=5, alpha=0.5) is the transient-saturation
FILTER that WBF applies inside the over-saturation policy. It is a separate
component from the forecaster, so it is NOT applied here: forecast accuracy is
measured on the raw CPU series (the honest quantity the forecaster receives).
The Bollinger constants are kept below only for documentation.

--------------------------------------------------------------------------------
TRACE FORMATS (one file == one VM; representative "*_100_mostDiff" folder each)
--------------------------------------------------------------------------------
  PlanetLab : no header, single column of integer CPU% (0-100). 288 samples, 5-min.
              CPU series = column 0.                         (loader: read_csv header=None)
  Alibaba   : CSV w/ header idx,time_stamp,cpu_util_percent,mem_util_percent,...
              time_stamp step = 300 s. ~577 samples. CPU series = "cpu_util_percent".
              NOTE: the shipped pymodule AlibabaWorkloadLoader used "mem_util_percent"
              as its load proxy; flip ALIBABA_CPU_COL below to reproduce that choice.
  Materna   : ';'-separated, decimal COMMA. Header incl. "CPU usage [%]". 288 samples,
              5-min. CPU series = "CPU usage [%]".            (decimal=',', sep=';')
  Azure     : CSV w/ header timestamp,min,max,avg. timestamp step = 300 s. ~386 samples.
              CPU series = "avg" (per-window average CPU%).   (no pymodule loader existed)

--------------------------------------------------------------------------------
HOW TO RUN (later -- the CPU is busy with a simulation campaign; DO NOT run now)
--------------------------------------------------------------------------------
    cd C:\\Users\\PcVIP\\Desktop\\_publish_vmcons\\SOTA
    python forecast_accuracy.py                 # uses defaults below
    python forecast_accuracy.py --max-vms 100 --stride 1     # full/thorough run
    python forecast_accuracy.py --no-prophet    # baselines only (fast smoke test)
    python forecast_accuracy.py --horizon 6     # mirror the 6-step migration cadence
Requires: numpy, pandas, and (optionally) prophet. If prophet cannot be imported
the script degrades gracefully: it reports Prophet as "n/a" and still computes the
naive-last and EWMA baselines. Output: a table on stdout + forecast_accuracy.md
written next to this script.

RUNTIME NOTE: cost is dominated by Prophet, which refits from scratch on every
sliding window (~30 points). With the defaults (MAX_VMS=20, WINDOW_STRIDE=3) that
is on the order of a few thousand Prophet fits total (~1-2 s each incl. cmdstan
warmup), i.e. tens of minutes. A full run (--max-vms 100 --stride 1) is ~100x more
windows and can take many hours -- run it off the critical path. naive-last and
EWMA are effectively free.
"""

from __future__ import annotations

import argparse
import contextlib
import glob
import logging
import math
import os
import sys
import time

import numpy as np
import pandas as pd

# =============================================================================
# CONFIG (defaults; several are overridable on the command line)
# =============================================================================
HISTORY_WINDOW = 30      # forecasting history length in steps (paper: forecastingHistoryLength=30)
HORIZON        = 1       # steps ahead to forecast. 1 = next step. 6 = one migration interval.
RESUME         = "mean"  # collapse the HORIZON-vector to a scalar: "mean" (paper) or "last"
STEP_MINUTES   = 5       # every workload is sampled every 5 min -> HISTORY_WINDOW*5 = 150 min

EWMA_ALPHA     = 0.5     # EWMA baseline smoothing factor (pandas ewm alpha; adjust=False)
                         # (pymodule SimpleExpSmoothing used smoothing_level=0.8; this is a
                         #  neutral baseline, not the paper forecaster -- tune via --ewma-alpha)
MAPE_EPS       = 1.0     # exclude |actual| < MAPE_EPS (percent) from MAPE to avoid /0 blow-ups

# --- cost controls (keep Prophet tractable; scale up for a thorough run) ---
MAX_VMS            = 20   # VMs (files) per workload, taken as the first N sorted. None = all 100.
WINDOW_STRIDE      = 3    # evaluate every k-th sliding window. 1 = every step (thorough).
MAX_WINDOWS_PER_VM = None # hard cap on windows per VM after striding. None = no cap.

# --- WBF Bollinger filter config (documented only; NOT applied to accuracy) ---
BOLLINGER_WINMA = 5
BOLLINGER_ALPHA = 0.5

# --- paths ---
SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
WORKLOADS_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "workloads"))
OUTPUT_MD      = os.path.join(SCRIPT_DIR, "forecast_accuracy.md")

# Column choice for Alibaba: the shipped pymodule AlibabaWorkloadLoader
# (traceImporter.py:105) feeds "mem_util_percent" as the load proxy to the
# simulator, so we forecast the SAME series the simulator forecasts.
ALIBABA_CPU_COL = "mem_util_percent"

# =============================================================================
# Optional Prophet import (graceful degradation)
# =============================================================================
PROPHET_OK = False
try:
    # silence cmdstanpy / prophet chatter before import side effects
    logging.getLogger("prophet").setLevel(logging.CRITICAL)
    logging.getLogger("cmdstanpy").setLevel(logging.CRITICAL)
    from prophet import Prophet  # type: ignore
    PROPHET_OK = True
except Exception as _e:  # ImportError or backend/init failure
    Prophet = None  # type: ignore
    _PROPHET_IMPORT_ERROR = repr(_e)


@contextlib.contextmanager
def _suppressed():
    """Redirect stdout/stderr to os.devnull (Prophet/cmdstan are noisy)."""
    with open(os.devnull, "w") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            yield


# =============================================================================
# Per-workload CPU-series loaders (one pandas Series of floats per VM file)
# =============================================================================
def _list_vm_files(folder, pattern):
    files = sorted(f for f in glob.glob(os.path.join(folder, pattern)) if os.path.isfile(f))
    return files


def load_planetlab(path):
    # no header, single integer column of CPU%
    df = pd.read_csv(path, header=None)
    return pd.to_numeric(df[0], errors="coerce").astype(float)


def load_alibaba(path):
    df = pd.read_csv(path)
    col = ALIBABA_CPU_COL if ALIBABA_CPU_COL in df.columns else "cpu_util_percent"
    return pd.to_numeric(df[col], errors="coerce").astype(float)


def load_materna(path):
    # ';'-separated, decimal COMMA (European); CPU column is "CPU usage [%]"
    df = pd.read_csv(path, sep=";", decimal=",", engine="python")
    return pd.to_numeric(df["CPU usage [%]"], errors="coerce").astype(float)


def load_azure(path):
    df = pd.read_csv(path)
    return pd.to_numeric(df["avg"], errors="coerce").astype(float)


# name -> (subfolder relative to WORKLOADS_ROOT, glob pattern, loader)
WORKLOADS = {
    "PlanetLab": ("planetlab/planetlab_20110303_100_mostDiff",            "*",     load_planetlab),
    "Alibaba":   ("alibaba2018/alibaba2018_fixed_first_500_100_mostDiff", "*.csv", load_alibaba),
    "Materna":   ("materna/materna_trace1_valid_0_288_100_mostDiff",      "*.csv", load_materna),
    "Azure":     ("azure/azure_azure2019_traces_100_mostDiff",            "*.csv", load_azure),
}

# =============================================================================
# Forecasters. Each takes a 1-D history array (length HISTORY_WINDOW) and the
# horizon, and returns a single scalar prediction (already resumed).
# =============================================================================
def _resume(vec):
    vec = np.asarray(vec, dtype=float)
    if vec.size == 0 or not np.isfinite(vec).any():
        return float("nan")
    return float(np.nanmean(vec)) if RESUME == "mean" else float(vec[-1])


def forecast_naive_last(history, horizon):
    """Persistence baseline: next value == last observed value."""
    return float(history[-1])


def forecast_ewma(history, horizon, alpha=None):
    """EWMA baseline: last exponentially-weighted level (flat over the horizon)."""
    a = EWMA_ALPHA if alpha is None else alpha
    level = pd.Series(np.asarray(history, dtype=float)).ewm(alpha=a, adjust=False).mean().iloc[-1]
    return float(level)


def forecast_prophet(history, horizon):
    """
    Facebook Prophet, invoked EXACTLY as pymodule/forecastingTechniques.py
    (Prophet(uncertainty_samples=None), fake daily 'ds', fit, make_future_dataframe,
    take the last `horizon` yhat), then resumed to a scalar. Returns NaN on failure.
    """
    if not PROPHET_OK:
        return float("nan")
    ser = pd.Series(np.asarray(history, dtype=float))
    if not np.isfinite(ser).all():
        return float("nan")
    try:
        with _suppressed():
            m = Prophet(uncertainty_samples=None)
            df = pd.DataFrame({
                "ds": pd.date_range("1970-01-01 0:00:00", freq="1D", periods=len(ser)),
                "y": ser.values,
            })
            m.fit(df)
            future = m.make_future_dataframe(periods=horizon)
            fc = m.predict(future)
        return _resume(fc["yhat"].iloc[-horizon:].values)
    except Exception:
        return float("nan")


# =============================================================================
# Metrics
# =============================================================================
class ErrorAccumulator:
    """Collects (prediction, actual) pairs and computes MAE / RMSE / MAPE / sMAPE."""
    def __init__(self):
        self.preds = []
        self.acts = []
        self.failures = 0  # forecast returned NaN

    def add(self, pred, actual):
        if pred is None or (isinstance(pred, float) and math.isnan(pred)):
            self.failures += 1
            return
        self.preds.append(float(pred))
        self.acts.append(float(actual))

    def compute(self):
        p = np.asarray(self.preds, dtype=float)
        a = np.asarray(self.acts, dtype=float)
        n = p.size
        if n == 0:
            return dict(n=0, mae=float("nan"), rmse=float("nan"),
                       mape=float("nan"), smape=float("nan"),
                       n_mape=0, failures=self.failures)
        err = p - a
        mae = float(np.mean(np.abs(err)))
        rmse = float(np.sqrt(np.mean(err ** 2)))
        # MAPE only where |actual| >= MAPE_EPS (percent series can be ~0)
        mask = np.abs(a) >= MAPE_EPS
        n_mape = int(mask.sum())
        mape = float(np.mean(np.abs(err[mask] / a[mask])) * 100.0) if n_mape else float("nan")
        # sMAPE (symmetric, defined everywhere except p==a==0)
        denom = (np.abs(p) + np.abs(a))
        sm = np.where(denom == 0, 0.0, 2.0 * np.abs(err) / denom)
        smape = float(np.mean(sm) * 100.0)
        return dict(n=n, mae=mae, rmse=rmse, mape=mape, smape=smape,
                    n_mape=n_mape, failures=self.failures)


# =============================================================================
# Sliding-window evaluation
# =============================================================================
METHODS = [
    ("Prophet",    forecast_prophet),
    ("naive-last", forecast_naive_last),
    ("EWMA",       forecast_ewma),
]


def iter_windows(series_len, window, horizon, stride, cap):
    """Yield start indices t so history = y[t-window:t], target = y[t:t+horizon]."""
    count = 0
    t = window
    last_target_start = series_len - horizon
    while t <= last_target_start:
        yield t
        count += 1
        if cap is not None and count >= cap:
            return
        t += stride


def evaluate_workload(name, folder_rel, pattern, loader, args, accs):
    folder = os.path.join(WORKLOADS_ROOT, folder_rel)
    files = _list_vm_files(folder, pattern)
    if not files:
        print(f"  [WARN] no VM files found in {folder}", file=sys.stderr)
        return 0
    if args.max_vms is not None:
        files = files[: args.max_vms]

    n_windows = 0
    for fi, path in enumerate(files):
        try:
            s = loader(path)
        except Exception as e:
            print(f"  [WARN] failed to load {os.path.basename(path)}: {e}", file=sys.stderr)
            continue
        y = s.dropna().to_numpy(dtype=float)
        if y.size < args.window + args.horizon:
            continue
        for t in iter_windows(y.size, args.window, args.horizon,
                              args.stride, args.max_windows):
            hist = y[t - args.window: t]
            target = y[t: t + args.horizon]
            actual = float(np.mean(target)) if RESUME == "mean" else float(target[-1])
            for mname, fn in METHODS:
                if mname == "Prophet" and not (PROPHET_OK and not args.no_prophet):
                    continue
                pred = fn(hist, args.horizon)
                accs[mname].add(pred, actual)
            n_windows += 1
        if args.verbose:
            print(f"    {name}: VM {fi + 1}/{len(files)} done "
                  f"({n_windows} windows so far)", file=sys.stderr)
    return n_windows


# =============================================================================
# Reporting
# =============================================================================
def format_table(results):
    """results: {workload: {method: metrics_dict}} -> plain-text table string."""
    lines = []
    header = (f"{'Workload':<11} {'Method':<11} {'n':>7} {'MAE':>8} "
              f"{'RMSE':>8} {'MAPE%':>8} {'sMAPE%':>8} {'fails':>6}")
    sep = "-" * len(header)
    lines.append(header)
    lines.append(sep)
    for wl, per_method in results.items():
        for mname, _ in METHODS:
            m = per_method.get(mname)
            if m is None:
                continue
            mape = "n/a" if math.isnan(m["mape"]) else f"{m['mape']:.2f}"
            if m["n"] == 0:
                lines.append(f"{wl:<11} {mname:<11} {'n/a':>7} {'--':>8} "
                             f"{'--':>8} {'--':>8} {'--':>8} {m['failures']:>6}")
            else:
                lines.append(f"{wl:<11} {mname:<11} {m['n']:>7} {m['mae']:>8.3f} "
                             f"{m['rmse']:>8.3f} {mape:>8} {m['smape']:>8.2f} "
                             f"{m['failures']:>6}")
        lines.append(sep)
    return "\n".join(lines)


def write_markdown(results, args, elapsed):
    prophet_state = ("available" if PROPHET_OK else
                     f"NOT available ({_PROPHET_IMPORT_ERROR})")
    if args.no_prophet:
        prophet_state += " (disabled via --no-prophet)"
    lines = []
    lines.append("# Forecast-accuracy analysis (Paper 4 / WBF)\n")
    lines.append("One-step-ahead forecast accuracy of Facebook Prophet vs. two trivial "
                 "baselines, measured on the raw CPU time series the simulator forecasts. "
                 "The simulator itself is untouched.\n")
    lines.append("## Configuration\n")
    lines.append(f"- History window: **{args.window} steps** "
                 f"(= {args.window * STEP_MINUTES} min at {STEP_MINUTES}-min sampling)")
    lines.append(f"- Horizon: **{args.horizon} step(s)**, resumed to a scalar by **{RESUME}**")
    lines.append(f"- EWMA alpha: {args.ewma_alpha if args.ewma_alpha is not None else EWMA_ALPHA}")
    lines.append(f"- MAPE excludes |actual| < {MAPE_EPS}% (avoids divide-by-~0)")
    lines.append(f"- VMs per workload: {args.max_vms if args.max_vms is not None else 'all'}; "
                 f"window stride: {args.stride}; "
                 f"cap/VM: {args.max_windows if args.max_windows is not None else 'none'}")
    lines.append(f"- Alibaba CPU column: `{ALIBABA_CPU_COL}`")
    lines.append(f"- Prophet: {prophet_state}")
    lines.append(f"- Prophet invocation identical to "
                 f"`pymodule/forecastingTechniques.py::python_getFacebookProphet` "
                 f"(`Prophet(uncertainty_samples=None)`, fake daily `ds`)")
    lines.append(f"- Bollinger filter (winma={BOLLINGER_WINMA}, alpha={BOLLINGER_ALPHA}) is a "
                 f"separate WBF component and is intentionally NOT applied here")
    lines.append(f"- Wall-clock: {elapsed:.1f} s\n")
    lines.append("## Results\n")
    lines.append("| Workload | Method | n | MAE | RMSE | MAPE% | sMAPE% | fails |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for wl, per_method in results.items():
        for mname, _ in METHODS:
            m = per_method.get(mname)
            if m is None:
                continue
            if m["n"] == 0:
                lines.append(f"| {wl} | {mname} | n/a | -- | -- | -- | -- | {m['failures']} |")
            else:
                mape = "n/a" if math.isnan(m["mape"]) else f"{m['mape']:.2f}"
                lines.append(f"| {wl} | {mname} | {m['n']} | {m['mae']:.3f} | "
                             f"{m['rmse']:.3f} | {mape} | {m['smape']:.2f} | {m['failures']} |")
    lines.append("")
    lines.append("**Reading.** Lower is better on every column. MAE/RMSE are in CPU%% "
                 "(same units as the series). MAPE is over points with |actual| >= "
                 f"{MAPE_EPS}%%; sMAPE is reported over all points as a zero-robust "
                 "complement. `fails` counts windows where the forecaster returned no "
                 "value (e.g. Prophet convergence failure).\n")
    lines.append("> Generated by `SOTA/forecast_accuracy.py`. Re-run with "
                 "`--max-vms 100 --stride 1` for the full-population figures.\n")
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# =============================================================================
# Main
# =============================================================================
def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Standalone forecast-accuracy analysis (Paper 4 / WBF).")
    p.add_argument("--window", type=int, default=HISTORY_WINDOW,
                   help=f"history window in steps (default {HISTORY_WINDOW})")
    p.add_argument("--horizon", type=int, default=HORIZON,
                   help=f"forecast horizon in steps (default {HORIZON})")
    p.add_argument("--max-vms", type=int, default=MAX_VMS, dest="max_vms",
                   help=f"VMs per workload (default {MAX_VMS}; use e.g. 100 for all)")
    p.add_argument("--stride", type=int, default=WINDOW_STRIDE,
                   help=f"sliding-window stride (default {WINDOW_STRIDE}; 1 = thorough)")
    p.add_argument("--max-windows", type=int, default=MAX_WINDOWS_PER_VM, dest="max_windows",
                   help="cap windows per VM (default none)")
    p.add_argument("--ewma-alpha", type=float, default=None, dest="ewma_alpha",
                   help=f"EWMA alpha (default {EWMA_ALPHA})")
    p.add_argument("--no-prophet", action="store_true",
                   help="skip Prophet (baselines only; fast)")
    p.add_argument("--workloads", nargs="+", default=list(WORKLOADS.keys()),
                   choices=list(WORKLOADS.keys()),
                   help="subset of workloads to evaluate")
    p.add_argument("--verbose", action="store_true", help="per-VM progress to stderr")
    return p.parse_args(argv)


def main(argv=None):
    global EWMA_ALPHA
    args = parse_args(argv)
    if args.ewma_alpha is not None:
        EWMA_ALPHA = args.ewma_alpha

    if not os.path.isdir(WORKLOADS_ROOT):
        print(f"[FATAL] workloads root not found: {WORKLOADS_ROOT}", file=sys.stderr)
        return 2

    print("Forecast-accuracy analysis (Paper 4 / WBF)")
    print(f"  window={args.window} steps ({args.window * STEP_MINUTES} min)  "
          f"horizon={args.horizon}  resume={RESUME}")
    print(f"  max_vms={args.max_vms}  stride={args.stride}  "
          f"prophet={'on' if (PROPHET_OK and not args.no_prophet) else 'off'}")
    if not PROPHET_OK:
        print(f"  [note] Prophet unavailable -> {_PROPHET_IMPORT_ERROR}")
    print()

    t0 = time.time()
    results = {}
    total_windows = 0
    for name in args.workloads:
        folder_rel, pattern, loader = WORKLOADS[name]
        accs = {mname: ErrorAccumulator() for mname, _ in METHODS}
        print(f"[{name}] evaluating...", flush=True)
        nw = evaluate_workload(name, folder_rel, pattern, loader, args, accs)
        total_windows += nw
        results[name] = {mname: acc.compute() for mname, acc in accs.items()}
        print(f"  {nw} windows evaluated.", flush=True)

    elapsed = time.time() - t0
    print()
    print(format_table(results))
    print()
    print(f"Total windows: {total_windows}   wall-clock: {elapsed:.1f} s")
    write_markdown(results, args, elapsed)
    print(f"Markdown written to: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
