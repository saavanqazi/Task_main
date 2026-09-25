#!/usr/bin/env python3
"""Derive the golden key from the shipped inputs alone, and check it against solution/files (GLD-11).

Author tool, not on the reward path. It reads only environment/input/ and applies the disclosed rules of
layout_spec.md:
  L1  30 lines a page; passages run back to back in ledger order from line 1; a passage's page is the
      page its first line falls on
  L2  the edit register is a log: an edit can have several lines under its edit_code, and it stands as
      its LATEST line records it (that line's line_change and edit_state)
  L2b a passage's length is its drafted lines plus the line change of EVERY accepted edit proposed for
      it (a passage can carry more than one edit); a deferred edit changes nothing
  L3  a passage never falls below 1 line: where its accepted edits would take it under that, it is held
      at 1 line (floored), and that line still pushes every later passage down
  L4  verdict priority: floored > carrying a deferred edit > first and last line on different pages
      (STRADDLES_BREAK) > all on one page (WHOLLY_ON_PAGE)
  L5  final_page_count is the page the manuscript's last line falls on
It also asserts the fixture's invariants (every edit names a ledger passage and keeps one passage
across its lines, states are ACCEPTED or DEFERRED, the log is in logged_on order with no ties inside an
edit, ledger ids unique, and the design cases of README section 5 are present) and that every pin in
tests/verifier.json equals the derived gold.

  python3 tests/derive_gold.py            compare with solution/files, exit 1 on any difference
  python3 tests/derive_gold.py --write    rewrite solution/files/page_register.csv and results.json
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INP = ROOT / "environment" / "input"
GOLD = ROOT / "solution" / "files"
LINES_PER_PAGE = 30
HEADER = ["passage_id", "page_number", "verdict"]


def page_of(line: int) -> int:
    return (line - 1) // LINES_PER_PAGE + 1


def read_inputs():
    ledger = list(csv.DictReader(io.open(INP / "passage_ledger.csv", encoding="utf-8")))
    register = list(csv.DictReader(io.open(INP / "edit_register.csv", encoding="utf-8")))
    return ledger, register


def derive():
    ledger, register = read_inputs()
    ids = [p["passage_id"] for p in ledger]
    assert len(ids) == len(set(ids)), "ledger ids repeat"
    dates = [e["logged_on"] for e in register]
    assert dates == sorted(dates), "the log is not in logged_on order"
    history: dict[str, list[dict]] = {}
    for e in register:
        assert e["passage_id"] in ids, f"{e['edit_code']}: names no ledger passage"
        assert e["edit_state"] in ("ACCEPTED", "DEFERRED"), f"{e['edit_code']}: state {e['edit_state']}"
        history.setdefault(e["edit_code"], []).append(e)
    for code, lines in history.items():
        assert len({l["passage_id"] for l in lines}) == 1, f"{code}: lines disagree on the passage"
        assert len({l["logged_on"] for l in lines}) == len(lines), f"{code}: two lines on one date"
    current = {code: lines[-1] for code, lines in history.items()}   # an edit stands as its latest line
    edits: dict[str, list[dict]] = {}
    for e in current.values():
        edits.setdefault(e["passage_id"], []).append(e)

    rows, notes = [], {}
    counts = {"STRADDLES_BREAK": 0, "EDIT_DEFERRED": 0, "LENGTH_FLOORED": 0, "WHOLLY_ON_PAGE": 0}
    line = 1
    for p in ledger:
        pid, drafted = p["passage_id"], int(p["drafted_lines"])
        mine = edits.get(pid, [])
        length = drafted + sum(int(e["line_change"]) for e in mine if e["edit_state"] == "ACCEPTED")
        floored = length < 1
        if floored:
            length = 1
        first, last = line, line + length - 1
        if floored:
            verdict = "LENGTH_FLOORED"
        elif any(e["edit_state"] == "DEFERRED" for e in mine):
            verdict = "EDIT_DEFERRED"
        elif page_of(first) != page_of(last):
            verdict = "STRADDLES_BREAK"
        else:
            verdict = "WHOLLY_ON_PAGE"
        counts[verdict] += 1
        rows.append([pid, page_of(first), verdict])
        notes[pid] = {"first": first, "last": last, "length": length,
                      "edits": [f"{e['edit_code']} {e['line_change']} {e['edit_state']}" for e in mine]}
        line = last + 1

    # design invariants: the cases the difficulty design (README section 5) depends on
    drafted = {p["passage_id"]: int(p["drafted_lines"]) for p in ledger}
    relogged = {c: l for c, l in history.items() if len(l) > 1}
    assert any(l[0]["edit_state"] == "ACCEPTED" and l[-1]["edit_state"] == "DEFERRED"
               and -int(l[0]["line_change"]) == drafted[l[0]["passage_id"]] for l in relogged.values()), \
        "no exact-length cut accepted first and deferred later"
    assert any(l[0]["edit_state"] == "DEFERRED" and l[-1]["edit_state"] == "ACCEPTED" for l in relogged.values()), \
        "no edit deferred first and accepted later"
    assert any(l[0]["line_change"] != l[-1]["line_change"] for l in relogged.values()), \
        "no edit whose line change was revised"
    multi = [pid for pid, es in edits.items() if len(es) > 1]
    assert multi and any(notes[pid]["length"] == 1 and drafted[pid] > 1 for pid in multi), \
        "no passage whose several accepted edits together floor it"
    assert any(n["last"] % LINES_PER_PAGE == 0 and n["length"] > 1 for n in notes.values()), \
        "no passage ends on a page's last line"

    results = {
        "straddling_passage_count": counts["STRADDLES_BREAK"],
        "deferred_edit_count": counts["EDIT_DEFERRED"],
        "length_floored_count": counts["LENGTH_FLOORED"],
        "wholly_on_page_count": counts["WHOLLY_ON_PAGE"],
        "final_page_count": page_of(line - 1),
    }
    return rows, results, notes


def render_csv(rows) -> str:
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(HEADER)
    w.writerows(rows)
    return out.getvalue()


def render_json(results) -> str:
    return json.dumps(results, indent=2) + "\n"


def check_pins(rows, results) -> list[str]:
    """Every value tests/verifier.json pins must equal the derived gold."""
    spec = json.loads((ROOT / "tests" / "verifier.json").read_text(encoding="utf-8"))
    gold = {r[0]: {"page_number": str(r[1]), "verdict": r[2]} for r in rows}
    problems, graded = [], set()
    for v in spec["verifiers"]:
        exp = v["assertion"].get("expected")
        if isinstance(exp, dict) and "rows" in exp:
            for pid, cells in exp["rows"].items():
                graded.add(pid)
                if cells != gold.get(pid):
                    problems.append(f"{v['name']}: {pid} pinned {cells}, gold {gold.get(pid)}")
            if "row_set" in exp and sorted(exp["row_set"]) != sorted(gold):
                problems.append(f"{v['name']}: row_set differs from the ledger")
        if isinstance(exp, dict) and "keys" in exp:
            pinned = {k: s["value"] for k, s in exp["keys"].items()}
            if pinned != results:
                problems.append(f"{v['name']}: pins {pinned}, gold {results}")
    if graded != set(gold):
        problems.append(f"rows graded {sorted(graded)} != ledger {sorted(gold)}")
    return problems


def main() -> int:
    rows, results, notes = derive()
    csv_text, json_text = render_csv(rows), render_json(results)
    if "--write" in sys.argv:
        (GOLD / "page_register.csv").write_text(csv_text, encoding="utf-8")
        (GOLD / "results.json").write_text(json_text, encoding="utf-8")
        print("wrote solution/files/page_register.csv and results.json")
    for pid, n in notes.items():
        print(f"  {pid}: lines {n['first']}-{n['last']} ({n['length']}) edits {n['edits']}")
    print("  " + json.dumps(results))
    bad = []
    if (GOLD / "page_register.csv").read_text(encoding="utf-8") != csv_text:
        bad.append("solution/files/page_register.csv differs from the derivation")
    if (GOLD / "results.json").read_text(encoding="utf-8") != json_text:
        bad.append("solution/files/results.json differs from the derivation")
    bad += check_pins(rows, results)
    if bad:
        print("\n".join("MISMATCH " + b for b in bad))
        return 1
    print("gold agrees with the inputs, and every verifier pin agrees with the gold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
