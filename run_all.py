"""
Runs all three experiments and the evaluation.

  python run_all.py                    # WASP + your own edits (if the file has rows)
  python run_all.py --threshold 0.3    # cut-off for "major" (default 0.30)

Outputs (in results/):
  per_change_results.csv  one row per change x tool, every metric
  summary.md              tables for the paper: RQ1, RQ2, RQ3 + sensitivity analysis
"""

import argparse
import csv
import random
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from scipy.stats import mannwhitneyu, spearmanr  # noqa: E402

import exp1_word_matching  # noqa: E402
import exp2_semantic  # noqa: E402
import exp3_llm  # noqa: E402
from common import (
    RESULTS,
    candidates,
    edit_size,
    load_own_edits,
    load_requirements,
    load_wasp_changes,
)  # noqa: E402

KS = (5, 10)
MIN_GROUP = 3  # below this, statistical tests are not meaningful and are skipped


# ------------------------------------------------------------------ metrics
def metrics(ranking, impact):
    rel = set(impact)
    out = {}
    for k in KS:
        hits = len(rel & set(ranking[:k]))
        out[f"recall@{k}"] = hits / len(rel)
        # FAIR version: divide by the best score possible in a top-k list.
        # A change with 9 affected requirements can never get more than 5/9 in a top-5 list,
        # so plain recall@5 would punish big changes automatically.
        out[f"norm_recall@{k}"] = hits / min(k, len(rel))
        out[f"precision@{k}"] = hits / k
        p_, r_ = hits / k, hits / len(rel)
        out[f"F1@{k}"] = 2 * p_ * r_ / (p_ + r_) if hits else 0.0
    hits, ap = 0, 0.0
    for i, r in enumerate(ranking, 1):
        if r in rel:
            hits += 1
            ap += hits / i
    out["AP"] = ap / len(rel)  # average precision
    out["R-precision"] = len(rel & set(ranking[: len(rel)])) / len(rel)
    return out


def bootstrap_diff(a, b, n=5000, seed=0):
    rng = random.Random(seed)
    diffs = sorted(
        st.mean(rng.choices(a, k=len(a))) - st.mean(rng.choices(b, k=len(b)))
        for _ in range(n)
    )
    return diffs[int(0.025 * n)], diffs[int(0.975 * n)]


def cohen_kappa(x, y):
    labels = sorted(set(x) | set(y))
    n = len(x)
    po = sum(a == b for a, b in zip(x, y)) / n
    pe = sum((x.count(l) / n) * (y.count(l) / n) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def fmt(v):
    return f"{v:.3f}" if isinstance(v, float) else str(v)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.30)
    ap.add_argument("--no-llm", action="store_true", help="skip Experiment 3")
    ap.add_argument(
        "--exclude",
        default="",
        help="change IDs to leave out, e.g. C6 (to match the 5-change WASP benchmark)",
    )
    args = ap.parse_args()
    thr = args.threshold

    req = load_requirements(ROOT / "data/wasp/requirements.json")
    changes = load_wasp_changes(ROOT / "data/wasp/changes.json")
    own = ROOT / "data/own_edits/edits.csv"
    if own.exists():
        changes += load_own_edits(own, req)
    drop = {x.strip() for x in args.exclude.split(",") if x.strip()}
    changes = [c for c in changes if c["id"] not in drop]
    for c in changes:
        c["edit_size"] = edit_size(c["old_text"], c["new_text"])
        c["n_impact"] = len(c["impact"])

    experiments = [exp1_word_matching, exp2_semantic]
    if args.no_llm:
        print("[exp3] skipped (--no-llm)")
    elif exp3_llm.available():
        experiments.append(exp3_llm)
    else:
        print(
            "[exp3] skipped: set GEMINI_API_KEY (see src/exp3_llm.py) to run the Gemini experiment"
        )

    rows = []
    for exp in experiments:
        print(f"Running {exp.NAME} on {len(changes)} changes ...", flush=True)
        for c in changes:
            ranking = exp.rank(c, candidates(req, c))
            m = metrics(ranking, c["impact"])
            rows.append(
                dict(
                    tool=exp.NAME,
                    change=c["id"],
                    source=c["source"],
                    change_type=c["change_type"],
                    edit_size=c["edit_size"],
                    n_impact=c["n_impact"],
                    top10=" ".join(ranking[:10]),
                    **m,
                )
            )
    tools = list(dict.fromkeys(r["tool"] for r in rows))

    with open(
        RESULTS / "per_change_results.csv", "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows({k: fmt(v) for k, v in r.items()} for r in rows)

    # ---------------------------------------------------------- summary report
    L = []
    add = L.append
    n_wasp = sum(c["source"] == "WASP" for c in changes)
    add("# Results summary\n")
    add(
        f"Changes: {len(changes)} ({n_wasp} WASP, {len(changes) - n_wasp} own). "
        f"Major = edit size >= {thr:.2f}. Tools: {', '.join(tools)}.\n"
    )

    add("## The changes\n")
    add("| Change | Type | Edit size | Group | Affected (n) |")
    add("|---|---|---|---|---|")
    for c in changes:
        add(
            f"| {c['id']} | {c['change_type']} | {c['edit_size']:.2f} | "
            f"{'major' if c['edit_size'] >= thr else 'minor'} | {c['n_impact']} |"
        )
    add("")

    # RQ1 ---------------------------------------------------------------------
    add("## RQ1 - Does the edit-size score agree with human judgement?\n")
    labelled = [c for c in changes if c["human_label"] in ("minor", "major")]
    if len(labelled) >= 5:
        auto = ["major" if c["edit_size"] >= thr else "minor" for c in labelled]
        human = [c["human_label"] for c in labelled]
        agree = sum(a == h for a, h in zip(auto, human)) / len(labelled)
        add(
            f"{len(labelled)} edits labelled by hand. Agreement {agree:.0%}, "
            f"Cohen's kappa = {cohen_kappa(auto, human):.2f}.\n"
        )
    else:
        add(
            "Not enough hand labels yet. Fill the `human_label` column (minor/major) in "
            "data/own_edits/edits.csv. Also have the two reviewers label separately and report "
            "their agreement with each other.\n"
        )

    # Overall comparison (all changes together) -------------------------------
    add("## Overall comparison of the three methods (all changes)\n")
    add(
        "Existing method = Exp 1 word matching (baseline). Proposed = Exp 2 semantic, Exp 3 LLM.\n"
    )
    om = ["precision@5", "recall@5", "F1@5", "norm_recall@5", "recall@10", "AP"]
    add("| Method | n | " + " | ".join(m if m != "AP" else "MAP" for m in om) + " |")
    add("|---|---|" + "---|" * len(om))
    for t in tools:
        rs = [r for r in rows if r["tool"] == t]
        add(
            f"| {t} | {len(rs)} | "
            + " | ".join(f"{st.mean(r[m] for r in rs):.2f}" for m in om)
            + " |"
        )
    add("")

    # RQ2 ---------------------------------------------------------------------
    add("## RQ2 - Do tools miss more affected requirements for major edits?\n")
    add(
        "Main metric: **norm_recall@k** (fair to big impact sets). Plain recall@k shown for comparison.\n"
    )
    metric_names = ["recall@5", "norm_recall@5", "recall@10", "norm_recall@10", "AP"]
    add("| Tool | Group | n | " + " | ".join(metric_names) + " |")
    add("|---|---|---|" + "---|" * len(metric_names))
    for t in tools:
        for g in ("minor", "major"):
            rs = [
                r
                for r in rows
                if r["tool"] == t and (r["edit_size"] >= thr) == (g == "major")
            ]
            if rs:
                add(
                    f"| {t} | {g} | {len(rs)} | "
                    + " | ".join(
                        f"{st.mean(r[m] for r in rs):.2f}" for m in metric_names
                    )
                    + " |"
                )
    add("")
    add(
        "Statistical test (Mann-Whitney U, two-sided) and 95% bootstrap CI of the difference "
        "(major minus minor):\n"
    )
    for t in tools:
        for m in ("norm_recall@5", "norm_recall@10", "AP"):
            mi = [r[m] for r in rows if r["tool"] == t and r["edit_size"] < thr]
            ma = [r[m] for r in rows if r["tool"] == t and r["edit_size"] >= thr]
            if len(mi) < MIN_GROUP or len(ma) < MIN_GROUP:
                add(
                    f"- {t} / {m}: skipped (minor n={len(mi)}, major n={len(ma)}; need >= {MIN_GROUP} each)"
                )
                continue
            p = mannwhitneyu(ma, mi, alternative="two-sided").pvalue
            lo, hi = bootstrap_diff(ma, mi)
            add(
                f"- {t} / {m}: diff = {st.mean(ma) - st.mean(mi):+.3f} [{lo:+.3f}, {hi:+.3f}], p = {p:.3f}"
            )
    add("")

    add(
        "### Sensitivity: does the answer change with the cut-off? (norm_recall@5, major minus minor)\n"
    )
    cut = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    add("| Tool | " + " | ".join(f"{x:.2f}" for x in cut) + " |")
    add("|---|" + "---|" * len(cut))
    for t in tools:
        cells = []
        for x in cut:
            mi = [
                r["norm_recall@5"]
                for r in rows
                if r["tool"] == t and r["edit_size"] < x
            ]
            ma = [
                r["norm_recall@5"]
                for r in rows
                if r["tool"] == t and r["edit_size"] >= x
            ]
            cells.append(
                f"{st.mean(ma) - st.mean(mi):+.2f} ({len(mi)}/{len(ma)})"
                if mi and ma
                else "n/a"
            )
        add(f"| {t} | " + " | ".join(cells) + " |")
    add("\n(numbers in brackets = minor/major group sizes)\n")

    add("### By change type (modify vs delete), norm_recall@5\n")
    types = sorted({c["change_type"] for c in changes})
    add("| Tool | " + " | ".join(f"{ty} (n)" for ty in types) + " |")
    add("|---|" + "---|" * len(types))
    for t in tools:
        cells = []
        for ty in types:
            v = [
                r["norm_recall@5"]
                for r in rows
                if r["tool"] == t and r["change_type"] == ty
            ]
            cells.append(f"{st.mean(v):.2f} ({len(v)})")
        add(f"| {t} | " + " | ".join(cells) + " |")
    add("")

    # RQ3 ---------------------------------------------------------------------
    add(
        "## RQ3 - Does the amount of rewritten text predict how many requirements are affected?\n"
    )
    xs = [c["edit_size"] for c in changes]
    ys = [c["n_impact"] for c in changes]
    if len(changes) >= 5 and len(set(xs)) > 1:
        rho, p = spearmanr(xs, ys)
        add(
            f"Spearman rho (edit size vs number affected) = {rho:.2f}, p = {p:.3f}, n = {len(changes)}.\n"
        )
    for ty in types:
        n = [c["n_impact"] for c in changes if c["change_type"] == ty]
        add(f"- {ty}: mean affected = {st.mean(n):.2f} (n = {len(n)})")
    add("")
    add(
        "_With fewer than ~20 changes per group these numbers are a pilot only; "
        "do not claim significance from WASP alone._"
    )

    (RESULTS / "summary.md").write_text("\n".join(L), encoding="utf-8")
    import figures

    figures.make_all(rows, tools, changes, thr)
    print(f"Figures: {figures.FIG}")
    print("\n".join(L))
    print(
        f"\nSaved: {RESULTS / 'per_change_results.csv'}\n       {RESULTS / 'summary.md'}"
    )


if __name__ == "__main__":
    main()
