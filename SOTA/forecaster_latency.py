#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------------------------
# Latency of ONE isolated forecast call, measured outside the simulator (SUBMITTED version of the
# manuscript, 24 September 2026). Added to the package in the revision for traceability. The
# windows are taken from the memory column (mem_util_percent) of ten Alibaba series and the
# horizon is one step. The revised manuscript reports instead the time of a complete
# consolidation decision measured inside the simulation loop.
# ------------------------------------------------------------------------------------------------
"""Per-operation forecaster latency: time ONE forecast call (fit+predict on a
30-step window, exactly as the simulator invokes it) for Prophet, NeuralProphet,
naive-last, EWMA and DWMA. Real CPU windows from the Alibaba trace. Reports
mean +/- sd over N calls (after 2 warm-up calls per forecaster)."""
import glob, os, sys, time, contextlib, logging
import numpy as np
import pandas as pd

W = 30          # history window (forecastingHistoryLength=30)
HORIZON = 1
NCALLS = 25     # timed calls per forecaster
TRACES = r"/workspace/workloads/alibaba2018/alibaba2018_fixed_first_500_100_mostDiff"

logging.disable(logging.CRITICAL)


@contextlib.contextmanager
def quiet():
    with open(os.devnull, "w") as dn:
        with contextlib.redirect_stdout(dn), contextlib.redirect_stderr(dn):
            yield


def windows():
    out = []
    for f in sorted(glob.glob(os.path.join(TRACES, "*.csv")))[:10]:
        s = pd.read_csv(f)["mem_util_percent"].dropna().to_numpy(float)
        for t in range(W, len(s) - 1, 97):
            win = s[t - W:t]
            if np.std(win) > 0.5:   # NeuralProphet 0.2.7 cannot fit constant windows
                out.append(win)
    return out


WINS = windows()
print(f"{len(WINS)} windows available", flush=True)


def t_prophet(hist):
    from prophet import Prophet
    with quiet():
        m = Prophet(uncertainty_samples=None)
        df = pd.DataFrame({"ds": pd.date_range("1970-01-01", freq="1D", periods=len(hist)), "y": hist})
        m.fit(df)
        fut = m.make_future_dataframe(periods=HORIZON)
        m.predict(fut)


def t_neuralprophet(hist):
    # exactly as pymodule/forecastingTechniques.py::python_getNeuralProphet
    from neuralprophet import NeuralProphet
    with quiet():
        m = NeuralProphet(yearly_seasonality=False, weekly_seasonality=False,
                          daily_seasonality=False, epochs=50)
        df = pd.DataFrame({"ds": pd.date_range("1970-01-01", freq="1D", periods=len(hist)), "y": hist})
        m.fit(df, freq="D")
        fut = m.make_future_dataframe(df, periods=HORIZON)
        m.predict(fut)


def t_naive(hist):
    _ = hist[-1]


def t_ewma(hist):
    pd.Series(hist).ewm(alpha=0.5, adjust=False).mean().iloc[-1]


def t_dwma(hist):
    w = np.arange(1, len(hist) + 1, dtype=float)
    _ = float((hist * w).sum() / w.sum())


ONLY = os.environ.get("ONLY", "")
BENCH = [("naive-last", t_naive), ("EWMA", t_ewma), ("DWMA", t_dwma),
         ("Prophet", t_prophet), ("NeuralProphet", t_neuralprophet)]
if ONLY:
    BENCH = [(n, f) for n, f in BENCH if n == ONLY]

for name, fn in BENCH:
    try:
        for i in range(2):          # warm-up (imports, JIT, stan binary)
            fn(WINS[i])
        ts = []
        for i in range(NCALLS):
            h = WINS[(i * 7) % len(WINS)]
            t0 = time.perf_counter()
            fn(h)
            ts.append(time.perf_counter() - t0)
        a = np.array(ts)
        unit = "s" if a.mean() > 0.1 else "ms"
        f = 1 if unit == "s" else 1e3
        print(f"{name:14} {a.mean()*f:9.3f} +/- {a.std()*f:.3f} {unit}/call  "
              f"(median {np.median(a)*f:.3f}, n={NCALLS})", flush=True)
    except Exception as e:
        print(f"{name:14} FAILED: {e!r}", flush=True)
print("done", flush=True)
