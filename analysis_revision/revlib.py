"""Shared helpers for the revision analysis (read-only on the simulation outputs).

First part: helpers from the verification of the submitted version (metric definitions as
published then, kept so that the submitted tables can still be reproduced).
Second part (bottom of the file): corrected metric definitions used by the revised manuscript."""
import json, math, os
import numpy as np
from scipy import stats

DAYS = ["20110303", "20110306", "20110309", "20110322", "20110325",
        "20110403", "20110409", "20110411", "20110412", "20110420"]
WLS = ["planetlab", "alibaba", "materna", "azure"]
WLNAME = {"planetlab": "PlanetLab", "alibaba": "Alibaba", "materna": "Materna", "azure": "Microsoft Azure"}
MAIN_T = ["MU", "MMT", "RS", "MC", "WPSP", "WP", "WBP"]
SOTA_T = ["WBP", "BB+NeoPro", "AMOVMC", "EUQ-VMC"]
ALL_T = ["MU", "MMT", "RS", "MC", "WPSP", "WP", "WBP", "BB+NeoPro", "AMOVMC", "EUQ-VMC"]
SIM_END = 86400


def load_cache(cache):
    runs, folders = [], {}
    with open(os.path.join(cache, "runs.jsonl"), encoding="utf-8") as fh:
        for ln in fh:
            r = json.loads(ln)
            if r["file"] == "__FOLDER__":
                folders[r["folder"]] = r
            else:
                runs.append(r)
    return runs, folders


def _sig(r):
    s = r.get("cfg_hostSignalProcessing")
    return str(s).lower() if s is not None else "none"


def technique(r):
    """Label a run from its own experimentConfiguration (not from the folder name)."""
    sel = str(r.get("cfg_selectionPolicy", "")).lower()
    fc = str(r.get("cfg_hostForecastingTechnique", "")).lower()
    boll = "bollinger" in _sig(r)
    if sel in ("mu", "mmt", "rs", "mc"):
        return sel.upper() if fc == "last" and not boll else f"{sel.upper()}?{fc}/{_sig(r)}"
    if sel == "psp2":
        if fc == "last" and not boll:
            return "WPSP"
        if fc == "fbprophet":
            return "WBP" if boll else "WP"
        if fc == "neuralprophet":
            return "BB+NeoPro" if boll else "NeoPro(noBB)"
        return f"psp2?{fc}/{_sig(r)}"
    if sel == "amovmc":
        return "AMOVMC"
    if sel == "euqvmc":
        return "EUQ-VMC"
    return f"other:{sel}/{fc}/{_sig(r)}"


def variant(r):
    """Distinguish shared/native/tuned variants of the SOTA methods."""
    t = technique(r)
    hos = str(r.get("cfg_hostOverSaturationPolicy"))
    mig = str(r.get("cfg_vmMigrationPolicy"))
    par = str(r.get("cfg_parameter"))
    if t in ("AMOVMC", "EUQ-VMC"):
        return f"{t}[hos={hos},mig={mig},param={par}]"
    return t


def workload(r):
    tr = str(r.get("cfg_workloadTrace", "")).lower()
    if tr.startswith("planetlab"):
        return "planetlab"
    for w in ("alibaba", "materna", "azure"):
        if w in tr:
            return w
    return "unknown"


def trace_day(r):
    tr = str(r.get("cfg_workloadTrace", ""))
    if tr.lower().startswith("planetlab_"):
        return tr.split("_")[1]
    return None


def complete(r):
    return bool(r.get("parse_ok")) and r.get("t_lastClock") is not None and \
        abs(float(r["t_lastClock"]) - SIM_END) < 1e-6


# ----------------------------------------------------------------------------- metrics
def e_mig_paths_script(ram_in_bw):
    """Migration-routing energy exactly as the analysis scripts compute it [kWh]:
    (4.096 J/MB * totalRAMInBW[MB] + 20.165 J) * 1.1 / 3.6e6."""
    return (4.096 * ram_in_bw + 20.165) * 1.1 / (3600.0 * 1000.0)


def metrics(r):
    ram = r.get("np_totalRAMInBW") or 0.0
    ewh = r.get("cs_energyWithExtraHost")
    if ewh is None:
        ewh = r.get("cs_energy", 0.0)
    e = ewh + e_mig_paths_script(ram)
    alloc = r.get("cs_vmTotalAllocatedMips") or 0.0
    return dict(
        energy=e,                                              # kWh, composite
        hosts=r.get("cpu_totalUsedHosts", 0),                  # accumulated active hosts over snapshots
        sla=(r.get("cs_slaOverall") or 0.0) * 100.0,           # %
        migr=r.get("cs_numberOfMigrations", 0),                # count
        me=(alloc / e / 1e7) if e else 0.0,                    # x1e7 MIPS-s per kWh
        avmips=r.get("cpu_averageFreeMIPSActiveHosts", 0.0),   # MIPS
        disp=(r.get("cpu_medianCPUDispersionOfActiveHosts") or 0.0) * 100.0,
        vmcomm=(r.get("np_totalBWUsed") or 0.0) / 1e5,         # MB x1e5 (physical network)
        rambw=ram / 1e5,                                       # MB x1e5
        # energy parts
        e_host=r.get("cs_energy", 0.0),
        e_on=r.get("cs_energyOpenHosts", 0.0),
        e_onoff=r.get("cs_energyOpenCloseHosts", 0.0),
        e_mig=e_mig_paths_script(ram),
    )


def mean_ci(vals):
    a = np.asarray(vals, float)
    n = len(a)
    if n == 0:
        return 0, float("nan"), float("nan"), float("nan")
    m = float(a.mean())
    if n < 2:
        return n, m, float("nan"), float("nan")
    sd = float(a.std(ddof=1))
    ci = float(stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n))
    return n, m, sd, ci


def holm(p):
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for rank, idx in enumerate(order):
        run = max(run, min((m - rank) * p[idx], 1.0))
        adj[idx] = run
    return adj


def compress(seeds):
    s = sorted(set(int(x) for x in seeds if x is not None))
    if not s:
        return "-"
    out, start, prev = [], s[0], s[0]
    for x in s[1:]:
        if x == prev + 1:
            prev = x
            continue
        out.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = x
    out.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ",".join(out)


# ----------------------------------------------------------------------------- folder map
def table_folders(wl):
    """Folders feeding the manuscript tables, as encoded in SOTA/emit_workload_tables.py
    (classicals + WP/WBP) and SOTA/emit_transposed.py (WBP, BB+NeoPro, AMOVMC, EUQ-VMC)."""
    if wl == "planetlab":
        return dict(static=[f"pl_static_{d}" for d in DAYS],
                    prophet=[f"p4_pl_{d}_st" for d in DAYS],
                    np=[f"np_pl_{d}_st" for d in DAYS],
                    amovmc=[f"amovmc_pl_{d}" for d in DAYS],
                    euqvmc=[f"euqvmc_pl_{d}" for d in DAYS])
    return dict(static=[f"paper4_full_{wl}_static"], prophet=[f"paper4_full_{wl}_prophet_st"],
                np=[f"np_{wl}_st"], amovmc=[f"amovmc_{wl}"], euqvmc=[f"euqvmc_{wl}"])


def collect_table_runs(runs, wl):
    """{technique: [run records]} from the table folders, technique taken from each run's
    own config.  Classicals/WPSP only from the static folders, WP/WBP only from the
    prophet folders, etc. (same rule as the scripts)."""
    tf = table_folders(wl)
    byf = {}
    for r in runs:
        byf.setdefault(r["folder"], []).append(r)
    out = {t: [] for t in ALL_T}
    for fo in tf["static"]:
        for r in byf.get(fo, []):
            t = technique(r)
            if t in ("MU", "MMT", "RS", "MC", "WPSP"):
                out[t].append(r)
    for fo in tf["prophet"]:
        for r in byf.get(fo, []):
            t = technique(r)
            if t in ("WP", "WBP"):
                out[t].append(r)
    for fo in tf["np"]:
        for r in byf.get(fo, []):
            if technique(r) == "BB+NeoPro":
                out["BB+NeoPro"].append(r)
    for fo in tf["amovmc"]:
        for r in byf.get(fo, []):
            if technique(r) == "AMOVMC":
                out["AMOVMC"].append(r)
    for fo in tf["euqvmc"]:
        for r in byf.get(fo, []):
            if technique(r) == "EUQ-VMC":
                out["EUQ-VMC"].append(r)
    return out


def pair_key(r):
    return (trace_day(r), r.get("cfg_randomSeed"))


# ============================================================================= revision
# Corrected definitions used by the revised manuscript.
#
#  * Migration traffic.  The simulator registers every migration twice in the physical
#    network section (NetworkResults.instance and NetworkPhysicalResults.instance are the
#    same object, and PowerDatacenter calls calculateMigrationData on both).  In all the
#    5,838 outputs len(migrationDistances) == 2 * sum(numMigrationsPerSnapshot), so the
#    single-count value is exactly totalRAMInBW / 2.
#  * totalRAMInBW is hop-weighted: sum over migrations of RAM[MB] * path length between
#    source and destination hosts.
#  * Migration energy:  E_mig = (KAPPA * traffic[MB.hop] + BETA * n_migrations) / 3.6e6 kWh.
#    No 1.1 multiplier (it was not part of the published model); the fixed term is charged
#    once per migration (the submitted scripts added it once per simulation).
#  * Host-side energy = execution + switch-on + switch-off = energyWithExtraHost.
KAPPA_REF = 0.512      # J per MB per hop: coefficient of the linear model of Liu et al.
KAPPA_SUBMITTED = 4.096  # value used in the submitted version (8 x 0.512)
# Constant hard-coded in NetworkResults.java. Source (checked in the article): Sarji et al. 2011,
# Sec. IV, energy to migrate 1 MB of a VM, inbound 1.7892 J/MB + outbound 1.7596 J/MB, measured on one server
# with a 100 Mbps interface.
KAPPA_SIMULATOR = 1.7892 + 1.7596
BETA = 20.165          # J per migration (fixed term of the same model)


def traffic_single(r):
    """Hop-weighted migration traffic [MB.hop], each migration counted once."""
    return (r.get("np_totalRAMInBW") or 0.0) / 2.0


def migrated_ram_single(r):
    """RAM moved by migrations [MB], each migration counted once."""
    return (r.get("np_totalMigratedRAM") or 0.0) / 2.0


def n_mig_net(r):
    """Migrations registered by the network accounting (each counted once)."""
    return (r.get("np_len_migrationDistances") or 0) // 2


def e_mig_kwh(r, kappa=KAPPA_REF, beta=BETA):
    return (kappa * traffic_single(r) + beta * n_mig_net(r)) / 3.6e6


def metrics_rev(r, kappa=KAPPA_REF, beta=BETA):
    e_exec = r.get("cs_energy") or 0.0
    e_on = r.get("cs_energyOpenHosts") or 0.0
    e_onoff = r.get("cs_energyOpenCloseHosts") or 0.0
    e_hosts = r.get("cs_energyWithExtraHost")
    if e_hosts is None:
        e_hosts = e_exec + e_onoff
    e_mig = e_mig_kwh(r, kappa, beta)
    e_tot = e_hosts + e_mig
    alloc = r.get("cs_vmTotalAllocatedMips") or 0.0
    nsnap = r.get("cpu_len_usedHostsPerSnapshot") or 0
    n = n_mig_net(r)
    return dict(
        e_exec=e_exec, e_on=e_on, e_off=e_onoff - e_on, e_onoff=e_onoff,
        e_hosts=e_hosts, e_mig=e_mig, e_total=e_tot,
        act_hosts=(r.get("cpu_totalUsedHosts", 0) / nsnap) if nsnap else float("nan"),
        hosts_acc=r.get("cpu_totalUsedHosts", 0),
        sla=(r.get("cs_slaOverall") or 0.0) * 100.0,
        migr=r.get("cs_numberOfMigrations", 0),
        traffic=traffic_single(r) / 1000.0,                 # GB.hop
        ram_moved=migrated_ram_single(r) / 1000.0,          # GB
        hops=(traffic_single(r) / migrated_ram_single(r)) if migrated_ram_single(r) else float("nan"),
        me=(alloc / e_tot / 1e7) if e_tot else 0.0,         # x1e7 MIPS.s per kWh
        me_hosts=(alloc / e_hosts / 1e7) if e_hosts else 0.0,
        avmips=r.get("cpu_averageFreeMIPSActiveHosts", 0.0),
        vmcomm=(r.get("np_totalBWUsed") or 0.0) / 1e5,
        esv=e_tot * (r.get("cs_slaOverall") or 0.0) * 100.0,  # energy x SLA(%) product
        n_net=n,
    )
