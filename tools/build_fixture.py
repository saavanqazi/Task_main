#!/usr/bin/env python3
"""Build the task's input fixture from one table of data (author tool, not in the task package).

Writes environment/input/passage_ledger.csv and environment/input/edit_register.xlsx (sheets Log,
About, Not in). The Log records each decision in the reader's own words; what each wording means is
declared once, in tests/derive_gold.py (DECISIONS), which asserts every Log decision is covered.

  python3 tools/build_fixture.py writing-b52-a9-manuscript-page-ledger-recompute

Needs openpyxl. After a rebuild run tests/derive_gold.py --write, tools/build_verifier.py, and re-pin
tests/input_hashes.json (PLAN.md, "After any lever").
"""
import csv
import datetime as dt
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

# passage_id, drafted_lines -- manuscript order
PASSAGES = [
    ("PS-01", 12), ("PS-02", 18), ("PS-03", 9), ("PS-04", 22), ("PS-05", 12), ("PS-06", 7),
    ("PS-07", 25), ("PS-08", 11), ("PS-09", 16), ("PS-10", 8), ("PS-11", 17), ("PS-12", 13),
    ("PS-13", 20), ("PS-14", 6), ("PS-15", 15), ("PS-16", 24), ("PS-17", 15), ("PS-18", 19),
    ("PS-19", 12), ("PS-20", 27), ("PS-21", 9), ("PS-22", 14), ("PS-23", 23), ("PS-24", 11),
    ("PS-25", 16), ("PS-26", 7), ("PS-27", 21), ("PS-28", 13), ("PS-29", 10), ("PS-30", 19),
]

EDITS = {  # edit_code: (passage_id, description)
    "ED-01": ("PS-01", "Restore the epigraph dropped from the draft"),
    "ED-02": ("PS-03", "Tighten the exchange on the station platform"),
    "ED-03": ("PS-04", "Cut the dream sequence"),
    "ED-04": ("PS-06", "Expand Wren's letter"),
    "ED-05": ("PS-07", "Cut the harbour flashback"),
    "ED-06": ("PS-08", "Restore the two lines of the ferry song"),
    "ED-07": ("PS-10", "Add a coda to the market scene"),
    "ED-08": ("PS-11", "Trim the weather paragraph"),
    "ED-09": ("PS-07", "Drop the second foghorn paragraph"),
    "ED-10": ("PS-13", "Compress the inquest testimony"),
    "ED-11": ("PS-13", "Add the coroner's closing line"),
    "ED-12": ("PS-15", "Restore the list of ship names"),
    "ED-13": ("PS-16", "Cut the second telling of the wreck"),
    "ED-14": ("PS-18", "Add the lighthouse keeper's log entry"),
    "ED-15": ("PS-20", "Trim the auction catalogue"),
    "ED-16": ("PS-22", "Restore Maud's reply"),
    "ED-17": ("PS-24", "Cut the recipe interlude"),
    "ED-18": ("PS-25", "Expand the storm at the quay"),
    "ED-19": ("PS-28", "Trim the sermon"),
    "ED-20": ("PS-02", "Drop the repeated greeting"),
    "ED-21": ("PS-19", "Add the harbourmaster's warning"),
    "ED-22": ("PS-27", "Tighten the reading of the will"),
    "ED-23": ("PS-29", "Restore the last line of the postcard"),
    "ED-24": ("PS-26", "Add a postscript to the letter"),
}

# logged_on, edit_code, proposed_change (first line of an edit only), reader, decision -- entry order
LOG = [
    ("2026-08-03", "ED-01", 4, "Ines", "Yes, take it."),
    ("2026-08-03", "ED-02", -3, "Ines", "Agreed."),
    ("2026-08-04", "ED-03", -22, "Ines", "Yes, cut the whole sequence."),
    ("2026-08-04", "ED-04", 6, "Ines", "Park until the author has read it."),
    ("2026-08-05", "ED-05", -21, "Ines", "Agreed."),
    ("2026-08-05", "ED-06", 2, "Ines", "Fine as proposed."),
    ("2026-08-06", "ED-07", 14, "Ines", "Park until the author has read it."),
    ("2026-08-06", "ED-08", -4, "Ines", "Yes, take it."),
    ("2026-08-10", "ED-10", -6, "Ines", "Agreed."),
    ("2026-08-10", "ED-11", 3, "Ines", "Agreed."),
    ("2026-08-11", "ED-12", 5, "Ines", "No. The list of ship names stays out."),
    ("2026-08-12", "ED-13", -9, "Ines", "Yes, take it."),
    ("2026-08-13", "ED-14", 4, "Ines", "Park until the author has read it."),
    ("2026-08-17", "ED-15", -7, "Ines", "Yes, but only five lines out, not seven."),
    ("2026-08-18", "ED-16", 2, "Ines", "Agreed."),
    ("2026-08-19", "ED-17", -11, "Ines", "Yes, the whole interlude goes."),
    ("2026-08-20", "ED-18", 6, "Ines", "Agreed."),
    ("2026-08-21", "ED-19", -5, "Ines", "Fine as proposed."),
    ("2026-09-07", "ED-01", None, "Tomas", "Yes, but six lines, not four."),
    ("2026-09-07", "ED-20", -2, "Tomas", "Agreed."),
    ("2026-09-08", "ED-03", None, "Tomas", "On reflection, leave this for the author."),
    ("2026-09-08", "ED-06", None, "Tomas", "Agreed."),
    ("2026-09-08", "ED-15", None, "Tomas", "Park until the author has read it."),
    ("2026-09-09", "ED-07", None, "Tomas", "Author says go ahead."),
    ("2026-09-09", "ED-09", -5, "Tomas", "Agreed."),
    ("2026-09-10", "ED-21", 3, "Tomas", "Park until the author has read it."),
    ("2026-09-10", "ED-13", None, "Tomas", "Yes, and take the next three lines with it: twelve out."),
    ("2026-09-11", "ED-22", -4, "Tomas", "Agreed."),
    ("2026-09-11", "ED-17", None, "Tomas", "No. The author wants the interlude kept."),
    ("2026-09-11", "ED-24", 3, "Tomas", "Withdrawn: the letter stays as drafted."),
    ("2026-09-12", "ED-23", 2, "Tomas", "Agreed."),
    ("2026-09-12", "ED-15", None, "Tomas", "Back to Ines's call."),
]

ABOUT = [
    "Edit register, Everly manuscript: both reads",
    "",
    "Log: one line per decision on an edit, in the order the decisions were made, in the reader's own words. "
    "An edit's first line gives its line change as proposed; later lines for the same edit leave "
    "proposed_change blank. An edit's latest decision is its call.",
    "A call is one of three. Accepted: the edit goes in, with the number of lines the decision gives, or, if it "
    "gives none, the edit's number as it last stood. Deferred: the edit is parked for the author; it does not go "
    "in, and it stays open against its passage. Withdrawn: the edit is turned down; it does not go in, and "
    "nothing stays open. A decision that returns an edit to an earlier call makes the edit stand as that call did.",
    "First read (Ines): 3 to 21 August. Second read (Tomas): 7 to 12 September.",
    "",
    "Not in: Tomas's list, at the end of the second read, of the edits that are not going into this pass.",
]


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("writing-b52-a9-manuscript-page-ledger-recompute")
    inp = root / "environment" / "input"
    sys.path.insert(0, str(root / "tests"))
    from derive_gold import standing   # the declared meaning of every decision (DECISIONS)

    dates = [r[0] for r in LOG]
    assert dates == sorted(dates), "log not in entry order"
    seen = set()
    for _, code, proposed, _, _ in LOG:
        assert (proposed is not None) == (code not in seen), f"{code}: proposed_change on the wrong line"
        seen.add(code)

    with (inp / "passage_ledger.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["passage_id", "drafted_lines"])
        w.writerows(PASSAGES)

    wb = openpyxl.Workbook()
    log = wb.active
    log.title = "Log"
    log.append(["logged_on", "edit_code", "passage_id", "description", "proposed_change", "reader", "decision"])
    for c in log[1]:
        c.font = Font(bold=True)
    for date, code, proposed, reader, decision in LOG:
        pid, desc = EDITS[code]
        log.append([dt.date.fromisoformat(date), code, pid, desc, proposed, reader, decision])
        log.cell(row=log.max_row, column=1).number_format = "yyyy-mm-dd"
    for col, width in zip("ABCDEFG", (12, 10, 11, 44, 16, 8, 56)):
        log.column_dimensions[col].width = width

    about = wb.create_sheet("About")
    for line in ABOUT:
        about.append([line])
    about["A1"].font = Font(bold=True)
    about.column_dimensions["A"].width = 120
    for row in about.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")

    notin = wb.create_sheet("Not in")
    notin.append(["edit_code", "passage_id", "description"])
    for c in notin[1]:
        c.font = Font(bold=True)
    calls = standing([{"logged_on": d, "edit_code": c, "passage_id": EDITS[c][0], "proposed_change": p,
                       "reader": r, "decision": t} for d, c, p, r, t in LOG])
    for code in sorted(calls):
        if calls[code]["state"] != "ACCEPTED":
            notin.append([code, EDITS[code][0], EDITS[code][1]])
    notin.column_dimensions["C"].width = 44

    fixed = dt.datetime(2026, 9, 12, 17, 0, 0)
    wb.properties.creator = "Ines Moreau"
    wb.properties.lastModifiedBy = "Tomas Aird"
    wb.properties.created = fixed
    wb.properties.modified = fixed
    wb.save(inp / "edit_register.xlsx")
    print(f"wrote {len(PASSAGES)} passages and {len(LOG)} log lines over {len(EDITS)} edits; "
          f"Not in: {sum(1 for c in calls.values() if c['state'] != 'ACCEPTED')} edits")


if __name__ == "__main__":
    main()
