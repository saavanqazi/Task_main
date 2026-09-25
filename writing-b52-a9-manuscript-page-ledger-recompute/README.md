# writing-b52-a9-manuscript-page-ledger-recompute

Built to the Non-Connector Task Standard v2 (2026-09-04). Every figure below is read from a file shipped in
this package (`tests/`, `solution/files/`, and, once the battery is in, `evaluations/`); earlier builds are
described in words only.

> **Status: static rework complete and verified locally; Layer 2 battery pending.** Sections 8 and the
> `Layer 2 Difficulty` / `Cross-trial · Calibration` rows of `review.csv` are filled in from the GLM-5.2
> battery (see `PLAN.md` at the repository root). Nothing in sections 1-7 or 9-10 depends on it.

## 1. Task description

An author has to hand a manuscript back to the press with a page number against every passage they flagged,
after two edit reads. The agent gets four files: the passage ledger (12 flagged passages, in manuscript order,
with drafted line counts), the edit register (a running log of 12 entries over 9 edits: date, edit code,
passage, line change, ACCEPTED or DEFERRED, description), the press's layout spec, and the submission format.
It delivers the page register as a CSV (one row per passage: the page the passage now starts on and how it
sits there) and five roll-up figures in `results.json`.

The work is real repagination bookkeeping: 30 lines a page, passages back to back in ledger order; the
register is a log in which an edit stands as its **latest** line records it; a passage's length is its
drafted lines plus the line change of **every** accepted edit proposed for it; a deferred edit changes
nothing; a passage is never shorter than 1 line (and the held line still pushes every later passage down);
and each passage is recorded as floored, carrying a deferred edit, crossing a break or sitting wholly on a
page, in that priority.

**The population is not handed over.** The instruction names no count, page or passage; it names the four
treatments only by pointing at the layout rules.

**Why it is hard.** The register has to be aggregated at two levels in opposite directions. Lines of one
edit collapse to the latest (the second read revisited three first-read calls), while edits of one passage
add up. Each of the three revisited edits flips an answer:
- **ED-03** is PS-04's cut of exactly its 22 lines. It was ACCEPTED on the first read and DEFERRED on the
  second, so PS-04 keeps 22 lines and is recorded as deferred. This is the case the mined task was built
  around, so a reader who floors it on sight fails.
- **ED-07** (+14 on PS-10) was DEFERRED, then ACCEPTED. PS-10 runs 22 lines across the page 4/5 break.
- **ED-01** (PS-01) was revised from +4 to +6.

Meanwhile **PS-07** carries two distinct edits: ED-05 (−21, first read) and ED-09 (−5, second read). Together
they take its 25 lines below zero, so it floors at 1. The rules define the data, not a method. The requester's
one lead is literally true and pulls toward counting every line: "Nothing has been struck from it; every line
in it is a call one of us made."

## 2. Departures from the mined version

The mined package arrived with a template-residue instruction that disclosed the floor trap, a ledger that
pinned one edit code per passage (so no join was needed), 22 checks all core (two existence-only checks,
a row-count check, twelve regex row pins, a core key-set guard, five single-figure checks), a harness with no
guards, a shared engine without the compound comparators, and GLM-5.2 solving 3/3 envelope renderings.

| file | was | now | why |
|---|---|---|---|
| `instruction.md` | "# Task" heading, `---` dividers, relative `input/…` paths, deliverables named twice, "must be your final action; confirm each one exists", a "Working environment" block, and "One of the cuts is as long as the passage it is cutting, so do not let that passage vanish and pull everything else back with it" | the requester's own paragraph; every path absolute and named once; the floor hint removed; the register described as "the edit register we kept through both reads" with the lead "Nothing has been struck from it; every line in it is a call one of us made."; the five figures named by pointing at the layout rules | INS-1, INS-11, INS-13, INS-15, PKG-14; the removed sentence named the deciding case and its fix (INS-8/FIX-3); the lead is literally true (no line was deleted; each records a call) |
| `environment/input/passage_ledger.csv` | `passage_id,drafted_lines,edit_code` (one edit code per passage, `NONE` for none); PS-11 20 lines | `passage_id,drafted_lines`; PS-11 17 lines | the ledger no longer does the join; PS-11 now ends on line 150, the last line of page 5, which separates an off-by-one last-line reading |
| `environment/input/edit_register.csv` | `edit_code,line_change,edit_state`; 8 edits, one line each, one per passage | `logged_on,edit_code,passage_id,line_change,edit_state,description`; a dated log of 12 lines over 9 edits: 8 first-read lines, then 4 second-read lines (ED-01 revised +4 → +6; ED-03 ACCEPTED → DEFERRED; ED-07 DEFERRED → ACCEPTED; ED-09 new, a second edit on PS-07) | the crux (§5); a re-logged line repeats the edit's description, as a log would |
| `environment/input/layout_spec.md` | "plus the line change of the edit proposed for it"; "A passage whose edit was deferred"; "Where an accepted edit would take it under that" | new section "How the edit register is kept" ("a log … one edit can have several lines under its `edit_code`. An edit stands as its latest line records it"); "plus the line change of every accepted edit proposed for it"; "A passage with a deferred edit"; "Where its accepted edits would take it under that" | the unit stated as definitions where the rules live (FIX-2); the singular wording implied one edit per passage and one line per edit |
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
- Key: 12 passages; the manuscript runs to line 163; `straddling_passage_count` 3, `deferred_edit_count` 2,
  `length_floored_count` 1, `wholly_on_page_count` 6, `final_page_count` 6.

| passage | drafted | edits as they stand (latest line) | lines | page | verdict |
|---|---|---|---|---|---|
| PS-01 | 12 | ED-01 +6 (revised from +4) | 1-18 | 1 | WHOLLY_ON_PAGE |
| PS-02 | 18 | none | 19-36 | 1 | STRADDLES_BREAK |
| PS-03 | 9 | ED-02 −3 | 37-42 | 2 | WHOLLY_ON_PAGE |
| PS-04 | 22 | ED-03 −22 DEFERRED (was ACCEPTED) | 43-64 | 2 | EDIT_DEFERRED |
| PS-05 | 14 | none | 65-78 | 3 | WHOLLY_ON_PAGE |
| PS-06 | 7 | ED-04 +6 DEFERRED | 79-85 | 3 | EDIT_DEFERRED |
| PS-07 | 25 | ED-05 −21, ED-09 −5 → −1, held at 1 | 86 | 3 | LENGTH_FLOORED |
| PS-08 | 11 | ED-06 +2 | 87-99 | 3 | STRADDLES_BREAK |
| PS-09 | 16 | none | 100-115 | 4 | WHOLLY_ON_PAGE |
| PS-10 | 8 | ED-07 +14 ACCEPTED (was DEFERRED) | 116-137 | 4 | STRADDLES_BREAK |
| PS-11 | 17 | ED-08 −4 | 138-150 | 5 | WHOLLY_ON_PAGE |
| PS-12 | 13 | none | 151-163 | 6 | WHOLLY_ON_PAGE |

- Hand checks of the deciding rows (GLD-4):
  - **PS-04:** ED-03's latest line (2026-09-09) is DEFERRED, so there is no accepted edit. It keeps 22 lines,
    43-64, starting on page 2; the deferral outranks the page break.
  - **PS-07:** 25 − 21 − 5 = −1 < 1, so it is held at 1 line, on line 86, page 3 (lines 61-90).
  - **PS-10:** ED-07's latest line (2026-09-10) is ACCEPTED, so 8 + 14 = 22 lines, 116-137: it starts on
    page 4 and ends on page 5, so it straddles.
  - **PS-11:** ends on line 150 = 5 × 30, so it sits wholly on page 5. **PS-12** is 151-163, page 6.

## 5. Difficulty design (declared before the measuring battery)

**Crux: unit of analysis at two levels** (sanctioned pattern). The register's rows are log entries, not
edits, and edits are not passages. Lines of one edit collapse to the latest ("An edit stands as its latest
line records it"), and edits of one passage add up ("every accepted edit proposed for it"). Both definitions
are stated where the rules live, and no sentence names a passage, an edit or a date. The requester's lead,
"every line in it is a call one of us made", is literally true and invites treating each line as an edit
to apply. The deciding revisions sit on the log's last lines, far from the lines they revise (ordering
assumption, T5). The salient exact-length cut, which the previous build and the mined task both turned on,
is now a deferral.

Expected wrong readings, each recomputed from the inputs by `tests/discrimination.py` (all twelve readings,
gold included, give pairwise-distinct deliverables):

| id | reading | what it changes | checks that fail |
|---|---|---|---|
| W1 | every register line counts (re-logged accepted lines applied again) | PS-01 +10; PS-04 floored; PS-10 still deferred | `register_trap_ps04`, `register_trap_ps10`, `register_rows`, `results_figures` |
| W2 | each edit read from its first line (the first-read state) | PS-04 floored; PS-10 deferred | `register_trap_ps04`, `register_trap_ps10`, `register_rows`, `results_figures` |
| W3 | one line per passage, the last wins (a `passage_id` dict) | PS-07 20 lines; later rows move | `register_trap_ps07`, `register_trap_ps10`, `register_rows`, `results_figures` |
| W4 | one line per passage, the first wins | PS-04 floored, PS-07 4 lines, PS-10 deferred | all three traps, `register_rows`, `results_figures` |
| W5 | one output row per edit (a left join) | 13 rows, PS-07 twice | `register_trap_ps07`, `register_rows`, `results_figures` |
| W6 | a DEFERRED line anywhere in an edit's history makes the passage deferred | PS-10 EDIT_DEFERRED | `register_trap_ps10`, `results_figures` |
| W7 | no floor | PS-07 shrinks the manuscript | `register_trap_ps07`, `register_rows`, `results_figures` |
| W8 | floored, but the held line not counted | later rows move | `register_rows` |
| W9 | deferred edits counted in the length | PS-04 floored; rows move | `register_trap_ps04`, `register_rows` |
| W10 | the last line taken one past the passage | PS-11 straddles | `register_rows`, `results_figures` |
| W11 | geometry ranked above a deferred edit | PS-04 straddles | `register_trap_ps04`, `results_figures` |

Under W1 and W2 the output passes every check a run can apply to itself: 12 rows, one per passage, all four
verdicts used, the figures summing to 12, and PS-04 "not vanishing".

## 6. Probes and solvers

- **Discrimination** (`tests/discrimination.py`, deterministic): **38 of 38 as expected**. 11 equivalence
  variants pass: row shuffle, JSON key order, JSON figures as N.0, quoted fields, CRLF, no trailing newline,
  BOM, page numbers as N.0, padded fields, lower-case verdicts, and an extra scratch file. 16 breaking variants
  fail on their own check: a page off, a verdict wrong, a row deleted, appended or duplicated, an extra column,
  each of the three trap rows wrong, a figure off by one, empty deliverables, each deliverable deleted, a bare
  header with `{}`, figures as a list, and an extra JSON key on `results_keyset`. The 11 wrong readings W1-W11
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
(GOLD or W1-W11) and lists the rows it got wrong. The table layout to fill in:

| started (UTC) | trial | reward | slot | checks | what happened |
|---|---|---|---|---|---|

**Earlier builds (described, not quoted).** The mined task disclosed its only trap in the instruction; GLM-5.2
solved 3/3 envelope renderings. The first rework moved the join into the data: an edit-keyed register with
PS-07 carrying two accepted edits, the second on the last line, and the floor hint removed. GLM-5.2 through
opencode 1.18.18 solved it **5 of 5** (job `b52a9-glm5x-run1`, all 5 concurrent). Summing a passage's edits
is a stated rule the model applies reliably. The current build keeps that case and adds the log level
(latest line per edit), which reverses the exact-length cut and the PS-10 deferral.

## 9. Isolation proof

In a fresh container built from `environment/` (network off): a whole-filesystem search for `solve.sh`,
`test.sh`, `verifier.json`, `score.py`, `test_outputs.py`, `derive_gold.py`, `discrimination.py`,
`golden_trajectory.json`, `input_hashes.json` and every deliverable name returns nothing outside Python's
own site-packages; `/tests`, `/solution` and `/logs/verifier` are absent; no file contains the gold-only
string `PS-10,4,STRADDLES_BREAK`, while the positive control `2026-09-09,ED-03` is found in the edit register. The
Dockerfile copies `input/` only. Inputs are read-only in the image (advisory: root can still write), and
nothing on the grading path reads `/app/input`; `check_inputs.py` records their hashes as evidence only.

## 10. Reproducing this

```bash
# gold, re-derived from the shipped inputs, and every verifier pin checked against it
python3 tests/derive_gold.py

docker build -t b52a9 environment/
# equivalence, breaking and wrong-reading suites
docker run --rm --network none -v "$PWD/tests:/tests:ro" -v "$PWD/solution/files:/gold:ro" \
    -v "$PWD/environment/input:/inputs:ro" b52a9 python3 /tests/discrimination.py
# oracle and nop
harbor run -p . -a oracle -y
harbor run -p . -a nop -y
```
