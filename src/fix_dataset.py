"""
Step 0 - Fix the WASP dataset.

What this fixes (compared to the old changes.json):
  1. C6 was missing. The original file has 6 change requests; C6 is restored.
  2. Some requirement IDs had trailing spaces in the impact file ("R16 "). They are trimmed.
  3. Every change now has an explicit OLD text and NEW text, so the edit-size score
     (0 = unchanged, 1 = completely different) can actually be computed.
  4. Every change gets a change_type label (modify / delete) so edit SIZE and edit TYPE
     can be analysed separately instead of being mixed up.

The old/new pairs below are our own annotation, based on reading each change request
next to the requirement it targets. Write this down in the paper's Method section.

Run:  python src/fix_dataset.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIG = ROOT / "data" / "wasp" / "original"
OUT = ROOT / "data" / "wasp"


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ---- manual annotation: which requirement each change edits, and how -------------------
# new_text = ""  means the requirement is deleted completely (a FULL change).
ANNOTATION = {
    "C1": dict(
        target="R26",
        change_type="modify",
        new_text="A WASP application shall be able to setup a phone call connection and a "
        "video chat connection using the 3G Platform via the WASP platform.",
        note="Adds video chat to the phone-call requirement R26.",
    ),
    "C2": dict(
        target="R67",
        change_type="delete",
        new_text="The platform must be able to store POI profiles.",
        note="Removes the 'service profile' part of R67 (rationale: 'Remove service profile functionality').",
    ),
    "C3": dict(
        target="R42",
        change_type="modify",
        new_text="The WASP platform must be able to show the location of users on a map by "
        "marking them with a circle.",
        note="Adds 'marking them with a circle' to R42.",
    ),
    "C4": dict(
        target="R51",
        change_type="modify",
        new_text="The WASP platform should be possible to determine the location of touristic "
        "attractions.",
        note="Drops 'close to a calculated route' from R51 (user may deviate from the route).",
    ),
    "C5": dict(
        target="R16",
        change_type="delete",
        new_text="",
        note="Whole POI feature removed; the main POI requirement R16 is deleted entirely.",
    ),
    "C6": dict(
        target="R25",
        change_type="delete",
        new_text="When changes are discovered in the status of a user's buddy, the WASP platform "
        "must sent out notifications according to the alerts set by the user (see also REQ_NOT_006).",
        note="Removes 'and/or location' from R25 (rationale: remove location tracking). "
        "This change was MISSING from the old changes.json.",
    ),
}


def main():
    reqs = [
        {"Id": r["ID"].strip(), "Requirement": r["Description"].strip()}
        for r in read_csv(ORIG / "W_Requirements_Set.csv")
    ]
    req_text = {r["Id"]: r["Requirement"] for r in reqs}

    impact = {}
    for row in read_csv(ORIG / "WASP_ImpactSet_byChetan.csv"):
        if row["score"].strip() == "1":
            impact.setdefault(row["query-id"].strip(), []).append(
                row["corpus-id"].strip()
            )

    changes = []
    for row in read_csv(ORIG / "WASP_ChangeRequests_byChetan.csv"):
        cid = row["_id"].strip()
        a = ANNOTATION[cid]
        missing = [r for r in impact.get(cid, []) if r not in req_text]
        assert not missing, f"{cid}: impact set has unknown IDs {missing}"
        changes.append(
            {
                "Id": cid,
                "Change Rational": " ".join(
                    row["text"].split()
                ),  # collapse double spaces
                "target_requirement": a["target"],
                "old_text": req_text[a["target"]],
                "new_text": a["new_text"],
                "change_type": a["change_type"],
                "annotation_note": a["note"],
                "Impact Set": impact.get(cid, []),
            }
        )

    (OUT / "requirements.json").write_text(
        json.dumps({"requirements": reqs}, indent=1), encoding="utf-8"
    )
    (OUT / "changes.json").write_text(json.dumps(changes, indent=1), encoding="utf-8")

    pairs = sum(len(c["Impact Set"]) for c in changes)
    distinct = len({r for c in changes for r in c["Impact Set"]})
    print(
        f"requirements: {len(reqs)} | changes: {len(changes)} | "
        f"change-requirement pairs: {pairs} | distinct affected requirements: {distinct}"
    )


if __name__ == "__main__":
    main()
