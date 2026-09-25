#!/usr/bin/env python3
"""Build the task's input fixture from one table of data (author tool, not in the task package).

Writes environment/input/passage_ledger.csv and environment/input/edit_register.xlsx (sheets Log,
About, Tally). The workbook is written with fixed document properties so the same data always gives
the same answers; its bytes are pinned by tests/input_hashes.json after each build.

  python3 tools/build_fixture.py writing-b52-a9-manuscript-page-ledger-recompute

Needs openpyxl (the task image has it). After a rebuild, run tests/derive_gold.py --write,
tools/build_verifier.py, and re-pin tests/input_hashes.json (PLAN.md, "After any lever").
"""
import csv
import datetime as dt
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

# passage_id, drafted_lines -- manuscript order
PASSAGES = [
    ("PS-01", 12), ("PS-02", 18), ("PS-03", 9), ("PS-04", 22), ("PS-05", 14), ("PS-06", 7),
    ("PS-07", 25), ("PS-08", 11), ("PS-09", 16), ("PS-10", 8), ("PS-11", 17), ("PS-12", 13),
    ("PS-13", 20), ("PS-14", 6), ("PS-15", 15), ("PS-16", 24), ("PS-17", 10), ("PS-18", 19),
    ("PS-19", 12), ("PS-20", 27), ("PS-21", 9), ("PS-22", 14), ("PS-23", 18), ("PS-24", 11),
    ("PS-25", 16), ("PS-26", 7), ("PS-27", 21), ("PS-28", 13), ("PS-29", 10), ("PS-30", 15),
]

# logged_on, edit_code, passage_id, line_change, edit_state, reader, description -- entry order
FIRST_READ = [
    ("2026-08-03", "ED-01", "PS-01", 4, "ACCEPTED", "Ines", "Restore the epigraph dropped from the draft"),
    ("2026-08-03", "ED-02", "PS-03", -3, "ACCEPTED", "Ines", "Tighten the exchange on the station platform"),
    ("2026-08-04", "ED-03", "PS-04", -22, "ACCEPTED", "Ines", "Cut the dream sequence"),
    ("2026-08-04", "ED-04", "PS-06", 6, "DEFERRED", "Ines", "Expand Wren's letter"),
    ("2026-08-05", "ED-05", "PS-07", -21, "ACCEPTED", "Ines", "Cut the harbour flashback"),
    ("2026-08-05", "ED-06", "PS-08", 2, "ACCEPTED", "Ines", "Restore the two lines of the ferry song"),
    ("2026-08-06", "ED-07", "PS-10", 14, "DEFERRED", "Ines", "Add a coda to the market scene"),
    ("2026-08-06", "ED-08", "PS-11", -4, "ACCEPTED", "Ines", "Trim the weather paragraph"),
    ("2026-08-10", "ED-10", "PS-13", -6, "ACCEPTED", "Ines", "Compress the inquest testimony"),
    ("2026-08-10", "ED-11", "PS-13", 3, "ACCEPTED", "Ines", "Add the coroner's closing line"),
    ("2026-08-11", "ED-12", "PS-15", 5, "ACCEPTED", "Ines", "Restore the list of ship names"),
    ("2026-08-12", "ED-13", "PS-16", -9, "ACCEPTED", "Ines", "Cut the second telling of the wreck"),
    ("2026-08-13", "ED-14", "PS-18", 4, "DEFERRED", "Ines", "Add the lighthouse keeper's log entry"),
    ("2026-08-17", "ED-15", "PS-20", -7, "ACCEPTED", "Ines", "Trim the auction catalogue"),
    ("2026-08-18", "ED-16", "PS-22", 2, "ACCEPTED", "Ines", "Restore Maud's reply"),
    ("2026-08-19", "ED-17", "PS-24", -11, "ACCEPTED", "Ines", "Cut the recipe interlude"),
    ("2026-08-20", "ED-18", "PS-25", 6, "ACCEPTED", "Ines", "Expand the storm at the quay"),
    ("2026-08-21", "ED-19", "PS-28", -5, "ACCEPTED", "Ines", "Trim the sermon"),
]
SECOND_READ = [
    ("2026-09-07", "ED-01", "PS-01", 6, "ACCEPTED", "Tomas", "Restore the epigraph dropped from the draft"),
    ("2026-09-07", "ED-20", "PS-02", -2, "ACCEPTED", "Tomas", "Drop the repeated greeting"),
    ("2026-09-08", "ED-03", "PS-04", -22, "DEFERRED", "Tomas", "Cut the dream sequence"),
    ("2026-09-08", "ED-06", "PS-08", 2, "ACCEPTED", "Tomas", "Restore the two lines of the ferry song"),
    ("2026-09-09", "ED-07", "PS-10", 14, "ACCEPTED", "Tomas", "Add a coda to the market scene"),
    ("2026-09-09", "ED-09", "PS-07", -5, "ACCEPTED", "Tomas", "Drop the second foghorn paragraph"),
    ("2026-09-10", "ED-21", "PS-19", 3, "DEFERRED", "Tomas", "Add the harbourmaster's warning"),
    ("2026-09-10", "ED-13", "PS-16", -12, "ACCEPTED", "Tomas", "Cut the second telling of the wreck"),
    ("2026-09-11", "ED-22", "PS-27", -4, "ACCEPTED", "Tomas", "Tighten the reading of the will"),
    ("2026-09-11", "ED-17", "PS-24", -11, "DEFERRED", "Tomas", "Cut the recipe interlude"),
    ("2026-09-12", "ED-23", "PS-29", 2, "ACCEPTED", "Tomas", "Restore the last line of the postcard"),
]
LOG = FIRST_READ + SECOND_READ

ABOUT = [
    "Edit register, Everly manuscript: both reads",
    "",
    "Log: one line per entry, in the order the entries were made. A line is added when an edit is proposed, "
    "and a new line is added whenever the call on an edit is revisited; from then on the edit's latest line is "
    "its call, with that line's line change and state. Nothing is struck: earlier lines stay as the record of "
    "earlier calls.",
    "First read (Ines): 3 to 21 August. Second read (Tomas): 7 to 12 September.",
    "",
    "Tally: Ines's sum at the end of the first read. For each passage, the total line change of its accepted "
    "edits and whether it was left carrying a deferred edit. Not updated since 21 August.",
]


def first_read_tally():
    current = {}
    for row in FIRST_READ:
        current[row[1]] = row
    change = {pid: 0 for pid, _ in PASSAGES}
    deferred = {pid: False for pid, _ in PASSAGES}
    for _, _, pid, delta, state, _, _ in current.values():
        if state == "ACCEPTED":
            change[pid] += delta
        else:
            deferred[pid] = True
    return [(pid, change[pid], "yes" if deferred[pid] else "no") for pid, _ in PASSAGES]


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("writing-b52-a9-manuscript-page-ledger-recompute")
    inp = root / "environment" / "input"
    dates = [r[0] for r in LOG]
    assert dates == sorted(dates), "log not in entry order"
    with (inp / "passage_ledger.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["passage_id", "drafted_lines"])
        w.writerows(PASSAGES)

    wb = openpyxl.Workbook()
    log = wb.active
    log.title = "Log"
    log.append(["logged_on", "edit_code", "passage_id", "line_change", "edit_state", "reader", "description"])
    for c in log[1]:
        c.font = Font(bold=True)
    for row in LOG:
        log.append([dt.date.fromisoformat(row[0]), *row[1:]])
        log.cell(row=log.max_row, column=1).number_format = "yyyy-mm-dd"
    for col, width in zip("ABCDEFG", (12, 10, 11, 12, 11, 8, 48)):
        log.column_dimensions[col].width = width

    about = wb.create_sheet("About")
    for line in ABOUT:
        about.append([line])
    about["A1"].font = Font(bold=True)
    about.column_dimensions["A"].width = 120

    tally = wb.create_sheet("Tally")
    tally.append(["passage_id", "accepted_line_change", "deferred_edit"])
    for c in tally[1]:
        c.font = Font(bold=True)
    for row in first_read_tally():
        tally.append(list(row))

    fixed = dt.datetime(2026, 9, 12, 17, 0, 0)
    wb.properties.creator = "Ines Moreau"
    wb.properties.lastModifiedBy = "Tomas Aird"
    wb.properties.created = fixed
    wb.properties.modified = fixed
    wb.save(inp / "edit_register.xlsx")
    old = inp / "edit_register.csv"
    if old.exists():
        old.unlink()
    print(f"wrote {inp/'passage_ledger.csv'} ({len(PASSAGES)} passages) and "
          f"{inp/'edit_register.xlsx'} ({len(LOG)} log lines)")


if __name__ == "__main__":
    main()
