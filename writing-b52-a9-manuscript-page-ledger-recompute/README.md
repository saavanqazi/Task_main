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
  - `Log`: 32 decisions on 24 edits, each with date, edit, passage, description, the proposed line change
    (first line of an edit only), reader, and **the decision in the reader's own words**;
  - `About`: how the log is kept, and what the three kinds of call mean;
  - `Not in`: Tomas's list of the edits not going into this pass;
- the press's layout spec;
- the submission format.

It delivers the page register as a CSV (one row per passage: the page the passage now starts on and how it
sits there) and five roll-up figures in `results.json`.

The work is real repagination after an editorial query round:
- **Read every decision.** An edit's latest decision is its call, and a call is one of three:
  - accepted: it goes in, with the number of lines the decision gives, or else its number as it stood;
  - deferred: parked for the author; it stays open against the passage;
  - withdrawn: turned down; nothing stays open.

  A decision can also return an edit to an earlier call.
- Sum every accepted edit per passage.
- Floor a passage at 1 line, and keep that line pushing later passages down.
- Record each passage as floored, carrying a deferred edit, crossing a break or sitting wholly on a page, in
  that priority.

**The population is not handed over.** The instruction names no count, page or passage.

**Why it is hard.** The deciding facts are in prose, one decision at a time, so they cannot be parsed and
cannot be checked against anything in the workbook:
- The 32 decisions use 15 wordings.
- Three decisions revise a count in words: "Yes, but only five lines out, not seven.", "Yes, but six lines,
  not four." and "Yes, and take the next three lines with it: twelve out."
- One edit (ED-15, PS-20) is accepted at a revised count, parked, then returned: "Back to Ines's call."
- Two accepted cuts that were each exactly as long as their passage are later reversed in different ways.
  PS-04's is parked ("On reflection, leave this for the author.", so deferred). PS-24's is turned down ("No.
  The author wants the interlude kept.", so withdrawn: no deferred mark, and the passage is recorded by its
  geometry).
- A parked addition is accepted ("Author says go ahead.").
- PS-07's two accepted cuts together floor it.

The deliverable has only four verdicts, and three calls have to be mapped onto them. The requester's lead
about the `Not in` sheet is literally true ("lists every edit that isn't going into this pass";
`derive_gold.py` asserts it). That sheet mixes deferred and withdrawn edits with no state column, so a run
that checks its work against it confirms the binary "not in = deferred" reading.

## 2. Departures from the mined version

The mined package arrived with a template-residue instruction that disclosed the floor trap, a ledger that
pinned one edit code per passage (so no join was needed), 22 checks all core (two existence-only checks,
a row-count check, twelve regex row pins, a core key-set guard, five single-figure checks), a harness with no
guards, a shared engine without the compound comparators, and GLM-5.2 solving 3/3 envelope renderings.

| file | was | now | why |
|---|---|---|---|
| `instruction.md` | "# Task" heading, `---` dividers, relative `input/…` paths, deliverables named twice, "must be your final action; confirm each one exists", a "Working environment" block, and "One of the cuts is as long as the passage it is cutting, so do not let that passage vanish and pull everything else back with it" | the requester's own paragraph; every path absolute and named once; the floor hint removed; the register described as "the edit register Ines and Tomas kept through both reads", its Log as "every decision either of them made on an edit, in their own words", "nothing has been struck from it", and the lead "Tomas's Not in sheet lists every edit that isn't going into this pass"; the five figures named by pointing at the layout rules | INS-1, INS-11, INS-13, INS-15, PKG-14; the removed sentence named the deciding case and its fix (INS-8/FIX-3); the leads are literally true (no line was deleted; the Not in sheet equals the edits whose call is not accepted, asserted by derive_gold.py) |
| `environment/input/passage_ledger.csv` | 12 passages, `passage_id,drafted_lines,edit_code` (one edit code per passage, `NONE` for none) | 30 passages, `passage_id,drafted_lines` | the ledger no longer does the join; at 30 passages and 29 log lines the work is done in code, not by eye; PS-26 ends on line 360, the last line of page 12, which separates an off-by-one last-line reading |
| `environment/input/edit_register.csv` → `edit_register.xlsx` | `edit_code,line_change,edit_state`; 8 edits, one line each, one per passage | a workbook: `Log` (32 dated decisions on 24 edits, in the reader's words, `proposed_change` on each edit's first line only; 18 first-read decisions by Ines, 14 second-read decisions by Tomas), `About` (the log's keeping and the three calls: accepted / deferred / withdrawn, and returns to an earlier call), `Not in` (Tomas's list of edits not going in, no state column) | the crux (§5); built by `tools/build_fixture.py` (repository root); every wording's meaning is declared in `tests/derive_gold.py` (`DECISIONS`) and asserted to cover the Log |
| `environment/input/layout_spec.md` | "plus the line change of the edit proposed for it"; "A passage whose edit was deferred"; "Where an accepted edit would take it under that" | "plus the line change of every edit that stands accepted for it"; "An edit that is not accepted changes nothing"; "A passage with an edit that stands deferred"; a pointer to the register's About sheet for the log and the three calls | definitions where the data lives (FIX-2), as the reference's About sheet does |
| `environment/input/submission_format.md` | "One row per record, keyed by `passage_id`" and "in the order the file lists them" (order ungraded); a thousands-separator / currency clause for page numbers | "One row per passage in `passage_ledger.csv`, in any order, with `passage_id` in the ledger's own form"; "`page_number` … a plain whole number" | P6 over-specification: order was demanded but never graded; the currency clause did not fit page numbers |
| `environment/Dockerfile` | `python:3.12-slim-bookworm` unpinned | pinned by digest `@sha256:4766d8…58a2` (same base as the accepted Task_17 bundle) | ENV-3 |
| `task.toml` | `artifacts = []`, no reward shape | two artifact paths; `reward_shape`; description rewritten | TOML-4/5, HAR-2, PKG-14 |
| `tests/verifier.json` | 22 checks, all core: `register_exists`, `results_exists`, `register_row_count`, `ps01_pin`…`ps12_pin` (regex, ungraded order), core `results_keyset`, five `result_*` figures | 9 checks (8 core, 1 incidental), §3; every pin read from the gold files by `tools/build_verifier.py`; every `why_justification` quotes its sentence verbatim | P0 #1, VER-21, DIS-2, GLD-11 |
| `tests/rl_world_verifiers/` | the b52 engine (no `table_equals` / `object_equals`) | the engine vendored in the accepted Task_17 bundle (compound comparators, equivalence contract) | the row and figure checks need `table_equals` / `object_equals` |
| `tests/test.sh`, `score.py`, `test_outputs.py` | pytest + a score over all checks; no guards | the accepted Task_17 harness with this task's deliverables: symlink/size guard and snapshot, controlled interpreter, input-integrity evidence, core gate + weighted fraction, output-truncation guard | HAR-1..11, VER-25, ENV-5 |
| `tests/` (new) | none | `check_inputs.py`, `input_hashes.json`, `derive_gold.py`, `discrimination.py` (author tools, not on the reward path) | FIX-11, GLD-11, VER-24 |
| `solution/files/` | the one-edit-per-passage gold | re-derived from the inputs by `tests/derive_gold.py` | GLD-11 |
| `solution/golden_trajectory.json`, `solve.sh` | 6 hand-built steps that `cat` the gold into place | 6 steps that read the inputs and compute the answer (verified to reproduce the gold); `solve.sh` also replays an ATIF trajectory, so a reward-1.0 GLM-5.2 run can be promoted in place | PKG-8 (promotion is a Phase 6 step in `PLAN.md`) |
| `consistency/`, `evaluations/{oracle,nop}` | mined evidence for the old fixture | removed; `evaluations/` holds this package's runs | PKG-1 |

## 3. Declarations

- **Reward shape:** core-gated weighted fraction over 9 equally weighted checks (as `task.toml`
  `reward_shape` and `tests/score.py`): any failed core check scores 0; otherwise the passing weight; 1.0
  only when every check passes.
- **Checks by kind:**
  - core, deterministic (8): `register_header`; five trap rows isolated, each its own check:
    `register_trap_ps04` (exact cut accepted, then parked), `register_trap_ps07` (two accepted cuts floor it),
    `register_trap_ps10` (parked addition accepted), `register_trap_ps20` (revised, parked, returned to the
    earlier call), `register_trap_ps24` (exact cut accepted, then withdrawn); `register_rows` (the other 25
    passages cell by cell, row set locked to the 30 ledger ids, columns closed); `results_figures` (five
    figures, key set open).
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
- Key: 30 passages; the manuscript runs to line 421; `straddling_passage_count` 11, `deferred_edit_count` 4,
  `length_floored_count` 1, `wholly_on_page_count` 14, `final_page_count` 15.

| passage | drafted | edits as they stand (call after the latest decision) | lines | page | verdict |
|---|---|---|---|---|---|
| PS-01 | 12 | ED-01 +6 ACCEPTED | 1-18 | 1 | WHOLLY_ON_PAGE |
| PS-02 | 18 | ED-20 -2 ACCEPTED | 19-34 | 1 | STRADDLES_BREAK |
| PS-03 | 9 | ED-02 -3 ACCEPTED | 35-40 | 2 | WHOLLY_ON_PAGE |
| PS-04 | 22 | ED-03 -22 DEFERRED | 41-62 | 2 | EDIT_DEFERRED |
| PS-05 | 12 | none | 63-74 | 3 | WHOLLY_ON_PAGE |
| PS-06 | 7 | ED-04 +6 DEFERRED | 75-81 | 3 | EDIT_DEFERRED |
| PS-07 | 25 | ED-05 -21 ACCEPTED, ED-09 -5 ACCEPTED | 82-82 | 3 | LENGTH_FLOORED |
| PS-08 | 11 | ED-06 +2 ACCEPTED | 83-95 | 3 | STRADDLES_BREAK |
| PS-09 | 16 | none | 96-111 | 4 | WHOLLY_ON_PAGE |
| PS-10 | 8 | ED-07 +14 ACCEPTED | 112-133 | 4 | STRADDLES_BREAK |
| PS-11 | 17 | ED-08 -4 ACCEPTED | 134-146 | 5 | WHOLLY_ON_PAGE |
| PS-12 | 13 | none | 147-159 | 5 | STRADDLES_BREAK |
| PS-13 | 20 | ED-10 -6 ACCEPTED, ED-11 +3 ACCEPTED | 160-176 | 6 | WHOLLY_ON_PAGE |
| PS-14 | 6 | none | 177-182 | 6 | STRADDLES_BREAK |
| PS-15 | 15 | ED-12 +5 WITHDRAWN | 183-197 | 7 | WHOLLY_ON_PAGE |
| PS-16 | 24 | ED-13 -12 ACCEPTED | 198-209 | 7 | WHOLLY_ON_PAGE |
| PS-17 | 15 | none | 210-224 | 7 | STRADDLES_BREAK |
| PS-18 | 19 | ED-14 +4 DEFERRED | 225-243 | 8 | EDIT_DEFERRED |
| PS-19 | 12 | ED-21 +3 DEFERRED | 244-255 | 9 | EDIT_DEFERRED |
| PS-20 | 27 | ED-15 -5 ACCEPTED | 256-277 | 9 | STRADDLES_BREAK |
| PS-21 | 9 | none | 278-286 | 10 | WHOLLY_ON_PAGE |
| PS-22 | 14 | ED-16 +2 ACCEPTED | 287-302 | 10 | STRADDLES_BREAK |
| PS-23 | 23 | none | 303-325 | 11 | WHOLLY_ON_PAGE |
| PS-24 | 11 | ED-17 -11 WITHDRAWN | 326-336 | 11 | STRADDLES_BREAK |
| PS-25 | 16 | ED-18 +6 ACCEPTED | 337-358 | 12 | WHOLLY_ON_PAGE |
| PS-26 | 7 | ED-24 +3 WITHDRAWN | 359-365 | 12 | STRADDLES_BREAK |
| PS-27 | 21 | ED-22 -4 ACCEPTED | 366-382 | 13 | WHOLLY_ON_PAGE |
| PS-28 | 13 | ED-19 -5 ACCEPTED | 383-390 | 13 | WHOLLY_ON_PAGE |
| PS-29 | 10 | ED-23 +2 ACCEPTED | 391-402 | 14 | WHOLLY_ON_PAGE |
| PS-30 | 19 | none | 403-421 | 14 | STRADDLES_BREAK |

- The interpretation key: every wording in the Log and its declared meaning is `DECISIONS` in
  `tests/derive_gold.py` (15 wordings: 6 accept as they stand, 3 accept at a revised count, 2 defer,
  3 withdraw, 1 return to Ines's call).
- Hand checks of the deciding rows (GLD-4):
  - **PS-04:** ED-03 (−22) was accepted, then "On reflection, leave this for the author." It stands deferred,
    so PS-04 keeps 22 lines, 41-62, starting on page 2: EDIT_DEFERRED.
  - **PS-07:** ED-05 −21 and ED-09 −5 give 25 − 26 = −1, so it is held at 1 line, on line 82, page 3.
  - **PS-10:** ED-07 +14 was parked, then "Author says go ahead." That gives 22 lines,
    112-133, from page 4 to page 5: straddles.
  - **PS-20:** ED-15 was proposed at −7 and accepted by Ines at −5, then parked by Tomas, then "Back to
    Ines's call." It stands accepted at −5, so 22 lines, 256-277: straddles, page 9.
  - **PS-24:** ED-17 (−11 = its whole length) was accepted, then "No. The author wants the interlude kept."
    It stands withdrawn, so PS-24 keeps 11 lines, 326-336, from page 11 to page 12,
    and is not deferred: STRADDLES_BREAK.
  - **PS-28:** ends on line 390 = 13 × 30, so it sits wholly on page 13.

## 5. Difficulty design (declared before the measuring battery)

**Crux: the call has to be read, not parsed, and there are three of them** (the reference's pattern: the
definition sits on an About sheet, and a helper sheet the requester truthfully vouches for corroborates the
wrong reading).
- Every edit's standing call comes from prose decisions: revised counts in words, a return to an earlier
  call, and parks and turn-downs of earlier acceptances.
- The About sheet defines three calls. The deliverable, the instruction ("the edits we accepted") and the
  `Not in` sheet all present the question as binary.
- A run that maps "not going in" to deferred marks withdrawn PS-15, PS-24 and PS-26 as EDIT_DEFERRED. That
  output agrees with the `Not in` sheet, gives 30 rows with the figures summing to 30, and passes every check
  a run can apply to itself.

Why this and not a stated rule: in builds v2-v4 every GLM-5.2 run (15 of 15) turned each written rule into a
checklist item, applied it in one script, and cross-checked its result against any helper sheet (in v4 it used
the Tally to confirm the correct method). Here no helper can confirm the three-way reading, and no script can
read the decisions for the model.

Expected wrong readings, each recomputed from the inputs by `tests/discrimination.py` with the gold's own
solver. All thirteen readings, gold included, give pairwise-distinct deliverables:

| id | reading | checks that fail |
|---|---|---|
| W1 | withdrawn read as deferred (the `Not in` sheet taken as "parked") | `register_trap_ps24`, `register_rows`, `results_figures` |
| W2 | revised counts ignored (the proposed change kept) | `register_rows`, `results_figures` |
| W3 | "Back to Ines's call." ignored (the parked call stands) | `register_trap_ps20`, `register_trap_ps24`, `register_rows`, `results_figures` |
| W4 | "Back to Ines's call." read as the proposed −7 | `register_rows`, `results_figures` |
| W5 | each edit read from its first decision | all five traps, `register_rows`, `results_figures` |
| W6 | the first read only | all five traps, `register_rows`, `results_figures` |
| W7 | every accepting line applied again | four traps, `register_rows`, `results_figures` |
| W8 | no floor | `register_trap_ps07`, `register_rows`, `results_figures` |
| W9 | floored, but the held line not counted | `register_rows`, `results_figures` |
| W10 | deferred edits counted in the length | four traps, `register_rows`, `results_figures` |
| W11 | the last line taken one past the passage | `register_rows`, `results_figures` |
| W12 | geometry ranked above a deferred edit | `register_trap_ps04`, `register_rows`, `results_figures` |

## 6. Probes and solvers

- **Discrimination** (`tests/discrimination.py`, deterministic): **41 of 41 as expected**. 11 equivalence
  variants pass: row shuffle, JSON key order, JSON figures as N.0, quoted fields, CRLF, no trailing newline,
  BOM, page numbers as N.0, padded fields, lower-case verdicts, and an extra scratch file. 18 breaking variants
  fail on their own check: a page off, a verdict wrong, a row deleted, appended or duplicated, an extra column,
  each of the five trap rows wrong, a figure off by one, empty deliverables, each deliverable deleted, a bare
  header with `{}`, figures as a list, and an extra JSON key on `results_keyset`. The 12 wrong readings W1-W12
  fail as declared.
- **Reward floor** (shipped `test.sh`): empty workspace 0.0; bare header + `{}` 0.0.

## 7. Environment tests

Run with the shipped `test.sh` in the task image: gold 1.0 (9/9 checks, 17 pytest items passed); gold +
unrelated scratch files 1.0; both deliverables replaced by symlinks to the gold 0.0 (guard); planted
`conftest.py`, `sitecustomize.py` and `usercustomize.py` beside a CSV with one wrong page 0.0 (the plants
have no effect; `register_rows` fails); extra key in `results.json` 0.888889 (incidental only); nop 0.0;
`solve.sh` (oracle path) 1.0 with `agent/trajectory.json` written. `input_integrity.json` reports the inputs
intact in every run.

## 8. Trial results

**PENDING.** Filled in from the GLM-5.2 battery (opencode 1.18.18, `glmproxy/glm-5.2`): one job, every run on
one `task_checksum`, lane pre-registered as the first five by `started_at`. Each run is classified with
`python3 tools/triage_trials.py <job_dir>` (repository root), which names the reading its deliverables match
(GOLD or W1-W12) and lists the rows it got wrong. The table layout to fill in:

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
- **v5, current:** decisions in prose with three calls; a helper that corroborates the binary misreading.

## 9. Isolation proof

In a fresh container built from `environment/` (network off): a whole-filesystem search for `solve.sh`,
`test.sh`, `verifier.json`, `score.py`, `test_outputs.py`, `derive_gold.py`, `discrimination.py`,
`golden_trajectory.json`, `input_hashes.json` and every deliverable name returns nothing outside Python's
own site-packages; `/tests`, `/solution` and `/logs/verifier` are absent; no file contains the gold-only
string `PS-24,11,STRADDLES_BREAK`, while the positive control `ED-03` is found in the edit register. The
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
