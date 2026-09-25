#!/usr/bin/env python3
"""Classify every trial of a Harbor job against the gold and the declared wrong readings.

Author tool for the Layer 2 battery; it is not part of the task package. For each trial directory under
the job directory (any folder holding a result.json), it reads the reward, the per-check outcomes and
the exported deliverables (artifacts/app/page_register.csv, artifacts/app/results.json), and says which
reading the delivered answer matches: GOLD, one of the README section 5 wrong readings W1-W8, or
UNMATCHED (read the trajectory by hand). It also prints the rows that differ from the gold.

  python3 tools/triage_trials.py <job_dir> [--task writing-b52-a9-manuscript-page-ledger-recompute]

The first four trials by started_at are the pre-registered lane; the rest are spares.
"""
import argparse
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def solve(inputs, last_wins=False, first_wins=False, row_per_edit=False, no_floor=False,
          floor_takes_no_line=False, deferred_counts=False, exclusive_end=False, geometry_first=False):
    """The same one-switch solver as tests/discrimination.py (kept standalone: no engine import)."""
    ledger = list(csv.DictReader(io.open(inputs / "passage_ledger.csv", encoding="utf-8")))
    register = list(csv.DictReader(io.open(inputs / "edit_register.csv", encoding="utf-8")))
    edits = {}
    for e in register:
        if last_wins:
            edits[e["passage_id"]] = [e]
        elif first_wins:
            edits.setdefault(e["passage_id"], [e])
        else:
            edits.setdefault(e["passage_id"], []).append(e)
    units = []
    for p in ledger:
        mine = edits.get(p["passage_id"], [])
        if row_per_edit and len(mine) > 1:
            units += [(p["passage_id"], int(p["drafted_lines"]), [e]) for e in mine]
        else:
            units.append((p["passage_id"], int(p["drafted_lines"]), mine))

    def page(line):
        return (line - 1) // 30 + 1

    rows, counts, line = [], {"S": 0, "D": 0, "F": 0, "W": 0}, 1
    for pid, drafted, mine in units:
        counted = [e for e in mine if e["edit_state"] == "ACCEPTED" or deferred_counts]
        raw = drafted + sum(int(e["line_change"]) for e in counted)
        floored = raw < 1 and not no_floor
        length = 1 if floored else raw
        occupies = max(raw, 0) if (floored and floor_takes_no_line) else length
        first = line
        last_page = (first - 1 + length) // 30 + 1 if exclusive_end else page(first + length - 1)
        geo = "S" if page(first) != last_page else "W"
        deferred = any(e["edit_state"] == "DEFERRED" for e in mine)
        v = "F" if floored else (("S" if geo == "S" else ("D" if deferred else "W")) if geometry_first
                                 else ("D" if deferred else geo))
        counts[v] += 1
        rows.append((pid, page(first), {"S": "STRADDLES_BREAK", "D": "EDIT_DEFERRED",
                                        "F": "LENGTH_FLOORED", "W": "WHOLLY_ON_PAGE"}[v]))
        line = first + occupies
    return rows, {"straddling_passage_count": counts["S"], "deferred_edit_count": counts["D"],
                  "length_floored_count": counts["F"], "wholly_on_page_count": counts["W"],
                  "final_page_count": page(line - 1)}


READINGS = {
    "GOLD": {},
    "W1 last edit wins (dict overwrite)": dict(last_wins=True),
    "W2 first edit wins": dict(first_wins=True),
    "W3 one row per edit": dict(row_per_edit=True),
    "W4 no floor": dict(no_floor=True),
    "W5 floor line not counted": dict(floor_takes_no_line=True),
    "W6 deferred counted": dict(deferred_counts=True),
    "W7 last line one past": dict(exclusive_end=True),
    "W8 geometry above deferred": dict(geometry_first=True),
}


def delivered(trial):
    app = trial / "artifacts" / "app"
    rows, res = None, None
    try:
        text = (app / "page_register.csv").read_text(encoding="utf-8-sig")
        rows = []
        for r in list(csv.reader(io.StringIO(text)))[1:]:
            if r and r[0].strip():
                try:
                    pg = int(float(r[1].strip()))
                except (ValueError, IndexError):
                    pg = r[1] if len(r) > 1 else None
                rows.append((r[0].strip(), pg, (r[2].strip().upper() if len(r) > 2 else None)))
    except OSError:
        pass
    try:
        res = {k: (int(v) if isinstance(v, (int, float)) else v)
               for k, v in json.loads((app / "results.json").read_text(encoding="utf-8")).items()}
    except (OSError, ValueError, AttributeError):
        pass
    return rows, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job_dir", type=Path)
    ap.add_argument("--task", default="writing-b52-a9-manuscript-page-ledger-recompute")
    args = ap.parse_args()
    inputs = ROOT / args.task / "environment" / "input"
    expected = {name: solve(inputs, **kw) for name, kw in READINGS.items()}
    gold_rows = {r[0]: r for r in expected["GOLD"][0]}

    trials = []
    for result in sorted(args.job_dir.rglob("result.json")):
        trial = result.parent
        if not (trial / "verifier").is_dir() and not (trial / "artifacts").is_dir():
            continue
        r = json.loads(result.read_text(encoding="utf-8"))
        reward = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        exc = (r.get("exception_info") or {}) and (r["exception_info"].get("exception_type") or "exception")
        trials.append((r.get("started_at") or "", trial, reward, exc, r.get("task_checksum", "")[:12]))
    trials.sort(key=lambda t: t[0])

    print("| # | lane | started | trial | checksum | reward | checks | matches | rows differing from gold |")
    print("|---|---|---|---|---|---|---|---|---|")
    for i, (started, trial, reward, exc, checksum) in enumerate(trials, 1):
        rows, res = delivered(trial)
        match = [name for name, (erows, eres) in expected.items()
                 if rows is not None and sorted(rows) == sorted(erows) and res == eres]
        diff = []
        if rows is not None:
            for pid, pg, v in rows:
                g = gold_rows.get(pid)
                if g is None or (pg, v) != g[1:]:
                    diff.append(f"{pid} {pg} {v}")
            if len(rows) != len(gold_rows):
                diff.append(f"{len(rows)} rows")
        checks = "?"
        score = trial / "verifier" / "score.json"
        if score.is_file():
            s = json.loads(score.read_text(encoding="utf-8"))
            checks = f"{s.get('passed')}/{s.get('total')}"
        verdict = ", ".join(match) or ("EXCEPTION " + str(exc) if exc else
                                       ("NO DELIVERABLES" if rows is None and res is None else "UNMATCHED"))
        print(f"| {i} | {'lane' if i <= 4 else 'spare'} | {started[11:19]} | {trial.name} | {checksum} | "
              f"{reward} | {checks} | {verdict} | {'; '.join(diff) or '-'} |")
    lane = [t for t in trials[:4]]
    passes = sum(1 for t in lane if t[2] == 1.0)
    print(f"\nlane (first four by started_at): {passes}/{len(lane)} strict passes; "
          f"all: {sum(1 for t in trials if t[2] == 1.0)}/{len(trials)}")
    print("checksums seen:", sorted({t[4] for t in trials}))


if __name__ == "__main__":
    main()
