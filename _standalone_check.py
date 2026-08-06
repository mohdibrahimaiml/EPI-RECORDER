from epi_core.container import EPIContainer
from epi_core.trust import verify_embedded_manifest_signature
from pathlib import Path
import re, json, base64, zipfile, tempfile, shutil

epi = Path("epi-recordings/demo_refund.epi")

# Check standalone export HTML (used by export-html)
html = open("_test_standalone.html", "r", encoding="utf-8").read()

# Find preloaded data in standalone
m = re.search(r'id="epi-preloaded-cases"[^>]*>([^<]+)', html)
if m:
    data = json.loads(m.group(1))
    case = data["cases"][0]
    sig = case.get("signature", {})
    man = case.get("manifest", {})
    with open("_standalone_check.txt", "w") as out:
        out.write("=== STANDALONE EXPORT HTML ===\n")
        out.write(f"  signature.valid: {sig.get('valid')} (type={type(sig.get('valid')).__name__})\n")
        out.write(f"  manifest.signature: {bool(man.get('signature'))}\n")
    
    print("Standalone signature.valid:", sig.get("valid"))

# Verify the invariant: tampered manifest -> _bake_signature_status returns False
# (Can't actually tamper, but test the edge case with unsigned manifest)
from epi_core.container import _bake_signature_status
m = EPIContainer.read_manifest(epi)
valid_result = _bake_signature_status(m)
print(f"_bake_signature_status(valid): {valid_result}")

# Test with no manifest (no signature)
from epi_core.schemas import ManifestModel
dummy = ManifestModel()
dummy.signature = None
dummy.public_key = None
null_result = _bake_signature_status(dummy)
print(f"_bake_signature_status(no sig): {null_result}")
