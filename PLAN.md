# writing-b52-a9-manuscript-page-ledger-recompute: phase-wise plan

Target: the same accepted shape as `tech-mg-it-b10-a8-practice-log-spring-redating` (FINAL-v3, IN-BAND).
Package: `writing-b52-a9-manuscript-page-ledger-recompute/`. Author tools that are not part of the
package: `tools/`.

| phase | what | owner | status |
|---|---|---|---|
| 0 | Intake: diff the mined practice-log package against its accepted version to learn the standard | Claude | done |
| 1 | Static rework: instruction, inputs, crux, verifier, harness, gold, docs | Claude | done |
| 2 | Local verification in the task image (gold, discrimination, harness attacks, isolation) | Claude | done |
| 3 | Resolve the 4 preflight NEEDS_REVIEW flags | Claude (you sign off) | done, in `review.csv` |
| 4 | Layer 2: oracle + nop through Harbor, then the GLM-5.2 battery | **you** | round 1 done (5/5, too easy); round 2 pending |
| 5 | Calibrate: in band → package; out of band → one lever, re-verify, re-run the battery | you (+ Claude) | build v3 hardened and verified; re-run pending |
| 6 | Package: `evaluations/`, golden trajectory, README §8, `review.csv` Layer 2 rows, zip | you (+ Claude) | pending |

---

## Phase 0: what the reference teaches (done)

The accepted practice-log bundle differs from its mined version in these ways, and each one is applied here:

1. **`consistency/` and mined `evaluations/{oracle,nop}` removed.** `evaluations/` holds only the package's
   own battery: `difficulty/r1..rN` (the pre-registered lane) and `solvability/r1` (a passing spare).
2. **Instruction rewritten as the requester's own paragraph:** absolute paths named once, no template residue,
   and no sentence that names the deciding case or a graded figure (the reference removed "16 of them at night").
3. **Difficulty moved into the data:** a unit-of-analysis trap with the unit *defined* in the rules (not a
   recipe), plus literally true requester leads that invite the shortcut. Stated-rule cruxes were solved by
   every run.
4. **Verifier rebuilt:** few checks, core-gated; trap rows isolated; the rest graded by `table_equals` with a
   row-set lock; figures by `object_equals`; the key-set guard incidental; no existence-only checks.
5. **Accepted harness:** symlink/size guard + snapshot, controlled interpreter, input-integrity evidence,
   core gate, truncation guard.
6. **Author tools shipped in `tests/`:** `derive_gold.py`, `discrimination.py`, `check_inputs.py`,
   `input_hashes.json`.
7. **Base image pinned by digest.**
8. **Golden trajectory = an unedited reward-1.0 GLM-5.2 run**, replayed by `solve.sh`.
9. **README (10 sections) + `review.csv`** in the client's layer vocabulary, every figure read from shipped files.

## Phase 1: static rework (done)

See README §2 for the full was/now/why table. In short:

- **Crux.** The edit register is now keyed by edit (`edit_code,passage_id,line_change,edit_state,description`)
  and the ledger no longer carries an edit code. PS-07 has two accepted edits: ED-05 (−21) in place, and
  ED-09 (−5) on the register's **last** line. Together they take 25 lines to −1, so PS-07 floors at 1.
  The spec defines length over "every accepted edit proposed for it". A `passage_id → edit` dict keeps only
  ED-09, so PS-07 becomes 20 lines, and five rows and four figures move (W1).
- **Leak removed.** "One of the cuts is as long as the passage it is cutting, so do not let that passage
  vanish…" is gone. PS-04 (22 lines, −22) is still in the data, and the floor rule is still in the spec.
- **Boundary.** PS-11 now ends exactly on line 120, the last line of page 4. That catches the off-by-one
  last-line reading.
- **Gold:** 2 straddling / 2 deferred / 2 floored / 6 wholly / final page 5 (was 3/2/1/6/5).
- **Checks:** 22 all-core → 6 (5 core + 1 incidental). The engine is swapped for the accepted bundle's
  (it has `table_equals` / `object_equals`).

## Phase 2: local verification (done, all in the task image)

| check | result |
|---|---|
| `tests/derive_gold.py` | gold agrees with the inputs; every verifier pin agrees with the gold |
| `tests/discrimination.py` | 34/34: 11 equivalence pass, 15 breaking fail on their own check, W1-W8 fail as declared; all 9 readings give distinct outputs |
| `test.sh` gold / gold + scratch | 1.0 / 1.0 |
| `test.sh` nop / header + `{}` / symlinks / planted hooks + wrong page | 0.0 / 0.0 / 0.0 / 0.0 |
| `test.sh` extra JSON key | 0.833333 (incidental only) |
| `solve.sh` + `test.sh` (oracle path) | 1.0, `agent/trajectory.json` written |
| golden trajectory's script | reproduces `solution/files` byte for byte |
| isolation (fresh container) | no harness or gold files, no gold-only string; positive control found |

Local caveat: this sandbox's network blocks Debian mirrors, so the local image skipped the Dockerfile's
`apt-get` layer (bash/curl/git/unzip; nothing the verifier uses). The shipped Dockerfile is unchanged apart
from the digest pin. **Your Harbor oracle run in Phase 4 is the first full build of the shipped Dockerfile;
check that it builds.**

## Phase 3: the 4 NEEDS_REVIEW flags (done, in `review.csv`; read and sign off)

| preflight flag | resolution | where |
|---|---|---|
| `layer1_clarity_scope` (interface vs method) | interface-only instruction/format; rules state the domain, never a method; 9 guess points each settled by a quoted sentence | `review.csv` "Layer 1 · Clarity and scope" |
| `layer1_realism_leakage__domain_correctness` (fictional or cited?) | fictional and self-contained; the 30-line page is the fixture's own stated spec; nothing cited | "Layer 1 · Realism and leakage" (a) |
| `layer1_realism_leakage__workflow_realism` | repaginating flagged/queried passages after an edit round is routine production work; accepted/deferred = tracked changes; two readers' cuts on one draft passage exceeding it is realistic | same row (b) |
| `layer1_realism_leakage` (roll-up) | children resolved; the instruction's leak removed | same row (c) |

## Phase 4: Layer 2 battery (you)

Harbor must run the task **exactly as committed**. Any edit afterwards changes `task_checksum` and voids
the runs.

Run everything from the repository root (the folder holding `glm.env`, `tools/` and the task folder).
The job file `tools/glm5x.yaml` carries the reference battery's agent block (opencode 1.18.18,
`glmproxy/glm-5.2`, same provider config), 5 attempts, concurrency 2; it was validated with
`harbor run --print-config` and `--dry-run` (Harbor 0.23.0: "Dry run OK — 5 trial(s)").

```bash
# 4a. sanity: shipped Dockerfile builds; oracle 1.0 (6/6); nop 0.0
harbor run -p writing-b52-a9-manuscript-page-ledger-recompute -a oracle --job-name b52a9-oracle -y
harbor run -p writing-b52-a9-manuscript-page-ledger-recompute -a nop    --job-name b52a9-nop    -y

# 4b. the battery: GLM-5.2 x 5
harbor run -c tools/glm5x.yaml --env-file glm.env \
    --job-name b52a9-glm5x-$(date -u +%Y%m%dT%H%M%SZ) -y

# 4c. classify every run
python3 tools/triage_trials.py jobs/<the b52a9-glm5x-... folder>
```

**Pre-register before you look at results:** the lane is the **first five trials by `started_at`**
(the reference used the first four; use whichever your gate states). Every shipped run must share one
`task_checksum`; the triage tool prints the checksums it saw.

For every **failure**, `triage_trials.py` names the reading it matches (W1-W8) or `UNMATCHED`. Then open
its `agent/trajectory.json` and classify it:

- **MODEL**: it misapplied a stated rule (e.g. a dict that dropped ED-05, never checked for repeated
  passage ids).
- **TEXT-SUPPORTED**: it quoted a sentence of ours that supports the wrong reading (e.g. read "the edits
  from the second read" as revisions *and* cited wording for it). That is a fairness defect: fix the
  wording, then re-run the whole battery.
- **INFRA**: timeout, exception, or truncation. Exclude it and re-run.

## Phase 5: calibrate (band: 1-3 of 5 strict passes in the lane)

| lane result | action |
|---|---|
| **1-3 / 5**, failures MODEL | in band. Go to Phase 6. |
| any failure TEXT-SUPPORTED | fix that wording first (it is a defect whatever the rate), then re-run the full battery |
| **4-5 / 5** (too easy) | apply **one** hardening lever, re-verify, re-run the battery |
| **0 / 5** (too hard) | apply **one** easing lever, re-verify, re-run the battery |

### Round log

| round | build | change | GLM-5.2 (lane) | verdict |
|---|---|---|---|---|
| 1 | v2 | edit-keyed register; PS-07 two accepted edits (second on the last line); floor hint removed | **5/5** (`b52a9-glm5x-run1`, concurrency 5, 9m 7s) | too easy |
| 2 | v3 | register made a dated **log**: an edit stands as its latest line. Second read re-logs ED-01 (+4 → +6), ED-03 (PS-04's exact cut, ACCEPTED → DEFERRED) and ED-07 (PS-10, DEFERRED → ACCEPTED); ED-09 stays as PS-07's second edit. PS-11 17 lines (ends on line 150). Lead: "Nothing has been struck from it; every line in it is a call one of us made." New trap check `register_trap_ps10`; 7 checks | pending (`b52a9-glm5x-run2`) | |

Gold v3: 3 straddling / 2 deferred / 1 floored / 6 wholly / final page 6. Local: derive_gold clean, discrimination
38/38, oracle 1.0, nop 0.0, symlinks 0.0, planted hooks 0.0, extra key 0.857143.

Hardening levers for round 3 (if v3 is still 4-5/5), mildest first; each keeps the definitions in the rules:

- **H1:** a third line for one edit: ED-07 ACCEPTED → DEFERRED → ACCEPTED with the last line revising +14 → +11,
  so "any ACCEPTED line", "first line" and "any DEFERRED line" readings all diverge on one passage.
- **H2:** ledger order ≠ id order: list PS-06 before PS-05 (a chapter move). The spec already says passages run
  "in the order the ledger lists them"; runs that sort by id fail.
- **H3:** a second two-edit passage whose edits sit on different reads with mixed states (e.g. `ED-10,PS-10,-3,…`
  accepted on the second read), so a passage-keyed dict loses an accepted edit on a second passage.

Easing levers for round 3 (if v3 is 0/5), mildest first:

- **E1:** delete the lead "Nothing has been struck from it; every line in it is a call one of us made."
- **E2:** drop the ED-01 revision line (fewer re-logs; the two state flips stay).
- **E3:** add to `layout_spec.md`: "The second read revisited some first-read calls." (near-recipe; last resort)

After **any** lever:

```bash
python3 tests/derive_gold.py --write            # new gold (in the package dir)
python3 ../tools/build_verifier.py .            # new pins; edit its trap table(...) calls if the trap rows change
python3 tests/derive_gold.py                    # must print "gold agrees ... every verifier pin agrees"
python3 -c "import hashlib,json,pathlib as p;print(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.Path('environment/input').iterdir())},indent=2))" > tests/input_hashes.json
docker build -t b52a9 environment/
docker run --rm --network none -v "$PWD/tests:/tests:ro" -v "$PWD/solution/files:/gold:ro" \
    -v "$PWD/environment/input:/inputs:ro" b52a9 python3 /tests/discrimination.py   # 0 problems
# update tools/triage_trials.py READINGS / discrimination.py expectations if a lever adds a reading
# rewrite golden_trajectory.json's script only if the rules changed (it computes, it does not paste)
```

Then update README §2 (rows for the changed files), §4 (key and hand checks), §5 (readings table) and
`review.csv`, and **re-run the full battery**. Earlier builds go in README §8 in words only, as the
reference does.

## Phase 6: package (you, Claude can do the write-up from your job folder)

1. **`evaluations/`**: copy each lane trial into `difficulty/r1..r5` (in `started_at` order) and one passing
   spare into `solvability/r1`. Each slot keeps `agent/trajectory.json`, `artifacts/`, `config.json`
   (**redact API keys and the gateway IP**), `result.json` and `verifier/*` (the reference kept exactly these).
   Delete `evaluations/.gitkeep`.
2. **Golden trajectory**: copy a *different* passing run's `agent/trajectory.json` over
   `solution/golden_trajectory.json` as is. `solve.sh` detects the ATIF form and replays it as
   `oracle-replay`. Re-run `harbor run -p . -a oracle` once more (expect 1.0). The trajectory lives in
   `solution/`, which is outside the checksummed environment, so check whether your Harbor version
   includes `solution/` in `task_checksum`. If it does, promote the trajectory *before* the battery,
   using a pass from a pilot run.
3. **README §8**: one row per trial (started, trial id, reward, slot, checks, what happened), lane and pooled
   rates, the failure census by reading, the MODEL/TEXT classification, and any disclosed fairness point
   (e.g. a run that followed the second-read lead).
4. **`review.csv`**: fill the `PENDING_BATTERY` rows (Layer 2 Difficulty, Cross-trial · Calibration) and the
   "FILL FROM BATTERY" cells; set their status to `FIXED_AND_VERIFIED`.
5. **Remove the README status banner** at the top. Zip the package folder only (not `PLAN.md` / `tools/`) as
   `writing-b52-a9-manuscript-page-ledger-recompute-FINAL-v1-IN-BAND.zip`.

### Final checklist

- [ ] oracle 1.0 (6/6) and nop 0.0 on the committed package
- [ ] lane within 1-3/5; every failure read and attributed; one checksum across shipped runs
- [ ] `derive_gold.py` and `discrimination.py` clean on the final package
- [ ] `evaluations/` = `difficulty/r1..r5` + `solvability/r1`, keys redacted
- [ ] golden trajectory = unedited passing GLM run
- [ ] README §8 and `review.csv` Layer 2 rows filled, banner removed
- [ ] no `consistency/`, no stray files
