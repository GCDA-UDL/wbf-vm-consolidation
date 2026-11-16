#!/usr/bin/env python3
"""Draws the simulated network from its topology file and reports its structure.

Layers are derived from the graph, not assumed: CENTRAL nodes are the core switches; TREE
nodes adjacent to a core switch are aggregation switches; TREE nodes adjacent to a LEAF
are edge switches; LEAF nodes are the hosts.  A pod is a connected component of the graph
without the core switches.  Read-only on the topology file.  Usage:
  python -B fig_topology.py --topology <file.json> --out <dir> [--preview <dir>] [--note <file.md>]
"""
import argparse
import collections
import json

import figstyle as S

ap = argparse.ArgumentParser()
ap.add_argument("--topology", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--preview", default=None)
ap.add_argument("--note", default=None)
a = ap.parse_args()

d = json.load(open(a.topology, encoding="utf-8"))
typ = {n["id"]: n["type"] for n in d["nodes"]}
und = {}
for l in d["links"]:
    und[(min(l["source"], l["end"]), max(l["source"], l["end"]))] = (l["weight"], l["linkType"])
adj = collections.defaultdict(set)
for (u, v) in und:
    adj[u].add(v)
    adj[v].add(u)

core = sorted(i for i, t in typ.items() if t == "CENTRAL")
hosts = sorted(i for i, t in typ.items() if t == "LEAF")
tree = [i for i, t in typ.items() if t == "TREE"]
agg = sorted(i for i in tree if any(typ[j] == "CENTRAL" for j in adj[i]))
edge = sorted(i for i in tree if any(typ[j] == "LEAF" for j in adj[i]))
assert not (set(agg) & set(edge)) and len(agg) + len(edge) == len(tree)

# pods: connected components once the core switches are removed
seen, pods = set(), []
for s in sorted(agg):
    if s in seen:
        continue
    comp, q = {s}, [s]
    for u in q:
        for v in adj[u]:
            if typ[v] != "CENTRAL" and v not in comp:
                comp.add(v)
                q.append(v)
    seen |= comp
    pods.append(comp)


def bfs(s):
    dist, q = {s: 0}, [s]
    for u in q:
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


pairs = collections.Counter()
for i, h in enumerate(hosts):
    dh = bfs(h)
    for g in hosts[i + 1:]:
        pairs[dh[g]] += 1
npairs = sum(pairs.values())
mean_len = sum(k * v for k, v in pairs.items()) / npairs
wclass = collections.Counter()
for (u, v), (w, lt) in und.items():
    kind = "host-edge" if "LEAF" in (typ[u], typ[v]) else \
        ("aggregation-core" if "CENTRAL" in (typ[u], typ[v]) else "edge-aggregation")
    wclass[(kind, w, lt)] += 1

report = [
    f"Topology file: {a.topology}",
    f"info block: {d['info']}",
    f"hosts: {len(hosts)}; switches: {len(core) + len(agg) + len(edge)} "
    f"(core {len(core)}, aggregation {len(agg)}, edge {len(edge)}); pods: {len(pods)} "
    f"(each with {len([i for i in pods[0] if i in agg])} aggregation and "
    f"{len([i for i in pods[0] if i in edge])} edge switches and "
    f"{len([i for i in pods[0] if i in hosts])} hosts)",
    f"links: {len(und)} undirected ({len(d['links'])} directed entries): " + "; ".join(
        f"{n} {kind} (weight {w}, {lt})" for (kind, w, lt), n in sorted(wclass.items())),
    "degree: " + "; ".join(f"{name} {sorted({len(adj[i]) for i in grp})}" for name, grp in
                           [("core", core), ("aggregation", agg), ("edge", edge), ("host", hosts)]),
    "host-to-host shortest path, in links (the simulator sets every link weight to 1 in "
    "TopologyHostDistanceManager and uses this value as the migration distance): " + "; ".join(
        f"{k} links for {v} host pairs" for k, v in sorted(pairs.items())) +
    f"; mean over the {npairs} pairs {mean_len:.2f}",
]
print("\n".join(report))
if a.note:
    with open(a.note, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Simulated topology (from the topology file)\n\n" + "\n".join("- " + r for r in report) + "\n")

# ----------------------------------------------------------------------------- drawing
S.apply()
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.lines import Line2D                  # noqa: E402
from matplotlib.patches import FancyBboxPatch        # noqa: E402

pods.sort(key=min)
pos = {}
x = 0.0
PITCH, GAP = 1.0, 0.55          # host pitch and extra gap between pods
for comp in pods:
    p_edge = sorted(i for i in comp if i in edge)
    x0 = x
    for e in p_edge:
        hs = sorted(j for j in adj[e] if typ[j] == "LEAF")
        for h in hs:
            pos[h] = (x, 0.0)
            x += PITCH
        pos[e] = (sum(pos[h][0] for h in hs) / len(hs), 1.0)
    x1 = x - PITCH
    p_agg = sorted(i for i in comp if i in agg)
    for k, g in enumerate(p_agg):       # aggregation switches above the edge switches of the pod
        pos[g] = (pos[p_edge[min(k, len(p_edge) - 1)]][0], 2.0)
    x += GAP
width = x - GAP - PITCH
for k, c in enumerate(core):
    pos[c] = (width * (k + 1) / (len(core) + 1), 3.25)

fig, ax = plt.subplots(figsize=(S.COL1, 54 * S.MM))
for (u, v), (w, lt) in und.items():
    host_link = "LEAF" in (typ[u], typ[v])
    ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color=S.INK2,
            linewidth=0.6 if host_link else 1.3, zorder=1, solid_capstyle="round")
for comp in pods:
    xs = [pos[i][0] for i in comp if typ[i] == "TREE"]
    ax.add_patch(FancyBboxPatch((min(xs) - 0.55, 0.62), max(xs) - min(xs) + 1.1, 1.76,
                                boxstyle="round,pad=0,rounding_size=0.25", fill=False,
                                edgecolor=S.INK2, linewidth=0.6, linestyle=(0, (3, 2)), zorder=0))
for grp, col in [(core, "#52514e"), (agg, "#9a9993"), (edge, "#e4e3df")]:
    ax.scatter([pos[i][0] for i in grp], [pos[i][1] for i in grp], s=34, marker="o", color=col,
               edgecolor=S.INK, linewidth=0.6, zorder=3)
ax.scatter([pos[i][0] for i in hosts], [pos[i][1] for i in hosts], s=26, marker="s",
           color=S.C_FAMILY["WP"], edgecolor=S.INK, linewidth=0.6, zorder=3)
for y, lab in [(3.25, f"Core ({len(core)})"), (2.0, f"Aggregation ({len(agg)})"),
               (1.0, f"Edge ({len(edge)})"), (0.0, f"Hosts ({len(hosts)})")]:
    ax.text(-0.9, y, lab, ha="right", va="center")
ax.legend(handles=[Line2D([], [], color=S.INK2, linewidth=1.3, label="Switch–switch link"),
                   Line2D([], [], color=S.INK2, linewidth=0.6, label="Host–edge link"),
                   Line2D([], [], color=S.INK2, linewidth=0.6, linestyle=(0, (3, 2)), label="Pod")],
          loc="lower center", ncol=3, bbox_to_anchor=(0.36, -0.21), handlelength=1.6,
          columnspacing=1.0, handletextpad=0.4)
ax.set_xlim(-0.6, width + 0.6)
ax.set_ylim(-0.35, 3.6)
ax.axis("off")
fig.subplots_adjust(left=0.265, right=0.995, top=0.995, bottom=0.13)
S.save(fig, a.out, a.preview, "fig_topology")
