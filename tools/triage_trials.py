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


def read_log(inputs):
    """The Log sheet of edit_register.xlsx as header-keyed rows (dates as ISO strings)."""
    import openpyxl
    ws = openpyxl.load_workbook(inputs / "edit_register.xlsx", data_only=True)["Log"]
    head = [c.value for c in ws[1]]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        rows.append({h: (v.date().isoformat() if hasattr(v, "date") and callable(v.date) else str(v))
                     for h, v in zip(head, r)})
    return rows


def solve(inputs, select="latest", any_deferred=False, no_floor=False, floor_takes_no_line=False,
          deferred_counts=False, exclusive_end=False, geometry_first=False):
    """One solver, one switch per wrong reading.

    select: which register lines decide a passage's edits
      latest         each edit stands as its latest line; every such edit counts (the gold)
      every_line     every line is an edit in its own right (re-logged edits counted again); also what
                     folding the second read onto the Tally as additions gives on this fixture
      tally_only     the first read's standing (the Tally sheet), second read ignored
      first_line     each edit stands as its FIRST line (the first-read state)
      passage_last   one line per passage: the passage's last line wins (a passage_id dict)
      passage_first  one line per passage: its first line wins
      row_per_edit   latest line per edit, but one register row per edit (a left join)
    any_deferred: a passage with a DEFERRED line anywhere in its history counts as deferred
    """
    ledger = list(csv.DictReader(io.open(inputs / "passage_ledger.csv", encoding="utf-8")))
    register = read_log(inputs)
    if select == "every_line":
        chosen = register
    elif select == "tally_only":
        second = min(e["logged_on"] for e in register if e["logged_on"] >= "2026-09")
        chosen = list({e["edit_code"]: e for e in register if e["logged_on"] < second}.values())
    elif select == "first_line":
        chosen = list({e["edit_code"]: e for e in reversed(register)}.values())
    elif select == "passage_last":
        chosen = list({e["passage_id"]: e for e in register}.values())
    elif select == "passage_first":
        chosen = list({e["passage_id"]: e for e in reversed(register)}.values())
    else:
        chosen = list({e["edit_code"]: e for e in register}.values())
    edits = {}
    for e in chosen:
        edits.setdefault(e["passage_id"], []).append(e)
    ever_deferred = {e["passage_id"] for e in register if e["edit_state"] == "DEFERRED"}
    units = []  # (passage_id, drafted, [edits]) -- one per ledger line, or one per joined edit
    for p in ledger:
        mine = edits.get(p["passage_id"], [])
        if select == "row_per_edit" and len(mine) > 1:
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
        deferred = any(e["edit_state"] == "DEFERRED" for e in mine) or (any_deferred and pid in ever_deferred)
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
    "W1 every line counts / 2nd read added onto Tally": dict(select="every_line"),
    "W1b Tally only (2nd read ignored)": dict(select="tally_only"),
    "W2 first line per edit": dict(select="first_line"),
    "W3 last line per passage (dict)": dict(select="passage_last"),
    "W4 first line per passage": dict(select="passage_first"),
    "W5 one row per edit": dict(select="row_per_edit"),
    "W6 any DEFERRED line = deferred": dict(any_deferred=True),
    "W7 no floor": dict(no_floor=True),
    "W8 floor line not counted": dict(floor_takes_no_line=True),
    "W9 deferred counted": dict(deferred_counts=True),
    "W10 last line one past": dict(exclusive_end=True),
    "W11 geometry above deferred": dict(geometry_first=True),
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
