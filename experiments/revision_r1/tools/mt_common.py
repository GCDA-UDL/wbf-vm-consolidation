"""Shared definitions of the robustness check on four additional traces (runs `mt_*`).

Imported by the other tools/mt_*.py scripts; no side effects.  One place for the trace
folders, the techniques, the templates they are cloned from and the run names, so that the
generator, the diff proof, the verifier and the table cannot disagree.
"""
import os

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # .../experiments/revision_r1
REPO = os.path.normpath(os.path.join(EXP, "..", ".."))                       # repository root
PKG = os.path.abspath(os.environ.get("PKG", REPO))     # holds testbed/ and workloads/ (as start_campaign.sh)
TESTBED = os.path.join(PKG, "testbed")
LISTS = os.path.join(EXP, "lists")
ANALYSIS = os.path.join(REPO, "analysis_revision")     # revlib.py, extract_runs.py
# Original, full-length traces (not shipped): needed only by tools/mt_check_traces.py, which proves
# how the four subsets were cut from them. Set WBF_ORIG_WORKLOADS to a folder with the same layout as
# workloads/ that also holds the source folders named in tables/mt_trace_check.md.
ORIG_WORKLOADS = os.environ.get("WBF_ORIG_WORKLOADS", "")

SEEDS = list(range(30))
NUM_SAMPLES = 288       # the reader fills numData - 1 = 288 values (numData = 289) after dataStartStep rows

PROVIDERS = {
    # wtype: first token of workloadTrace (selects the Java reader); sim: the simulated trace of the paper
    "materna": dict(wtype="materna", sim="materna_trace1_valid_0_288_100_mostDiff", vms="vms4_materna",
                    sep=";", col=4, colname="CPU usage [%]"),
    "alibaba": dict(wtype="alibaba2018", sim="alibaba2018_fixed_first_500_100_mostDiff", vms="vms4",
                    sep=",", col=2, colname="cpu_util_percent"),
}

# The four additional traces.  `start` is the dataStartStep of the configs (unchanged: 0).
# Alibaba: `first_index` is the value of the index column (first CSV column) of the first row
# the reader takes from the folder; `full` is the full-length copy of the same 100 files.
TRACES = [
    dict(key="materna2", exp="mt_materna2", provider="materna", start=0,
         folder="materna_trace2_valid_0_288_100_mostDiff", label="Materna trace 2",
         source="trace2_valid_0_288", date="04.12.2015"),
    dict(key="materna3", exp="mt_materna3", provider="materna", start=0,
         folder="materna_trace3_valid_0_288_100_mostDiff", label="Materna trace 3",
         source="trace3_valid_0_288", date="04.01.2016"),
    dict(key="alibaba5", exp="mt_alibaba5", provider="alibaba", start=0,
         folder="alibaba2018_fixed_first_500_100_mostDiff_day5_final", label="Alibaba day 5",
         full="alibaba2018_fixed_first_500_100_mostDiff_testing_day5", day_index=4, first_index=1150),
    dict(key="alibaba8", exp="mt_alibaba8", provider="alibaba", start=0,
         folder="alibaba2018_fixed_first_500_100_mostDiff_day8_final", label="Alibaba day 8",
         full="alibaba2018_fixed_first_500_100_mostDiff_testing_day8", day_index=7, first_index=2014),
]
TRACE_BY_EXP = {t["exp"]: t for t in TRACES}
TRACE_BY_FOLDER = {t["folder"]: t for t in TRACES}

# template configs (testbed/, the configurations of the main tables) per family and provider
FAMILIES = {
    "static": "paper4_full_{p}_static",          # MU, MMT, RS, MC, WPSP (selectionPolicy swept)
    "prophet_st": "paper4_full_{p}_prophet_st",  # WP, WBP (hostSignalProcessing swept); LVP = WPSP
    "amovmc": "amovmc_{p}",                      # AMOVMC, shared placement (ac), built-in gamma = 0.80
    "euqvmc": "euqvmc_{p}",                      # EUQ-VMC, shared placement (ac), safe = parameter = 1.5
    "np_st": "np_{p}_st",                        # BB+NeoPro: psp2 + neuralProphet + Bollinger (5, 0.5)
}

# tag, label (as in the paper), family, values fixed by make_singles.py --set (the same as in the
# November tooling: t0/h2 for the classical policies, gen_t1.sh for LVP/WP/WBP), list
TECHS = [
    ("mu", "MU", "static", {"selectionPolicy": "mu"}, "fast"),
    ("mmt", "MMT", "static", {"selectionPolicy": "mmt"}, "fast"),
    ("rs", "RS", "static", {"selectionPolicy": "rs"}, "fast"),
    ("mc", "MC", "static", {"selectionPolicy": "mc"}, "fast"),
    ("wpsp", "WPSP", "prophet_st", {"hostForecastingTechnique": ["last"], "hostSignalProcessing": ["none"]}, "fast"),
    ("wp", "WP", "prophet_st", {"hostForecastingTechnique": ["fbProphet"], "hostSignalProcessing": ["none"]}, "prophet"),
    ("wbp", "WBP", "prophet_st", {"hostForecastingTechnique": ["fbProphet"],
                                  "hostSignalProcessing": ["bollinger", 5, 0.5]}, "prophet"),
    ("amovmc", "AMOVMC", "amovmc", {}, "sota"),
    ("euqvmc", "EUQ-VMC", "euqvmc", {}, "sota"),
    ("bbneopro", "BB+NeoPro", "np_st", {}, "neural"),
]
TECH_BY_TAG = {t[0]: t for t in TECHS}
TAG_BY_LABEL = {t[1]: t[0] for t in TECHS}

# single-run configs of the November campaign with the same provider, technique and seed (used by the
# diff proof when they exist): {tag: [name patterns]}, {p} = provider, {s} = seed
NOVEMBER = {
    "mu": ["t0_static__mu_s{s:02d}"],
    "mmt": ["t0_static__mmt_s{s:02d}", "h2_{p}__mmt_s{s:02d}"],
    "rs": ["t0_static__rs_s{s:02d}"],
    "mc": ["t0_static__mc_s{s:02d}", "h2_{p}__mc_s{s:02d}"],
    "wpsp": ["cl_{p}__lvp_s{s:02d}", "t0_static__psp2_s{s:02d}"],
    "wp": ["cl_{p}__wp_s{s:02d}"],
    "wbp": ["cl_{p}__wbp_s{s:02d}"],
    "amovmc": [], "euqvmc": [], "bbneopro": [],
}

LIST_FILES = {"fast": "mt_fast.txt", "prophet": "mt_prophet.txt", "sota": "mt_sota.txt", "neural": "mt_neural.txt"}
SMOKE_FILE = "mt_smoke.txt"              # seed 0, every technique except BB+NeoPro, image metacloudsim:rev1
SMOKE_NEURAL_FILE = "mt_smoke_neural.txt"  # seed 0, BB+NeoPro, image metacloudsim-neural:latest

# run-identifying fields and the workload folder: the only fields a new config may change
ALLOWED_DIFF = {"name", "experimentOutputFolder", "workloadTrace"}


def base_name(trace, family):
    return f"mt_{trace['key']}_{family}"


def template_name(provider, family):
    return FAMILIES[family].format(p=provider)


def single_name(trace, tag, seed):
    return f"{trace['exp']}__{tag}_s{seed:02d}"


def workload_trace(trace):
    return f"{PROVIDERS[trace['provider']]['wtype']}/{trace['folder']}"
