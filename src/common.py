"""Shared helpers: loading data, edit-size score, text cleaning."""

import csv
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

STOPWORDS = set(
    """a an the and or of to in on for by with be is are must shall should may can
could would will that this these those it its as at from into via his her their he she they
able possible""".split()
)


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


# ---------------- edit size: 0 = text unchanged, 1 = text completely different -------------
def edit_size(old_text, new_text):
    """Word-level difference between old and new wording (1 - similarity ratio).
    A deleted requirement (new_text empty) is a FULL change and scores 1.0."""
    if not new_text.strip():
        return 1.0
    a = re.findall(r"\w+", old_text.lower())
    b = re.findall(r"\w+", new_text.lower())
    return round(1 - SequenceMatcher(None, a, b).ratio(), 4)


# ---------------- data loading (WASP or your own edits, same format) ----------------------
def load_requirements(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {r["Id"]: r["Requirement"] for r in data["requirements"]}


def load_wasp_changes(path):
    out = []
    for c in json.loads(Path(path).read_text(encoding="utf-8")):
        out.append(
            dict(
                id=c["Id"],
                source="WASP",
                query=c["Change Rational"],
                target=c["target_requirement"],
                old_text=c["old_text"],
                new_text=c["new_text"],
                change_type=c["change_type"],
                impact=list(dict.fromkeys(c["Impact Set"])),
                human_label="",
            )
        )
    return out


def load_own_edits(path, req_text):
    """Your own edits, one row per edit (see data/own_edits/edits_template.csv).
    impact_set = requirement IDs separated by ';'  e.g.  R12;R15;R30"""
    out = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("edit_id", "").strip() or row["edit_id"].startswith("#"):
                continue
            target = row["target_requirement"].strip()
            old = row.get("old_text", "").strip() or req_text.get(target, "")
            new = row.get("new_text", "").strip()
            query = (
                row.get("change_description", "").strip()
                or new
                or f"Delete requirement: {old}"
            )
            impact = [r.strip() for r in row["impact_set"].split(";") if r.strip()]
            if not impact:
                print(
                    f"[data] {row['edit_id']}: impact_set is empty - skipped (label it first)"
                )
                continue
            unknown = [r for r in impact + [target] if r not in req_text]
            if unknown:
                raise ValueError(f"{row['edit_id']}: unknown requirement IDs {unknown}")
            out.append(
                dict(
                    id=row["edit_id"].strip(),
                    source="own",
                    query=query,
                    target=target,
                    old_text=old,
                    new_text=new,
                    change_type=row.get("change_type", "").strip()
                    or ("delete" if not new else "modify"),
                    impact=impact,
                    human_label=row.get("human_label", "").strip().lower(),
                )
            )
    return out


def candidates(req_text, change):
    """Requirements the tool may suggest. All requirements are candidates, because in WASP
    the edited requirement itself is counted inside the impact set (e.g. C3 -> R42)."""
    return dict(req_text)
