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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def solve(inputs, **switches):
    """The gold's own solver (the task's tests/derive_gold.py), one switch per declared wrong reading."""
    sys.path.insert(0, str(inputs.parent.parent / "tests"))
    import derive_gold
    rows, results, _ = derive_gold.solve(inputs, **switches)
    return [tuple(r) for r in rows], results


READINGS = {
    "GOLD": {},
    "W1 withdrawn as deferred": dict(withdrawn_as_deferred=True),
    "W2 revisions ignored": dict(ignore_revisions=True),
    "W3 revert ignored": dict(revert_noop=True),
    "W4 revert to proposed": dict(revert_to_proposed=True),
    "W5 first decision per edit": dict(first_line_only=True),
    "W6 first read only": dict(first_read_only=True),
    "W7 every accepting line again": dict(every_line=True),
    "W8 same-as copies number": dict(same_copies_number=True),
    "W9 ditto = accept": dict(ditto_is_accept=True),
    "W10 ledger in file order (draft_line ignored)": dict(file_order=True),
    "W11 stretches as separate passages": dict(stretch_separate=True),
    "W12 later stretch overwrites": dict(stretch_overwrite=True),
    "W13 no floor": dict(no_floor=True),
    "W14 floor line not counted": dict(floor_takes_no_line=True),
    "W15 deferred counted": dict(deferred_counts=True),
    "W16 last line one past": dict(exclusive_end=True),
    "W17 geometry above deferred": dict(geometry_first=True),
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
