"""Evidence-only input integrity check (ENV-5).

Compares the SHA-256 of every file under /app/input, after the agent phase, with the
hashes pinned in tests/input_hashes.json when the fixture was generated, and prints the
result as JSON (test.sh saves it to /logs/verifier/input_integrity.json). It never
affects the reward: every graded expectation is fixed in verifier.json, so nothing on
the grading path reads the live inputs.
"""
import hashlib
import json
from pathlib import Path

TESTS = Path(__file__).resolve().parent
pinned = json.loads((TESTS / "input_hashes.json").read_text(encoding="utf-8"))
root = Path("/app/input")
live = {}
if root.is_dir():
    live = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.iterdir()) if p.is_file()}
mismatched = sorted(name for name in set(pinned) | set(live) if pinned.get(name) != live.get(name))
print(json.dumps({"intact": not mismatched, "mismatched": mismatched,
                  "pinned": pinned, "live": live}, indent=2))
