"""Test: pre_commit without response = orphaned commitment."""
import sys, os, tempfile, json, zipfile
from pathlib import Path

sys.path.insert(0, r"C:\Users\dell\epi-recorder")
from epi_recorder.api import record

# Simulate crash: pre_commit logged, but process "dies" before response
test_path = "epi-recordings/test_precommit_crash.epi"
try:
    with record(test_path, goal="pre-commit crash simulation", auto_sign=True) as epi:
        # Log pre_commit as if wrapper fired before API call
        epi.log_step("llm.pre_commit", {
            "provider": "openai",
            "model": "gpt-4",
            "message_count": 1,
            "timestamp": "2026-07-27T00:00:00Z",
        })
        # llm.request is NOT logged (process "crashed" mid-way)
        # llm.response is NOT logged
        print("pre_commit logged, simulating crash...")
        # process exits here in the real scenario
    print("CRASH TEST: artifact completed (clean exit)")
except Exception as e:
    print(f"CRASH TEST ERROR: {e}")

# Now run epi verify on it to check AUD-CO-01 detects the orphan
print("\n--- Running epi verify ---")
import subprocess
result = subprocess.run(
    ["python", "-m", "epi_cli.verify", test_path],
    capture_output=True, text=True, cwd=r"C:\Users\dell\epi-recorder"
)

# Check output for orphan detection
output = result.stdout + result.stderr
print(output[:2000])

# Verify the orphan was detected
passes = all([
    "pre_commit" in output.lower(),
    ("orphan" in output.lower() or "never executed" in output.lower() or "missing" in output.lower() or "committed but never" in output.lower()),
])

if passes:
    print("\nPASS: AUD-CO-01 detected orphaned pre_commit")
else:
    print("\nFAIL: AUD-CO-01 did NOT detect orphaned pre_commit")
    print("Full output sample:")
    print(output[:1000])

# Also verify the artifact structure
with zipfile.ZipFile(test_path, "r") as zf:
    steps_data = zf.read("steps.jsonl").decode("utf-8")
    steps = [json.loads(l) for l in steps_data.strip().split("\n") if l.strip()]
    pre_commits = [s for s in steps if s["kind"] == "llm.pre_commit"]
    requests = [s for s in steps if s["kind"] == "llm.request"]
    responses = [s for s in steps if s["kind"] == "llm.response"]
    print(f"\nSteps: {len(steps)} total, {len(pre_commits)} pre_commit, {len(requests)} requests, {len(responses)} responses")
