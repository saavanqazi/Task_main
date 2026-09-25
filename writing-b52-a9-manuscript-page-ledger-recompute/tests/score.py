#!/usr/bin/env python3
"""score.py — turn per-verifier outcomes into one reward, with a core gate.

The client register's first and highest-volume finding was all-or-nothing aggregation: a
single incidental check collapsing a substantively perfect submission to 0.0, with
"submissions scoring 76/78, 64/65, 63/64 and 30/31" all rewarded exactly the same as
delivering nothing.

So the checks are split by `metadata.tag`:

  core        the checks that decide whether the work is RIGHT — the deliverables exist
              and their graded content is correct. All of them must pass. If one fails
              the answer is wrong, and reward is 0.
  incidental  the check on results.json tidiness (results_keyset). It carries weight and
              is added to the reward when it passes. It can never produce a 0 on its
              own.

Outcomes are read from checks.jsonl, written by test_outputs.py as each check runs, so the
reward agrees with the pytest grid. Every check here is deterministic; the infra_error path
below is kept from the shared harness and is never taken by this task.

The same holds for a run the agent harness cut off. If the agent's last model turn stopped
because it hit the harness's output-token cap, and a deliverable is missing, the missing file
measures the cap, not the model's ability to do the task (client standard TRL-1 rule 4: "stop
reason length before deliverables: harness limit, exclude and re-run"). Scoring it 0.0 would
count it as a valid failure. So this script refuses to emit a reward for it either.

Gold passes everything and scores exactly 1.0, so the oracle gate is unchanged.
"""
import json
import os
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))

from rl_world_verifiers.models import VerifierSpec, effective_weights

CHECKS_PATH = Path(os.environ.get("VERIFIER_CHECKS_PATH", "/logs/verifier/checks.jsonl"))
SPEC = VerifierSpec.model_validate_json((TESTS_DIR / "verifier.json").read_text(encoding="utf-8"))
WEIGHTS = effective_weights(SPEC.verifiers)

seen, infra = {}, []
try:
    for line in CHECKS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("infra_error"):
            infra.append(row["name"])
        else:
            seen[row["name"]] = row
except FileNotFoundError:
    pass

if infra:
    print(json.dumps({"reward": None, "infra_error": sorted(set(infra))}, indent=2))
    sys.stderr.write(
        "INFRASTRUCTURE FAILURE: no judge verdict for " + ", ".join(sorted(set(infra)))
        + ". Refusing to emit a reward; this run is not graded.\n"
    )
    sys.exit(3)

#: The graded deliverables, and where test.sh snapshotted the ones that passed its guard.
DELIVERABLES = ("page_register.csv", "results.json")
WORKSPACE = Path(os.environ.get("HARBOR_TASK_WORKSPACE", "/app"))
#: OpenCode streams one JSON event per line to this file (Harbor tees it there in the
#: container the verifier shares). Absent for the oracle and for re-scoring a saved answer.
AGENT_LOG = Path(os.environ.get("AGENT_LOG_DIR", "/logs/agent")) / "opencode.txt"


def final_stop_reason():
    """The stop reason of the agent's last model turn, or None when there is no agent log.

    Only the last step_finish event counts. Every tool call OpenCode runs is followed by its own
    step_finish, so a line written into the log from inside a tool call is never the last one.
    """
    try:
        text = AGENT_LOG.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    reason = None
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "step_finish":
            reason = (event.get("part") or {}).get("reason")
    return reason


missing = [f for f in DELIVERABLES if not (WORKSPACE / f).is_file()]
if missing and final_stop_reason() == "length":
    print(json.dumps({"reward": None, "ineligible": "agent_output_truncated",
                      "missing_deliverables": missing}, indent=2))
    sys.stderr.write(
        "HARNESS LIMIT: the agent's last turn stopped at the output-token cap before "
        + ", ".join(missing) + " existed. Refusing to emit a reward; this run is not graded.\n"
    )
    sys.exit(4)

results, core_failures, earned = [], [], 0.0
for definition in SPEC.verifiers:
    tag = definition.metadata.tag or "core"
    row = seen.get(definition.name)
    ok = bool(row and row.get("success"))
    detail = (row or {}).get("detail") or ("" if row else "check was never recorded")
    results.append({"name": definition.name, "tag": tag, "passed": ok,
                    "weight": WEIGHTS[definition.name], "detail": str(detail)[:200]})
    if ok:
        earned += WEIGHTS[definition.name]
    elif tag == "core":
        core_failures.append(definition.name)

all_passed = all(r["passed"] for r in results)
reward = 0.0 if core_failures else (1.0 if all_passed else round(min(earned, 1.0), 6))
print(json.dumps({
    "reward": reward,
    "core_failures": core_failures,
    "passed": sum(1 for r in results if r["passed"]),
    "total": len(results),
    "checks": results,
}, indent=2))
