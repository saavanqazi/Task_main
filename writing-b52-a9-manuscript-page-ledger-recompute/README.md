# writing-b52-a9-manuscript-page-ledger-recompute

Built to the Non-Connector Task Standard v2 (2026-09-04). Every figure below is read from a file shipped in
this package (`tests/`, `solution/files/`, and, once the battery is in, `evaluations/`); earlier builds are
described in words only.

> **Status: static rework complete and verified locally; Layer 2 battery pending.** Sections 8 and the
> `Layer 2 Difficulty` / `Cross-trial · Calibration` rows of `review.csv` are filled in from the GLM-5.2
> battery (see `PLAN.md` at the repository root). Nothing in sections 1-7 or 9-10 depends on it.

## 1. Task description

An author has to hand a manuscript back to the press with a page number against every passage they flagged,
after two edit reads. The agent gets four files:
- the passage ledger: 30 flagged passages in manuscript order, with drafted line counts;
- the edit register, `edit_register.xlsx`, with three sheets:
  - `Log`: 29 entries over 23 edits, each with date, edit code, passage, line change, ACCEPTED or DEFERRED,
    reader and description;
  - `About`: how the log is kept;
  - `Tally`: Ines's per-passage sum at the end of the first read;
- the press's layout spec;
- the submission format.

It delivers the page register as a CSV (one row per passage: the page the passage now starts on and how it
sits there) and five roll-up figures in `results.json`.

The work is real repagination bookkeeping:
- 30 lines a page, with passages back to back in ledger order;
- the log is kept so that an edit's **latest** line is its call (About sheet);
- a passage's length is its drafted lines plus the line change of **every** edit that stands accepted for it;
- a deferred edit changes nothing;
- a passage is never shorter than 1 line, and the held line still pushes every later passage down;
- each passage is recorded as floored, carrying a deferred edit, crossing a break or sitting wholly on a page,
  in that priority.

**The population is not handed over.** The instruction names no count, page or passage; it names the four
treatments only by pointing at the layout rules.

**Why it is hard.** The register has to be aggregated at two levels in opposite directions: an edit's lines
collapse to the latest, while a passage's edits add up. The workbook also offers a shortcut. The requester
vouches for the `Tally` sheet: "it's right as far as it goes, and only Tomas's second read needs folding in".
That is literally true, and `tests/derive_gold.py` asserts the Tally is exactly the first read's standing.
Tomas's second read, the log's last 11 lines, does not only add. It:
- **re-confirms** ED-06 unchanged;
- **revises** ED-01 (+4 → +6) and ED-13 (−9 → −12);
- **retracts** two accepted cuts that were each exactly as long as their passage: ED-03 on PS-04 and ED-17
  on PS-24, both ACCEPTED → DEFERRED;
- **accepts** a parked addition: ED-07 on PS-10, DEFERRED → ACCEPTED;
- adds new edits, among them ED-09, PS-07's second cut. Together with ED-05 it floors PS-07.

Folding the second read onto the Tally as additions, which is the natural reading of the lead, double-counts
the re-confirmed and revised edits. It also keeps both retracted cuts (flooring PS-04 and PS-24) and leaves
PS-10 deferred, which moves 25 of the 30 rows. The About sheet defines the log; no sentence names a passage,
an edit or a date.

## 2. Departures from the mined version

The mined package arrived with a template-residue instruction that disclosed the floor trap, a ledger that
pinned one edit code per passage (so no join was needed), 22 checks all core (two existence-only checks,
a row-count check, twelve regex row pins, a core key-set guard, five single-figure checks), a harness with no
guards, a shared engine without the compound comparators, and GLM-5.2 solving 3/3 envelope renderings.

| file | was | now | why |
|---|---|---|---|
| `instruction.md` | "# Task" heading, `---` dividers, relative `input/…` paths, deliverables named twice, "must be your final action; confirm each one exists", a "Working environment" block, and "One of the cuts is as long as the passage it is cutting, so do not let that passage vanish and pull everything else back with it" | the requester's own paragraph; every path absolute and named once; the floor hint removed; the register described as "the edit register we kept through both reads", "nothing has been struck from it", and the Tally lead "it's right as far as it goes, and only Tomas's second read needs folding in"; the five figures named by pointing at the layout rules | INS-1, INS-11, INS-13, INS-15, PKG-14; the removed sentence named the deciding case and its fix (INS-8/FIX-3); both leads are literally true (no line was deleted; the Tally equals the first read's standing, asserted by derive_gold.py) |
| `environment/input/passage_ledger.csv` | 12 passages, `passage_id,drafted_lines,edit_code` (one edit code per passage, `NONE` for none) | 30 passages, `passage_id,drafted_lines` | the ledger no longer does the join; at 30 passages and 29 log lines the work is done in code, not by eye; PS-26 ends on line 360, the last line of page 12, which separates an off-by-one last-line reading |
| `environment/input/edit_register.csv` → `edit_register.xlsx` | `edit_code,line_change,edit_state`; 8 edits, one line each, one per passage | a workbook: `Log` (29 dated entries over 23 edits: 18 first-read lines by Ines, then 11 second-read lines by Tomas that re-confirm, revise, retract, accept and add), `About` (how the log is kept: "a new line is added whenever the call on an edit is revisited; from then on the edit's latest line is its call"), `Tally` (Ines's per-passage first-read sum, "Not updated since 21 August") | the crux (§5); built by `tools/build_fixture.py` (repository root) from one data table; the Tally is asserted equal to the first read's standing |
| `environment/input/layout_spec.md` | "plus the line change of the edit proposed for it"; "A passage whose edit was deferred"; "Where an accepted edit would take it under that" | "plus the line change of every edit that stands accepted for it"; a pointer to the register's About sheet for how the log is kept; "A passage with a deferred edit"; "Where its accepted edits would take it under that" | the unit stated as definitions where the data lives (FIX-2), as the reference's About sheet does |
| `environment/input/submission_format.md` | "One row per record, keyed by `passage_id`" and "in the order the file lists them" (order ungraded); a thousands-separator / currency clause for page numbers | "One row per passage in `passage_ledger.csv`, in any order, with `passage_id` in the ledger's own form"; "`page_number` … a plain whole number" | P6 over-specification: order was demanded but never graded; the currency clause did not fit page numbers |
| `environment/Dockerfile` | `python:3.12-slim-bookworm` unpinned | pinned by digest `@sha256:4766d8…58a2` (same base as the accepted Task_17 bundle) | ENV-3 |
| `task.toml` | `artifacts = []`, no reward shape | two artifact paths; `reward_shape`; description rewritten | TOML-4/5, HAR-2, PKG-14 |
| `tests/verifier.json` | 22 checks, all core: `register_exists`, `results_exists`, `register_row_count`, `ps01_pin`…`ps12_pin` (regex, ungraded order), core `results_keyset`, five `result_*` figures | 7 checks (6 core, 1 incidental), §3; every pin read from the gold files by `tools/build_verifier.py`; every `why_justification` quotes its sentence verbatim | P0 #1, VER-21, DIS-2, GLD-11 |
| `tests/rl_world_verifiers/` | the b52 engine (no `table_equals` / `object_equals`) | the engine vendored in the accepted Task_17 bundle (compound comparators, equivalence contract) | the row and figure checks need `table_equals` / `object_equals` |
| `tests/test.sh`, `score.py`, `test_outputs.py` | pytest + a score over all checks; no guards | the accepted Task_17 harness with this task's deliverables: symlink/size guard and snapshot, controlled interpreter, input-integrity evidence, core gate + weighted fraction, output-truncation guard | HAR-1..11, VER-25, ENV-5 |
| `tests/` (new) | none | `check_inputs.py`, `input_hashes.json`, `derive_gold.py`, `discrimination.py` (author tools, not on the reward path) | FIX-11, GLD-11, VER-24 |
| `solution/files/` | the one-edit-per-passage gold | re-derived from the inputs by `tests/derive_gold.py` | GLD-11 |
| `solution/golden_trajectory.json`, `solve.sh` | 6 hand-built steps that `cat` the gold into place | 6 steps that read the inputs and compute the answer (verified to reproduce the gold); `solve.sh` also replays an ATIF trajectory, so a reward-1.0 GLM-5.2 run can be promoted in place | PKG-8 (promotion is a Phase 6 step in `PLAN.md`) |
| `consistency/`, `evaluations/{oracle,nop}` | mined evidence for the old fixture | removed; `evaluations/` holds this package's runs | PKG-1 |

## 3. Declarations

- **Reward shape:** core-gated weighted fraction over 7 equally weighted checks (as `task.toml`
  `reward_shape` and `tests/score.py`): any failed core check scores 0; otherwise the passing weight; 1.0
  only when every check passes.
- **Checks by kind:**
  - core, deterministic (6): `register_header`; `register_trap_ps04` (the exact-length cut deferred on the
    second read); `register_trap_ps07` (the two-edit passage); `register_trap_ps10` (the deferral accepted
    on the second read); `register_rows` (the other 9 passages cell by cell, row set locked to the 12 ledger
    ids, columns closed); `results_figures` (five figures, key set open).
  - incidental, deterministic (1): `results_keyset` (no extra keys).
- **No judge.** Every graded value is a number or a closed label; there is no prose deliverable.
- **Network mode:** `public`, as mined (the agent harness reaches its model through it). The verifier
  makes no network call.

## 4. Golden key derivation

- `python3 tests/derive_gold.py` re-derives the CSV and `results.json` from the shipped inputs and compares
  them byte for byte with `solution/files/`, then checks every pin in `tests/verifier.json` against that
  gold: **gold agrees with the inputs, and every verifier pin agrees with the gold**. It also asserts the
  fixture's design invariants: one passage with two edits, the second on the register's last line; a single
  cut as long as its passage; a passage ending on a page's last line.
- Key: 30 passages; the manuscript runs to line 412; `straddling_passage_count` 9, `deferred_edit_count` 5,
  `length_floored_count` 1, `wholly_on_page_count` 15, `final_page_count` 14.

| passage | drafted | edits as they stand (latest line) | lines | page | verdict |
|---|---|---|---|---|---|
| PS-01 | 12 | ED-01 6 ACCEPTED | 1-18 | 1 | WHOLLY_ON_PAGE |
| PS-02 | 18 | ED-20 -2 ACCEPTED | 19-34 | 1 | STRADDLES_BREAK |
| PS-03 | 9 | ED-02 -3 ACCEPTED | 35-40 | 2 | WHOLLY_ON_PAGE |
| PS-04 | 22 | ED-03 -22 DEFERRED | 41-62 | 2 | EDIT_DEFERRED |
| PS-05 | 14 | none | 63-76 | 3 | WHOLLY_ON_PAGE |
| PS-06 | 7 | ED-04 6 DEFERRED | 77-83 | 3 | EDIT_DEFERRED |
| PS-07 | 25 | ED-05 -21 ACCEPTED, ED-09 -5 ACCEPTED | 84-84 | 3 | LENGTH_FLOORED |
| PS-08 | 11 | ED-06 2 ACCEPTED | 85-97 | 3 | STRADDLES_BREAK |
| PS-09 | 16 | none | 98-113 | 4 | WHOLLY_ON_PAGE |
| PS-10 | 8 | ED-07 14 ACCEPTED | 114-135 | 4 | STRADDLES_BREAK |
| PS-11 | 17 | ED-08 -4 ACCEPTED | 136-148 | 5 | WHOLLY_ON_PAGE |
| PS-12 | 13 | none | 149-161 | 5 | STRADDLES_BREAK |
| PS-13 | 20 | ED-10 -6 ACCEPTED, ED-11 3 ACCEPTED | 162-178 | 6 | WHOLLY_ON_PAGE |
| PS-14 | 6 | none | 179-184 | 6 | STRADDLES_BREAK |
| PS-15 | 15 | ED-12 5 ACCEPTED | 185-204 | 7 | WHOLLY_ON_PAGE |
| PS-16 | 24 | ED-13 -12 ACCEPTED | 205-216 | 7 | STRADDLES_BREAK |
| PS-17 | 10 | none | 217-226 | 8 | WHOLLY_ON_PAGE |
| PS-18 | 19 | ED-14 4 DEFERRED | 227-245 | 8 | EDIT_DEFERRED |
| PS-19 | 12 | ED-21 3 DEFERRED | 246-257 | 9 | EDIT_DEFERRED |
| PS-20 | 27 | ED-15 -7 ACCEPTED | 258-277 | 9 | STRADDLES_BREAK |
| PS-21 | 9 | none | 278-286 | 10 | WHOLLY_ON_PAGE |
| PS-22 | 14 | ED-16 2 ACCEPTED | 287-302 | 10 | STRADDLES_BREAK |
| PS-23 | 18 | none | 303-320 | 11 | WHOLLY_ON_PAGE |
| PS-24 | 11 | ED-17 -11 DEFERRED | 321-331 | 11 | EDIT_DEFERRED |
| PS-25 | 16 | ED-18 6 ACCEPTED | 332-353 | 12 | WHOLLY_ON_PAGE |
| PS-26 | 7 | none | 354-360 | 12 | WHOLLY_ON_PAGE |
| PS-27 | 21 | ED-22 -4 ACCEPTED | 361-377 | 13 | WHOLLY_ON_PAGE |
| PS-28 | 13 | ED-19 -5 ACCEPTED | 378-385 | 13 | WHOLLY_ON_PAGE |
| PS-29 | 10 | ED-23 2 ACCEPTED | 386-397 | 13 | STRADDLES_BREAK |
| PS-30 | 15 | none | 398-412 | 14 | WHOLLY_ON_PAGE |

- Hand checks of the deciding rows (GLD-4):
  - **PS-04:** ED-03's latest line (2026-09-08) is DEFERRED, so there is no accepted edit. It keeps 22 lines,
    41-62, starting on page 2; the deferral outranks the page break. The Tally still carries its −22.
  - **PS-07:** ED-05 −21 (first read) and ED-09 −5 (second read) give 25 − 26 = −1 < 1, so it is held at
    1 line, on line 84, page 3.
  - **PS-10:** ED-07's latest line (2026-09-09) is ACCEPTED, so 8 + 14 = 22 lines, 114-135: page 4 to page 5,
    so it straddles. The Tally marks PS-10 deferred.
  - **PS-26:** ends on line 360 = 12 × 30, so it sits wholly on page 12.

## 5. Difficulty design (declared before the measuring battery)

**Crux: unit of analysis at two levels, with a vouched-for shortcut** (the reference's sanctioned pattern:
definition in an About sheet, a helper tab the requester partly vouches for, literally true leads).
- The Log's rows are entries, not edits: an edit's lines collapse to the latest.
- Edits are not passages: a passage's standing accepted edits add up.
- The `Tally` sheet is a correct first-read sum, and the instruction says only the second read needs folding in.

Folding the second read in as additions is where the unit bites. The second read revisits five calls and
re-confirms one; an additive fold double-counts, keeps retracted cuts and keeps stale deferrals. Every run in
builds v2 and v3, where the rule was a spec sentence and the data fit on one screen, followed it; the rule now
lives where the data does.

Expected wrong readings, each recomputed from the inputs by `tests/discrimination.py`. All thirteen
readings, gold included, give pairwise-distinct deliverables:

| id | reading | checks that fail |
|---|---|---|
| W1 | every Log line counts; equivalently here, the second read added onto the Tally | `register_trap_ps04`, `register_trap_ps10`, `register_rows`, `results_figures` |
| W1b | the Tally as it stands (second read ignored) | all three traps, `register_rows`, `results_figures` |
| W2 | each edit read from its first line | `register_trap_ps04`, `register_trap_ps10`, `register_rows`, `results_figures` |
| W3 | one line per passage, the last wins (a `passage_id` dict) | `register_trap_ps07`, `register_trap_ps10`, `register_rows`, `results_figures` |
| W4 | one line per passage, the first wins | all three traps, `register_rows`, `results_figures` |
| W5 | one output row per edit (a left join) | `register_trap_ps07`, `register_trap_ps10`, `register_rows`, `results_figures` |
| W6 | a DEFERRED line anywhere in an edit's history makes the passage deferred | `register_trap_ps10`, `results_figures` |
| W7 | no floor | `register_trap_ps07`, `register_rows`, `results_figures` |
| W8 | floored, but the held line not counted | `register_rows`, `results_figures` |
| W9 | deferred edits counted in the length | `register_trap_ps04`, `register_trap_ps10`, `register_rows`, `results_figures` |
| W10 | the last line taken one past the passage | `register_rows`, `results_figures` |
| W11 | geometry ranked above a deferred edit | `register_trap_ps04`, `register_rows`, `results_figures` |

Under W1 the output passes every check a run can apply to itself: 30 rows, one per passage, all four
verdicts used, and the figures summing to 30.

## 6. Probes and solvers

- **Discrimination** (`tests/discrimination.py`, deterministic): **39 of 39 as expected**. 11 equivalence
  variants pass: row shuffle, JSON key order, JSON figures as N.0, quoted fields, CRLF, no trailing newline,
  BOM, page numbers as N.0, padded fields, lower-case verdicts, and an extra scratch file. 16 breaking variants
  fail on their own check: a page off, a verdict wrong, a row deleted, appended or duplicated, an extra column,
  each of the three trap rows wrong, a figure off by one, empty deliverables, each deliverable deleted, a bare
  header with `{}`, figures as a list, and an extra JSON key on `results_keyset`. The 12 wrong readings (W1, W1b, W2-W11)
  fail as declared.
- **Reward floor** (shipped `test.sh`): empty workspace 0.0; bare header + `{}` 0.0.

## 7. Environment tests

Run with the shipped `test.sh` in the task image: gold 1.0 (7/7 checks, 15 pytest items passed); gold +
unrelated scratch files 1.0; both deliverables replaced by symlinks to the gold 0.0 (guard); planted
`conftest.py`, `sitecustomize.py` and `usercustomize.py` beside a CSV with one wrong page 0.0 (the plants
have no effect; `register_rows` fails); extra key in `results.json` 0.857143 (incidental only); nop 0.0;
`solve.sh` (oracle path) 1.0 with `agent/trajectory.json` written. `input_integrity.json` reports the inputs
intact in every run.

## 8. Trial results

**PENDING.** Filled in from the GLM-5.2 battery (opencode 1.18.18, `glmproxy/glm-5.2`): one job, every run on
one `task_checksum`, lane pre-registered as the first five by `started_at`. Each run is classified with
`python3 tools/triage_trials.py <job_dir>` (repository root), which names the reading its deliverables match
(GOLD, W1, W1b or W2-W11) and lists the rows it got wrong. The table layout to fill in:

| started (UTC) | trial | reward | slot | checks | what happened |
|---|---|---|---|---|---|

**Earlier builds (described, not quoted).**
- **Mined task:** it disclosed its only trap in the instruction; GLM-5.2 solved 3/3 envelope renderings.
- **v2:** an edit-keyed register with PS-07 carrying two accepted edits, and the floor hint removed.
  GLM-5.2 (opencode 1.18.18) solved it 5/5 (job `b52a9-glm5x-run1`).
- **v3:** the register became a dated CSV log with "An edit stands as its latest line records it" in the
  spec, and three calls revisited on 12 passages. GLM solved it 5/5 (job `b52a9-glm5x-run3`; job
  `b52a9-glm5x-run2` was a Windows cp1252 crash in Harbor's opencode adapter, INFRA, discarded). All ten
  trajectories read every input in full, restated each spec rule as a checklist item, and applied it in one
  script, with no hesitation anywhere.
- **v4, current:** follows the reference instead. The data is scaled to 30 passages, the log semantics move
  to the register's About sheet, and a correct first-read Tally sheet is vouched for by the requester.

## 9. Isolation proof

In a fresh container built from `environment/` (network off): a whole-filesystem search for `solve.sh`,
`test.sh`, `verifier.json`, `score.py`, `test_outputs.py`, `derive_gold.py`, `discrimination.py`,
`golden_trajectory.json`, `input_hashes.json` and every deliverable name returns nothing outside Python's
own site-packages; `/tests`, `/solution` and `/logs/verifier` are absent; no file contains the gold-only
string `PS-10,4,STRADDLES_BREAK`, while the positive control `ED-03` is found in the edit register. The
Dockerfile copies `input/` only. Inputs are read-only in the image (advisory: root can still write), and
nothing on the grading path reads `/app/input`; `check_inputs.py` records their hashes as evidence only.

## 10. Reproducing this

```bash
# gold, re-derived from the shipped inputs, and every verifier pin checked against it (needs openpyxl)
python3 tests/derive_gold.py

docker build -t b52a9 environment/
# equivalence, breaking and wrong-reading suites
docker run --rm --network none -v "$PWD/tests:/tests:ro" -v "$PWD/solution/files:/gold:ro" \
    -v "$PWD/environment/input:/inputs:ro" b52a9 python3 /tests/discrimination.py
# oracle and nop
harbor run -p . -a oracle -y
harbor run -p . -a nop -y
```
