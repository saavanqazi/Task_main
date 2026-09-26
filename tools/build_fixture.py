#!/usr/bin/env python3
"""Build the task's input fixture from one table of data (author tool, not in the task package).

Writes environment/input/passage_ledger.csv and environment/input/edit_register.xlsx (sheets Log,
About, Draft pages, Not in). The Log records each decision in the reader's own words; what each wording means is
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

# The manuscript, in order, as (passage_id, drafted_lines); a passage flagged in two stretches appears twice,
# its stretches adjacent. The draft line each flag starts on is computed from this order.
MANUSCRIPT = [
    ("PS-01", 12), ("PS-02", 18), ("PS-03", 9), ("PS-04", 22), ("PS-05", 12), ("PS-35", 9), ("PS-06", 7),
    ("PS-07", 25), ("PS-08", 11), ("PS-09", 16), ("PS-10", 8), ("PS-11", 17), ("PS-12", 13), ("PS-36", 14),
    ("PS-13", 20), ("PS-14", 6), ("PS-15", 15), ("PS-16", 24), ("PS-16", 9), ("PS-17", 15), ("PS-18", 19),
    ("PS-19", 12), ("PS-37", 6), ("PS-20", 27), ("PS-21", 9), ("PS-22", 14), ("PS-23", 23), ("PS-24", 11),
    ("PS-25", 16), ("PS-26", 7), ("PS-27", 21), ("PS-38", 18), ("PS-28", 13), ("PS-29", 10), ("PS-30", 19),
    ("PS-39", 12), ("PS-31", 14), ("PS-32", 8), ("PS-33", 17), ("PS-40", 10), ("PS-34", 11),
]
# The flag ledger is in the order the flags were raised: the first read's 34 flags in manuscript order, then
# the second read's seven, among them the second stretch of PS-16.
FIRST_READ_FLAGS = [f"PS-{i:02d}" for i in range(1, 35)]
SECOND_READ_FLAGS = ["PS-35", "PS-36", "PS-37", ("PS-16", 2), "PS-38", "PS-39", "PS-40"]


def ledger_rows():
    """(passage_id, draft_line, drafted_lines) in flagging order."""
    starts, line, seen = {}, 1, {}
    for pid, n in MANUSCRIPT:
        seen[pid] = seen.get(pid, 0) + 1
        starts[(pid, seen[pid])] = (line, n)
        line += n
    rows = []
    for f in FIRST_READ_FLAGS + SECOND_READ_FLAGS:
        key = f if isinstance(f, tuple) else (f, 1)
        rows.append((key[0], *starts[key]))
    return rows


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
    "ED-25": ("PS-31", "Cut the second description of the chapel"),
    "ED-26": ("PS-32", "Add Aunt Bea's aside"),
    "ED-27": ("PS-33", "Trim the walk to the headland"),
    "ED-28": ("PS-34", "Restore the dedication"),
    "ED-29": ("PS-30", "Cut the inventory of the chest"),
    "ED-30": ("PS-21", "Add the date to the telegram"),
    "ED-31": ("PS-23", "Tighten the argument at the gate"),
    "ED-32": ("PS-12", "Restore the verse Maud sings"),
    "ED-33": ("PS-35", "Cut the aside on the tides"),
    "ED-34": ("PS-36", "Add the doctor's second visit"),
    "ED-35": ("PS-37", "Drop the second mention of the bell"),
    "ED-36": ("PS-38", "Cut the list of guests"),
    "ED-37": ("PS-39", "Add the reply to the telegram"),
    "ED-38": ("PS-40", "Trim the closing paragraph"),
    "ED-39": ("PS-09", "Restore the dropped stanza"),
    "ED-40": ("PS-17", "Cut the description of the pier"),
    "ED-41": ("PS-14", "Add the ferryman's line"),
    "ED-42": ("PS-31", "Add the chapel bell"),
    "ED-43": ("PS-33", "Cut the second view from the headland"),
    "ED-44": ("PS-05", "Trim the account of the journey"),
    "ED-45": ("PS-38", "Add the toast"),
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
    ("2026-08-10", "ED-11", 3, "Ines", "Ditto."),
    ("2026-08-11", "ED-12", 5, "Ines", "No. The list of ship names stays out."),
    ("2026-08-12", "ED-13", -9, "Ines", "Yes, take it."),
    ("2026-08-12", "ED-39", 4, "Ines", "Hold it."),
    ("2026-08-13", "ED-14", 4, "Ines", "Park until the author has read it."),
    ("2026-08-13", "ED-40", -7, "Ines", "Go ahead."),
    ("2026-08-17", "ED-15", -7, "Ines", "Yes, but only five lines out, not seven."),
    ("2026-08-17", "ED-41", 2, "Ines", "Drop it."),
    ("2026-08-18", "ED-16", 2, "Ines", "Agreed."),
    ("2026-08-19", "ED-17", -11, "Ines", "Yes, the whole interlude goes."),
    ("2026-08-19", "ED-25", -8, "Ines", "Cut, but six lines only."),
    ("2026-08-20", "ED-18", 6, "Ines", "Agreed."),
    ("2026-08-20", "ED-26", 3, "Ines", "Ditto."),
    ("2026-08-21", "ED-19", -5, "Ines", "Fine as proposed."),
    ("2026-08-21", "ED-27", -5, "Ines", "Same call as ED-15."),
    ("2026-08-21", "ED-28", 2, "Ines", "Leave it with the author."),
    ("2026-08-21", "ED-29", -9, "Ines", "Not this time."),
    ("2026-09-07", "ED-01", None, "Tomas", "Yes, but six lines, not four."),
    ("2026-09-07", "ED-20", -2, "Tomas", "Agreed."),
    ("2026-09-07", "ED-30", 1, "Tomas", "Ditto."),
    ("2026-09-08", "ED-03", None, "Tomas", "On reflection, leave this for the author."),
    ("2026-09-08", "ED-06", None, "Tomas", "Agreed."),
    ("2026-09-08", "ED-15", None, "Tomas", "Park until the author has read it."),
    ("2026-09-08", "ED-31", -4, "Tomas", "In, but two lines out, not four."),
    ("2026-09-09", "ED-07", None, "Tomas", "Author says go ahead."),
    ("2026-09-09", "ED-09", -5, "Tomas", "Agreed."),
    ("2026-09-09", "ED-32", 3, "Tomas", "Same call as ED-12."),
    ("2026-09-09", "ED-39", None, "Tomas", "Author says go ahead."),
    ("2026-09-10", "ED-21", 3, "Tomas", "Park until the author has read it."),
    ("2026-09-10", "ED-13", None, "Tomas", "Yes, and take the next three lines with it: twelve out."),
    ("2026-09-10", "ED-33", -4, "Tomas", "Agreed."),
    ("2026-09-10", "ED-34", 5, "Tomas", "Hold it."),
    ("2026-09-10", "ED-28", None, "Tomas", "Take it, at the number Ines had."),
    ("2026-09-11", "ED-22", -4, "Tomas", "Agreed."),
    ("2026-09-11", "ED-17", None, "Tomas", "No. The author wants the interlude kept."),
    ("2026-09-11", "ED-24", 3, "Tomas", "Withdrawn: the letter stays as drafted."),
    ("2026-09-11", "ED-35", -2, "Tomas", "Ditto."),
    ("2026-09-11", "ED-36", -6, "Tomas", "Cut, but four lines only."),
    ("2026-09-11", "ED-40", None, "Tomas", "Same call as ED-24."),
    ("2026-09-12", "ED-23", 2, "Tomas", "Agreed."),
    ("2026-09-12", "ED-15", None, "Tomas", "Back to Ines's call."),
    ("2026-09-12", "ED-37", 4, "Tomas", "Go ahead."),
    ("2026-09-12", "ED-38", -3, "Tomas", "Leave it with the author."),
    ("2026-09-12", "ED-42", 2, "Tomas", "Ditto."),
    ("2026-09-12", "ED-25", None, "Tomas", "As Ines had it."),
    ("2026-09-12", "ED-43", -6, "Tomas", "Same call as ED-33."),
    ("2026-09-12", "ED-44", -3, "Tomas", "Not this time."),
    ("2026-09-12", "ED-45", 3, "Tomas", "Go ahead."),
    ("2026-09-12", "ED-27", None, "Tomas", "Back to Ines's call."),
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
    "nothing stays open. A decision that returns an edit to an earlier call makes the edit stand as that call did. "
    "A decision given as the same call as another decision makes the same kind of call, at this edit's own number.",
    "First read (Ines): 3 to 21 August. Second read (Tomas): 7 to 12 September.",
    "",
    "Draft pages: Tomas's register of every flag against the draft's pages (30 lines a page, the draft as it "
    "stood before either read), for checking off. Not in: Tomas's list, at the end of the second read, of the edits "
    "that are not going into this pass.",
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
        assert code in EDITS, code
        assert (proposed is not None) == (code not in seen), f"{code}: proposed_change on the wrong line"
        seen.add(code)
    assert seen == set(EDITS), sorted(set(EDITS) - seen)
    LEDGER = ledger_rows()
    assert len({r[1] for r in LEDGER}) == len(LEDGER), "draft lines repeat"

    with (inp / "passage_ledger.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["passage_id", "draft_line", "drafted_lines"])
        w.writerows(LEDGER)

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

    draft = wb.create_sheet("Draft pages")   # Tomas's per-flag register against the DRAFT's pages
    draft.append(["passage_id", "draft_line", "drafted_lines", "draft_page", "sits"])
    for c in draft[1]:
        c.font = Font(bold=True)
    for pid, start, n in LEDGER:
        first, last = (start - 1) // 30 + 1, (start + n - 2) // 30 + 1
        draft.append([pid, start, n, first, "on one page" if first == last else "over a break"])
    for col, width in zip("ABCDE", (11, 11, 13, 11, 14)):
        draft.column_dimensions[col].width = width

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
    print(f"wrote {len(LEDGER)} ledger rows ({len({r[0] for r in LEDGER})} passages, draft {sum(n for _, n in MANUSCRIPT)} lines) and {len(LOG)} log lines "
          f"over {len(EDITS)} edits; Not in: {sum(1 for c in calls.values() if c['state'] != 'ACCEPTED')} edits")


if __name__ == "__main__":
    main()
