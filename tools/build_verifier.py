#!/usr/bin/env python3
"""Regenerate tests/verifier.json from solution/files (author tool, not in the task package).

Every pin is read from the gold files and every why_justification is asserted to quote the
inputs verbatim, so run tests/derive_gold.py --write first, then:

  python3 tools/build_verifier.py writing-b52-a9-manuscript-page-ledger-recompute

If you change the trap passages (PS-04, PS-07), edit the two table(...) calls below.
"""
import csv, json, re, sys
from pathlib import Path
ROOT = Path(sys.argv[1])
INP = ROOT / "environment/input"
gold = {r["passage_id"]: r for r in csv.DictReader(open(ROOT / "solution/files/page_register.csv"))}
res = json.loads((ROOT / "solution/files/results.json").read_text())
texts = {n: (INP / n).read_text() for n in ("layout_spec.md", "submission_format.md")}
texts["instruction.md"] = (ROOT / "instruction.md").read_text()
def q(src, s):
    flat = re.sub(r"\s+", " ", texts[src])
    assert s in flat, (src, s)
    return f'{src}: "{s}"'
ROWQ = q("submission_format.md", "One row per passage in `passage_ledger.csv`, in any order, with `passage_id` in the ledger's own form (`PS-04`, not `PS4` or `4`).")
PAGEQ = q("submission_format.md", "`page_number` is the page that passage's first line falls on once the accepted edits are in, and `verdict` is how the passage is recorded under the layout spec")
FLOORQ = q("layout_spec.md", "A passage never falls below 1 line. Where its accepted edits would take it under that, the passage is held at 1 line and recorded as floored.")
PUSHQ = q("layout_spec.md", "The lines the floor holds back are real lines: every passage after it sits that much further down the manuscript than the edit register alone would suggest.")
EVERYQ = q("layout_spec.md", "A passage's length is its drafted lines plus the line change of every accepted edit proposed for it.")
PRIOQ = q("layout_spec.md", "A passage held at the minimum is recorded as floored, whatever else is true of it.")
DEFQ = q("layout_spec.md", "A deferred edit changes nothing: the lines it would add or remove are not counted, and the passage is recorded as carrying a deferred edit.")
LAYQ = q("layout_spec.md", "A page holds 30 lines. The passages run one after another in the order the ledger lists them, the first passage beginning on the first line of the manuscript, and each passage beginning on the line after the one before it ends.")
def cells(pid): return {"page_number": gold[pid]["page_number"], "verdict": gold[pid]["verdict"]}
TYPES = {"page_number": "number", "verdict": "text"}
def table(name, pids, why, how, row_set=False):
    exp = {"id_column": "passage_id", "rows": {p: cells(p) for p in pids}, "cell_types": TYPES}
    if row_set:
        exp["row_set"] = list(gold)
        exp["columns"] = ["passage_id", "page_number", "verdict"]
    return {"name": name, "metadata": {"tag": "core", "why_justification": why, "how_justification": how},
            "source": {"type": "file", "file": {"type": "csv", "command": "read_rows", "arguments": {"path": "page_register.csv"}}},
            "assertion": {"type": "deterministic", "expected": exp, "deterministic": {"path": "$", "comparison": "table_equals"}}}
keys = {k: {"value": v, "tolerance": None} for k, v in res.items()}
others = [p for p in gold if p not in ("PS-04", "PS-07")]
V = [
 {"name": "register_header", "metadata": {"tag": "core",
   "why_justification": q("submission_format.md", "Header, exactly: `passage_id,page_number,verdict`"),
   "how_justification": "Regex anchored at the start of the file's text: the three column names in order, case-insensitive, optional quotes and spaces around each, then a line break. It also fails on a missing file."},
  "source": {"type": "file", "file": {"type": "csv", "command": "extract_text", "arguments": {"path": "page_register.csv"}}},
  "assertion": {"type": "deterministic", "expected": r"(?i)\A\x22?passage_id\x22?[ \t]*,[ \t]*\x22?page_number\x22?[ \t]*,[ \t]*\x22?verdict\x22?[ \t]*\r?\n",
                "deterministic": {"path": "$.text", "comparison": "regex_match"}}},
 table("register_trap_ps04", ["PS-04"], "; ".join([ROWQ, PAGEQ, FLOORQ, PRIOQ]),
   "csv.read_rows + table_equals on the PS-04 row only (page_number as a number, verdict as text; a duplicated PS-04 row fails). PS-04's only edit, ED-03, cuts as many lines as the passage has, so it is held at 1 line: page 2, LENGTH_FLOORED. Isolated so a run that lets the passage vanish is named by its own check."),
 table("register_trap_ps07", ["PS-07"], "; ".join([ROWQ, PAGEQ, EVERYQ, FLOORQ, PRIOQ]),
   "csv.read_rows + table_equals on the PS-07 row only. PS-07 carries two accepted edits, ED-05 (-21, in register order) and ED-09 (-5, the register's last line); together they take its 25 drafted lines to -1, so it is held at 1 line: page 3, LENGTH_FLOORED. A run that keeps only one of the two edits gets 4 or 20 lines and a geometric verdict. Isolated so the one-edit-per-passage reading is named by its own check."),
 table("register_rows", others, "; ".join([ROWQ, PAGEQ, LAYQ, PUSHQ, DEFQ]),
   "csv.read_rows + table_equals on the other ten passages cell by cell, with the row set locked to the ledger's twelve passage ids (a missing, extra or duplicated passage fails) and the column set closed to the three header columns. Row order is not graded.", row_set=True),
 {"name": "results_figures", "metadata": {"tag": "core",
   "why_justification": "; ".join([q("instruction.md", "And five figures in `/app/results.json`: how many passages are recorded under each of the four treatments in the layout rules, and the page the manuscript now ends on."),
                                    q("layout_spec.md", "`straddling_passage_count`, `deferred_edit_count`, `length_floored_count` and `wholly_on_page_count` are the numbers of passages recorded under each of those four treatments. `final_page_count` is the final page, meaning the page the manuscript's last line falls on.")]),
   "how_justification": "json.read_file + object_equals on the five figures, each numeric (a numeric string or N.0 parses), key set open. Extra keys are graded by the incidental results_keyset."},
  "source": {"type": "file", "file": {"type": "json", "command": "read_file", "arguments": {"path": "results.json"}}},
  "assertion": {"type": "deterministic", "expected": {"keys": keys, "closed": False}, "deterministic": {"path": "$", "comparison": "object_equals"}}},
 {"name": "results_keyset", "metadata": {"tag": "incidental",
   "why_justification": q("submission_format.md", "A JSON object with exactly these keys and nothing else"),
   "how_justification": "object_equals with the key set closed (the engine grades closure only with every value enumerated, so it re-reads the five values). Incidental: an extra key makes the file untidy, not the figures wrong; a wrong value already fails the core results_figures."},
  "source": {"type": "file", "file": {"type": "json", "command": "read_file", "arguments": {"path": "results.json"}}},
  "assertion": {"type": "deterministic", "expected": {"keys": keys, "closed": True}, "deterministic": {"path": "$", "comparison": "object_equals"}}},
]
spec = {"task_id": "writing-b52_a9-manuscript-page-ledger-recompute", "verifiers": V}
(ROOT / "tests/verifier.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
print("wrote", len(V), "checks")
