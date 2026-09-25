#!/bin/bash
# Harbor verifier entrypoint. Harbor copies this to /tests/test.sh and runs it; the reward is
# read back from /logs/verifier/reward.txt.
#
#   1. Guard and snapshot. Only the two named deliverables are graded, and each only when it
#      is a regular file (not a symlink, not a directory) of at most 5 MB. Those are copied
#      into a fresh directory, and every check reads that snapshot, never /app itself.
#   2. Input integrity, evidence only. The SHA-256 of each file under /app/input is compared
#      with tests/input_hashes.json and written to input_integrity.json. It never touches the
#      reward: no graded expectation reads the live inputs.
#   3. pytest, for Harbor's per-check grid and the CTRF report. As each check runs,
#      test_outputs.py records its outcome to checks.jsonl.
#   4. score.py decides the reward from checks.jsonl: core checks gate it, incidental checks
#      add weight. It is NOT the pytest exit code.
#
# Every check is deterministic (no LLM judge, no network). A run whose agent was cut off at the
# harness's output-token cap before writing its deliverables is not graded: score.py exits
# non-zero, no reward.txt is written, and this script exits 2, so the run is classified as
# ineligible instead of being reported as reward 0.0.
mkdir -p /logs/verifier
rm -f /logs/verifier/checks.jsonl /logs/verifier/reward.txt /logs/verifier/score.json

# A controlled interpreter: fixed PATH, nothing inherited through PYTHON* variables, and
# python's isolated mode for every call.
export PATH=/usr/local/bin:/usr/bin:/bin
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP
PY=/usr/local/bin/python3

SNAP=$(mktemp -d /tmp/graded.XXXXXX)
for f in page_register.csv results.json; do
    src="/app/$f"
    if [ -L "$src" ]; then
        echo "guard: $src is a symlink; not graded"
    elif [ -f "$src" ] && [ "$(stat -c %s "$src")" -le 5242880 ]; then
        cp "$src" "$SNAP/$f"
    else
        echo "guard: $src is missing, not a regular file, or over 5 MB; not graded"
    fi
done
export HARBOR_TASK_WORKSPACE="$SNAP"

"$PY" -I /tests/check_inputs.py > /logs/verifier/input_integrity.json 2>&1 || true

cd /tests || exit 2
"$PY" -I -m pytest --rootdir=/tests -p no:cacheprovider \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_outputs.py \
    -rA

if ! "$PY" -I /tests/score.py > /logs/verifier/score.json; then
    rm -f /logs/verifier/reward.txt
    cat /logs/verifier/score.json
    exit 2
fi
"$PY" -I -c "import json;print(json.load(open('/logs/verifier/score.json'))['reward'])" \
    > /logs/verifier/reward.txt

cat /logs/verifier/score.json
exit 0
