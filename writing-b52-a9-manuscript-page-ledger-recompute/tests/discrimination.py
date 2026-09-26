#!/usr/bin/env python3
"""Discrimination harness (VER-24, VER-11, VER-23, HAR-4) for writing-b52-a9.

Builds perturbed copies of the golden deliverables and replays every check of verifier.json on each
through the vendored engine: no judge, no network. Every equivalence variant (11.1) must pass every
check; every breaking variant (11.2) and every declared wrong reading (README section 5) must fail, on
the check written for it.

The wrong readings are not typed in: each is recomputed from the shipped inputs by the gold's own solver
(tests/derive_gold.py) with one rule switched, so editing the fixture cannot leave this harness testing a
wrong answer that no longer follows from the data.

Run inside the task image, from the package root:
  docker build -t b52a9 environment/
  docker run --rm --network none -v "$PWD/tests:/tests:ro" \\
      -v "$PWD/solution/files:/gold:ro" -v "$PWD/environment/input:/inputs:ro" \\
      b52a9 python3 /tests/discrimination.py
"""
import csv
import io
import json
import os
import random
import shutil
import sys
import tempfile
from pathlib import Path

TESTS = Path(os.environ.get("B52A9_TESTS", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS))
from rl_world_verifiers.models import VerifierSpec, effective_weights  # noqa: E402
from rl_world_verifiers.sources.registry import SourceRegistry  # noqa: E402
from rl_world_verifiers.verifiers import verify_definition  # noqa: E402

GOLD = Path(os.environ.get("B52A9_GOLD", "/gold"))
INPUTS = Path(os.environ.get("B52A9_INPUTS", "/inputs"))
SPEC = VerifierSpec.model_validate_json((TESTS / "verifier.json").read_text(encoding="utf-8"))
WEIGHTS = effective_weights(SPEC.verifiers)
HEADER = ["passage_id", "page_number", "verdict"]
G_CSV = (GOLD / "page_register.csv").read_text(encoding="utf-8")
G_JSON = json.loads((GOLD / "results.json").read_text(encoding="utf-8"))


# --- one solver over the shipped inputs, one rule switchable per wrong reading ----------------------
def solve(inputs, **switches):
    """The one solver (tests/derive_gold.py), with one switch per declared wrong reading."""
    import derive_gold
    rows, results, _ = derive_gold.solve(inputs, **switches)
    return rows, results


def render(rows):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(HEADER)
    w.writerows(rows)
    return out.getvalue()


def failing(csv_text=None, json_obj=None, extra=None, drop=(), raw_json=None):
    ws = Path(tempfile.mkdtemp())
    try:
        if "page_register.csv" not in drop:
            (ws / "page_register.csv").write_text(csv_text if csv_text is not None else G_CSV,
                                                  encoding="utf-8", newline="")
        if "results.json" not in drop:
            (ws / "results.json").write_text(
                raw_json if raw_json is not None else json.dumps(json_obj if json_obj is not None else G_JSON),
                encoding="utf-8")
        for name, content in (extra or {}).items():
            (ws / name).write_text(content, encoding="utf-8")
        reg = SourceRegistry(ws)
        return sorted(d.name for d in SPEC.verifiers
                      if not verify_definition(d, reg, WEIGHTS[d.name], config=SPEC.config,
                                               completion_fn=None)["result"]["success"])
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def body():
    return [r for r in csv.reader(io.StringIO(G_CSV))][1:]


def main():
    gold_rows, gold_res = solve(INPUTS)
    assert render(gold_rows) == G_CSV and gold_res == G_JSON, "solver does not reproduce the gold"
    rows = body()
    rnd = random.Random(52)
    bad = []

    def expect(label, failed, must):
        ok = (not failed) if must is None else (bool(failed) and set(must) <= set(failed))
        print(f"  {'ok  ' if ok else 'BAD '} {label}: failed={failed}"
              + ("" if must is None else f" (must include {must})"))
        if not ok:
            bad.append(label)

    def edit(pid, col, value):
        out = [r[:] for r in rows]
        out[next(k for k, r in enumerate(out) if r[0] == pid)][col] = value
        return out

    print("11.1 equivalence suite: must pass every check")
    shuffled = rows[:]
    rnd.shuffle(shuffled)
    expect("E1 shuffle row order", failing(render(shuffled)), None)
    expect("E2 reorder JSON keys", failing(json_obj=dict(reversed(list(G_JSON.items())))), None)
    expect("E3 JSON figures written N.0", failing(json_obj={k: float(v) for k, v in G_JSON.items()}), None)
    expect("E4 quote every CSV field",
           failing("\n".join(",".join(f'"{c}"' for c in r) for r in [HEADER] + rows) + "\n"), None)
    expect("E5 LF to CRLF", failing(G_CSV.replace("\n", "\r\n")), None)
    expect("E6 strip the trailing newline", failing(G_CSV.rstrip("\n")), None)
    expect("E7 prepend a UTF-8 BOM", failing("﻿" + G_CSV), None)
    expect("E8 page numbers written N.0", failing(render([[r[0], f"{r[1]}.0", r[2]] for r in rows])), None)
    expect("E9 pad fields with spaces", failing("\n".join(", ".join(r) for r in [HEADER] + rows) + "\n"), None)
    expect("E10 verdicts in lower case", failing(render([[r[0], r[1], r[2].lower()] for r in rows])), None)
    expect("E11 add an unrelated scratch file", failing(extra={"scratch.py": "print(1)\n"}), None)

    print("11.2 breaking suite: must fail on the check written for it")
    expect("B1 one page off (PS-09 +1)", failing(render(edit("PS-09", 1, str(int(dict((r[0], r[1]) for r in rows)["PS-09"]) + 1)))),
           ["register_rows"])
    expect("B2 one verdict wrong (PS-06 EDIT_DEFERRED -> WHOLLY_ON_PAGE)",
           failing(render(edit("PS-06", 2, "WHOLLY_ON_PAGE"))), ["register_rows"])
    expect("B3 delete one row (PS-12)", failing(render([r for r in rows if r[0] != "PS-12"])), ["register_rows"])
    expect("B4 append a spurious row (PS-41)", failing(render(rows + [["PS-41", "18", "WHOLLY_ON_PAGE"]])),
           ["register_rows"])
    expect("B5 duplicate a row (PS-05)", failing(render(rows + [r for r in rows if r[0] == "PS-05"])),
           ["register_rows"])
    expect("B6 an extra column", failing(render([r + ["x"] for r in rows]).replace("verdict\n", "verdict,note\n", 1)),
           ["register_rows"])
    expect("B7.1 PS-04 verdict EDIT_DEFERRED -> WHOLLY_ON_PAGE", failing(render(edit("PS-04", 2, "WHOLLY_ON_PAGE"))), ["register_trap_ps04"])
    expect("B7.2 PS-07 verdict LENGTH_FLOORED -> WHOLLY_ON_PAGE", failing(render(edit("PS-07", 2, "WHOLLY_ON_PAGE"))), ["register_trap_ps07"])
    expect("B7.3 PS-10 verdict WHOLLY_ON_PAGE -> STRADDLES_BREAK", failing(render(edit("PS-10", 2, "STRADDLES_BREAK"))), ["register_trap_ps10"])
    expect("B7.4 PS-16 verdict STRADDLES_BREAK -> WHOLLY_ON_PAGE", failing(render(edit("PS-16", 2, "WHOLLY_ON_PAGE"))), ["register_trap_ps16"])
    expect("B7.5 PS-17 verdict WHOLLY_ON_PAGE -> STRADDLES_BREAK", failing(render(edit("PS-17", 2, "STRADDLES_BREAK"))), ["register_trap_ps17"])
    expect("B7.6 PS-20 verdict STRADDLES_BREAK -> WHOLLY_ON_PAGE", failing(render(edit("PS-20", 2, "WHOLLY_ON_PAGE"))), ["register_trap_ps20"])
    expect("B7.7 PS-24 verdict WHOLLY_ON_PAGE -> STRADDLES_BREAK", failing(render(edit("PS-24", 2, "STRADDLES_BREAK"))), ["register_trap_ps24"])
    expect("B7.8 PS-31 verdict EDIT_DEFERRED -> WHOLLY_ON_PAGE", failing(render(edit("PS-31", 2, "WHOLLY_ON_PAGE"))), ["register_trap_ps31"])
    expect("B7.9 PS-34 verdict WHOLLY_ON_PAGE -> STRADDLES_BREAK", failing(render(edit("PS-34", 2, "STRADDLES_BREAK"))), ["register_trap_ps34"])
    expect("B9 a figure off by one", failing(json_obj=dict(G_JSON, final_page_count=G_JSON["final_page_count"] + 1)),
           ["results_figures"])
    expect("B10 every deliverable empty", failing("", raw_json=""),
           ["register_header", "register_rows", "results_figures"])
    expect("B11 delete the CSV", failing(drop=("page_register.csv",)), ["register_header", "register_rows"])
    expect("B12 delete results.json", failing(drop=("results.json",)), ["results_figures"])
    expect("B13 bare header and {}", failing(",".join(HEADER) + "\n", raw_json="{}"),
           ["register_rows", "results_figures"])
    expect("B14 figures as a JSON list", failing(raw_json=json.dumps(list(G_JSON.values()))), ["results_figures"])
    expect("extra key in results.json (incidental)", failing(json_obj=dict(G_JSON, total_lines=539)),
           ["results_keyset"])

    print("declared wrong readings (README section 5), recomputed from the inputs")
    T4, T7, T10, T20, T24 = ("register_trap_ps04", "register_trap_ps07", "register_trap_ps10",
                             "register_trap_ps20", "register_trap_ps24")
    for label, kw, must in (
        ("W1 withdrawn read as deferred (the Not in sheet taken as 'parked')", dict(withdrawn_as_deferred=True),
         ['register_trap_ps17', 'register_trap_ps24', 'register_rows', 'results_figures']),
        ('W2 revised numbers ignored (the proposed change kept)', dict(ignore_revisions=True),
         ['register_trap_ps10', 'register_trap_ps24', 'register_rows', 'results_figures']),
        ("W3 'Back to Ines's call' / 'As Ines had it' ignored (the later call stands)", dict(revert_noop=True),
         ['register_trap_ps20', 'register_trap_ps34', 'register_rows', 'results_figures']),
        ("W4 a return to Ines's call read as the proposed number", dict(revert_to_proposed=True),
         ['register_rows']),
        ('W5 each edit read from its first decision', dict(first_line_only=True),
         ['register_trap_ps04', 'register_trap_ps10', 'register_trap_ps16', 'register_trap_ps17', 'register_trap_ps20', 'register_trap_ps24', 'register_trap_ps31', 'register_trap_ps34', 'register_rows', 'results_figures']),
        ('W6 the first read only (second read ignored)', dict(first_read_only=True),
         ['register_trap_ps04', 'register_trap_ps07', 'register_trap_ps10', 'register_trap_ps16', 'register_trap_ps17', 'register_trap_ps20', 'register_trap_ps24', 'register_trap_ps31', 'register_trap_ps34', 'register_rows', 'results_figures']),
        ('W7 every accepting line applied again', dict(every_line=True),
         ['register_trap_ps04', 'register_trap_ps10', 'register_trap_ps16', 'register_trap_ps17', 'register_trap_ps20', 'register_trap_ps24', 'register_trap_ps31', 'register_trap_ps34', 'register_rows', 'results_figures']),
        ("W8 'Same call as' copying the other edit's number", dict(same_copies_number=True),
         ['register_trap_ps34', 'results_figures']),
        ("W9 'Ditto.' read as an acceptance", dict(ditto_is_accept=True),
         ['register_trap_ps31', 'register_rows', 'results_figures']),
        ('W10 the ledger laid out in file order (draft_line ignored)', dict(file_order=True),
         ['register_trap_ps10', 'register_trap_ps16', 'register_trap_ps17', 'register_trap_ps20', 'register_trap_ps24', 'register_trap_ps31', 'register_trap_ps34', 'register_rows', 'results_figures']),
        ('W11 each ledger stretch its own passage (PS-16 twice)', dict(stretch_separate=True),
         ['register_trap_ps16', 'register_trap_ps17', 'register_trap_ps24', 'register_rows', 'results_figures']),
        ('W12 a later stretch overwriting the first (PS-16 = 9 lines)', dict(stretch_overwrite=True),
         ['register_trap_ps16', 'register_trap_ps17', 'register_trap_ps20', 'register_trap_ps24', 'register_trap_ps31', 'register_trap_ps34', 'register_rows', 'results_figures']),
        ('W13 no floor', dict(no_floor=True),
         ['register_trap_ps07', 'register_trap_ps10', 'register_trap_ps16', 'register_trap_ps17', 'register_rows', 'results_figures']),
        ('W14 floored but its line not counted', dict(floor_takes_no_line=True),
         ['register_trap_ps10', 'register_trap_ps16', 'register_rows', 'results_figures']),
        ('W15 deferred edits counted in the length', dict(deferred_counts=True),
         ['register_trap_ps04', 'register_trap_ps10', 'register_trap_ps16', 'register_trap_ps17', 'register_trap_ps24', 'register_rows', 'results_figures']),
        ('W16 last line taken one past the passage', dict(exclusive_end=True),
         ['register_rows', 'results_figures']),
        ('W17 geometry ranked above a deferred edit', dict(geometry_first=True),
         ['register_trap_ps04', 'register_rows', 'results_figures']),
    ):
        wrong_rows, wrong_res = solve(INPUTS, **kw)
        expect(label, failing(render(wrong_rows), json_obj=wrong_res), must)

    print(f"\n{len(bad)} problem(s)" + (": " + "; ".join(bad) if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
