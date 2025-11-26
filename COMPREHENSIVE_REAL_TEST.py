"""
COMPREHENSIVE REAL TESTING - NO HALLUCINATIONS
Tests every aspect of epi-recorder with actual verification
"""
import sys
import time
import json
import zipfile
from pathlib import Path

print("=" * 80)
print("COMPREHENSIVE EPI-RECORDER TESTING")
print("Testing every function with real verification")
print("=" * 80)

test_results = []
failed_tests = []

def test(name, func):
    """Run a test and record results"""
    print(f"\n[TEST] {name}")
    try:
        func()
        print(f"  [PASS] {name}")
        test_results.append((name, "PASS", None))
        return True
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        import traceback
        tb = traceback.format_exc()
        test_results.append((name, "FAIL", str(e)))
        failed_tests.append((name, e, tb))
        return False

# ============================================================================
# TEST 1: Module Imports
# ============================================================================
def test_imports():
    """Verify all modules can be imported"""
    from epi_recorder import record, EpiRecorderSession
    from epi_core.container import EPIContainer
    from epi_core.trust import sign_manifest, verify_signature
    from epi_core.redactor import Redactor
    from epi_core.schemas import ManifestModel, StepModel
    from epi_cli.keys import KeyManager
    from epi_recorder.patcher import patch_openai
    from epi_recorder.environment import capture_environment
    assert record is not None
    assert EPIContainer is not None

test("1. Module Imports", test_imports)

# ============================================================================
# TEST 2: File Creation with record()
# ============================================================================
def test_record_function():
    """Test file creation using record() function"""
    from epi_recorder import record
    
    test_file = Path(f"test_record_{int(time.time())}.epi")
    
    with record(test_file, goal="Test Goal", metadata_tags=["test"]) as session:
        session.log_step("test.step", {"data": "value"})
    
    # Verify file exists
    assert test_file.exists(), f"File {test_file} was not created"
    
    # Verify file size
    size = test_file.stat().st_size
    assert size > 1000, f"File too small: {size} bytes"
    
    # Verify it's a valid ZIP
    with zipfile.ZipFile(test_file) as zf:
        files = zf.namelist()
        assert "manifest.json" in files, "manifest.json missing"
        assert "steps.jsonl" in files, "steps.jsonl missing"
        assert "viewer.html" in files, "viewer.html missing"
    
    test_file.unlink()

test("2. File Creation with record()", test_record_function)

# ============================================================================
# TEST 3: File Creation with EpiRecorderSession
# ============================================================================
def test_session_class():
    """Test file creation using EpiRecorderSession class"""
    from epi_recorder import EpiRecorderSession
    
    test_file = Path(f"test_session_{int(time.time())}.epi")
    
    with EpiRecorderSession(test_file, goal="Session Test") as session:
        session.log_step("session.test", {"key": "value"})
    
    assert test_file.exists(), f"File {test_file} was not created"
    assert test_file.stat().st_size > 1000, "File too small"
    
    test_file.unlink()

test("3. File Creation with EpiRecorderSession", test_session_class)

# ============================================================================
# TEST 4: Auto-Signing (Critical Fix)
# ============================================================================
def test_auto_signing():
    """Test auto-signing functionality"""
    from epi_recorder import record
    from epi_core.container import EPIContainer
    
    test_file = Path(f"test_signed_{int(time.time())}.epi")
    
    with record(test_file, auto_sign=True, goal="Signing Test") as session:
        session.log_step("sign.test", {"signed": True})
    
    # Verify file exists
    assert test_file.exists(), "Signed file was not created"
    
    # Read and verify manifest
    manifest = EPIContainer.read_manifest(test_file)
    assert manifest.signature is not None, "File not signed"
    assert manifest.signature.startswith("ed25519:"), f"Invalid signature format: {manifest.signature}"
    
    # Verify signature has content after prefix
    sig_parts = manifest.signature.split(":")
    assert len(sig_parts) >= 3, "Signature missing components"
    
    test_file.unlink()

test("4. Auto-Signing (Critical Fix)", test_auto_signing)

# ============================================================================
# TEST 5: Path Resolution (Critical Fix)
# ============================================================================
def test_path_resolution():
    """Test that paths are respected (not moved to epi-recordings/)"""
    from epi_recorder import record
    
    # Test with just filename
    test_file = Path(f"test_path_{int(time.time())}.epi")
    
    with record(test_file, goal="Path Test", auto_sign=False) as session:
        session.log_step("path.test", {"test": True})
    
    # File should be in current directory, not epi-recordings/
    assert test_file.exists(), f"File not in current directory: {test_file}"
    assert not Path("epi-recordings") / test_file.name in Path("epi-recordings").glob("*.epi") if Path("epi-recordings").exists() else True
    
    test_file.unlink()

test("5. Path Resolution (Critical Fix)", test_path_resolution)

# ============================================================================
# TEST 6: Artifact Logging
# ============================================================================
def test_artifact_logging():
    """Test artifact file logging"""
    from epi_recorder import record
    
    # Create test artifact
    artifact = Path("test_artifact_real.txt")
    artifact.write_text("This is test content for artifact")
    
    test_file = Path(f"test_artifact_{int(time.time())}.epi")
    
    with record(test_file, auto_sign=False) as session:
        session.log_artifact(artifact)
    
    assert test_file.exists(), "File not created"
    
    # Verify artifact is in ZIP
    with zipfile.ZipFile(test_file) as zf:
        files = zf.namelist()
        artifact_found = any('test_artifact_real.txt' in f for f in files)
        assert artifact_found, f"Artifact not in ZIP. Files: {files}"
    
    test_file.unlink()
    artifact.unlink()

test("6. Artifact Logging", test_artifact_logging)

# ============================================================================
# TEST 7: Redaction
# ============================================================================
def test_redaction():
    """Test sensitive data redaction"""
    from epi_core.redactor import Redactor
    
    r = Redactor()
    
    # Test with realistic fake keys
    fake_openai = "sk-proj-" + "a" * 48
    fake_github = "ghp_" + "b" * 36
    sensitive = f"API key: {fake_openai}, Token: {fake_github}"
    
    redacted, count = r.redact(sensitive)
    
    assert fake_openai not in redacted, "OpenAI key not redacted"
    assert fake_github not in redacted, "GitHub token not redacted"
    assert count >= 2, f"Expected 2+ redactions, got {count}"
    assert "***REDACTED***" in redacted, "Redaction placeholder not found"

test("7. Redaction", test_redaction)

# ============================================================================
# TEST 8: File Integrity Verification
# ============================================================================
def test_integrity():
    """Test file integrity verification"""
    from epi_recorder import record
    from epi_core.container import EPIContainer
    
    test_file = Path(f"test_integrity_{int(time.time())}.epi")
    
    with record(test_file, auto_sign=False) as session:
        session.log_step("integrity.test", {"data": "test"})
    
    # Verify integrity
    integrity_ok, issues = EPIContainer.verify_integrity(test_file)
    assert integrity_ok, f"Integrity check failed: {issues}"
    
    test_file.unlink()

test("8. File Integrity Verification", test_integrity)

# ============================================================================
# TEST 9: Metadata Handling
# ============================================================================
def test_metadata():
    """Test metadata in manifest"""
    from epi_recorder import record
    from epi_core.container import EPIContainer
    
    test_file = Path(f"test_metadata_{int(time.time())}.epi")
    
    with record(test_file, 
                goal="Test Goal",
                notes="Test Notes",
                metrics={"accuracy": 0.95},
                approved_by="tester@test.com",
                metadata_tags=["tag1", "tag2"],
                auto_sign=False) as session:
        session.log_step("test", {"x": 1})
    
    # Read manifest
    manifest = EPIContainer.read_manifest(test_file)
    
    assert manifest.metadata is not None, "Metadata missing"
    assert manifest.metadata.goal == "Test Goal", "Goal not saved"
    assert manifest.metadata.notes == "Test Notes", "Notes not saved"
    assert manifest.metadata.metrics == {"accuracy": 0.95}, "Metrics not saved"
    assert manifest.metadata.approved_by == "tester@test.com", "approved_by not saved"
    assert manifest.metadata.tags == ["tag1", "tag2"], "Tags not saved"
    
    test_file.unlink()

test("9. Metadata Handling", test_metadata)

# ============================================================================
# TEST 10: Steps Recording
# ============================================================================
def test_steps_recording():
    """Test that steps are properly recorded"""
    from epi_recorder import record
    
    test_file = Path(f"test_steps_{int(time.time())}.epi")
    
    with record(test_file, auto_sign=False) as session:
        session.log_step("step1", {"data": "first"})
        session.log_step("step2", {"data": "second"})
        session.log_step("step3", {"data": "third"})
    
    # Read steps from ZIP
    with zipfile.ZipFile(test_file) as zf:
        steps_data = zf.read("steps.jsonl").decode('utf-8')
    
    # Count steps
    lines = [line for line in steps_data.strip().split('\n') if line]
    assert len(lines) >= 3, f"Expected 3+ steps, got {len(lines)}"
    
    # Verify step content
    step1 = json.loads(lines[0])
    assert step1['kind'] == 'step1', "Step kind mismatch"
    assert step1['content']['data'] == 'first', "Step content mismatch"
    
    test_file.unlink()

test("10. Steps Recording", test_steps_recording)

# ============================================================================
# TEST 11: Environment Capture
# ============================================================================
def test_environment_capture():
    """Test environment capture"""
    from epi_recorder.environment import capture_environment
    
    env = capture_environment()
    
    assert "os" in env, "OS info missing"
    assert "python" in env, "Python info missing"
    assert "packages" in env, "Packages info missing"
    assert env["python"]["version"], "Python version missing"

test("11. Environment Capture", test_environment_capture)

# ============================================================================
# TEST 12: KeyManager
# ============================================================================
def test_keymanager():
    """Test KeyManager functionality"""
    from epi_cli.keys import KeyManager
    
    km = KeyManager()
    assert km.keys_dir.exists(), "Keys directory not created"
    
    # Check if we can generate a test key
    test_key_name = f"test_key_{int(time.time())}"
    km.generate_keypair(test_key_name)
    
    assert km.has_key(test_key_name), "Test key not generated"
    
    # Load the key
    private_key = km.load_private_key(test_key_name)
    assert private_key is not None, "Could not load private key"
    
    # Cleanup
    (km.keys_dir / f"{test_key_name}.key").unlink()
    (km.keys_dir / f"{test_key_name}.pub").unlink()

test("12. KeyManager", test_keymanager)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

passed = sum(1 for _, status, _ in test_results if status == "PASS")
failed = sum(1 for _, status, _ in test_results if status == "FAIL")

print(f"\nTotal Tests: {len(test_results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

if failed > 0:
    print("\n" + "=" * 80)
    print("FAILED TESTS DETAILS:")
    print("=" * 80)
    for name, error, traceback in failed_tests:
        print(f"\n{name}:")
        print(f"  Error: {error}")
        print(f"  Traceback:\n{traceback}")

print("\n" + "=" * 80)
if failed == 0:
    print("ALL TESTS PASSED - Package is production-ready!")
    print("=" * 80)
    sys.exit(0)
else:
    print(f"FAILED - {failed} test(s) failed")
    print("=" * 80)
    sys.exit(1)
