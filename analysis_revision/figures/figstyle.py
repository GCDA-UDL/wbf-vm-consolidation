"""Common style of the revision figures: vector PDF, Type 42 (TrueType) fonts, print sizes.

Sizes are the printed sizes: single column 88 mm, double column 180 mm.  Text is 8 pt at
that size (never below 7 pt), so the figures must be included at their natural width
(\\includegraphics[width=\\columnwidth] or [width=\\textwidth]).
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MM = 1 / 25.4
COL1 = 88 * MM      # single column width [in]
COL2 = 180 * MM     # double column width [in]

# ink and surfaces
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"

# technique groups: classical techniques in neutral grey; the proposed family is one hue,
# light -> dark in the order in which the components are added (WPSP -> WP -> WBP).
# Ordinal ramp: single hue, monotone lightness.
C_CLASSICAL = "#c9c8c2"
C_FAMILY = {"WPSP": "#86b6ef", "WP": "#3987e5", "WBP": "#1c5cab"}

# energy terms and compared methods: categorical hues checked for colour-vision deficiency
# (all pairs); every mark also carries a hatch or a marker shape.
C_ONOFF = "#eb6834"
C_MIG = "#1baf7a"
C_EXEC = "#9ec5f4"
C_METHOD = {"WBP": "#1c5cab", "BB+NeoPro": "#eb6834", "AMOVMC": "#1baf7a", "EUQ-VMC": "#52514e"}
M_METHOD = {"WBP": "o", "BB+NeoPro": "s", "AMOVMC": "^", "EUQ-VMC": "D"}

MAIN_T = ["MU", "MMT", "RS", "MC", "WPSP", "WP", "WBP"]
CLASSICAL = ["MU", "MMT", "RS", "MC"]
WLS = ["planetlab", "alibaba", "materna", "azure"]
WLNAME = {"planetlab": "PlanetLab", "alibaba": "Alibaba", "materna": "Materna", "azure": "Microsoft Azure"}


def tech_color(t):
    return C_FAMILY.get(t, C_CLASSICAL)


def apply():
    plt.rcParams.update({
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "axes.linewidth": 0.6, "axes.edgecolor": INK2, "axes.labelcolor": INK,
        "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.6,
        "legend.frameon": False, "hatch.linewidth": 0.5,
        "lines.linewidth": 1.2, "savefig.facecolor": "white", "figure.facecolor": "white",
    })


def hgrid(ax):
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)


def save(fig, out_dir, preview_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, name + ".pdf"))
    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)
        fig.savefig(os.path.join(preview_dir, name + ".png"), dpi=200)
    plt.close(fig)
    print("written", name + ".pdf")
