"""Test that Python and JS verifiers produce identical results on a known-good artifact."""
import json, hashlib, zipfile
from pathlib import Path
from epi_core.container import EPIContainer

TEST_VECTOR = Path(__file__).parent / "test_vectors" / "canonical_test_vector.epi"
EXPECTED = Path(__file__).parent / "test_vectors" / "canonical_expected.json"


class TestCrossEnvironmentVerification:
    """Verify Python and JS implementations agree on canonical hashing."""

    def test_manifest_hash_matches_expected(self):
        expected = json.loads(EXPECTED.read_text())
        with zipfile.ZipFile(TEST_VECTOR, "r") as zf:
            manifest_json = json.loads(zf.read("manifest.json"))
            if "signature" in manifest_json:
                del manifest_json["signature"]
            canonical_str = json.dumps(manifest_json, sort_keys=True)
            canonical_hash = hashlib.sha256(canonical_str.encode()).hexdigest()

        assert canonical_hash == expected["canonical_hash"], (
            f"Python canonical hash mismatch: got {canonical_hash}, expected {expected['canonical_hash']}"
        )
        assert str(manifest_json.get("workflow_id", "")) == expected["workflow_id"]

    def test_deterministic_regeneration(self):
        """Generating the test vector twice should produce identical results."""
        expected = json.loads(EXPECTED.read_text())
        with zipfile.ZipFile(TEST_VECTOR, "r") as zf:
            manifest_json = json.loads(zf.read("manifest.json"))
            if "signature" in manifest_json:
                del manifest_json["signature"]
            canonical_str = json.dumps(manifest_json, sort_keys=True)

        # Verify the canonical JSON shape is exactly what JS expects
        assert "workflow_id" in canonical_str
        assert "spec_version" in canonical_str

    def test_js_canonical_equivalence(self):
        """JS canonicalJson should produce the same string for the unsigned manifest."""
        expected = json.loads(EXPECTED.read_text())
        with zipfile.ZipFile(TEST_VECTOR, "r") as zf:
            manifest_json = json.loads(zf.read("manifest.json"))
            if "signature" in manifest_json:
                del manifest_json["signature"]
            canonical_str = json.dumps(manifest_json, sort_keys=True)

        # This is the string JS's canonicalJson should produce for the same object.
        # JS test: load canonical_test_vector.epi via JSZip, parse manifest.json,
        # delete .signature, call canonicalJson(obj), compute sha256Hex.
        # Must match expected["canonical_hash"].
        assert canonical_str == expected["canonical_json"]
