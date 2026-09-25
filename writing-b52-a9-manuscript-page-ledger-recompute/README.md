# writing-b52-a9-manuscript-page-ledger-recompute

Built to the Non-Connector Task Standard v2 (2026-09-04). Every figure below is read from a file shipped in
this package (`tests/`, `solution/files/`, and, once the battery is in, `evaluations/`); earlier builds are
described in words only.

> **Status: static rework complete and verified locally; Layer 2 battery pending.** Sections 8 and the
> `Layer 2 Difficulty` / `Cross-trial · Calibration` rows of `review.csv` are filled in from the GLM-5.2
> battery (see `PLAN.md` at the repository root). Nothing in sections 1-7 or 9-10 depends on it.

## 1. Task description

An author has to hand a manuscript back to the press with a page number against every passage they flagged,
after an edit round. The agent gets four files: the passage ledger (12 flagged passages, in manuscript order,
with drafted line counts), the edit register (9 edits, each naming the passage it was proposed for, its line
change, whether it was ACCEPTED or DEFERRED and a one-line description), the press's layout spec, and the
submission format. It delivers the page register as a CSV (one row per passage: the page the passage now
starts on and how it sits there) and five roll-up figures in `results.json`.

The work is real repagination bookkeeping: 30 lines a page, passages back to back in ledger order, a
passage's length is its drafted lines plus the line change of **every accepted edit proposed for it**, a
deferred edit changes nothing, a passage is never shorter than 1 line (and the held line still pushes every
later passage down), and each passage is recorded as floored, carrying a deferred edit, crossing a break or
sitting wholly on a page, in that priority.

**The population is not handed over.** The instruction names no count, page or passage; it names the four
treatments only by pointing at the layout rules.

**Why it is hard.** The edit register is keyed by edit, not by passage, and PS-07 carries two accepted
edits: ED-05 (−21, "Cut the harbour flashback") in register order, and ED-09 (−5, "Drop the second foghorn
paragraph") on the register's last line. Together they take PS-07's 25 drafted lines to −1, so it floors at
1 line. The definition is in the spec ("the line change of every accepted edit proposed for it"); no
sentence describes PS-07 or says a passage may carry two edits. The natural join (a `passage_id → edit`
dict) silently keeps only ED-09: PS-07 becomes 20 lines, and five later rows and four of the five figures
move. The requester's one true sentence about the register ("the edits from the second read are the ones at
the bottom") invites that last-wins reading without supporting it. A second, independent rule check is
PS-04, whose only edit cuts exactly its 22 drafted lines. The mined instruction told the agent about this
case ("do not let that passage vanish"). That sentence is gone, so the agent has to apply the floor rule
itself.

## 2. Departures from the mined version

The mined package arrived with a template-residue instruction that disclosed the floor trap, a ledger that
pinned one edit code per passage (so no join was needed), 22 checks all core (two existence-only checks,
a row-count check, twelve regex row pins, a core key-set guard, five single-figure checks), a harness with no
guards, a shared engine without the compound comparators, and GLM-5.2 solving 3/3 envelope renderings.

| file | was | now | why |
|---|---|---|---|
| `instruction.md` | "# Task" heading, `---` dividers, relative `input/…` paths, deliverables named twice, "must be your final action; confirm each one exists", a "Working environment" block, and "One of the cuts is as long as the passage it is cutting, so do not let that passage vanish and pull everything else back with it" | the requester's own paragraph; every path absolute and named once; the floor hint removed; the register described as it is ("each edit, the passage it was proposed for, …; the edits from the second read are the ones at the bottom"); the five figures named by pointing at the layout rules | INS-1, INS-11, INS-13, INS-15, PKG-14; the removed sentence named the deciding case and its fix (INS-8/FIX-3) |
| `environment/input/passage_ledger.csv` | `passage_id,drafted_lines,edit_code` (one edit code per passage, `NONE` for none); PS-11 20 lines | `passage_id,drafted_lines`; PS-11 24 lines | the ledger no longer does the join; PS-11 now ends on line 120, the last line of page 4, which separates an off-by-one last-line reading (W7) |
| `environment/input/edit_register.csv` | `edit_code,line_change,edit_state`; 8 edits, one per passage | `edit_code,passage_id,line_change,edit_state,description`; 9 edits; PS-07 carries ED-05 (−21) and ED-09 (−5, last line); ED-07 (DEFERRED) +9 → +14 | the crux (§5); descriptions make the two PS-07 edits visibly distinct cuts (fairness), and ED-07's size separates W6 from W7 without touching the gold |
| `environment/input/layout_spec.md` | "plus the line change of the edit proposed for it"; "A passage whose edit was deferred"; "Where an accepted edit would take it under that" | "plus the line change of every accepted edit proposed for it"; "`edit_register.csv` names the passage each edit was proposed for"; "A passage with a deferred edit"; "Where its accepted edits would take it under that" | the unit is stated as a definition where the rules live (FIX-2); the singular wording implied one edit per passage |
| `environment/input/submission_format.md` | "One row per record, keyed by `passage_id`" and "in the order the file lists them" (order ungraded); a thousands-separator / currency clause for page numbers | "One row per passage in `passage_ledger.csv`, in any order, with `passage_id` in the ledger's own form"; "`page_number` … a plain whole number" | P6 over-specification: order was demanded but never graded; the currency clause did not fit page numbers |
| `environment/Dockerfile` | `python:3.12-slim-bookworm` unpinned | pinned by digest `@sha256:4766d8…58a2` (same base as the accepted Task_17 bundle) | ENV-3 |
| `task.toml` | `artifacts = []`, no reward shape | two artifact paths; `reward_shape`; description rewritten | TOML-4/5, HAR-2, PKG-14 |
| `tests/verifier.json` | 22 checks, all core: `register_exists`, `results_exists`, `register_row_count`, `ps01_pin`…`ps12_pin` (regex, ungraded order), core `results_keyset`, five `result_*` figures | 6 checks (5 core, 1 incidental), §3; every pin read from the gold files by `tools/build_verifier.py`; every `why_justification` quotes its sentence verbatim | P0 #1, VER-21, DIS-2, GLD-11 |
| `tests/rl_world_verifiers/` | the b52 engine (no `table_equals` / `object_equals`) | the engine vendored in the accepted Task_17 bundle (compound comparators, equivalence contract) | the row and figure checks need `table_equals` / `object_equals` |
| `tests/test.sh`, `score.py`, `test_outputs.py` | pytest + a score over all checks; no guards | the accepted Task_17 harness with this task's deliverables: symlink/size guard and snapshot, controlled interpreter, input-integrity evidence, core gate + weighted fraction, output-truncation guard | HAR-1..11, VER-25, ENV-5 |
| `tests/` (new) | none | `check_inputs.py`, `input_hashes.json`, `derive_gold.py`, `discrimination.py` (author tools, not on the reward path) | FIX-11, GLD-11, VER-24 |
| `solution/files/` | the one-edit-per-passage gold | re-derived from the inputs by `tests/derive_gold.py` | GLD-11 |
| `solution/golden_trajectory.json`, `solve.sh` | 6 hand-built steps that `cat` the gold into place | 6 steps that read the inputs and compute the answer (verified to reproduce the gold); `solve.sh` also replays an ATIF trajectory, so a reward-1.0 GLM-5.2 run can be promoted in place | PKG-8 (promotion is a Phase 6 step in `PLAN.md`) |
| `consistency/`, `evaluations/{oracle,nop}` | mined evidence for the old fixture | removed; `evaluations/` holds this package's runs | PKG-1 |

## 3. Declarations

- **Reward shape:** core-gated weighted fraction over 6 equally weighted checks (as `task.toml`
  `reward_shape` and `tests/score.py`): any failed core check scores 0; otherwise the passing weight; 1.0
  only when every check passes.
- **Checks by kind:**
  - core, deterministic (5): `register_header`; `register_trap_ps04` (the exact-length cut);
    `register_trap_ps07` (the two-edit passage); `register_rows` (the other 10 passages cell by cell, row set
    locked to the 12 ledger ids, columns closed); `results_figures` (five figures, key set open).
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
- Key: 12 passages; the manuscript runs to line 133; `straddling_passage_count` 2, `deferred_edit_count` 2,
  `length_floored_count` 2, `wholly_on_page_count` 6, `final_page_count` 5.

| passage | drafted | accepted edits | lines | page | verdict |
|---|---|---|---|---|---|
| PS-01 | 12 | ED-01 +4 | 1-16 | 1 | WHOLLY_ON_PAGE |
| PS-02 | 18 | none | 17-34 | 1 | STRADDLES_BREAK |
| PS-03 | 9 | ED-02 −3 | 35-40 | 2 | WHOLLY_ON_PAGE |
| PS-04 | 22 | ED-03 −22 → 0, held at 1 | 41 | 2 | LENGTH_FLOORED |
| PS-05 | 14 | none | 42-55 | 2 | WHOLLY_ON_PAGE |
| PS-06 | 7 | none (ED-04 +6 deferred) | 56-62 | 2 | EDIT_DEFERRED |
| PS-07 | 25 | ED-05 −21, ED-09 −5 → −1, held at 1 | 63 | 3 | LENGTH_FLOORED |
| PS-08 | 11 | ED-06 +2 | 64-76 | 3 | WHOLLY_ON_PAGE |
| PS-09 | 16 | none | 77-92 | 3 | STRADDLES_BREAK |
| PS-10 | 8 | none (ED-07 +14 deferred) | 93-100 | 4 | EDIT_DEFERRED |
| PS-11 | 24 | ED-08 −4 | 101-120 | 4 | WHOLLY_ON_PAGE |
| PS-12 | 13 | none | 121-133 | 5 | WHOLLY_ON_PAGE |

- Hand checks of the deciding rows (GLD-4): **PS-04** 22 − 22 = 0 < 1, held at 1 line on line 41 →
  page 2 (lines 31-60), floored. **PS-07** 25 − 21 − 5 = −1 < 1, held at 1 line on line 63 → page 3,
  floored; with ED-09 alone it would be 20 lines (63-82), with ED-05 alone 4 lines. **PS-11** ends on line
  120 = 4 × 30, the last line of page 4, so it sits wholly on page 4. **PS-12** starts on line 121 → page 5;
  the last line, 133, is on page 5.

## 5. Difficulty design (declared before the measuring battery)

**Crux: unit of analysis in the edit register** (sanctioned pattern). The register is keyed by edit, and the
length rule is defined over every accepted edit proposed for a passage. The deciding passage's second edit is
far from its first (the register's last line), and one literally true requester sentence invites reading the
later edit as a revision of the earlier one ("the edits from the second read are the ones at the bottom").
The definition is stated where the rules live. No sentence describes PS-07 or tells the reader what to do
with it, and the descriptions show two distinct cuts. A secondary rule check, the exact-length cut on PS-04,
is no longer flagged in the instruction.

Expected wrong readings, each recomputed from the inputs by `tests/discrimination.py` (all nine readings,
gold included, give pairwise-distinct deliverables):

| id | reading | what it changes | checks that fail |
|---|---|---|---|
| W1 | one edit per passage, the last listed wins (a `passage_id → edit` dict) | PS-07 20 lines; PS-07-PS-12 move; figures 4/2/1/5/6 | `register_trap_ps07`, `register_rows`, `results_figures` |
| W2 | one edit per passage, the first listed wins | PS-07 4 lines, WHOLLY; PS-11 straddles | `register_trap_ps07`, `register_rows`, `results_figures` |
| W3 | one output row per register row (a left join) | 13 rows, PS-07 twice | `register_trap_ps07`, `register_rows`, `results_figures` |
| W4 | no floor: a passage cut to nothing vanishes | PS-04, PS-07 not floored; later rows move | both traps, `register_rows`, `results_figures` |
| W5 | floored, but the held line not counted | PS-09, PS-12 move | `register_rows` |
| W6 | deferred edits counted in the length | PS-11, PS-12 move; final page 6 | `register_rows`, `results_figures` |
| W7 | the last line taken one past the passage | PS-11 straddles | `register_rows`, `results_figures` |
| W8 | geometry ranked above a deferred edit | PS-06 straddles | `register_rows`, `results_figures` |

Under W1 the output passes every check a run can apply to itself: 12 rows, one per passage, all four
verdicts used, the figures summing to 12.

## 6. Probes and solvers

- **Discrimination** (`tests/discrimination.py`, deterministic): **34 of 34 as expected**: 11 equivalence
  variants pass (row shuffle, JSON key order, JSON figures as N.0, quoted fields, CRLF, no trailing newline,
  BOM, page numbers as N.0, padded fields, lower-case verdicts, an extra scratch file); 15 breaking variants
  fail on their own check (a page off, a verdict wrong, a row deleted, appended or duplicated, an extra column,
  each trap row wrong, a figure off by one, empty deliverables, each deliverable deleted, bare header + `{}`,
  figures as a list, an extra JSON key on `results_keyset`); the 8 wrong readings W1-W8 fail as declared.
- **Reward floor** (shipped `test.sh`): empty workspace 0.0; bare header + `{}` 0.0.

## 7. Environment tests

Run with the shipped `test.sh` in the task image: gold 1.0 (6/6 checks, 14 pytest items passed); gold +
unrelated scratch files 1.0; both deliverables replaced by symlinks to the gold 0.0 (guard); planted
`conftest.py`, `sitecustomize.py` and `usercustomize.py` beside a CSV with one wrong page 0.0 (the plants
have no effect; `register_rows` fails); extra key in `results.json` 0.833333 (incidental only); nop 0.0;
`solve.sh` (oracle path) 1.0 with `agent/trajectory.json` written. `input_integrity.json` reports the inputs
intact in every run.

## 8. Trial results

**PENDING.** Filled in from the GLM-5.2 battery (opencode 1.18.18, `glmproxy/glm-5.2`): one job, every run on
one `task_checksum`, lane pre-registered as the first five by `started_at`. Each run is classified with
`python3 tools/triage_trials.py <job_dir>` (repository root), which names the reading its deliverables match
(GOLD or W1-W8) and lists the rows it got wrong. The table layout to fill in:

| started (UTC) | trial | reward | slot | checks | what happened |
|---|---|---|---|---|---|

## 9. Isolation proof

In a fresh container built from `environment/` (network off): a whole-filesystem search for `solve.sh`,
`test.sh`, `verifier.json`, `score.py`, `test_outputs.py`, `derive_gold.py`, `discrimination.py`,
`golden_trajectory.json`, `input_hashes.json` and every deliverable name returns nothing outside Python's
own site-packages; `/tests`, `/solution` and `/logs/verifier` are absent; no file contains the gold-only
string `PS-07,3,LENGTH_FLOORED`, while the positive control `ED-09` is found in the edit register. The
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
