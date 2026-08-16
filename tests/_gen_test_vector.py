"""Generate a deterministic .epi test vector and expected canonical hash.
Run: python tests/_gen_test_vector.py
"""
import json, hashlib, tempfile, zipfile, shutil
from pathlib import Path
from epi_core.container import EPIContainer, EPI_CONTAINER_FORMAT_LEGACY
from epi_core.schemas import ManifestModel

TEST_DIR = Path("tests/test_vectors")
TEST_DIR.mkdir(parents=True, exist_ok=True)

workspace = TEST_DIR / "_gen_tmp"
workspace.mkdir(parents=True, exist_ok=True)

steps = json.dumps({
    "kind": "policy.check",
    "content": {"rule_id": "feedback_vector_rule", "result": "passed", "rule": "All vectors must verify."},
    "timestamp": "2025-01-15T00:00:00.000000Z",
    "index": 0,
    "prev_hash": "CHAIN_START",
}, sort_keys=True) + "\n"
(workspace / "steps.jsonl").write_text(steps, encoding="utf-8")
(workspace / "environment.json").write_text(json.dumps({"python": "3.12", "platform": "test"}, sort_keys=True))

manifest = ManifestModel(
    goal="Test vector for cross-environment verification",
    notes="Deterministic offline artifact",
    tags=["test-vector", "offline"],
)
output = TEST_DIR / "canonical_test_vector.epi"
EPIContainer.pack(
    workspace, manifest, output,
    signer_function=None,
    preserve_generated=True,
    container_format=EPI_CONTAINER_FORMAT_LEGACY,
    generate_analysis=False,
)
shutil.rmtree(workspace, ignore_errors=True)

# Compute canonical hash of unsigned manifest
with zipfile.ZipFile(output, "r") as zf:
    manifest_json = json.loads(zf.read("manifest.json"))
    if "signature" in manifest_json:
        del manifest_json["signature"]
    canonical_str = json.dumps(manifest_json, sort_keys=True)
    canonical_hash = hashlib.sha256(canonical_str.encode()).hexdigest()

expected = {
    "workflow_id": str(manifest.workflow_id),
    "canonical_json": canonical_str,
    "canonical_hash": canonical_hash,
}
(Path(TEST_DIR) / "canonical_expected.json").write_text(json.dumps(expected, indent=2))
print(f"Generated: {output}")
print(f"canonical_hash: {canonical_hash}")
print(f"workflow_id: {manifest.workflow_id}")
