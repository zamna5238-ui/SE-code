"""Figures for the paper and slides (PNG, 200 dpi) saved in results/figures/."""

import statistics as st

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from common import RESULTS  # noqa: E402

FIG = RESULTS / "figures"
FIG.mkdir(exist_ok=True)
MINOR, MAJOR, THIRD = "#2a78d6", "#eb6834", "#1baf7a"  # validated categorical slots 1-3
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def _short(t):
    return (
        t.replace("exp1_word_matching", "Exp 1\nWord matching")
        .replace("exp2_semantic_LSA-fallback", "Exp 2\nSemantic (LSA fallback)")
        .replace("exp2_semantic", "Exp 2\nSemantic")
        .replace("exp3_llm_gemini", "Exp 3\nLLM (Gemini)")
    )


def recall_by_group(rows, tools, thr, metric="norm_recall@5"):
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    w = 0.36
    for gi, (g, col) in enumerate((("minor", MINOR), ("major", MAJOR))):
        for ti, t in enumerate(tools):
            v = [
                r[metric]
                for r in rows
                if r["tool"] == t and (r["edit_size"] >= thr) == (g == "major")
            ]
            if not v:
                continue
            x = ti + (gi - 0.5) * (w + 0.02)
            ax.bar(
                x,
                st.mean(v),
                w,
                color=col,
                label=f"{g} edits" if ti == 0 else None,
                zorder=2,
            )
            ax.text(
                x,
                st.mean(v) + 0.02,
                f"{st.mean(v):.2f}\n(n={len(v)})",
                ha="center",
                va="bottom",
                fontsize=8,
                color=INK,
            )
    ax.set_xticks(range(len(tools)), [_short(t) for t in tools])
    ax.set_ylim(0, 1.22)
    ax.set_ylabel(metric.replace("norm_recall", "Normalized recall"))
    ax.yaxis.grid(True, color=GRID, zorder=0)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    ax.set_title(
        f"Affected requirements found, minor vs major edits (cut-off {thr:.2f})",
        fontsize=10,
        loc="left",
        color=INK,
    )
    fig.tight_layout()
    fig.savefig(FIG / "fig1_recall_minor_vs_major.png", dpi=200)
    plt.close(fig)


def size_vs_impact(changes):
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for ty, col, mk in (("modify", MINOR, "o"), ("delete", MAJOR, "s")):
        cs = [c for c in changes if c["change_type"] == ty]
        ax.scatter(
            [c["edit_size"] for c in cs],
            [c["n_impact"] for c in cs],
            s=60,
            color=col,
            marker=mk,
            edgecolor="white",
            linewidth=1.5,
            label=ty,
            zorder=3,
        )
    groups = {}
    for c in changes:
        if c["source"] == "WASP":
            groups.setdefault((round(c["edit_size"], 1), c["n_impact"]), []).append(c)
    for cs in groups.values():
        x = st.mean(c["edit_size"] for c in cs)
        ax.annotate(
            ", ".join(c["id"] for c in cs),
            (x, cs[0]["n_impact"]),
            xytext=(8, 5),
            textcoords="offset points",
            fontsize=8,
            color=MUTED,
        )
    ax.set_xlabel("Edit size (0 = unchanged, 1 = completely different)")
    ax.set_ylabel("Affected requirements")
    ax.set_xlim(-0.03, 1.1)
    ax.grid(True, color=GRID, zorder=0)
    ax.legend(frameon=False, title="Change type")
    ax.set_title(
        "Edit size vs number of affected requirements",
        fontsize=10,
        loc="left",
        color=INK,
    )
    fig.tight_layout()
    fig.savefig(FIG / "fig2_edit_size_vs_impact.png", dpi=200)
    plt.close(fig)


def ceiling_effect(rows, tool):
    rs = [r for r in rows if r["tool"] == tool]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = range(len(rs))
    w = 0.36
    ax.bar(
        [i - w / 2 - 0.01 for i in x],
        [r["recall@5"] for r in rs],
        w,
        color=MINOR,
        label="Plain recall@5",
        zorder=2,
    )
    ax.bar(
        [i + w / 2 + 0.01 for i in x],
        [r["norm_recall@5"] for r in rs],
        w,
        color=THIRD,
        label="Normalized recall@5",
        zorder=2,
    )
    for i, r in enumerate(rs):
        cap = min(5, r["n_impact"]) / r["n_impact"]
        if cap < 1:
            ax.plot(
                [i - w - 0.05, i + 0.02],
                [cap, cap],
                color=INK,
                linestyle="--",
                linewidth=1.2,
                zorder=3,
            )
            ax.text(
                i - w / 2,
                cap + 0.03,
                f"max {cap:.2f}",
                ha="center",
                fontsize=7.5,
                color=INK,
            )
    ax.set_xticks(
        list(x), [f"{r['change']}\n|I|={r['n_impact']}" for r in rs], fontsize=8
    )
    ax.set_ylim(0, 1.15)
    ax.yaxis.grid(True, color=GRID, zorder=0)
    ax.legend(frameon=False, loc="upper right", ncol=2, fontsize=8)
    ax.set_title(
        f"Why plain top-5 recall is unfair to large impact sets ({_short(tool).replace(chr(10), ' ')})",
        fontsize=10,
        loc="left",
        color=INK,
    )
    fig.tight_layout()
    fig.savefig(FIG / "fig3_ceiling_effect.png", dpi=200)
    plt.close(fig)


def make_all(rows, tools, changes, thr):
    recall_by_group(rows, tools, thr)
    size_vs_impact(changes)
    ceiling_effect([r for r in rows if r["source"] == "WASP"] or rows, tools[0])
    overall_comparison(rows, tools)


def overall_comparison(
    rows, tools, metrics=("recall@5", "norm_recall@5", "recall@10", "AP")
):
    """Fig 4: all three methods side by side on the main metrics (all changes)."""
    cols = [MINOR, THIRD, MAJOR]
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    w = 0.26
    for ti, t in enumerate(tools):
        vals = [st.mean(r[m] for r in rows if r["tool"] == t) for m in metrics]
        xs = [i + (ti - (len(tools) - 1) / 2) * (w + 0.02) for i in range(len(metrics))]
        ax.bar(
            xs,
            vals,
            w,
            color=cols[ti % 3],
            label=_short(t).replace("\n", " "),
            zorder=2,
        )
        for x, v in zip(xs, vals):
            ax.text(
                x,
                v + 0.015,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=INK,
            )
    ax.set_xticks(
        range(len(metrics)),
        [
            m.replace("norm_recall", "Norm. recall")
            .replace("AP", "MAP")
            .replace("recall", "Recall")
            .replace("Norm. Recall", "Norm. recall")
            for m in metrics
        ],
    )
    ax.set_ylim(0, 1.15)
    ax.yaxis.grid(True, color=GRID, zorder=0)
    ax.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=3,
        fontsize=8.5,
    )
    ax.set_title(
        "Overall comparison of the three methods (all changes)",
        fontsize=10,
        loc="left",
        color=INK,
    )
    fig.tight_layout()
    fig.savefig(FIG / "fig4_overall_comparison.png", dpi=200)
    plt.close(fig)
