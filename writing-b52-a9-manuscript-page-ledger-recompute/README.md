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
- the flag ledger, `passage_ledger.csv`: 41 flags in the order they were raised (`passage_id, draft_line,
  drafted_lines`); the first read's 34 flags are in manuscript order, the second read's seven follow, and
  one of those, the ledger's 39th line, is the second stretch of PS-16, flagged on the first read at line 17;
- the edit register, `edit_register.xlsx`, with four sheets:
  - `Log`: 58 decisions on 45 edits, each with date, edit, passage, description, the proposed line change
    (first line of an edit only), reader, and **the decision in the reader's own words** (30 wordings);
  - `About`: how the log is kept, what the three kinds of call mean, and how a return, a "Ditto." and a
    "Same call as" decision read;
  - `Draft pages`: Tomas's register of every flag against the draft's pages (41 rows, PS-16 twice);
  - `Not in`: Tomas's list of the edits not going into this pass;
- the press's layout spec;
- the submission format.

It delivers the page register as a CSV (one row per passage: the page the passage now starts on and how it
sits there) and five roll-up figures in `results.json`.

The work is real repagination after an editorial query round: put the flags into manuscript order (the
draft's order, by `draft_line`) and join the two-stretch passage; read every decision (an edit's latest
decision is its call: accepted, deferred, or withdrawn; revised counts are given in words; "Ditto." and
"Same call as ED-xx." take another decision's kind of call; "Back to Ines's call." returns to an earlier
one); sum every accepted edit per passage; floor at 1 line; record each passage as floored, carrying a
deferred edit, crossing a break or wholly on a page.

**The population is not handed over.** The instruction names no count, page or passage.

**Why it is hard.** The unit of the register is the passage, and the ledger's unit is the flag. PS-16 is
listed twice under one id, 22 lines apart in the file, with nothing on either line saying so: its second
stretch's `draft_line` follows on from the first's, which a reader can check but no column or note
points at. The definition is in the layout spec as one parenthetical ("a passage flagged in more than one
stretch has the stretches' lines together") and in the submission format as another ("a passage is
everything `passage_ledger.csv` lists under one `passage_id`"). Two literally true requester sentences
invite one row per flag: "every line in it is a stretch I flagged, and none has been merged or dropped",
and "Tomas got the flags right; it's the pages that are stale", whose sheet lists PS-16 twice. A run that
writes one row per ledger line delivers 41 rows; a run that keys a dict by `passage_id` keeps 9 lines for
PS-16. Either moves every later row. On top of that, the 58 decisions have to be read one by one, with
"Ditto." and "Same call as" resolved against the log as it then stood, and no sheet confirms the reading.

## 2. Departures from the mined version

The mined package arrived with a template-residue instruction that disclosed the floor trap, a ledger that
pinned one edit code per passage (so no join was needed), 22 checks all core (two existence-only checks,
a row-count check, twelve regex row pins, a core key-set guard, five single-figure checks), a harness with no
guards, a shared engine without the compound comparators, and GLM-5.2 solving 3/3 envelope renderings.

| file | was | now | why |
|---|---|---|---|
| `instruction.md` | "# Task" heading, `---` dividers, relative `input/…` paths, deliverables named twice, "must be your final action; confirm each one exists", a "Working environment" block, and "One of the cuts is as long as the passage it is cutting, so do not let that passage vanish and pull everything else back with it" | the requester's own paragraph; every path absolute and named once; the floor hint removed; the ledger described as "in the order I flagged them, with the draft line each starts on; every line in it is a stretch I flagged, and none has been merged or dropped"; the register as "the edit register Ines and Tomas kept through both reads", its Log as "every decision either of them made on an edit, in their own words", "nothing has been struck from it", "Tomas's Draft pages sheet has every flag against the draft's pages", and "Tomas got the flags right; it's the pages that are stale"; the five figures named by pointing at the layout rules | INS-1, INS-11, INS-13, INS-15, PKG-14; the removed sentence named the deciding case and its fix (INS-8/FIX-3); the leads are literally true (every ledger line is one flagged stretch and none was merged; no log line was deleted; the Draft pages sheet is the per-flag draft layout and the Not in sheet equals the edits whose call is not accepted, both asserted by derive_gold.py) |
| `environment/input/passage_ledger.csv` | 12 passages, `passage_id,drafted_lines,edit_code` (one edit code per passage, `NONE` for none), in manuscript order | 41 flags over 40 passages, `passage_id,draft_line,drafted_lines`, in flagging order; the second read's flags appended, among them PS-16's second stretch (file line 39; its first stretch is line 17), with no note and no stretch column | the ledger no longer does the join; manuscript order comes from `draft_line`, and the two-stretch passage is the reference's unit-of-analysis trap done as the reference did it: a repeated id far down the file, nothing pointing at it (§5) |
| `environment/input/edit_register.csv` → `edit_register.xlsx` | `edit_code,line_change,edit_state`; 8 edits, one line each, one per passage | a workbook: `Log` (58 dated decisions on 45 edits in the readers' words, `proposed_change` on each edit's first line only), `About` (the log's keeping; the three calls; returns, "Ditto." and "Same call as"), `Draft pages` (Tomas's per-flag register against the draft's pages: 41 rows, PS-16 twice, every value true of the draft), `Not in` (Tomas's list of edits not going in, no state column) | the crux (§5); built by `tools/build_fixture.py` (repository root); every wording's meaning is declared in `tests/derive_gold.py` (`DECISIONS`) and asserted to cover the Log; `Draft pages` is asserted equal to the per-flag draft layout (it is Rui's tab: right ids, wrong unit) |
| `environment/input/layout_spec.md` | "The passages run one after another in the order the ledger lists them"; "plus the line change of the edit proposed for it"; "A passage whose edit was deferred" | "`draft_line` is the line of the draft each flag starts on, and the manuscript keeps the draft's order"; "its drafted lines (a passage flagged in more than one stretch has the stretches' lines together)"; "every edit that stands accepted for it"; "An edit that is not accepted changes nothing"; a pointer to the register's About sheet | definitions where the data lives (FIX-2), each stated once, as the reference's C4 parenthetical is |
| `environment/input/submission_format.md` | "One row per record, keyed by `passage_id`" and "in the order the file lists them" (order ungraded); a thousands-separator / currency clause for page numbers | "One row per passage (a passage is everything `passage_ledger.csv` lists under one `passage_id`), in any order, with `passage_id` in the ledger's own form"; "`page_number` … a plain whole number" | P6 over-specification: order was demanded but never graded; the currency clause did not fit page numbers |
| `environment/Dockerfile` | `python:3.12-slim-bookworm` unpinned | pinned by digest `@sha256:4766d8…58a2` (same base as the accepted Task_17 bundle) | ENV-3 |
| `task.toml` | `artifacts = []`, no reward shape | two artifact paths; `reward_shape`; description rewritten | TOML-4/5, HAR-2, PKG-14 |
| `tests/verifier.json` | 22 checks, all core: `register_exists`, `results_exists`, `register_row_count`, `ps01_pin`…`ps12_pin` (regex, ungraded order), core `results_keyset`, five `result_*` figures | 13 checks (12 core, 1 incidental), §3; every pin read from the gold files by `tools/build_verifier.py`; every `why_justification` quotes its sentence verbatim | P0 #1, VER-21, DIS-2, GLD-11 |
| `tests/rl_world_verifiers/` | the b52 engine (no `table_equals` / `object_equals`) | the engine vendored in the accepted Task_17 bundle (compound comparators, equivalence contract) | the row and figure checks need `table_equals` / `object_equals` |
| `tests/test.sh`, `score.py`, `test_outputs.py` | pytest + a score over all checks; no guards | the accepted Task_17 harness with this task's deliverables: symlink/size guard and snapshot, controlled interpreter, input-integrity evidence, core gate + weighted fraction, output-truncation guard | HAR-1..11, VER-25, ENV-5 |
| `tests/` (new) | none | `check_inputs.py`, `input_hashes.json`, `derive_gold.py`, `discrimination.py` (author tools, not on the reward path) | FIX-11, GLD-11, VER-24 |
| `solution/files/` | the one-edit-per-passage gold | re-derived from the inputs by `tests/derive_gold.py` | GLD-11 |
| `solution/golden_trajectory.json`, `solve.sh` | 6 hand-built steps that `cat` the gold into place | 6 steps that read the inputs and compute the answer (verified to reproduce the gold); `solve.sh` also replays an ATIF trajectory, so a reward-1.0 GLM-5.2 run can be promoted in place | PKG-8 (promotion is a Phase 6 step in `PLAN.md`) |
| `consistency/`, `evaluations/{oracle,nop}` | mined evidence for the old fixture | removed; `evaluations/` holds this package's runs | PKG-1 |

## 3. Declarations

- **Reward shape:** core-gated weighted fraction over 13 equally weighted checks (as `task.toml`
  `reward_shape` and `tests/score.py`): any failed core check scores 0; otherwise the passing weight; 1.0
  only when every check passes.
- **Checks by kind:**
  - core, deterministic (12): `register_header`; nine trap rows isolated, each its own check:
    `register_trap_ps04` (exact cut accepted, then parked), `_ps07` (two accepted cuts floor it), `_ps10`
    (parked addition accepted), `_ps16` (the two-stretch passage), `_ps17` ("Same call as" a withdrawn
    edit), `_ps20` (revised, parked, returned to the earlier call), `_ps24` (exact cut accepted, then
    withdrawn), `_ps31` ("Ditto." after a park), `_ps34` (parked, then taken "at the number Ines had");
    `register_rows` (the other 31 passages cell by cell, row set locked to the 40 ledger ids, columns
    closed); `results_figures` (five figures, key set open).
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
- Key: 40 passages in manuscript order; the manuscript runs to line 539; `straddling_passage_count` 12,
  `deferred_edit_count` 7, `length_floored_count` 1, `wholly_on_page_count` 20, `final_page_count` 18.

| passage (manuscript order) | drafted | edits as they stand (call after the latest decision) | lines | page | verdict |
|---|---|---|---|---|---|
| PS-01 | 12 | ED-01 +6 ACCEPTED | 1-18 | 1 | WHOLLY_ON_PAGE |
| PS-02 | 18 | ED-20 -2 ACCEPTED | 19-34 | 1 | STRADDLES_BREAK |
| PS-03 | 9 | ED-02 -3 ACCEPTED | 35-40 | 2 | WHOLLY_ON_PAGE |
| PS-04 | 22 | ED-03 -22 DEFERRED | 41-62 | 2 | EDIT_DEFERRED |
| PS-05 | 12 | ED-44 -3 WITHDRAWN | 63-74 | 3 | WHOLLY_ON_PAGE |
| PS-35 | 9 | ED-33 -4 ACCEPTED | 75-79 | 3 | WHOLLY_ON_PAGE |
| PS-06 | 7 | ED-04 +6 DEFERRED | 80-86 | 3 | EDIT_DEFERRED |
| PS-07 | 25 | ED-05 -21 ACCEPTED, ED-09 -5 ACCEPTED | 87-87 | 3 | LENGTH_FLOORED |
| PS-08 | 11 | ED-06 +2 ACCEPTED | 88-100 | 3 | STRADDLES_BREAK |
| PS-09 | 16 | ED-39 +4 ACCEPTED | 101-120 | 4 | WHOLLY_ON_PAGE |
| PS-10 | 8 | ED-07 +14 ACCEPTED | 121-142 | 5 | WHOLLY_ON_PAGE |
| PS-11 | 17 | ED-08 -4 ACCEPTED | 143-155 | 5 | STRADDLES_BREAK |
| PS-12 | 13 | ED-32 +3 WITHDRAWN | 156-168 | 6 | WHOLLY_ON_PAGE |
| PS-36 | 14 | ED-34 +5 DEFERRED | 169-182 | 6 | EDIT_DEFERRED |
| PS-13 | 20 | ED-10 -6 ACCEPTED, ED-11 +3 ACCEPTED | 183-199 | 7 | WHOLLY_ON_PAGE |
| PS-14 | 6 | ED-41 +2 WITHDRAWN | 200-205 | 7 | WHOLLY_ON_PAGE |
| PS-15 | 15 | ED-12 +5 WITHDRAWN | 206-220 | 7 | STRADDLES_BREAK |
| PS-16 | 33 | ED-13 -12 ACCEPTED | 221-241 | 8 | STRADDLES_BREAK |
| PS-17 | 15 | ED-40 -7 WITHDRAWN | 242-256 | 9 | WHOLLY_ON_PAGE |
| PS-18 | 19 | ED-14 +4 DEFERRED | 257-275 | 9 | EDIT_DEFERRED |
| PS-19 | 12 | ED-21 +3 DEFERRED | 276-287 | 10 | EDIT_DEFERRED |
| PS-37 | 6 | ED-35 -2 WITHDRAWN | 288-293 | 10 | WHOLLY_ON_PAGE |
| PS-20 | 27 | ED-15 -5 ACCEPTED | 294-315 | 10 | STRADDLES_BREAK |
| PS-21 | 9 | ED-30 +1 ACCEPTED | 316-325 | 11 | WHOLLY_ON_PAGE |
| PS-22 | 14 | ED-16 +2 ACCEPTED | 326-341 | 11 | STRADDLES_BREAK |
| PS-23 | 23 | ED-31 -2 ACCEPTED | 342-362 | 12 | STRADDLES_BREAK |
| PS-24 | 11 | ED-17 -11 WITHDRAWN | 363-373 | 13 | WHOLLY_ON_PAGE |
| PS-25 | 16 | ED-18 +6 ACCEPTED | 374-395 | 13 | STRADDLES_BREAK |
| PS-26 | 7 | ED-24 +3 WITHDRAWN | 396-402 | 14 | WHOLLY_ON_PAGE |
| PS-27 | 21 | ED-22 -4 ACCEPTED | 403-419 | 14 | WHOLLY_ON_PAGE |
| PS-38 | 18 | ED-36 -4 ACCEPTED, ED-45 +3 ACCEPTED | 420-436 | 14 | STRADDLES_BREAK |
| PS-28 | 13 | ED-19 -5 ACCEPTED | 437-444 | 15 | WHOLLY_ON_PAGE |
| PS-29 | 10 | ED-23 +2 ACCEPTED | 445-456 | 15 | STRADDLES_BREAK |
| PS-30 | 19 | ED-29 -9 WITHDRAWN | 457-475 | 16 | WHOLLY_ON_PAGE |
| PS-39 | 12 | ED-37 +4 ACCEPTED | 476-491 | 16 | STRADDLES_BREAK |
| PS-31 | 14 | ED-25 -6 ACCEPTED, ED-42 +2 DEFERRED | 492-499 | 17 | EDIT_DEFERRED |
| PS-32 | 8 | ED-26 +3 ACCEPTED | 500-510 | 17 | WHOLLY_ON_PAGE |
| PS-33 | 17 | ED-27 -5 ACCEPTED, ED-43 -6 ACCEPTED | 511-516 | 18 | WHOLLY_ON_PAGE |
| PS-40 | 10 | ED-38 -3 DEFERRED | 517-526 | 18 | EDIT_DEFERRED |
| PS-34 | 11 | ED-28 +2 ACCEPTED | 527-539 | 18 | WHOLLY_ON_PAGE |

- The interpretation key: every wording in the Log and its declared meaning is `DECISIONS` in
  `tests/derive_gold.py` (30 wordings: 8 accept as they stand, 6 accept at a revised count, 4 defer,
  5 withdraw, 2 return to Ines's call, "Ditto.", and 4 "Same call as ED-xx.").
- Hand checks of the deciding rows (GLD-4):
  - **PS-16:** two stretches, 24 lines from draft line 235 and 9 from draft line 259 (the ledger's 17th and
    39th lines), 33 drafted lines; ED-13 stands accepted at −12 ("Yes, and take the next three lines with it:
    twelve out."), so 21 lines, 221-241: STRADDLES_BREAK, page 8.
  - **PS-17:** ED-40 (−7) was "Go ahead." then "Same call as ED-24."; ED-24 stands withdrawn, so ED-40 stands
    withdrawn: PS-17 keeps 15 lines, 242-256, and is not deferred.
  - **PS-31:** ED-42 (+2) has one decision, "Ditto.", on the line after "Leave it with the author." (ED-38):
    it stands deferred, so PS-31 is recorded EDIT_DEFERRED at ED-25's −6 (accepted at "Cut, but six lines
    only.", parked, then "As Ines had it.").
  - **PS-34:** ED-28 (+2) was "Leave it with the author." then "Take it, at the number Ines had.": accepted
    at +2, 13 lines, 527-539.
  - **PS-04, PS-07, PS-10, PS-20, PS-24:** as in build v5 (parked exact cut; two cuts floor it; parked
    addition accepted; revised, parked, returned; exact cut withdrawn), now at lines
    41, 87, 121, 294 and 363.
  - **PS-11:** ends on line 155 = 5 × 30, so it sits wholly on page 5.

## 5. Difficulty design (declared before the measuring battery)

**Crux: unit of analysis, done as the reference did it.** Builds v2-v6 each stated a subtler rule and each
was solved 5/5: every run read all inputs, turned each rule into a checklist item, encoded the data by hand,
computed in a script and cross-checked against any helper. In v6 the two-stretch passage carried a `note`
("runs straight on") and a `position` column that sorted its stretches together, and every run merged it
at once. The reference's DR-16 carried nothing: a repeated id 25 rows down, one parenthetical definition,
two literally true leads and a helper tab listing it twice, and 5 of 8 runs took one row per line.

v7 does the same. PS-16 is a repeated id 22 lines down the ledger with no note and no stretch column;
`draft_line` gives manuscript order without pointing at the repeat; the definition is one parenthetical in
the spec and one in the submission format; the leads are "every line in it is a stretch I flagged, and
none has been merged or dropped" and "Tomas got the flags right; it's the pages that are stale"; and
Tomas's `Draft pages` sheet lists 41 flags, PS-16 twice, every value true of the draft. The wrong readings
pass every self-check: 41 rows with the figures summing to 41 (W11), or 40 rows with PS-16 at 9 lines
(W12), and both agree with `Draft pages`.

v5's and v6's difficulty stays underneath: 58 prose decisions with "Ditto." and "Same call as" references,
three calls onto four verdicts, and a `Not in` sheet that corroborates the binary misreading.

Expected wrong readings, each recomputed from the inputs by `tests/discrimination.py` with the gold's own
solver. All eighteen readings, gold included, give pairwise-distinct deliverables:

| id | reading | checks that fail |
|---|---|---|
| W1 | withdrawn read as deferred (the `Not in` sheet taken as "parked") | `_ps17`, `_ps24`, `register_rows`, `results_figures` |
| W2 | revised counts ignored (the proposed change kept) | `_ps10`, `_ps24`, `register_rows`, `results_figures` |
| W3 | returns to Ines's call ignored (the later call stands) | `_ps20`, `_ps34`, `register_rows`, `results_figures` |
| W4 | a return to Ines's call read as the proposed number | `register_rows` |
| W5 | each edit read from its first decision | eight traps, `register_rows`, `results_figures` |
| W6 | the first read only | nine traps, `register_rows`, `results_figures` |
| W7 | every accepting line applied again | eight traps, `register_rows`, `results_figures` |
| W8 | "Same call as" copying the other edit's number | `_ps34`, `results_figures` |
| W9 | "Ditto." read as an acceptance | `_ps31`, `register_rows`, `results_figures` |
| W10 | the ledger laid out in file order (`draft_line` ignored) | seven traps, `register_rows`, `results_figures` |
| W11 | one register row per ledger line (PS-16 twice; 41 rows) | `_ps16`, `_ps17`, `_ps24`, `register_rows`, `results_figures` |
| W12 | a `passage_id` dict: the later stretch overwrites (PS-16 = 9 lines) | six traps, `register_rows`, `results_figures` |
| W13 | no floor | `_ps07`, `_ps10`, `_ps16`, `_ps17`, `register_rows`, `results_figures` |
| W14 | floored, but the held line not counted | `_ps10`, `_ps16`, `register_rows`, `results_figures` |
| W15 | deferred edits counted in the length | five traps, `register_rows`, `results_figures` |
| W16 | the last line taken one past the passage | `register_rows`, `results_figures` |
| W17 | geometry ranked above a deferred edit | `_ps04`, `register_rows`, `results_figures` |

## 6. Probes and solvers

- **Discrimination** (`tests/discrimination.py`, deterministic): **50 of 50 as expected**. 11 equivalence
  variants pass: row shuffle, JSON key order, JSON figures as N.0, quoted fields, CRLF, no trailing newline,
  BOM, page numbers as N.0, padded fields, lower-case verdicts, and an extra scratch file. 22 breaking variants
  fail on their own check: a page off, a verdict wrong, a row deleted, appended or duplicated, an extra column,
  each of the nine trap rows wrong, a figure off by one, empty deliverables, each deliverable deleted, a bare
  header with `{}`, figures as a list, and an extra JSON key on `results_keyset`. The 17 wrong readings W1-W17
  fail as declared.
- **Reward floor** (shipped `test.sh`): empty workspace 0.0; bare header + `{}` 0.0.

## 7. Environment tests

Run with the shipped `test.sh` in the task image: gold 1.0 (13/13 checks, 21 pytest items passed); gold +
unrelated scratch files 1.0; both deliverables replaced by symlinks to the gold 0.0 (guard); planted
`conftest.py`, `sitecustomize.py` and `usercustomize.py` beside a CSV with one wrong page 0.0 (the plants
have no effect; `register_rows` fails); extra key in `results.json` 0.923077 (incidental only); nop 0.0;
`solve.sh` (oracle path) 1.0 with `agent/trajectory.json` written. `input_integrity.json` reports the inputs
intact in every run.

## 8. Trial results

**PENDING.** Filled in from the GLM-5.2 battery (opencode 1.18.18, `glmproxy/glm-5.2`): one job, every run on
one `task_checksum`, lane pre-registered as the first five by `started_at`. Each run is classified with
`python3 tools/triage_trials.py <job_dir>` (repository root), which names the reading its deliverables match
(GOLD or W1-W17) and lists the rows it got wrong. The table layout to fill in:

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
- **v4:** follows the reference's structure: 30 passages, the log semantics on the register's About sheet, and
  a correct first-read Tally vouched for. GLM solved it 5/5 (job `b52a9-glm5x-run4`). Every run used the Tally
  to cross-check its log handling ("Tally validation passes with 0 mismatches"), so the helper confirmed the
  right method.
- **v5:** decisions in prose with three calls; a helper that corroborates the binary misreading. GLM solved it
  5/5 (job `b52a9-glm5x-run5`): every run hand-encoded the 32 decisions into a dict with a rationale each,
  computed in a script, and re-checked against the `Not in` sheet.
- **v6:** 58 decisions with "Ditto." and "Same call as" references, plus a two-stretch passage in a ledger with a
  `position` column and a `note` ("the rest of the scene; runs straight on"). GLM solved it 5/5 (job
  `b52a9-glm5x-run6`, 20 min): one run's first note on the ledger was "some are duplicates (stretches of the
  same passage)"; one wrote a regex classifier for the decisions and cross-checked it against a manual pass.
- **v7, current:** the same two-stretch passage with nothing pointing at it (no note, no position column;
  `draft_line` orders the flags), a helper sheet that lists it twice, and the reference's leads.

## 9. Isolation proof

In a fresh container built from `environment/` (network off): a whole-filesystem search for `solve.sh`,
`test.sh`, `verifier.json`, `score.py`, `test_outputs.py`, `derive_gold.py`, `discrimination.py`,
`golden_trajectory.json`, `input_hashes.json` and every deliverable name returns nothing outside Python's
own site-packages; `/tests`, `/solution` and `/logs/verifier` are absent; no file contains the gold-only
string `PS-16,8,STRADDLES_BREAK`, while the positive control `ED-40` is found in the edit register. The
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
