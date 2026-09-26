#!/usr/bin/env python3
"""Derive the golden key from the shipped inputs alone, and check it against solution/files (GLD-11).

Author tool, not on the reward path. It reads only environment/input/ and applies the disclosed rules:
  R1  (About sheet) the Log records decisions in the reader's own words; an edit's latest decision is its
      call; a call is ACCEPTED (goes in, with the number the decision gives, else the edit's number as it
      last stood), DEFERRED (does not go in, stays open against the passage) or WITHDRAWN (does not go in,
      nothing stays open); a decision returning an edit to an earlier call makes it stand as that call did
  L1  30 lines a page; passages run back to back in ledger order from line 1; a passage's page is the
      page its first line falls on
  L2  a passage's length is its drafted lines plus the line change of every edit that stands accepted for
      it; a deferred or withdrawn edit changes nothing
  L3  a passage never falls below 1 line (held at 1, floored), and that line still pushes every later
      passage down
  L4  verdict priority: floored > carrying a deferred edit > first and last line on different pages
      (STRADDLES_BREAK) > all on one page (WHOLLY_ON_PAGE)
  L5  final_page_count is the page the manuscript's last line falls on

DECISIONS below is the declared meaning of every wording the Log uses (the interpretation key a reviewer
audits); derive() asserts every Log decision is covered. The same solver, with one switch per wrong
reading, is imported by tests/discrimination.py and tools/triage_trials.py.

It also asserts the fixture's design invariants (README section 5), that the Not in sheet the requester
vouches for lists exactly the edits whose call is not ACCEPTED, and that every pin in tests/verifier.json
equals the derived gold. Needs openpyxl (the task image has it).

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

#: decision wording -> (kind, lines). kind: accept | defer | withdraw | revert:<reader>.
#: lines: the signed line change the decision gives, or None when it gives none.
DECISIONS = {
    "Yes, take it.": ("accept", None),
    "Agreed.": ("accept", None),
    "Fine as proposed.": ("accept", None),
    "Yes, cut the whole sequence.": ("accept", None),
    "Yes, the whole interlude goes.": ("accept", None),
    "Author says go ahead.": ("accept", None),
    "Yes, but only five lines out, not seven.": ("accept", -5),
    "Yes, but six lines, not four.": ("accept", 6),
    "Yes, and take the next three lines with it: twelve out.": ("accept", -12),
    "Park until the author has read it.": ("defer", None),
    "On reflection, leave this for the author.": ("defer", None),
    "No. The list of ship names stays out.": ("withdraw", None),
    "No. The author wants the interlude kept.": ("withdraw", None),
    "Withdrawn: the letter stays as drafted.": ("withdraw", None),
    "Back to Ines's call.": ("revert:Ines", None),
}
STATE = {"accept": "ACCEPTED", "defer": "DEFERRED", "withdraw": "WITHDRAWN"}


def page_of(line: int) -> int:
    return (line - 1) // LINES_PER_PAGE + 1


def read_sheet(name: str, inp: Path = INP) -> list[dict]:
    """One sheet of edit_register.xlsx as header-keyed rows (dates as ISO strings)."""
    import openpyxl
    ws = openpyxl.load_workbook(inp / "edit_register.xlsx", data_only=True)[name]
    head = [c.value for c in ws[1]]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        rows.append({h: (v.date().isoformat() if hasattr(v, "date") and callable(v.date) else v)
                     for h, v in zip(head, r)})
    return rows


def read_inputs(inp: Path = INP):
    ledger = list(csv.DictReader(io.open(inp / "passage_ledger.csv", encoding="utf-8")))
    return ledger, read_sheet("Log", inp)


def standing(log, withdrawn_as_deferred=False, ignore_revisions=False, revert_noop=False,
             revert_to_proposed=False, first_line_only=False, first_read_only=False, every_line=False):
    """Each edit's call after the whole Log: {edit_code: {passage_id, state, change}}.

    The switches are the declared wrong readings (README section 5); all False is the gold.
    every_line returns one entry per Log line that reads as accepted (code#index), applied additively.
    """
    if first_read_only:
        second = min(l["logged_on"] for l in log if str(l["logged_on"]) >= "2026-09")
        log = [l for l in log if l["logged_on"] < second]
    calls, history, extra = {}, {}, {}
    for i, l in enumerate(log):
        code = l["edit_code"]
        kind, lines = DECISIONS[l["decision"]]
        if first_line_only and code in calls:
            continue
        prev = calls.get(code)
        number = l["proposed_change"] if prev is None else prev["change"]
        if kind.startswith("revert:"):
            if revert_noop:
                continue
            reader = kind.split(":", 1)[1]
            back = [h for h in history[code] if h["reader"] == reader][-1]
            call = dict(back["call"])
            if revert_to_proposed:
                call["change"] = int(history[code][0]["proposed"])
        else:
            state = STATE[kind]
            if state == "WITHDRAWN" and withdrawn_as_deferred:
                state = "DEFERRED"
            change = number if (lines is None or ignore_revisions) else lines
            call = {"passage_id": l["passage_id"], "state": state, "change": int(change)}
        calls[code] = call
        history.setdefault(code, []).append({"reader": l["reader"], "call": dict(call),
                                             "proposed": l["proposed_change"]})
        if every_line and call["state"] == "ACCEPTED":
            extra[f"{code}#{i}"] = dict(call)
    if every_line:
        for code, call in calls.items():
            if call["state"] != "ACCEPTED":
                extra[code] = call
        return extra
    return calls


def layout(ledger, calls, no_floor=False, floor_takes_no_line=False, deferred_counts=False,
           exclusive_end=False, geometry_first=False, row_per_edit=False):
    """Lay the passages out; returns (rows, results, notes). Switches are declared wrong readings."""
    edits: dict[str, list[dict]] = {}
    for code, c in calls.items():
        edits.setdefault(c["passage_id"], []).append(dict(c, code=code.split("#")[0]))
    units = []
    for p in ledger:
        mine = edits.get(p["passage_id"], [])
        if row_per_edit and len(mine) > 1:
            units += [(p["passage_id"], int(p["drafted_lines"]), [e]) for e in mine]
        else:
            units.append((p["passage_id"], int(p["drafted_lines"]), mine))
    rows, notes = [], {}
    counts = {"STRADDLES_BREAK": 0, "EDIT_DEFERRED": 0, "LENGTH_FLOORED": 0, "WHOLLY_ON_PAGE": 0}
    line = 1
    for pid, drafted, mine in units:
        counted = [e for e in mine if e["state"] == "ACCEPTED" or (deferred_counts and e["state"] == "DEFERRED")]
        raw = drafted + sum(e["change"] for e in counted)
        floored = raw < 1 and not no_floor
        length = 1 if floored else raw
        occupies = max(raw, 0) if (floored and floor_takes_no_line) else length
        first = line
        last_page = (first - 1 + length) // LINES_PER_PAGE + 1 if exclusive_end else page_of(first + length - 1)
        geo = "STRADDLES_BREAK" if page_of(first) != last_page else "WHOLLY_ON_PAGE"
        deferred = any(e["state"] == "DEFERRED" for e in mine)
        if floored:
            verdict = "LENGTH_FLOORED"
        elif geometry_first and geo == "STRADDLES_BREAK":
            verdict = geo
        elif deferred:
            verdict = "EDIT_DEFERRED"
        else:
            verdict = geo
        counts[verdict] += 1
        rows.append([pid, page_of(first), verdict])
        notes[pid] = {"first": first, "last": first + length - 1, "length": length,
                      "edits": [f"{e['code']} {e['change']:+d} {e['state']}" for e in mine]}
        line = first + occupies
    results = {
        "straddling_passage_count": counts["STRADDLES_BREAK"],
        "deferred_edit_count": counts["EDIT_DEFERRED"],
        "length_floored_count": counts["LENGTH_FLOORED"],
        "wholly_on_page_count": counts["WHOLLY_ON_PAGE"],
        "final_page_count": page_of(line - 1),
    }
    return rows, results, notes


def solve(inp: Path = INP, **switches):
    """The whole task under one set of switches: (rows, results, notes)."""
    ledger, log = read_inputs(inp)
    keys = {"withdrawn_as_deferred", "ignore_revisions", "revert_noop", "revert_to_proposed",
            "first_line_only", "first_read_only", "every_line"}
    calls = standing(log, **{k: v for k, v in switches.items() if k in keys})
    return layout(ledger, calls, **{k: v for k, v in switches.items() if k not in keys})


def derive():
    ledger, log = read_inputs()
    ids = [p["passage_id"] for p in ledger]
    assert len(ids) == len(set(ids)), "ledger ids repeat"
    dates = [l["logged_on"] for l in log]
    assert dates == sorted(dates), "the Log is not in entry order"
    missing = sorted({l["decision"] for l in log} - set(DECISIONS))
    assert not missing, f"decisions with no declared meaning: {missing}"
    history: dict[str, list[dict]] = {}
    for l in log:
        assert l["passage_id"] in ids, f"{l['edit_code']}: names no ledger passage"
        history.setdefault(l["edit_code"], []).append(l)
    for code, lines in history.items():
        assert len({x["passage_id"] for x in lines}) == 1, f"{code}: lines disagree on the passage"
        assert lines[0]["proposed_change"] is not None, f"{code}: first line has no proposed change"
        assert all(x["proposed_change"] is None for x in lines[1:]), f"{code}: proposed change repeated"

    calls = standing(log)
    rows, results, notes = layout(ledger, calls)

    # the requester vouches for the Not in sheet ("lists every edit that isn't going into this pass")
    notin = sorted(r["edit_code"] for r in read_sheet("Not in"))
    assert notin == sorted(c for c, v in calls.items() if v["state"] != "ACCEPTED"), "Not in sheet is wrong"

    # design invariants: the cases the difficulty design (README section 5) depends on
    drafted = {p["passage_id"]: int(p["drafted_lines"]) for p in ledger}
    kinds = {c: [DECISIONS[x["decision"]][0] for x in lines] for c, lines in history.items()}
    assert any(v["state"] == "WITHDRAWN" and kinds[c][0] == "accept"
               and -history[c][0]["proposed_change"] == drafted[v["passage_id"]] for c, v in calls.items()), \
        "no exact-length cut accepted and later withdrawn"
    assert any(v["state"] == "DEFERRED" and kinds[c][0] == "accept"
               and -history[c][0]["proposed_change"] == drafted[v["passage_id"]] for c, v in calls.items()), \
        "no exact-length cut accepted and later deferred"
    assert any(k[0] == "defer" and k[-1] == "accept" for k in kinds.values()), "no deferral later accepted"
    assert any(k[-1].startswith("revert") for k in kinds.values()), "no decision returning to an earlier call"
    assert any(DECISIONS[x["decision"]][1] is not None for lines in history.values() for x in lines[1:]), \
        "no revision on a later line"
    assert any(len(k) > 1 and set(k) == {"accept"} and DECISIONS[history[c][-1]["decision"]][1] is None
               for c, k in kinds.items()), "no accepted edit re-confirmed unchanged"
    multi = [pid for pid in drafted if sum(1 for v in calls.values()
                                           if v["passage_id"] == pid and v["state"] == "ACCEPTED") > 1]
    assert any(notes[pid]["length"] == 1 and drafted[pid] > 1 for pid in multi), \
        "no passage whose several accepted edits together floor it"
    assert any(n["last"] % LINES_PER_PAGE == 0 and n["length"] > 1 for n in notes.values()), \
        "no passage ends on a page's last line"
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
