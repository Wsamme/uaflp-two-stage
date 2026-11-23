"""Data figures of the final report that had to be redrawn.

fig_gap_box   gap of every protocol run, eight configurations (MINLP removed: its raw results are not available)
fig_layouts   best layouts that exist as stored files, each re-checked by the independent evaluator

Run from anywhere:  python make_figures.py   (writes ../figures/*.pdf and *.png, prints a check log)
"""
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "figures"
RUN = HERE.parents[3] / "项目" / "our-method" / "运行目录"
sys.path.insert(0, str(RUN))
sys.path.insert(0, str(HERE))
from flp import evaluate as ev  # noqa: E402
from flp import instance as fi  # noqa: E402
import collect  # noqa: E402

mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42, "savefig.bbox": "tight",
                     "savefig.pad_inches": 0.03})

LABEL = {"construct": "Construct", "swap": "Swap", "ga": "GA", "sa": "SA", "sa+polish": "SA+P",
         "cro": "CRO", "cro+polish": "CRO+P", "ours": "Ours"}
COL = {"construct": "#8c8c8c", "swap": "#8c8c8c", "ga": "#8c8c8c", "sa": "#e8692f", "sa+polish": "#e8692f",
       "cro": "#1a9e6e", "cro+polish": "#1a9e6e", "ours": "#2a6fd6"}
BUDGET = {"O7": 20, "vC10a": 20, "AB20": 60, "SC30": 60, "Du62": 150}


def gap_box():
    runs = collect.load()
    t = collect.table(runs)
    fig, axs = plt.subplots(1, 5, figsize=(13.2, 3.5))
    rng = np.random.default_rng(0)
    for ax, inst in zip(axs, collect.INSTS):
        ref = collect.REF[inst]
        for k, m in enumerate(collect.METHODS):
            r = t[(m, inst)]
            g = [100 * (c - ref) / ref for c in r["costs"]]
            if len(g) > 1:
                ax.boxplot([g], positions=[k], widths=0.55, whis=(0, 100), showfliers=False,
                           medianprops=dict(color="black", lw=1.0),
                           boxprops=dict(color=COL[m], lw=1.0), whiskerprops=dict(color=COL[m], lw=0.8),
                           capprops=dict(color=COL[m], lw=0.8))
            ax.scatter(k + rng.uniform(-0.16, 0.16, len(g)), g, s=9, color=COL[m], alpha=0.75, lw=0,
                       zorder=3)
            if r["nf"] < r["n"] and r["n"] > 1:
                ax.annotate(f"{r['nf']}/{r['n']}", (k, max(g)), xytext=(0, 5), textcoords="offset points",
                            ha="center", fontsize=7.5)
        ax.set_yscale("symlog", linthresh=0.01, linscale=0.6)
        ticks = [-1, -0.1, 0, 0.1, 1, 10, 100]
        ax.set_yticks(ticks)
        ax.set_yticklabels(["−1", "−0.1", "0", "0.1", "1", "10", "100"])
        ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
        ax.axhline(0, color="black", lw=0.7, ls="--")
        ax.set_xticks(range(len(collect.METHODS)))
        ax.set_xticklabels([LABEL[m] for m in collect.METHODS], rotation=90, fontsize=8)
        ax.set_title(f"{inst} ({BUDGET[inst]} s)", fontsize=9.5)
        ax.grid(axis="y", color="#e6e6e6", lw=0.6)
        ax.set_axisbelow(True)
    axs[0].set_ylabel("Gap to reference value (%)")
    fig.tight_layout(w_pad=1.2)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig_gap_box.{ext}", dpi=300)
    plt.close(fig)
    print("wrote fig_gap_box")


# best layouts with a stored layout file (path relative to results/)
RECORDS = [
    ("O7", "bench", "ours", None, "Ours, protocol run (20 s)"),
    ("vC10a", "bench", "ours", None, "Ours, protocol run (20 s)"),
    ("AB20", "bench", "ours_noelite", None, "Ours (elite pool 1), protocol run (60 s)"),
    ("SC30", "windows_rerun/records_long/ours_SC30_s101.json", None, None, "Ours, long run (1800 s)"),
    ("Du62", "windows_rerun/records_long/du62_seeds_polish/sa+polish_Du62_s209.json", None, None,
     "SA + polish, long run (600 s)"),
]


def best_file(folder, method, inst):
    best = None
    for f in (RUN / "results" / folder).glob(f"{method}_{inst}_s*.json"):
        j = json.load(open(f, encoding="utf8"))
        if j["feasible"] and (best is None or j["cost"] < best[1]["cost"]):
            best = (f, j)
    return best


def layouts():
    fig, axs = plt.subplots(1, 5, figsize=(13.2, 3.6), gridspec_kw=dict(width_ratios=[0.75, 0.62, 1.2, 1.0, 1.0]))
    log = []
    for ax, (inst, src, method, _, how) in zip(axs, RECORDS):
        if method:
            f, j = best_file(src, method, inst)
        else:
            f = RUN / "results" / src
            j = json.load(open(f, encoding="utf8"))
        I = fi.load(inst)
        rects = np.array(j["rects"], float)
        e = ev.evaluate(I, rects)
        ar = np.maximum(rects[:, 2] / rects[:, 3], rects[:, 3] / rects[:, 2])
        log.append(f"{inst}: file={f.relative_to(RUN / 'results')} stored={j['cost']:.6f} "
                   f"recomputed={e['cost']:.6f} feasible={e['feasible']} max_aspect={ar.max():.7f} "
                   f"limit={I.shape_value}")
        cx = rects[:, 0] + rects[:, 2] / 2
        cy = rects[:, 1] + rects[:, 3] / 2
        ax.add_patch(plt.Rectangle((0, 0), I.W, I.H, fc="white", ec="black", lw=1.6, zorder=1))
        for k, (x, y, w, h) in enumerate(rects):
            ax.add_patch(plt.Rectangle((x, y), w, h, fc="#dfe6f2", ec="#5b6f98", lw=0.5, zorder=2))
            if I.n <= 35:
                ax.text(x + w / 2, y + h / 2, str(k + 1), ha="center", va="center",
                        fontsize=7 if I.n <= 20 else 5.5, zorder=4)
        # largest flows: top 15 % of non-zero pairs, at least 5, at most 40 (25 for Du62)
        iu = np.argwhere(np.triu(I.w, 1) > 0)
        vals = I.w[iu[:, 0], iu[:, 1]]
        top = int(np.clip(round(0.15 * len(vals)), 5, 25 if I.n > 60 else 40))
        idx = np.argsort(-vals)[:top]
        vmax = vals[idx].max()
        for a, b in iu[idx]:
            ax.plot([cx[a], cx[b]], [cy[a], cy[b]], color="#d46a33", alpha=0.75,
                    lw=0.4 + 1.8 * I.w[a, b] / vmax, zorder=3)
        ax.set_xlim(-0.02 * I.W, 1.02 * I.W)
        ax.set_ylim(-0.02 * I.H, 1.02 * I.H)
        ax.set_aspect("equal")
        ax.axis("off")
        cost = f"{e['cost']:,.2f}" if inst != "O7" else f"{e['cost']:.4f}"
        ax.set_title(f"{inst}: {cost}\n{how}", fontsize=8.5)
    fig.tight_layout(w_pad=0.6)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig_layouts.{ext}", dpi=300)
    plt.close(fig)
    print("wrote fig_layouts")
    (HERE / "layout_check.log").write_text("\n".join(log) + "\n", encoding="utf8")
    print("\n".join(log))


if __name__ == "__main__":
    gap_box()
    layouts()
