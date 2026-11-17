#!/usr/bin/env python3
"""Read-only checks of the four additional traces of the robustness check (and of the simulated
trace of the same provider, for comparison).  Writes tables/mt_trace_check.md; exit code 1 if
any check fails.

  python -B tools/mt_check_traces.py

What it checks, per folder:
  * files: number, extension, no extra entries (the simulator lists the folder, sorts the names and
    takes the first numCloudlets = 100 files);
  * header identical in every file and identical to the simulated trace of the same provider; same
    number of fields in every row; the column the reader uses has the same name and position;
  * rows: every file has at least dataStartStep + 288 data rows (the reader skips the header and
    dataStartStep rows, then reads 288 rows and duplicates the last one, numData = 289);
  * values: the 288 values the reader takes from every file are parsed as the Java reader does
    (UtilizationModelMaternaInMemory: split(";")[4] with decimal comma; UtilizationModelAlibaba2018InMemory:
    split(",")[2]); none is empty, NaN or infinite; range reported;
  * which rows are read: Materna, the time stamps of the 288 rows (one calendar day, 00:00 to 23:55);
    Alibaba, the index column and time stamp of the rows, and the proof that they are the same rows,
    byte for byte, as rows first_index..first_index+287 of the full-length copy (_testing_dayN) and of
    the source files (fixed_first_500);
  * selection: the 100 files are the top 100 by accumulated absolute difference of the CPU column
    (the "mostDiff" rule of the author's notebooks) among the candidate files of that trace/day;
  * statistics of the 288 x 100 values read: pooled mean and standard deviation, and the two
    statistics of the manuscript's workload table (median over the VMs of the per-VM median and of the
    per-VM accumulated absolute difference, +- standard deviation over the VMs);
  * the copies in workloads are byte-identical to the original folders.
"""
import hashlib
import math
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mt_common as M  # noqa: E402

OUT = os.path.join(M.EXP, "tables", "mt_trace_check.md")
PKGW = os.path.join(M.PKG, "workloads")
PLAIN = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
FAIL = []
md = []


def fail(msg):
    FAIL.append(msg)
    md.append(f"- **FAIL**: {msg}")


def read_lines(path):
    """Lines as java.io.BufferedReader.readLine returns them (terminators \\n, \\r, \\r\\n)."""
    with open(path, "rb") as fh:
        txt = fh.read().decode("utf-8")
    parts = re.split(r"\r\n|\r|\n", txt)
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def java_trim(s):
    return s.strip("".join(chr(c) for c in range(0x21)))


def parse_value(line, provider):
    """Value the Java reader extracts from one line, before the division by 100."""
    p = M.PROVIDERS[provider]
    fields = line.split(p["sep"])
    if len(fields) <= p["col"]:
        raise ValueError(f"only {len(fields)} fields")
    s = fields[p["col"]]
    if provider == "materna":
        s = s.replace('"', "\0").replace(",", ".")
    s = java_trim(s)
    if not PLAIN.match(s):
        raise ValueError(f"not a plain decimal number: {s!r}")
    v = float(s)
    if math.isnan(v) or math.isinf(v):
        raise ValueError(f"non-finite: {s!r}")
    return v


def java_read(path, provider, start):
    """(values, raw rows) the reader takes: header skipped, `start` rows skipped, 288 rows read."""
    lines = read_lines(path)
    pos = 1 + start
    if pos + M.NUM_SAMPLES > len(lines):
        raise EOFError(f"{len(lines) - 1} data rows, needs {start + M.NUM_SAMPLES}")
    raw = lines[pos:pos + M.NUM_SAMPLES]
    return [parse_value(ln, provider) for ln in raw], raw


def files_of(folder):
    return sorted(os.listdir(folder))


def sha1(path):
    with open(path, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def acc_diff(v):
    return sum(abs(b - a) for a, b in zip(v, v[1:]))


def check_folder(provider, folder_name, start, label):
    """Structure, values and statistics of one trace folder of the original project."""
    p = M.PROVIDERS[provider]
    folder = os.path.join(M.ORIG_WORKLOADS, p["wtype"], folder_name)
    sim_folder = os.path.join(M.ORIG_WORKLOADS, p["wtype"], p["sim"])
    names = files_of(folder)
    md.append(f"### {label}: `{p['wtype']}/{folder_name}` (dataStartStep {start})")
    md.append("")
    extra = [n for n in names if not n.endswith(".csv") or os.path.isdir(os.path.join(folder, n))]
    md.append(f"- files: {len(names)} (all `.csv`: {not extra}); the simulator takes the first 100 after sorting "
              f"the names: first `{names[0]}`, last `{names[-1]}`")
    if len(names) != 100 or extra:
        fail(f"{label}: {len(names)} entries, extra {extra}")
    sim_header = read_lines(os.path.join(sim_folder, files_of(sim_folder)[0]))[0]
    headers, nrows, nfields_bad, vals, raws = set(), [], 0, {}, {}
    for n in names:
        lines = read_lines(os.path.join(folder, n))
        headers.add(lines[0])
        nrows.append(len(lines) - 1)
        nf = len(lines[0].split(p["sep"]))
        nfields_bad += sum(1 for ln in lines[1:] if len(ln.split(p["sep"])) != nf)
        try:
            vals[n], raws[n] = java_read(os.path.join(folder, n), provider, start)
        except Exception as ex:  # noqa: BLE001
            fail(f"{label}/{n}: reader would fail: {ex}")
    hdr = next(iter(headers))
    cols = hdr.split(p["sep"])
    md.append(f"- header: {len(headers)} distinct; identical to the simulated trace `{p['sim']}`: "
              f"{headers == {sim_header}}; {len(cols)} fields; field {p['col']} = `{cols[p['col']]}`")
    if headers != {sim_header} or cols[p["col"]] != p["colname"]:
        fail(f"{label}: header differs from the simulated trace or wrong column name")
    md.append(f"- data rows per file: min {min(nrows)}, max {max(nrows)} (needed: dataStartStep + 288 = "
              f"{start + M.NUM_SAMPLES}); rows with a different number of fields: {nfields_bad}")
    if min(nrows) < start + M.NUM_SAMPLES or nfields_bad:
        fail(f"{label}: too few rows or ragged rows")
    allv = [x for v in vals.values() for x in v]
    md.append(f"- values read (column `{p['colname']}`, {len(vals)} files x {M.NUM_SAMPLES}): "
              f"{len(allv)} parsed, none empty/NaN/infinite; min {min(allv):.3f}, max {max(allv):.3f}, "
              f"values > 100: {sum(1 for x in allv if x > 100)}, < 0: {sum(1 for x in allv if x < 0)}")
    # which rows: Materna time stamps / Alibaba index column
    if provider == "materna":
        days = set()
        ok = True
        for n, raw in raws.items():
            ts = [r.split(";")[0] for r in raw]
            days |= {t.split(" ")[0] for t in ts}
            want = [f"{h:02d}:{m:02d}:00" for h in range(24) for m in range(0, 60, 5)]
            ok &= [t.split(" ")[1] for t in ts] == want
        md.append(f"- rows read: time stamps {sorted(days)} from 00:00:00 to 23:55:00 every 5 min in every file: {ok}")
        if not ok or len(days) != 1:
            fail(f"{label}: the rows read are not one calendar day")
    else:
        firsts, lasts, ok = set(), set(), True
        for n, raw in raws.items():
            idx = [int(r.split(",")[0]) for r in raw]
            tsv = [int(float(r.split(",")[1])) for r in raw]
            firsts.add(idx[0])
            lasts.add(idx[-1])
            ok &= idx == list(range(idx[0], idx[0] + M.NUM_SAMPLES)) and tsv == [(i + 1) * 300 for i in idx]
        f0, l0 = min(firsts), max(lasts)
        md.append(f"- rows read: index column {sorted(firsts)} to {sorted(lasts)} in every file, consecutive, "
                  f"time_stamp = (index + 1) x 300 s: {ok}; time stamps {(f0 + 1) * 300} to {(l0 + 1) * 300} s "
                  f"(elapsed {(f0 + 1) * 300 / 86400:.4f} d to {(l0 + 1) * 300 / 86400:.4f} d from the start of the trace)")
        if not ok or len(firsts) != 1:
            fail(f"{label}: rows read are not the same consecutive window in every file")
    # statistics
    med = [st.median(v) for v in vals.values()]
    acc = [acc_diff(v) for v in vals.values()]
    stats = dict(mean=st.mean(allv), sd=st.stdev(allv), vm_mean_sd=st.stdev([st.mean(v) for v in vals.values()]),
                 med=st.median(med), med_sd=st.stdev(med), acc=st.median(acc), acc_sd=st.stdev(acc),
                 n=len(allv))
    md.append(f"- statistics of the values read: mean {stats['mean']:.2f} %, SD {stats['sd']:.2f} % (pooled, "
              f"{stats['n']} values); median of per-VM medians {stats['med']:.1f} +- {stats['med_sd']:.1f}; "
              f"median of per-VM accumulated difference {stats['acc']:.0f} +- {stats['acc_sd']:.0f}")
    md.append("")
    return dict(label=label, names=names, raws=raws, vals=vals, stats=stats, folder=folder)


def check_selection(provider, trace, res):
    """Re-derive the mostDiff subset (author's notebooks alibaba2018_wl_filter / materna_wl_filter_selection)."""
    p = M.PROVIDERS[provider]
    if provider == "materna":
        src = os.path.join(M.ORIG_WORKLOADS, "materna", trace["source"])
        window = (0, 288)
        rule = "accumulated |diff| of `CPU usage [%]` over the 288 rows of each file"
    else:
        src = os.path.join(M.ORIG_WORKLOADS, "alibaba2018", "fixed_first_500")
        first = max(0, trace["day_index"] * 288 - 1)
        window = (first, first + 289)
        rule = (f"accumulated |diff| of `cpu_util_percent` over data rows {window[0]}..{window[1] - 1} "
                f"(notebook: day = {trace['day_index']}, first_step = max(0, day*288-1), data[first_step:first_step+289])")
    scores = []
    for n in files_of(src):
        lines = read_lines(os.path.join(src, n))[1:]
        v = []
        for ln in lines[window[0]:window[1]]:
            s = ln.split(p["sep"])[p["col"]].replace(",", ".") if provider == "materna" else ln.split(",")[2]
            v.append(float(s))
        scores.append((acc_diff(v), n))
    scores.sort(key=lambda x: -x[0])
    top = {n for _, n in scores[:100]}
    ok = top == set(res["names"])
    md.append(f"- selection ({trace['label']}): top 100 of the {len(scores)} files of `{os.path.basename(src)}` by {rule} "
              f"== the 100 files of the folder: {ok} (score of #100 {scores[99][0]:.2f}, #101 "
              f"{scores[100][0] if len(scores) > 100 else float('nan'):.2f})")
    if not ok:
        fail(f"{trace['label']}: the folder is not the mostDiff top 100")


def check_alibaba_rows(trace, res):
    """The 288 rows read from the `_final` folder (dataStartStep 0) are rows first_index.. of the
    full-length copy and of the source file; equivalent dataStartStep in the full-length copy."""
    full = os.path.join(M.ORIG_WORKLOADS, "alibaba2018", trace["full"])
    src = os.path.join(M.ORIG_WORKLOADS, "alibaba2018", "fixed_first_500")
    k = trace["first_index"]
    same_full = same_src = same_vals = 0
    eof_next = []
    for n, raw in res["raws"].items():
        fl = read_lines(os.path.join(full, n))[1:]
        sl = read_lines(os.path.join(src, n))[1:]
        same_full += fl[k:k + M.NUM_SAMPLES] == raw
        same_src += sl[k:k + M.NUM_SAMPLES] == raw
        v_full, _ = java_read(os.path.join(full, n), "alibaba", k)
        same_vals += v_full == res["vals"][n]
        try:
            java_read(os.path.join(full, n), "alibaba", k + 1)
        except EOFError:
            eof_next.append(n)
    n = len(res["raws"])
    md.append(f"- proof ({trace['label']}): rows read from `{trace['folder']}` with dataStartStep 0 == rows "
              f"{k}..{k + 287} of `{trace['full']}`: {same_full}/{n} files; == the same rows of the source "
              f"`fixed_first_500`: {same_src}/{n}; values read with dataStartStep {k} from `{trace['full']}` == values "
              f"read from `{trace['folder']}` with dataStartStep 0: {same_vals}/{n}")
    cal0 = trace["day_index"] * 288
    md.append(f"  calendar day {trace['day_index'] + 1} of the trace = index {cal0}..{cal0 + 287} (time stamps "
              f"{(cal0 + 1) * 300} to {(cal0 + 288) * 300} s); window read = index {k}..{k + 287}, i.e. it starts "
              f"{cal0 - k} samples ({(cal0 - k) * 5} min) earlier; with dataStartStep {k + 1} on `{trace['full']}` "
              f"{len(eof_next)} file(s) would run out of rows: {eof_next}")
    if same_full != n or same_src != n or same_vals != n:
        fail(f"{trace['label']}: rows read are not the expected rows of the full-length/source files")


def check_copy(provider, folder_name):
    p = M.PROVIDERS[provider]
    a = os.path.join(M.ORIG_WORKLOADS, p["wtype"], folder_name)
    b = os.path.join(PKGW, p["wtype"], folder_name)
    if not os.path.isdir(b):
        fail(f"copy missing: workloads/{p['wtype']}/{folder_name} (run tools/mt_copy_workloads.sh)")
        return
    na, nb = files_of(a), files_of(b)
    same = na == nb and all(sha1(os.path.join(a, n)) == sha1(os.path.join(b, n)) for n in na)
    md.append(f"- `workloads/{p['wtype']}/{folder_name}`: {len(nb)} files, byte-identical to the original: {same}")
    if not same:
        fail(f"pkg copy of {folder_name} differs from the original")


md += ["# Additional traces of the robustness check: read-only verification", "",
       "Generated by `tools/mt_check_traces.py` (read-only on the traces). Reader emulated from "
       "`UtilizationModelPlanetLabInMemory` (header skipped, dataStartStep rows skipped, 288 rows read, last "
       "value duplicated), `UtilizationModelMaternaInMemory` (`split(\";\")[4]`, decimal comma) and "
       "`UtilizationModelAlibaba2018InMemory` (`split(\",\")[2]`). Original folders: `" + M.ORIG_WORKLOADS + "`.", ""]

RES = {}
md += ["## 1. Structure, values and rows read", ""]
for prov in ("materna", "alibaba"):
    p = M.PROVIDERS[prov]
    RES[("sim", prov)] = check_folder(prov, p["sim"], 0, f"{prov.capitalize()} simulated trace")
    for t in [t for t in M.TRACES if t["provider"] == prov]:
        RES[t["key"]] = check_folder(prov, t["folder"], t["start"], t["label"])

md += ["## 2. Which rows are read, and the selection rule", ""]
for t in M.TRACES:
    if t["provider"] == "alibaba":
        check_alibaba_rows(t, RES[t["key"]])
for t in M.TRACES:
    check_selection(t["provider"], t, RES[t["key"]])
md.append("")

md += ["## 3. CPU statistics of the values the simulator reads (288 samples x 100 VMs)", "",
       "Pooled mean and SD over the 28 800 values; per-VM medians and accumulated differences as in the "
       "manuscript's workload table (median over the VMs +- SD over the VMs).", "",
       "| trace | folder | mean (%) | SD (%) | SD of per-VM means (%) | median of per-VM median (%) | median of per-VM accumulated difference |",
       "|---|---|---|---|---|---|---|"]
for prov in ("materna", "alibaba"):
    for key in [("sim", prov)] + [t["key"] for t in M.TRACES if t["provider"] == prov]:
        r = RES[key]
        s = r["stats"]
        md.append(f"| {r['label']} | `{os.path.basename(r['folder'])}` | {s['mean']:.2f} | {s['sd']:.2f} | "
                  f"{s['vm_mean_sd']:.2f} | {s['med']:.1f} +- {s['med_sd']:.1f} | {s['acc']:.0f} +- {s['acc_sd']:.0f} |")
md += ["", "Self-check: for the simulated traces the last two columns must equal the manuscript's workload table "
       "(`analysis/out/tables/tab_workload_stats.tex`: Alibaba 32.3 +- 5.3 and 1343 +- 132; Materna 5.3 +- 6.4 and "
       "518 +- 631).", ""]
PUB = {"alibaba": (32.3, 5.3, 1343, 132), "materna": (5.3, 6.4, 518, 631)}
for prov, want in PUB.items():
    s = RES[("sim", prov)]["stats"]
    got = (round(s["med"], 1), round(s["med_sd"], 1), round(s["acc"]), round(s["acc_sd"]))
    if got != want:
        fail(f"{prov}: statistics of the simulated trace {got} != manuscript {want}")

md += ["## 4. Copies used by the container (`workloads`)", ""]
for prov in ("materna", "alibaba"):
    check_copy(prov, M.PROVIDERS[prov]["sim"])
for t in M.TRACES:
    check_copy(t["provider"], t["folder"])
md += ["", f"Result: {'all checks passed' if not FAIL else str(len(FAIL)) + ' check(s) FAILED'}.", ""]

with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(md) + "\n")
print("\n".join(md))
print(f"\nwritten {OUT}")
sys.exit(1 if FAIL else 0)
