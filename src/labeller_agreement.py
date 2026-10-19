"""
Agreement between the two people who label impact sets (report this in the paper).

Each person fills their OWN copy of the edits file without looking at the other's:
    data/own_edits/labels_A.csv   and   data/own_edits/labels_B.csv
(same columns as candidate_edits.csv; only edit_id and impact_set are used).

Every (edit, requirement) pair is a yes/no decision, so Cohen's kappa is computed over
all 72 requirements for every edit. It also lists the edits you disagree on, so you can
discuss them and write the final agreed impact_set into data/own_edits/edits.csv.

Run:  python src/labeller_agreement.py data/own_edits/labels_A.csv data/own_edits/labels_B.csv
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from common import load_requirements  # noqa: E402


def read(path):
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            eid = row["edit_id"].strip()
            if eid and not eid.startswith("#") and row["impact_set"].strip():
                out[eid] = {
                    r.strip() for r in row["impact_set"].split(";") if r.strip()
                }
    return out


def main(a_path, b_path):
    reqs = list(load_requirements(ROOT / "data/wasp/requirements.json"))
    a, b = read(a_path), read(b_path)
    common = sorted(set(a) & set(b))
    if not common:
        sys.exit("No edits labelled by both people yet.")
    yy = yn = ny = nn = 0
    disagreements = []
    for e in common:
        for r in reqs:
            x, y = r in a[e], r in b[e]
            yy += x and y
            yn += x and not y
            ny += (not x) and y
            nn += (not x) and (not y)
        if a[e] != b[e]:
            disagreements.append((e, sorted(a[e] - b[e]), sorted(b[e] - a[e])))
    n = yy + yn + ny + nn
    po = (yy + nn) / n
    pe = ((yy + yn) / n) * ((yy + ny) / n) + ((ny + nn) / n) * ((yn + nn) / n)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    print(f"Edits labelled by both: {len(common)}")
    print(f"Both said affected: {yy} | only A: {yn} | only B: {ny}")
    print(
        f"Cohen's kappa = {kappa:.2f}  (0.61-0.80 substantial, > 0.80 almost perfect)"
    )
    print(f"Edits with any disagreement: {len(disagreements)}")
    for e, only_a, only_b in disagreements:
        print(f"  {e}: only A -> {only_a or '-'} | only B -> {only_b or '-'}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
